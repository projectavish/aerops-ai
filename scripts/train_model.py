#!/usr/bin/env python3
"""Train the AerOps AI delay prediction model.

Usage
-----
    python -m scripts.train_model          # from project root
    python scripts/train_model.py          # direct execution

The script will:
    1. Ensure the database exists (generates demo data if empty).
    2. Train classifier + regressor on historical flight data.
    3. Run TimeSeriesSplit cross-validation (5 folds).
    4. Compute calibration and precision-recall curves.
    5. Print evaluation metrics and feature importances.
    6. Save the model artifacts to the configured MODEL_DIR.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

# Ensure the project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from aerops.config import DB_PATH, MODEL_DIR  # noqa: E402
from aerops.db import init_db, table_row_count  # noqa: E402
from aerops.models.delay_predictor import DelayPredictor  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def ensure_data(db_path: str) -> int:
    """Make sure the flights table has data; generate demo data if needed."""
    init_db(db_path)
    try:
        count = table_row_count(db_path, "flights")
    except Exception:
        count = 0

    if count == 0:
        logger.info("No flight data found - generating demo data ...")
        from aerops.data.demo_generator import generate_demo_data
        count = generate_demo_data(db_path)
        logger.info("Demo data generated: %d flights", count)
    else:
        logger.info("Database already contains %d flights", count)

    return count


def main() -> None:
    logger.info("=" * 60)
    logger.info("  AerOps AI - Delay Prediction Model Training")
    logger.info("=" * 60)
    logger.info("  Database : %s", DB_PATH)
    logger.info("  Model dir: %s", MODEL_DIR)

    # Step 1: ensure data exists
    flight_count = ensure_data(DB_PATH)
    logger.info("  Flights available: %d", flight_count)

    # Step 2: train (includes CV, calibration, PR curve)
    predictor = DelayPredictor()
    start = time.perf_counter()
    predictor.train(DB_PATH)
    elapsed = time.perf_counter() - start
    logger.info("Training completed in %.1fs", elapsed)

    # Step 3: save model + evaluation data
    predictor.save(MODEL_DIR)

    # Step 4: show feature importances
    importances = predictor.get_feature_importances()
    logger.info("Feature Importances (top 10):")
    logger.info("-" * 50)
    for i, (feat, imp) in enumerate(importances.items()):
        if i >= 10:
            break
        bar = "#" * int(imp * 200)
        logger.info("  %-25s %.4f  %s", feat, imp, bar)

    # Step 5: show CV summary
    if predictor.cv_scores:
        import numpy as np
        logger.info("Cross-Validation Summary (TimeSeriesSplit, 5 folds):")
        for metric_name, scores in predictor.cv_scores.items():
            logger.info("  %-12s: %.4f +/- %.4f", metric_name,
                        np.mean(scores), np.std(scores))

    # Step 6: sanity-check prediction
    sample = {
        "dep_hour": 8, "day_of_week": 2, "month": 7,
        "is_weekend": 0, "distance": 1500, "crs_elapsed_time": 210,
        "route_delay_rate": 0.20, "origin_delay_rate": 0.18,
        "dest_delay_rate": 0.22, "airline_delay_rate": 0.19,
        "dep_hour_sin": 0.866, "dep_hour_cos": 0.5,
        "month_sin": 0.5, "month_cos": -0.866,
        "origin_visibility": 10.0, "origin_wind_speed": 8,
        "origin_ceiling": 25000, "origin_flight_cat": 0,
    }
    prob, minutes = predictor.predict(sample)
    logger.info("Sample prediction -> P(delay) = %.2f%%, Est. delay = %.1f min",
                prob * 100, minutes)
    logger.info("Done.")


if __name__ == "__main__":
    main()
