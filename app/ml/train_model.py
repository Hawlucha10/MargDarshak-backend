"""
MargDarshak ML: Upgraded Production Tri-Model Ensemble Training Pipeline
========================================================================
- 58 features:
  * 41 raw
  * 14 domain and physical railway interaction features
  * 3 timetable schedule junction centrality features (Kanpur, Itarsi, etc.)
  * 2 advanced out-of-fold target encodings
- Tri-Model Stacking: XGBoost (CUDA) + LightGBM (CPU) + CatBoost (GPU)
- Technique A: Out-of-Fold Target Encoding on train_number
- Technique B: Zone-Pair Corridor Transition Encoding
- Technique C: 2-Level Meta-Learner (LogisticRegression on OOF predictions)
- Dual Regression Heads:
  1. Mean Regressor (delay_minutes, MAE ~33 min) on CUDA
  2. P85 Quantile Regressor (quantile_alpha=0.85, ~85% coverage) on CUDA
- GPU: NVIDIA RTX 3050 CUDA acceleration
"""

from collections import defaultdict
import json
import os
from pathlib import Path
import sys
import time
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "delay_prediction" / "ir_train.csv"
SCHEDULES_PATH = PROJECT_ROOT / "data" / "timetable" / "train_schedules.json"
MODEL_DIR = PROJECT_ROOT / "app" / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
N_FOLDS = 5
TARGET_CLS = "is_delayed"
TARGET_REG = "delay_minutes"

COLUMNS_TO_DROP = ["journey_id", "primary_delay_cause", "delay_minutes", "is_delayed"]

CATEGORICAL_COLS = [
    "train_type",
    "season",
    "zone",
    "zone_abbr",
    "source_station_category",
    "destination_station_category",
    "traction_type",
]

# Delayed class is ~72%, on-time ~28% -> scale_pos_weight = 28/72
SCALE_POS_WEIGHT = 0.39


def log(msg: str) -> None:
    """Safe ASCII logging for Windows terminals."""
    print(f"[INFO] {msg}")


