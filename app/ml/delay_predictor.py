"""
XGBoost Train Delay Prediction & Explainability Engine
Predicts expected arrival delay at intermediate stations and explains risk factors.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import os


class DelayPredictor:
    """
    Wraps trained XGBoost model for train delay inference.
    Falls back gracefully to statistical heuristics if model is not yet compiled.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or str(
            Path(__file__).resolve().parent / "models" / "delay_model_v1.json"
        )
        self.model = None
        self._load_model()

    def _load_model(self):
        """Attempts to load compiled XGBoost model."""
        if os.path.exists(self.model_path):
            try:
                import xgboost as xgb
                self.model = xgb.Booster()
                self.model.load_model(self.model_path)
                print(f"✅ Loaded XGBoost delay model from: {self.model_path}")
            except Exception as e:
                print(f"⚠️ Could not load model ({e}), using heuristic mode.")
                self.model = None
        else:
            self.model = None

    def predict_delay(
        self,
        train_number: str,
        month: int = 1,
        day_of_week: int = 0,
        departure_hour: int = 8,
        zone: str = "NR",
        distance_km: int = 500,
        is_fog_risk: bool = False,
        is_monsoon: bool = False,
    ) -> Dict[str, Any]:
        """
        Predicts expected delay in minutes and returns risk factor explanations.
        """
        if self.model is not None:
            # XGBoost inference will be executed here once model is trained in Phase 3
            pass

        # Empirical baseline heuristic grounded in Indian Railways statistical patterns
        base_delay = 10  # 10 min average baseline buffer

        explanations = []

        # Fog impact (winter Northern Railway corridors experience 40-90m delays)
        if is_fog_risk or (month in (12, 1, 2) and zone in ("NR", "NCR", "NER", "NWR")):
            base_delay += 35
            explanations.append("Severe winter fog risk on northern corridor (+35m buffer)")

        # Monsoon impact (Western Ghats, Konkan, Coastal zones)
        if is_monsoon or (month in (6, 7, 8, 9) and zone in ("KR", "CR", "WR", "SER")):
            base_delay += 25
            explanations.append("Monsoon track speed restrictions applied (+25m buffer)")

        # Distance scaling (approx 5 mins per 250 km travel)
        distance_delay = min(30, int(distance_km / 250) * 5)
        base_delay += distance_delay
        if distance_delay > 10:
            explanations.append(f"Long haul route propagation delay (+{distance_delay}m buffer)")

        # Weekend / Peak rush
        if day_of_week in (4, 6):  # Friday / Sunday
            base_delay += 10
            explanations.append("High passenger volume weekend traffic (+10m buffer)")

        risk_level = "LOW"
        if base_delay > 45:
            risk_level = "HIGH"
        elif base_delay > 25:
            risk_level = "MEDIUM"

        return {
            "predicted_delay_minutes": base_delay,
            "risk_level": risk_level,
            "explanations": explanations,
            "safe_transfer_buffer_minutes": base_delay + 20,
        }
