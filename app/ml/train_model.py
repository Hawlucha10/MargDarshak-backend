"""
XGBoost Train Delay Model Training Script
Trains delay prediction model on ir_train.csv using NVIDIA GPU acceleration (CUDA).
"""

import os
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Set project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "delay_prediction" / "ir_train.csv"
MODEL_DIR = PROJECT_ROOT / "app" / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODEL_OUT = MODEL_DIR / "delay_model_v1.json"


def train_delay_model(sample_size: int = 250000):
    """
    Trains an XGBoost regressor predicting arrival delay in minutes.
    Utilizes NVIDIA GPU acceleration if available.
    """
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score

    print("==================================================")
    print("🚀 MargDarshak ML: XGBoost Delay Training Pipeline")
    print("==================================================")

    if not DATA_PATH.exists():
        print(f"❌ Error: Training data not found at {DATA_PATH}")
        return

    print(f"Loading {sample_size} records from {DATA_PATH}...")
    t0 = time.time()
    
    # Load dataset sample
    df = pd.read_csv(DATA_PATH, nrows=sample_size, low_memory=False)
    print(f"Loaded dataset in {round(time.time() - t0, 2)}s. Shape: {df.shape}")

    # Selected features for delay prediction
    feature_cols = [
        "month",
        "day_of_week",
        "departure_hour",
        "is_weekend",
        "is_night_departure",
        "is_peak_hour",
        "is_festival_season",
        "is_monsoon_season",
        "is_fog_risk",
        "fog_risk_score",
        "zone_fog_index",
        "zone_congestion_index",
        "season_severity_score",
        "distance_km",
        "num_scheduled_stops",
        "track_doubled",
        "is_hdn_route",
        "is_electrified",
        "has_lhb_coaches",
        "late_incoming_rake",
    ]

    target_col = "delay_minutes"

    # Clean & fill missing numeric values
    for col in feature_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    df[target_col] = pd.to_numeric(df[target_col], errors="coerce").fillna(0)

    X = df[feature_cols].values
    y = df[target_col].values

    # Train/validation split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Check GPU availability for XGBoost
    params = {
        "objective": "reg:squarederror",
        "eval_metric": "mae",
        "learning_rate": 0.08,
        "max_depth": 7,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": 42,
    }

    try:
        # Attempt NVIDIA GPU training
        params["tree_method"] = "hist"
        params["device"] = "cuda"
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=feature_cols)
        print("⚡ Utilizing NVIDIA GPU (CUDA acceleration enabled)...")
    except Exception as e:
        print(f"⚠️ Falling back to CPU: {e}")
        params["device"] = "cpu"
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=feature_cols)
        dval = xgb.DMatrix(X_val, label=y_val, feature_names=feature_cols)

    evals = [(dtrain, "train"), (dval, "val")]
    
    t_train = time.time()
    print("Training XGBoost model for 100 boosting rounds...")
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=100,
        evals=evals,
        verbose_eval=20,
    )
    print(f"✅ Training completed in {round(time.time() - t_train, 2)}s!")

    # Evaluation
    preds = model.predict(dval)
    mae = mean_absolute_error(y_val, preds)
    r2 = r2_score(y_val, preds)
    print(f"\n📊 Validation Results:")
    print(f"   • Mean Absolute Error (MAE): {round(mae, 2)} minutes")
    print(f"   • R2 Score: {round(r2, 4)}")

    # Save compiled model
    model.save_model(str(MODEL_OUT))
    print(f"\n💾 Model successfully saved to: {MODEL_OUT}")


if __name__ == "__main__":
    train_delay_model()