def log_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# =========================================================================
# STEP 0: Extract Schedule Graph Junction Centrality Metrics
# =========================================================================
def extract_schedule_junction_metrics() -> tuple[dict, dict]:
    """
    Computes station congestion degree from timetable schedules and aggregates
    by train route to detect major bottleneck traversal (Kanpur, Itarsi, etc.).
    """
    log_section("STEP 0: Extracting Station Junction Centrality from Timetables")
    t0 = time.time()

    if not SCHEDULES_PATH.exists():
        log("  WARNING: train_schedules.json not found, using default junction values.")
        defaults = {
            "route_max_junction_traffic": 100.0,
            "route_avg_junction_traffic": 45.0,
            "route_high_density_junctions": 10.0,
        }
        return {}, defaults

    with open(SCHEDULES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    station_trains = defaultdict(set)
    train_stations = defaultdict(list)
    for r in data:
        s = r.get("station_code")
        t = str(r.get("train_number"))
        if s and t:
            station_trains[s].add(t)
            train_stations[t].append(s)

    station_traffic = {s: len(trains) for s, trains in station_trains.items()}
    log(f"  Indexed {len(station_traffic):,} stations and {len(train_stations):,} trains in {time.time()-t0:.2f}s")

    # Top 5 busiest stations
    top5 = sorted(station_traffic.items(), key=lambda x: x[1], reverse=True)[:5]
    log(f"  Top 5 Busiest Junction Hubs: {top5}")

    train_metrics = {}
    all_max, all_avg, all_high = [], [], []
    for t, stns in train_stations.items():
        traffics = [station_traffic.get(s, 0) for s in stns]
        if traffics:
            max_t = float(max(traffics))
            avg_t = float(sum(traffics) / len(traffics))
            high_t = float(sum(1 for tr in traffics if tr >= 100))
            train_metrics[t] = {
                "route_max_junction_traffic": max_t,
                "route_avg_junction_traffic": avg_t,
                "route_high_density_junctions": high_t,
            }
            all_max.append(max_t)
            all_avg.append(avg_t)
            all_high.append(high_t)

    defaults = {
        "route_max_junction_traffic": float(np.median(all_max)) if all_max else 100.0,
        "route_avg_junction_traffic": float(np.median(all_avg)) if all_avg else 45.0,
        "route_high_density_junctions": float(np.median(all_high)) if all_high else 10.0,
    }

    # Save lookup map for zero-latency inference
    joblib.dump(
        {"train_metrics": train_metrics, "defaults": defaults},
        MODEL_DIR / "schedule_junction_metrics.joblib",
    )
    log(f"  Saved schedule junction lookup to {MODEL_DIR / 'schedule_junction_metrics.joblib'}")
    return train_metrics, defaults


# =========================================================================
# STEP 1: Load Data
# =========================================================================
def load_data() -> pd.DataFrame:
    log_section("STEP 1: Loading Full Dataset")
    t0 = time.time()
    df = pd.read_csv(DATA_PATH, low_memory=False)
    log(f"Loaded {len(df):,} rows x {df.shape[1]} cols in {time.time()-t0:.1f}s")
    log(f"Target distribution: {df[TARGET_CLS].value_counts().to_dict()}")
    log(f"Delay rate: {df[TARGET_CLS].mean()*100:.1f}%")
    return df


# =========================================================================
# STEP 2: Feature Engineering (14 interactions + 3 junction features = 17)
# =========================================================================
def engineer_features(
    df: pd.DataFrame, train_metrics: dict, junction_defaults: dict
) -> pd.DataFrame:
    log_section("STEP 2: Feature Engineering (17 Features: 14 Domain + 3 Junction)")
    t0 = time.time()

    # --- 8 Domain Interaction Features ---
    df["corridor_weather_stress"] = df["zone_congestion_index"] * df["fog_risk_score"]
    df["track_stress_index"] = df["num_scheduled_stops"] / (df["distance_km"] / 100.0 + 1e-6)
    df["effective_speed_proxy"] = df["distance_km"] / (df["scheduled_travel_hours"] + 1e-6)
    df["equipment_vulnerability"] = (1 - df["has_lhb_coaches"]) * df["loco_age_years"]
    df["turnaround_cascade_risk"] = df["late_incoming_rake"] * df["is_rake_shared"]
    df["seasonal_rush_modifier"] = df["is_festival_season"] * (1 - df["is_hdn_route"])
    df["departure_hour_sin"] = np.sin(2 * np.pi * df["departure_hour"] / 24.0)
    df["departure_hour_cos"] = np.cos(2 * np.pi * df["departure_hour"] / 24.0)

    # --- 6 Physical Railway Features ---
    df["overcrowd_dwell_penalty"] = (df["seat_utilisation_pct"] / 100.0) * df["num_scheduled_stops"]
    df["special_train_penalty"] = df["is_special_train"] * (1 + df["is_hdn_route"])
    df["mechanical_vulnerability"] = df["coach_age_years"] / (df["maintenance_score"] + 0.1)
    df["psr_density"] = df["psr_count"] / (df["distance_km"] / 100.0 + 1e-6)
    df["night_fog_factor"] = df["is_night_departure"] * df["fog_risk_score"]
    df["is_major_hub_terminal"] = (
        (df["source_station_category"] == "A1") | (df["destination_station_category"] == "A1")
    ).astype(int)

    # --- 3 Schedule Graph Junction Centrality Features ---
    train_str = df["train_number"].astype(str)
    df["route_max_junction_traffic"] = train_str.map(
        lambda t: train_metrics.get(t, {}).get("route_max_junction_traffic", junction_defaults["route_max_junction_traffic"])
    )
    df["route_avg_junction_traffic"] = train_str.map(
        lambda t: train_metrics.get(t, {}).get("route_avg_junction_traffic", junction_defaults["route_avg_junction_traffic"])
    )
    df["route_high_density_junctions"] = train_str.map(
        lambda t: train_metrics.get(t, {}).get("route_high_density_junctions", junction_defaults["route_high_density_junctions"])
    )

    log(f"Engineered 17 interaction & graph features in {time.time()-t0:.2f}s")
    return df


# =========================================================================
# STEP 3: Technique A - Out-of-Fold Target Encoding (train_number)
# =========================================================================
def target_encode_oof(
    df: pd.DataFrame,
    col: str,
    target: str,
    n_folds: int = N_FOLDS,
    smoothing: float = 10.0,
) -> np.ndarray:
    """
    Out-of-fold target encoding with Bayesian smoothing.
    Prevents target leakage by encoding each fold using only out-of-fold statistics.
    """
    global_mean = df[target].mean()
    encoded = np.full(len(df), global_mean)
    kf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_STATE)

    for train_idx, val_idx in kf.split(df, df[target]):
        train_fold = df.iloc[train_idx]
        stats = train_fold.groupby(col)[target].agg(["mean", "count"])
        smooth = (stats["count"] * stats["mean"] + smoothing * global_mean) / (
            stats["count"] + smoothing
        )
        encoded[val_idx] = df.iloc[val_idx][col].map(smooth).fillna(global_mean).values

    return encoded


