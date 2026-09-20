"""
Unit & Integration Tests for MargDarshak ML Delay Prediction Ensemble (v3)
Tests the 58-feature pipeline, tri-model stacking (XGBoost + LightGBM + CatBoost),
meta-learner, mean regression, and P85 quantile safety buffer.
"""

import pytest
from app.ml.delay_predictor import DelayPredictor, get_predictor


@pytest.fixture
def predictor():
    return get_predictor()


def test_predictor_loaded(predictor):
    """Verifies that the trained ensemble models and schedule metrics are loaded."""
    assert predictor is not None
    assert predictor.ready is True
    assert len(predictor.xgb_models) == 5
    assert len(predictor.lgb_models) == 5
    assert len(predictor.cat_models) == 5
    assert len(predictor.reg_models) == 5
    assert len(predictor.quantile_models) == 5
    assert predictor.meta_learner is not None
    assert len(predictor.feature_names) == 58
    assert len(predictor.schedule_metrics) > 0


def test_ensemble_predict_output(predictor):
    """Tests that predict() produces dual-head classification, mean, and P85 quantile outputs."""
    sample_input = {
        "train_number": "12627",
        "train_type": "Superfast Express",
        "year": 2024,
        "month": 7,
        "day_of_week": 3,
        "departure_hour": 8,
        "is_weekend": 0,
        "is_night_departure": 0,
        "is_peak_hour": 1,
        "is_festival_season": 0,
        "season": "Monsoon",
        "zone": "North Western Railway (NWR)",
        "zone_abbr": "NWR",
        "source_station_category": "A",
        "destination_station_category": "B",
        "distance_km": 620,
        "num_scheduled_stops": 12,
        "scheduled_travel_hours": 10.3,
        "track_doubled": 1,
        "is_hdn_route": 0,
        "traction_type": "Dual",
        "is_electrified": 1,
        "psr_count": 3,
        "is_circular_route": 0,
        "is_monsoon_season": 1,
        "is_fog_risk": 0,
        "fog_risk_score": 0.0,
        "zone_fog_index": 0.58,
        "zone_congestion_index": 0.75,
        "season_severity_score": 0.78,
        "loco_age_years": 16.7,
        "coach_age_years": 7.8,
        "has_lhb_coaches": 0,
        "is_rake_shared": 1,
        "maintenance_score": 5.5,
        "seat_utilisation_pct": 88.8,
        "is_overloaded": 0,
        "late_incoming_rake": 0,
        "is_special_train": 0,
        "route_historical_ontime_pct": 67.8,
    }

    result = predictor.predict(sample_input)

    assert "predicted_delay_minutes" in result
    assert "p85_delay_buffer_minutes" in result
    assert "delay_probability" in result
    assert "risk_level" in result
    assert "explanations" in result
    assert "safe_transfer_buffer_minutes" in result
    assert "ensemble_detail" in result

    # Numerical sanity checks
    assert isinstance(result["predicted_delay_minutes"], float)
    assert result["predicted_delay_minutes"] >= 0.0
    assert isinstance(result["p85_delay_buffer_minutes"], float)
    # P85 quantile buffer must be greater than or equal to expected mean delay
    assert result["p85_delay_buffer_minutes"] >= result["predicted_delay_minutes"]
    assert 0.0 <= result["delay_probability"] <= 1.0
    assert result["safe_transfer_buffer_minutes"] >= result["p85_delay_buffer_minutes"]
    assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # Detailed probabilities across all 3 models + meta-learner + P85 buffer
    detail = result["ensemble_detail"]
    assert 0.0 <= detail["xgboost_prob"] <= 1.0
    assert 0.0 <= detail["lightgbm_prob"] <= 1.0
    assert 0.0 <= detail["catboost_prob"] <= 1.0
    assert 0.0 <= detail["meta_prob"] <= 1.0
    assert "p85_quantile_buffer" in detail


def test_predict_delay_wrapper(predictor):
    """Tests the convenience wrapper method used by API and routing algorithms."""
    res = predictor.predict_delay(
        train_number="12627",
        month=1,
        zone="NR",
        distance_km=850,
    )
    assert res["predicted_delay_minutes"] > 0
    assert res["p85_delay_buffer_minutes"] >= res["predicted_delay_minutes"]
    assert res["model_version"] == "ensemble_v3_p85"
    assert len(res["explanations"]) > 0
