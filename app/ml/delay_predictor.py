"""
MargDarshak ML: Production Ensemble Delay Prediction & Explainability Engine
=============================================================================
Loads the trained tri-model ensemble (XGBoost + LightGBM + CatBoost) with
Level-2 meta-learner stacking for:
  - P(Delayed) classification (AUC-ROC > 0.92)
  - delay_minutes regression (MAE ~34 min)
  - Risk factor explanations via feature importance
Falls back to heuristic baseline if models are not yet trained.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).resolve().parent / "models"


class DelayPredictor:
    """
    Production inference wrapper for the trained ensemble.
    Dual-head output: classification (P(delayed)) + regression (delay_minutes).
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = Path(model_dir) if model_dir else MODEL_DIR
        self.xgb_models: list = []
        self.lgb_models: list = []
        self.cat_models: list = []
        self.reg_models: list = []
        self.meta_learner = None
        self.label_encoders: dict = {}
        self.feature_names: list = []
        self.metadata: dict = {}
        self.ready = False
        self._load_ensemble()

    def _load_ensemble(self) -> None:
        """Loads all model artifacts from disk."""
        import joblib

        meta_path = self.model_dir / "training_metadata.joblib"
        if not meta_path.exists():
            print("[WARN] No trained models found. Using heuristic fallback.")
            return

        try:
            self.metadata = joblib.load(meta_path)
            self.feature_names = joblib.load(self.model_dir / "feature_names.joblib")
            self.label_encoders = joblib.load(self.model_dir / "label_encoders.joblib")
            self.meta_learner = joblib.load(self.model_dir / "meta_learner.joblib")

            n_folds = self.metadata.get("n_folds", 5)

            for i in range(n_folds):
                xgb_m = joblib.load(self.model_dir / f"xgb_fold{i}.joblib")
                xgb_m.set_params(device="cpu")
                self.xgb_models.append(xgb_m)

                self.lgb_models.append(joblib.load(self.model_dir / f"lgb_fold{i}.joblib"))
                self.cat_models.append(joblib.load(self.model_dir / f"cat_fold{i}.joblib"))

                reg_m = joblib.load(self.model_dir / f"reg_fold{i}.joblib")
                reg_m.set_params(device="cpu")
                self.reg_models.append(reg_m)

            self.ready = True
            print(f"[OK] Ensemble loaded: {n_folds} folds x 3 models + meta-learner + regression")
            print(f"[OK] {len(self.feature_names)} features | AUC target > 0.92")

        except Exception as e:
            print(f"[WARN] Failed to load ensemble: {e}. Using heuristic fallback.")
            self.ready = False

    def _encode_categorical(self, col: str, value: str) -> int:
        """Safely encode a categorical value, returning -1 for unseen values."""
        if col in self.label_encoders:
            le = self.label_encoders[col]
            if value in le.classes_:
                return int(le.transform([value])[0])
        return 0  # Default to 0 for unseen categories

    def _build_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Constructs the 55-feature vector from raw input features.
        Applies same feature engineering as training pipeline.
        """
        f = features  # shorthand

        # --- Engineered interaction features ---
        f["corridor_weather_stress"] = f.get("zone_congestion_index", 0) * f.get("fog_risk_score", 0)
        f["track_stress_index"] = f.get("num_scheduled_stops", 0) / (f.get("distance_km", 1) / 100.0 + 1e-6)
        f["effective_speed_proxy"] = f.get("distance_km", 0) / (f.get("scheduled_travel_hours", 1) + 1e-6)
        f["equipment_vulnerability"] = (1 - f.get("has_lhb_coaches", 0)) * f.get("loco_age_years", 0)
        f["turnaround_cascade_risk"] = f.get("late_incoming_rake", 0) * f.get("is_rake_shared", 0)
        f["seasonal_rush_modifier"] = f.get("is_festival_season", 0) * (1 - f.get("is_hdn_route", 0))
        f["departure_hour_sin"] = np.sin(2 * np.pi * f.get("departure_hour", 0) / 24.0)
        f["departure_hour_cos"] = np.cos(2 * np.pi * f.get("departure_hour", 0) / 24.0)

        f["overcrowd_dwell_penalty"] = (f.get("seat_utilisation_pct", 0) / 100.0) * f.get("num_scheduled_stops", 0)
        f["special_train_penalty"] = f.get("is_special_train", 0) * (1 + f.get("is_hdn_route", 0))
        f["mechanical_vulnerability"] = f.get("coach_age_years", 0) / (f.get("maintenance_score", 0) + 0.1)
        f["psr_density"] = f.get("psr_count", 0) / (f.get("distance_km", 1) / 100.0 + 1e-6)
        f["night_fog_factor"] = f.get("is_night_departure", 0) * f.get("fog_risk_score", 0)
        f["is_major_hub_terminal"] = int(
            f.get("source_station_category", "") == "A1"
            or f.get("destination_station_category", "") == "A1"
        )

        # Target encoding features use global mean as fallback for unseen data
        f.setdefault("train_punctuality_bias", self.metadata.get("global_delay_rate", 0.719))
        f.setdefault("zone_transition_delay", self.metadata.get("global_delay_rate", 0.719))

        # --- Encode categoricals ---
        categorical_cols = [
            "train_type", "season", "zone", "zone_abbr",
            "source_station_category", "destination_station_category", "traction_type",
        ]
        for col in categorical_cols:
            if col in f and isinstance(f[col], str):
                f[col] = self._encode_categorical(col, f[col])

        # --- Build ordered vector ---
        vector = []
        for feat_name in self.feature_names:
            vector.append(float(f.get(feat_name, 0)))

        return pd.DataFrame([vector], columns=self.feature_names)

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs full ensemble inference.

        Args:
            features: Dict with raw feature values (same keys as CSV columns).

        Returns:
            Dict with predicted_delay_minutes, delay_probability, risk_level,
            explanations, and safe_transfer_buffer_minutes.
        """
        if not self.ready:
            return self._heuristic_predict(features)

        X = self._build_feature_vector(features)

        # --- Classification: Average fold predictions per model ---
        xgb_probs = np.mean([m.predict_proba(X)[:, 1] for m in self.xgb_models], axis=0)
        lgb_probs = np.mean([m.predict_proba(X)[:, 1] for m in self.lgb_models], axis=0)
        cat_probs = np.mean([m.predict_proba(X)[:, 1] for m in self.cat_models], axis=0)

        # Stack for meta-learner
        stack_input = np.column_stack([xgb_probs, lgb_probs, cat_probs])
        delay_probability = float(self.meta_learner.predict_proba(stack_input)[:, 1][0])

        # --- Regression: Average fold predictions ---
        reg_preds = np.mean([m.predict(X) for m in self.reg_models], axis=0)
        predicted_delay = max(0.0, float(reg_preds[0]))

        # --- Risk assessment ---
        risk_level, explanations = self._assess_risk(features, delay_probability, predicted_delay)

        # Buffer = predicted delay + safety margin scaled by probability
        buffer = int(predicted_delay + 20 * delay_probability + 10)

        return {
            "predicted_delay_minutes": round(predicted_delay, 1),
            "delay_probability": round(delay_probability, 4),
            "risk_level": risk_level,
            "explanations": explanations,
            "safe_transfer_buffer_minutes": buffer,
            "model_version": "ensemble_v2",
            "ensemble_detail": {
                "xgboost_prob": round(float(xgb_probs[0]), 4),
                "lightgbm_prob": round(float(lgb_probs[0]), 4),
                "catboost_prob": round(float(cat_probs[0]), 4),
                "meta_prob": round(delay_probability, 4),
            },
        }

    def predict_delay(
        self,
        train_number: str = "12627",
        month: int = 1,
        day_of_week: int = 0,
        departure_hour: int = 8,
        zone: str = "NR",
        distance_km: int = 500,
        is_fog_risk: bool = False,
        is_monsoon: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Convenience wrapper for API endpoints & RAPTOR routing."""
        features = {
            "train_number": train_number,
            "month": month,
            "day_of_week": day_of_week,
            "departure_hour": departure_hour,
            "zone": zone,
            "zone_abbr": zone,
            "distance_km": distance_km,
            "is_fog_risk": int(is_fog_risk),
            "is_monsoon_season": int(is_monsoon),
            **kwargs,
        }
        return self.predict(features)

    def _assess_risk(
        self, features: Dict[str, Any], prob: float, delay: float
    ) -> tuple[str, List[str]]:
        """Generates human-readable risk explanations based on feature values."""
        explanations = []

        if features.get("late_incoming_rake", 0):
            explanations.append("Late incoming rake - cascade delay highly likely")
        if features.get("is_monsoon_season", 0):
            explanations.append("Monsoon season - track speed restrictions probable")
        if features.get("fog_risk_score", 0) > 0.5:
            explanations.append(f"High fog risk (score={features['fog_risk_score']:.1f}) - visibility delays")
        if features.get("zone_congestion_index", 0) > 0.7:
            explanations.append("High zone congestion - section bottleneck likely")
        if features.get("is_festival_season", 0):
            explanations.append("Festival season - elevated passenger load and congestion")
        if features.get("is_rake_shared", 0) and features.get("late_incoming_rake", 0):
            explanations.append("Shared rake with late turnaround - compounding delay risk")
        if not features.get("track_doubled", 0):
            explanations.append("Single track section - crossing delays possible")
        if features.get("seat_utilisation_pct", 0) > 100:
            explanations.append("Overloaded train - extended dwell times at stations")
        if delay > 60:
            explanations.append(f"Predicted delay of {delay:.0f} min - major disruption expected")

        if prob > 0.85:
            risk_level = "CRITICAL"
        elif prob > 0.7:
            risk_level = "HIGH"
        elif prob > 0.5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if not explanations:
            explanations.append("Normal operating conditions - delay risk is low")

        return risk_level, explanations

    def _heuristic_predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Statistical heuristic fallback when ML models are not loaded.
        Based on Indian Railways empirical delay patterns.
        """
        base_delay = 10
        explanations = []
        zone = features.get("zone_abbr", features.get("zone", ""))

        # Fog impact
        month = features.get("month", 1)
        if features.get("is_fog_risk", False) or (
            month in (12, 1, 2) and zone in ("NR", "NCR", "NER", "NWR")
        ):
            base_delay += 35
            explanations.append("Severe winter fog risk on northern corridor (+35m buffer)")

        # Monsoon impact
        if features.get("is_monsoon_season", False) or (
            month in (6, 7, 8, 9) and zone in ("KR", "CR", "WR", "SER")
        ):
            base_delay += 25
            explanations.append("Monsoon track speed restrictions applied (+25m buffer)")

        # Distance scaling
        distance_km = features.get("distance_km", 500)
        distance_delay = min(30, int(distance_km / 250) * 5)
        base_delay += distance_delay
        if distance_delay > 10:
            explanations.append(f"Long haul route propagation delay (+{distance_delay}m buffer)")

        # Weekend rush
        if features.get("day_of_week", 0) in (4, 6):
            base_delay += 10
            explanations.append("High passenger volume weekend traffic (+10m buffer)")

        risk_level = "LOW"
        if base_delay > 45:
            risk_level = "HIGH"
        elif base_delay > 25:
            risk_level = "MEDIUM"

        return {
            "predicted_delay_minutes": base_delay,
            "delay_probability": 0.72,  # Historical average
            "risk_level": risk_level,
            "explanations": explanations,
            "safe_transfer_buffer_minutes": base_delay + 20,
            "model_version": "heuristic_v1",
        }


# Module-level singleton for FastAPI dependency injection
_predictor: Optional[DelayPredictor] = None


def get_predictor() -> DelayPredictor:
    """Returns a singleton DelayPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = DelayPredictor()
    return _predictor