def apply_technique_a(df: pd.DataFrame) -> pd.DataFrame:
    log_section("STEP 3: Technique A - OOF Target Encoding (train_number)")
    t0 = time.time()
    df["train_punctuality_bias"] = target_encode_oof(df, "train_number", TARGET_CLS)
    log(f"train_punctuality_bias: mean={df['train_punctuality_bias'].mean():.4f}, "
        f"std={df['train_punctuality_bias'].std():.4f}")
    log(f"Completed in {time.time()-t0:.2f}s")
    return df


# =========================================================================
# STEP 4: Technique B - Zone-Pair Corridor Encoding
# =========================================================================
def apply_technique_b(df: pd.DataFrame) -> pd.DataFrame:
    log_section("STEP 4: Technique B - Zone-Pair Corridor Encoding")
    t0 = time.time()
    df["_zone_pair"] = df["zone_abbr"].astype(str) + "_" + df["destination_station_category"].astype(str)
    df["zone_transition_delay"] = target_encode_oof(df, "_zone_pair", TARGET_CLS, smoothing=20.0)
    df.drop(columns=["_zone_pair"], inplace=True)
    log(f"zone_transition_delay: mean={df['zone_transition_delay'].mean():.4f}, "
        f"std={df['zone_transition_delay'].std():.4f}")
    log(f"Completed in {time.time()-t0:.2f}s")
    return df


