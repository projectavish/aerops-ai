"""Tests for ML delay prediction model."""
import os
import pytest
from aerops.data.demo_generator import generate_demo_data
from aerops.db import init_db


def test_model_trains_on_small_data(tmp_db):
    """Test that the model can train on a small demo dataset."""
    # Generate small demo data
    generate_demo_data(tmp_db, num_flights=500)

    from aerops.models.delay_predictor import DelayPredictor
    predictor = DelayPredictor()
    predictor.train(tmp_db)

    assert predictor.classifier is not None
    assert predictor.regressor is not None


def test_predict_returns_valid_probability(tmp_db):
    """Test that predictions return valid probability range."""
    generate_demo_data(tmp_db, num_flights=500)

    from aerops.models.delay_predictor import DelayPredictor
    predictor = DelayPredictor()
    predictor.train(tmp_db)

    prob, minutes = predictor.predict({
        "origin": "JFK",
        "dest": "LAX",
        "airline": "AA",
        "dep_hour": 14,
        "day_of_week": 2,
        "month": 7,
        "is_weekend": 0,
        "distance": 2475,
        "crs_elapsed_time": 330,
    })

    assert 0 <= prob <= 1
    assert minutes >= 0


def test_feature_importances_not_empty(tmp_db):
    """Test that feature importances are returned."""
    generate_demo_data(tmp_db, num_flights=500)

    from aerops.models.delay_predictor import DelayPredictor
    predictor = DelayPredictor()
    predictor.train(tmp_db)

    importances = predictor.get_feature_importances()
    assert len(importances) > 0
    assert all(v >= 0 for v in importances.values())


def test_save_and_load(tmp_db, tmp_path):
    """Test model save/load roundtrip."""
    generate_demo_data(tmp_db, num_flights=500)

    from aerops.models.delay_predictor import DelayPredictor
    predictor = DelayPredictor()
    predictor.train(tmp_db)

    model_dir = str(tmp_path / "models")
    os.makedirs(model_dir, exist_ok=True)
    predictor.save(model_dir)

    loaded = DelayPredictor()
    loaded.load(model_dir)

    prob1, _ = predictor.predict({"origin": "ATL", "dest": "ORD", "airline": "DL",
                                   "dep_hour": 10, "day_of_week": 1, "month": 3,
                                   "is_weekend": 0, "distance": 606, "crs_elapsed_time": 120})
    prob2, _ = loaded.predict({"origin": "ATL", "dest": "ORD", "airline": "DL",
                                "dep_hour": 10, "day_of_week": 1, "month": 3,
                                "is_weekend": 0, "distance": 606, "crs_elapsed_time": 120})
    assert abs(prob1 - prob2) < 0.01
