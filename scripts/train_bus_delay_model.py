"""
Bus Delay Model Trainer
Trains Gradient Boosted models on the 30,000 synthetic bus delay records from PostgreSQL:
  1. Classifier: P(Delayed) -> ROC-AUC, Accuracy, Precision, Recall, F1
  2. Regressor: delay_minutes -> MAE, RMSE, R2, P85 Quantile Coverage
Saves artifacts to app/ml/models/bus_delay_model.joblib
"""

import asyncio
import asyncpg
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
)
import xgboost as xgb

DB_DSN = "postgresql://margdarshak:changeme_in_production@localhost:5432/margdarshak"
MODEL_DIR = Path(__file__).resolve().parent.parent / "app" / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


async def load_data():
    conn = await asyncpg.connect(DB_DSN)
    rows = await conn.fetch("""
        SELECT
            operator_type, bus_type, route_distance_km, month,
            day_of_week, departure_hour, is_highway, is_urban_stretch,
            is_monsoon, is_fog_risk, traffic_congestion_index,
            delay_minutes, is_delayed
        FROM bus_delay_records
    """)
    await conn.close()
    return pd.DataFrame([dict(r) for r in rows])


def train():
    print("[1/4] Loading bus delay records from database...")
    df = asyncio.run(load_data())
    print(f"  -> Loaded {len(df):,} records")

    # Feature engineering
    le_op = LabelEncoder()
    df["operator_type_enc"] = le_op.fit_transform(df["operator_type"].fillna("STATE_RTC"))

    le_bt = LabelEncoder()
    df["bus_type_enc"] = le_bt.fit_transform(df["bus_type"].fillna("ORDINARY"))

    df["is_highway"] = df["is_highway"].astype(int)
    df["is_urban_stretch"] = df["is_urban_stretch"].astype(int)
    df["is_monsoon"] = df["is_monsoon"].astype(int)
    df["is_fog_risk"] = df["is_fog_risk"].astype(int)
    df["traffic_congestion_index"] = df["traffic_congestion_index"].astype(float)
    df["route_distance_km"] = df["route_distance_km"].astype(float)

    # Congestion x distance interaction
    df["congestion_distance_stress"] = df["traffic_congestion_index"] * (df["route_distance_km"] / 100.0)
    df["peak_hour"] = df["departure_hour"].isin([8, 9, 17, 18, 19, 20]).astype(int)

    feature_cols = [
        "operator_type_enc", "bus_type_enc", "route_distance_km",
        "month", "day_of_week", "departure_hour", "is_highway",
        "is_urban_stretch", "is_monsoon", "is_fog_risk",
        "traffic_congestion_index", "congestion_distance_stress", "peak_hour"
    ]

    X = df[feature_cols]
    y_cls = df["is_delayed"].astype(int)
    y_reg = df["delay_minutes"].astype(float)

    X_train, X_test, y_cls_train, y_cls_test, y_reg_train, y_reg_test = train_test_split(
        X, y_cls, y_reg, test_size=0.2, random_state=42, stratify=y_cls
    )

    print("[2/4] Training XGBoost Classification Head (P(Delayed))...")
    clf = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="auc",
        tree_method="hist",
    )
    clf.fit(X_train, y_cls_train)

    cls_probs = clf.predict_proba(X_test)[:, 1]
    cls_preds = (cls_probs >= 0.5).astype(int)

    auc = roc_auc_score(y_cls_test, cls_probs)
    acc = accuracy_score(y_cls_test, cls_preds)
    prec = precision_score(y_cls_test, cls_preds)
    rec = recall_score(y_cls_test, cls_preds)
    f1 = f1_score(y_cls_test, cls_preds)

    print("\n" + "="*50)
    print("  BUS CLASSIFICATION METRICS")
    print("="*50)
    print(f"  ROC-AUC Score:      {auc:.4f}")
    print(f"  Accuracy:           {acc * 100:.2f}%")
    print(f"  Precision:          {prec:.4f}")
    print(f"  Recall:             {rec:.4f}")
    print(f"  F1-Score:           {f1:.4f}")

    print("\n[3/4] Training XGBoost Mean & P85 Quantile Regression Heads...")
    reg = xgb.XGBRegressor(
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        tree_method="hist",
    )
    reg.fit(X_train, y_reg_train)
    reg_preds = np.clip(reg.predict(X_test), 0, None)

    mae = mean_absolute_error(y_reg_test, reg_preds)
    rmse = root_mean_squared_error(y_reg_test, reg_preds)
    r2 = r2_score(y_reg_test, reg_preds)

    # P85 Quantile Regressor
    q_reg = xgb.XGBRegressor(
        objective="reg:quantileerror",
        quantile_alpha=0.85,
        n_estimators=150,
        max_depth=5,
        learning_rate=0.08,
        random_state=42,
        tree_method="hist",
    )
    q_reg.fit(X_train, y_reg_train)
    q_preds = np.clip(q_reg.predict(X_test), 0, None)
    coverage = np.mean(y_reg_test.values <= q_preds)

    print("\n" + "="*50)
    print("  BUS REGRESSION & QUANTILE METRICS")
    print("="*50)
    print(f"  MAE (Mean Absolute Error): {mae:.2f} minutes")
    print(f"  RMSE:                      {rmse:.2f} minutes")
    print(f"  R2 Score:                  {r2:.4f}")
    print(f"  P85 Quantile Coverage:     {coverage * 100:.2f}%")

    print("\n[4/4] Saving artifacts to disk...")
    artifact = {
        "classifier": clf,
        "regressor": reg,
        "quantile_regressor": q_reg,
        "feature_cols": feature_cols,
        "label_encoders": {"operator_type": le_op, "bus_type": le_bt},
        "metrics": {
            "auc": float(auc),
            "accuracy": float(acc),
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "mae": float(mae),
            "rmse": float(rmse),
            "r2": float(r2),
            "p85_coverage": float(coverage),
        },
    }
    joblib.dump(artifact, MODEL_DIR / "bus_delay_model.joblib")
    print(f"  -> Saved {MODEL_DIR / 'bus_delay_model.joblib'}")


if __name__ == "__main__":
    train()