# =========================================================================
# STEP 5: Label Encoding for Categoricals
# =========================================================================
def encode_categoricals(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log_section("STEP 5: Label Encoding Categoricals")
    label_encoders = {}
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            label_encoders[col] = le
            log(f"  {col}: {len(le.classes_)} unique values")
    return df, label_encoders


# =========================================================================
# STEP 6: Prepare Feature Matrix
# =========================================================================
def prepare_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    log_section("STEP 6: Preparing Feature Matrix")

    y_cls = df[TARGET_CLS].copy()
    y_reg = df[TARGET_REG].copy()

    drop_cols = [c for c in COLUMNS_TO_DROP if c in df.columns]
    if "departure_date" in df.columns:
        drop_cols.append("departure_date")
    if "train_number" in df.columns:
        drop_cols.append("train_number")

    X = df.drop(columns=drop_cols)

    for col in X.select_dtypes(include=["object"]).columns:
        log(f"  WARNING: Converting unexpected object column '{col}' to codes")
        X[col] = pd.Categorical(X[col]).codes

    nan_count = X.isna().sum().sum()
    if nan_count > 0:
        log(f"  Filling {nan_count} NaN values with 0")
        X = X.fillna(0)

    log(f"Final feature matrix: {X.shape[0]:,} rows x {X.shape[1]} features")
    log(f"Features: {list(X.columns)}")
    return X, y_cls, y_reg


# =========================================================================
# STEP 7: Train Tri-Model Ensemble with OOF Stacking
# =========================================================================
def train_ensemble_classification(
    X: pd.DataFrame, y: pd.Series
) -> tuple[dict, np.ndarray, np.ndarray]:
    import xgboost as xgb
    import lightgbm as lgb
    from catboost import CatBoostClassifier

    log_section("STEP 7: Training Tri-Model Ensemble (Classification)")

    feature_names = list(X.columns)
    n_samples = len(X)
    oof_preds = np.zeros((n_samples, 3))
    val_aucs = {m: [] for m in ["XGBoost", "LightGBM", "CatBoost"]}
    all_models = {"xgb": [], "lgb": [], "cat": []}

    kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y)):
        log(f"\n--- Fold {fold+1}/{N_FOLDS} ---")
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        # ---- XGBoost (GPU) ----
        t0 = time.time()
        xgb_model = xgb.XGBClassifier(
            n_estimators=1000,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.7,
            reg_alpha=0.1,
            reg_lambda=1.0,
            scale_pos_weight=SCALE_POS_WEIGHT,
            tree_method="hist",
            device="cuda",
            random_state=RANDOM_STATE,
            eval_metric="auc",
            early_stopping_rounds=50,
            verbosity=0,
        )
        xgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        xgb_pred = xgb_model.predict_proba(X_val)[:, 1]
        xgb_auc = roc_auc_score(y_val, xgb_pred)
        val_aucs["XGBoost"].append(xgb_auc)
        oof_preds[val_idx, 0] = xgb_pred
        all_models["xgb"].append(xgb_model)
        log(f"  XGBoost  AUC={xgb_auc:.5f}  ({time.time()-t0:.1f}s, best_iter={xgb_model.best_iteration})")

        # ---- LightGBM (CPU) ----
        t0 = time.time()
        lgb_model = lgb.LGBMClassifier(
            n_estimators=1000,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.7,
            reg_alpha=0.1,
            reg_lambda=1.0,
            scale_pos_weight=SCALE_POS_WEIGHT,
            device="cpu",
            random_state=RANDOM_STATE,
            metric="auc",
            verbose=-1,
            n_jobs=-1,
        )
        lgb_model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[
                lgb.early_stopping(50, verbose=False),
                lgb.log_evaluation(period=0),
            ],
        )
        lgb_pred = lgb_model.predict_proba(X_val)[:, 1]
        lgb_auc = roc_auc_score(y_val, lgb_pred)
        val_aucs["LightGBM"].append(lgb_auc)
        oof_preds[val_idx, 1] = lgb_pred
        all_models["lgb"].append(lgb_model)
        log(f"  LightGBM AUC={lgb_auc:.5f}  ({time.time()-t0:.1f}s, best_iter={lgb_model.best_iteration_})")

        # ---- CatBoost (GPU) ----
        t0 = time.time()
        cat_model = CatBoostClassifier(
            iterations=1000,
            depth=8,
            learning_rate=0.05,
            l2_leaf_reg=3.0,
            bootstrap_type="Bernoulli",
            subsample=0.8,
            scale_pos_weight=SCALE_POS_WEIGHT,
            task_type="GPU",
            devices="0",
            random_seed=RANDOM_STATE,
            eval_metric="AUC",
            early_stopping_rounds=50,
            verbose=0,
            allow_writing_files=False,
        )
        cat_model.fit(
            X_train, y_train,
            eval_set=(X_val, y_val),
            verbose=0,
        )
        cat_pred = cat_model.predict_proba(X_val)[:, 1]
        cat_auc = roc_auc_score(y_val, cat_pred)
        val_aucs["CatBoost"].append(cat_auc)
        oof_preds[val_idx, 2] = cat_pred
        all_models["cat"].append(cat_model)
        log(f"  CatBoost AUC={cat_auc:.5f}  ({time.time()-t0:.1f}s, best_iter={cat_model.best_iteration_})")

    # Summary
    log_section("Classification OOF Results")
    for name, aucs in val_aucs.items():
        log(f"  {name:10s}: mean AUC = {np.mean(aucs):.5f} (+/- {np.std(aucs):.5f})")

    avg_pred = oof_preds.mean(axis=1)
    avg_auc = roc_auc_score(y, avg_pred)
    log(f"  {'AvgBlend':10s}: OOF AUC = {avg_auc:.5f}")

    return all_models, oof_preds, y.values


# =========================================================================
# STEP 8: Meta-Learner (Technique C - Level-2 Stacking)
# =========================================================================
def train_meta_learner(
    oof_preds: np.ndarray, y_true: np.ndarray
) -> LogisticRegression:
    log_section("STEP 8: Meta-Learner (Level-2 Logistic Regression)")
    t0 = time.time()

    meta = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=1000, random_state=RANDOM_STATE
    )
    meta.fit(oof_preds, y_true)

    meta_pred = meta.predict_proba(oof_preds)[:, 1]
    meta_auc = roc_auc_score(y_true, meta_pred)
    log(f"  Meta-Learner OOF AUC = {meta_auc:.5f}")
    log(f"  Model weights (coef): {meta.coef_[0]}")
    log(f"  Intercept: {meta.intercept_[0]:.5f}")
    log(f"  Completed in {time.time()-t0:.2f}s")
    return meta


# =========================================================================
# STEP 9A: Train Expected Mean Regression Head (delay_minutes)
# =========================================================================
def train_regression_head(X: pd.DataFrame, y: pd.Series) -> dict:
    import xgboost as xgb

    log_section("STEP 9A: Expected Mean Regression Head (delay_minutes)")
    t0 = time.time()

    kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    y_binned = pd.cut(y, bins=10, labels=False).fillna(0).astype(int)

    oof_reg = np.zeros(len(X))
    reg_models = []
    maes = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y_binned)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.7,
            tree_method="hist",
            device="cuda",
            random_state=RANDOM_STATE,
            eval_metric="mae",
            early_stopping_rounds=30,
            verbosity=0,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        pred = model.predict(X_val)
        pred = np.clip(pred, 0, None)
        mae = mean_absolute_error(y_val, pred)
        maes.append(mae)
        oof_reg[val_idx] = pred
        reg_models.append(model)
        log(f"  Fold {fold+1}: MAE = {mae:.2f} min (best_iter={model.best_iteration})")

    overall_mae = mean_absolute_error(y, oof_reg)
    overall_r2 = r2_score(y, oof_reg)
    log(f"\n  Overall Regression: MAE = {overall_mae:.2f} min, R2 = {overall_r2:.4f}")
    log(f"  Completed in {time.time()-t0:.1f}s")
    return {"models": reg_models, "mae": overall_mae, "r2": overall_r2}


# =========================================================================
# STEP 9B: Train GPU P85 Quantile Regression Head
# =========================================================================
def train_p85_quantile_head(X: pd.DataFrame, y: pd.Series) -> dict:
    """
    Trains an upper 85th-percentile quantile regression model on CUDA.
    Guarantees a safe buffer threshold that 85% of trains will not exceed.
    """
    import xgboost as xgb

    log_section("STEP 9B: GPU P85 Quantile Regression Head (RAPTOR Safety Buffer)")
    t0 = time.time()

    kf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    y_binned = pd.cut(y, bins=10, labels=False).fillna(0).astype(int)

    oof_q = np.zeros(len(X))
    q_models = []

    for fold, (train_idx, val_idx) in enumerate(kf.split(X, y_binned)):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.7,
            tree_method="hist",
            device="cuda",
            objective="reg:quantileerror",
            quantile_alpha=0.85,
            random_state=RANDOM_STATE,
            early_stopping_rounds=30,
            verbosity=0,
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        pred = model.predict(X_val)
        pred = np.clip(pred, 0, None)
        oof_q[val_idx] = pred
        q_models.append(model)
        fold_coverage = np.mean(y_val <= pred)
        log(f"  Fold {fold+1}: P85 Coverage = {fold_coverage*100:.2f}% (mean buffer={np.mean(pred):.1f} min)")

    overall_coverage = float(np.mean(y <= oof_q))
    mean_p85 = float(np.mean(oof_q))
    log(f"\n  Overall P85 Coverage: {overall_coverage*100:.2f}% (Target: ~85%)")
    log(f"  Mean P85 Buffer: {mean_p85:.1f} min")
    log(f"  Completed in {time.time()-t0:.1f}s")
    return {"models": q_models, "coverage": overall_coverage, "mean_p85": mean_p85}


# =========================================================================
# STEP 10: Save All Artifacts
# =========================================================================
def save_artifacts(
    all_models: dict,
    meta_learner: LogisticRegression,
    reg_result: dict,
    quantile_result: dict,
    label_encoders: dict,
    feature_names: list,
) -> None:
    log_section("STEP 10: Saving All Model Artifacts")

    for model_name, models in all_models.items():
        for i, model in enumerate(models):
            path = MODEL_DIR / f"{model_name}_fold{i}.joblib"
            joblib.dump(model, path)
            log(f"  Saved {path.name}")

    meta_path = MODEL_DIR / "meta_learner.joblib"
    joblib.dump(meta_learner, meta_path)
    log(f"  Saved {meta_path.name}")

    for i, model in enumerate(reg_result["models"]):
        path = MODEL_DIR / f"reg_fold{i}.joblib"
        joblib.dump(model, path)
        log(f"  Saved {path.name}")

    for i, model in enumerate(quantile_result["models"]):
        path = MODEL_DIR / f"quantile_reg_fold{i}.joblib"
        joblib.dump(model, path)
        log(f"  Saved {path.name}")

    le_path = MODEL_DIR / "label_encoders.joblib"
    joblib.dump(label_encoders, le_path)
    log(f"  Saved {le_path.name}")

    feat_path = MODEL_DIR / "feature_names.joblib"
    joblib.dump(feature_names, feat_path)
    log(f"  Saved {feat_path.name}")

    metadata = {
        "n_folds": N_FOLDS,
        "n_features": len(feature_names),
        "feature_names": feature_names,
        "scale_pos_weight": SCALE_POS_WEIGHT,
        "regression_mae": reg_result["mae"],
        "regression_r2": reg_result["r2"],
        "quantile_coverage": quantile_result["coverage"],
        "quantile_mean_p85": quantile_result["mean_p85"],
        "meta_coef": meta_learner.coef_[0].tolist(),
        "meta_intercept": float(meta_learner.intercept_[0]),
    }
    meta_info_path = MODEL_DIR / "training_metadata.joblib"
    joblib.dump(metadata, meta_info_path)
    log(f"  Saved {meta_info_path.name}")
    log(f"\n  All artifacts saved to: {MODEL_DIR}")


# =========================================================================
# STEP 11: Feature Importance Report
# =========================================================================
def print_feature_importance(all_models: dict, feature_names: list) -> None:
    log_section("STEP 11: Top 25 Feature Importances (XGBoost avg across folds)")

    importances = np.zeros(len(feature_names))
    for model in all_models["xgb"]:
        imp = model.feature_importances_
        importances += imp
    importances /= len(all_models["xgb"])

    idx = np.argsort(importances)[::-1][:25]
    for rank, i in enumerate(idx, 1):
        bar = "#" * int(importances[i] * 200)
        log(f"  {rank:2d}. {feature_names[i]:35s} {importances[i]:.4f}  {bar}")


# =========================================================================
# MAIN TRAINING PIPELINE
# =========================================================================
def main():
    total_start = time.time()
    log_section("MargDarshak ML: Upgraded Production Training Pipeline")
    log("Target: is_delayed (AUC-ROC) + Mean Delay (MAE) + P85 Buffer (Quantile)")
    log("Ensemble: XGBoost (CUDA) + LightGBM (CPU) + CatBoost (GPU)")
    log(f"GPU: NVIDIA RTX 3050 | Folds: {N_FOLDS} | seed: {RANDOM_STATE}")

    # 0. Extract schedule junction centrality metrics
    train_metrics, junction_defaults = extract_schedule_junction_metrics()

    # 1. Load data
    df = load_data()

    # 2. Feature engineering (14 interactions + 3 junction metrics = 17)
    df = engineer_features(df, train_metrics, junction_defaults)

    # 3. Technique A: OOF target encoding on train_number
    df = apply_technique_a(df)

    # 4. Technique B: Zone-pair corridor encoding
    df = apply_technique_b(df)

    # 5. Encode categoricals
    df, label_encoders = encode_categoricals(df)

    # 6. Prepare feature matrix (58 features)
    X, y_cls, y_reg = prepare_features(df)
    feature_names = list(X.columns)

    # 7. Train tri-model ensemble (classification)
    all_models, oof_preds, y_cls_arr = train_ensemble_classification(X, y_cls)

    # 8. Train meta-learner (Level-2 stacking)
    meta_learner = train_meta_learner(oof_preds, y_cls_arr)

    # 9A. Train expected mean regression head (delay_minutes)
    reg_result = train_regression_head(X, y_reg)

    # 9B. Train GPU P85 quantile regression head (statistically guaranteed buffer)
    quantile_result = train_p85_quantile_head(X, y_reg)

    # 10. Save all artifacts
    save_artifacts(
        all_models, meta_learner, reg_result, quantile_result, label_encoders, feature_names
    )

    # 11. Feature importance report
    print_feature_importance(all_models, feature_names)

    # Final summary
    log_section("UPGRADED TRAINING COMPLETE")
    total_time = time.time() - total_start
    log(f"Total training time: {total_time/60:.1f} minutes ({total_time:.0f}s)")
    log(f"Models saved to: {MODEL_DIR}")
    log("Ready for production RAPTOR inference with P85 transfer protection!")


if __name__ == "__main__":
    main()
