"""GradientBoosting-based delay prediction model for aviation operations.

Trains a classifier (P(delay > 15 min)) and a regressor (estimated delay
minutes) on historical flight data.  Features include temporal encodings,
route / airport / airline historical delay rates, distance, and optional
weather observations.

Model evaluation includes:
    - Temporal train/test split (last 30 days held out)
    - TimeSeriesSplit cross-validation (5 folds)
    - Calibration curve for probability reliability
    - Precision-Recall curve with business threshold analysis
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder

from aerops.config import (
    DB_PATH,
    DELAY_MODEL_PATH,
    FEATURE_COLUMNS_PATH,
    MODEL_DIR,
)
from aerops.db import get_connection

logger = logging.getLogger(__name__)

# Weather flight-category encoding
FLIGHT_CAT_MAP: dict[str, int] = {"VFR": 0, "MVFR": 1, "IFR": 2, "LIFR": 3}


class DelayPredictor:
    """Aviation delay prediction model backed by GradientBoosting.

    Attributes
    ----------
    classifier : GradientBoostingClassifier | None
        Binary classifier predicting P(delay > 15 min).
    regressor : GradientBoostingRegressor | None
        Regressor predicting delay duration for delayed flights.
    feature_columns : list[str]
        Ordered list of feature names used during training.
    cv_scores : dict[str, list[float]]
        Cross-validation scores from TimeSeriesSplit.
    calibration_data : dict[str, Any]
        Calibration curve data for probability reliability.
    pr_curve_data : dict[str, Any]
        Precision-recall curve data with thresholds.
    """

    def __init__(self) -> None:
        self.classifier: GradientBoostingClassifier | None = None
        self.regressor: GradientBoostingRegressor | None = None
        self.feature_columns: list[str] = []
        self.label_encoders: dict[str, LabelEncoder] = {}
        self._trained: bool = False
        self.cv_scores: dict[str, list[float]] = {}
        self.calibration_data: dict[str, Any] = {}
        self.pr_curve_data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_flight_data(db_path: str) -> pd.DataFrame:
        """Load flight data from SQLite, excluding cancelled flights."""
        conn = get_connection(db_path)
        df = pd.read_sql_query(
            """
            SELECT
                flight_date,
                airline,
                origin,
                dest,
                route,
                dep_hour,
                day_of_week,
                month,
                is_weekend,
                distance,
                crs_elapsed_time,
                arr_delay_minutes,
                arr_del15,
                dep_delay_minutes
            FROM flights
            WHERE cancelled = 0
            ORDER BY flight_date
            """,
            conn,
        )
        conn.close()
        logger.info("Loaded %d non-cancelled flights from database", len(df))
        return df

    @staticmethod
    def _load_weather_data(db_path: str) -> pd.DataFrame | None:
        """Attempt to load weather observations; return None if empty."""
        conn = get_connection(db_path)
        try:
            df = pd.read_sql_query(
                """
                SELECT
                    icao_id,
                    visibility   AS origin_visibility,
                    wind_speed   AS origin_wind_speed,
                    ceiling      AS origin_ceiling,
                    flight_category AS origin_flight_cat
                FROM weather_observations
                """,
                conn,
            )
            conn.close()
            if df.empty:
                return None
            return df
        except Exception:
            conn.close()
            return None

    # ------------------------------------------------------------------
    # Feature engineering
    # ------------------------------------------------------------------

    @staticmethod
    def _add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add sin/cos encodings for dep_hour and month."""
        df = df.copy()
        df["dep_hour_sin"] = np.sin(2 * np.pi * df["dep_hour"] / 24)
        df["dep_hour_cos"] = np.cos(2 * np.pi * df["dep_hour"] / 24)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        return df

    @staticmethod
    def _add_historical_rates(df: pd.DataFrame) -> pd.DataFrame:
        """Compute historical delay rates per route, origin, dest, airline."""
        df = df.copy()
        df["route_delay_rate"] = df.groupby("route")["arr_del15"].transform("mean")
        df["origin_delay_rate"] = df.groupby("origin")["arr_del15"].transform("mean")
        df["dest_delay_rate"] = df.groupby("dest")["arr_del15"].transform("mean")
        df["airline_delay_rate"] = df.groupby("airline")["arr_del15"].transform("mean")
        return df

    @staticmethod
    def _add_weather_features(
        df: pd.DataFrame, weather_df: pd.DataFrame | None
    ) -> pd.DataFrame:
        """Merge weather features when available; fill defaults otherwise."""
        df = df.copy()

        if weather_df is not None and not weather_df.empty:
            weather_df = weather_df.copy()
            weather_df["origin_flight_cat"] = (
                weather_df["origin_flight_cat"]
                .map(FLIGHT_CAT_MAP)
                .fillna(0)
                .astype(int)
            )
            weather_df = weather_df.drop_duplicates(
                subset=["icao_id"], keep="last"
            )
            weather_df["origin"] = weather_df["icao_id"].str.replace(
                r"^K", "", regex=True
            )
            weather_df = weather_df.drop(columns=["icao_id"])
            df = df.merge(weather_df, on="origin", how="left")

        for col, default in [
            ("origin_visibility", 10.0),
            ("origin_wind_speed", 5),
            ("origin_ceiling", 25000),
            ("origin_flight_cat", 0),
        ]:
            if col not in df.columns:
                df[col] = default
            else:
                df[col] = df[col].fillna(default)

        return df

    def _engineer_features(
        self, df: pd.DataFrame, weather_df: pd.DataFrame | None = None
    ) -> pd.DataFrame:
        """Run the full feature-engineering pipeline."""
        df = self._add_cyclical_features(df)
        df = self._add_historical_rates(df)
        df = self._add_weather_features(df, weather_df)
        return df

    # ------------------------------------------------------------------
    # Cross-validation
    # ------------------------------------------------------------------

    def _run_cross_validation(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5,
    ) -> dict[str, list[float]]:
        """Run TimeSeriesSplit cross-validation for robust evaluation."""
        tscv = TimeSeriesSplit(n_splits=n_splits)
        scores: dict[str, list[float]] = {
            "accuracy": [], "auc": [], "precision": [], "recall": [],
        }

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

            clf = GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                subsample=0.8, min_samples_split=20, min_samples_leaf=10,
                random_state=42,
            )
            clf.fit(X_tr, y_tr)
            y_pred = clf.predict(X_val)
            y_proba = clf.predict_proba(X_val)[:, 1]

            scores["accuracy"].append(accuracy_score(y_val, y_pred))
            try:
                scores["auc"].append(roc_auc_score(y_val, y_proba))
            except ValueError:
                scores["auc"].append(0.0)
            scores["precision"].append(precision_score(y_val, y_pred, zero_division=0))
            scores["recall"].append(recall_score(y_val, y_pred, zero_division=0))

            logger.info("CV Fold %d: ACC=%.3f AUC=%.3f", fold + 1,
                        scores["accuracy"][-1], scores["auc"][-1])

        return scores

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, db_path: str = DB_PATH) -> dict[str, Any]:
        """Train classifier and regressor on historical flight data.

        Uses a temporal split: the most recent 30 days of data form the
        test set; everything before that is used for training. Also runs
        TimeSeriesSplit CV and computes calibration/PR curves.

        Returns a dict with evaluation metrics.
        """
        df = self._load_flight_data(db_path)
        if df.empty or len(df) < 100:
            raise ValueError(
                f"Insufficient training data: only {len(df)} rows. "
                "Run demo_generator or load BTS data first."
            )

        weather_df = self._load_weather_data(db_path)
        df = self._engineer_features(df, weather_df)

        self.feature_columns = [
            "dep_hour", "day_of_week", "month", "is_weekend",
            "distance", "crs_elapsed_time",
            "route_delay_rate", "origin_delay_rate",
            "dest_delay_rate", "airline_delay_rate",
            "dep_hour_sin", "dep_hour_cos", "month_sin", "month_cos",
            "origin_visibility", "origin_wind_speed",
            "origin_ceiling", "origin_flight_cat",
        ]

        # Temporal train/test split
        df["flight_date"] = pd.to_datetime(df["flight_date"])
        cutoff_date = df["flight_date"].max() - pd.Timedelta(days=30)
        train_df = df[df["flight_date"] <= cutoff_date].copy()
        test_df = df[df["flight_date"] > cutoff_date].copy()

        logger.info("Temporal split | train: %d (up to %s) | test: %d (after %s)",
                     len(train_df), cutoff_date.date(), len(test_df), cutoff_date.date())

        if len(train_df) < 50 or len(test_df) < 10:
            raise ValueError(
                f"Not enough data for temporal split. Train={len(train_df)}, Test={len(test_df)}."
            )

        X_train = train_df[self.feature_columns].astype(float).fillna(0)
        y_train_cls = train_df["arr_del15"].astype(int)
        X_test = test_df[self.feature_columns].astype(float).fillna(0)
        y_test_cls = test_df["arr_del15"].astype(int)

        # Cross-validation
        logger.info("Running TimeSeriesSplit cross-validation (5 folds) ...")
        self.cv_scores = self._run_cross_validation(X_train, y_train_cls)

        # Train classifier
        logger.info("Training GradientBoostingClassifier ...")
        self.classifier = GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, min_samples_split=20, min_samples_leaf=10,
            random_state=42,
        )
        self.classifier.fit(X_train, y_train_cls)

        # Train regressor on delayed flights only
        delayed_train = train_df[train_df["arr_del15"] == 1]
        if len(delayed_train) < 20:
            logger.warning("Only %d delayed flights; regressor may be unreliable", len(delayed_train))

        X_train_reg = delayed_train[self.feature_columns].astype(float).fillna(0)
        y_train_reg = delayed_train["arr_delay_minutes"].astype(float)

        logger.info("Training GradientBoostingRegressor on %d delayed flights ...", len(delayed_train))
        self.regressor = GradientBoostingRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, min_samples_split=20, min_samples_leaf=10,
            random_state=42,
        )
        self.regressor.fit(X_train_reg, y_train_reg)

        # Evaluate
        y_pred_cls = self.classifier.predict(X_test)
        y_pred_proba = self.classifier.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test_cls, y_pred_cls)
        precision = precision_score(y_test_cls, y_pred_cls, zero_division=0)
        recall = recall_score(y_test_cls, y_pred_cls, zero_division=0)
        auc = roc_auc_score(y_test_cls, y_pred_proba)
        avg_precision = average_precision_score(y_test_cls, y_pred_proba)

        # Calibration curve
        try:
            prob_true, prob_pred = calibration_curve(
                y_test_cls, y_pred_proba, n_bins=10, strategy="uniform"
            )
            self.calibration_data = {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
            }
        except Exception as e:
            logger.warning("Calibration curve failed: %s", e)
            self.calibration_data = {}

        # Precision-Recall curve
        try:
            pr_prec, pr_rec, pr_thresh = precision_recall_curve(y_test_cls, y_pred_proba)
            self.pr_curve_data = {
                "precision": pr_prec.tolist(),
                "recall": pr_rec.tolist(),
                "thresholds": pr_thresh.tolist(),
                "avg_precision": round(avg_precision, 4),
            }
        except Exception as e:
            logger.warning("PR curve failed: %s", e)
            self.pr_curve_data = {}

        cv_means = {f"cv_{k}_mean": round(float(np.mean(v)), 4) for k, v in self.cv_scores.items()}
        cv_stds = {f"cv_{k}_std": round(float(np.std(v)), 4) for k, v in self.cv_scores.items()}

        metrics: dict[str, Any] = {
            "accuracy": round(accuracy, 4),
            "auc": round(auc, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "avg_precision": round(avg_precision, 4),
            "train_size": len(train_df),
            "test_size": len(test_df),
            "delayed_train_size": len(delayed_train),
            "n_features": len(self.feature_columns),
            **cv_means, **cv_stds,
        }

        logger.info("=" * 60)
        logger.info("  DELAY PREDICTION MODEL - EVALUATION RESULTS")
        logger.info("=" * 60)
        logger.info("  Accuracy       : %.4f", accuracy)
        logger.info("  AUC-ROC        : %.4f", auc)
        logger.info("  Precision      : %.4f", precision)
        logger.info("  Recall         : %.4f", recall)
        logger.info("  Avg Precision  : %.4f", avg_precision)
        logger.info("  Train size     : %d  |  Test size: %d", len(train_df), len(test_df))
        logger.info("  CV AUC (5-fold): %.4f +/- %.4f",
                     cv_means.get("cv_auc_mean", 0), cv_stds.get("cv_auc_std", 0))
        logger.info("=" * 60)
        logger.info("\n%s", classification_report(
            y_test_cls, y_pred_cls, target_names=["On-Time", "Delayed"]
        ))

        self._trained = True
        return metrics

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features_dict: dict[str, Any]) -> tuple[float, float]:
        """Predict delay probability and estimated delay minutes.

        Parameters
        ----------
        features_dict : dict
            Must contain keys matching ``self.feature_columns``.
            Missing keys are filled with 0.

        Returns
        -------
        (delay_probability, estimated_minutes) : tuple[float, float]
        """
        if self.classifier is None or self.regressor is None:
            raise RuntimeError("Model not trained or loaded. Call train() or load() first.")

        row = {col: features_dict.get(col, 0) for col in self.feature_columns}
        X = pd.DataFrame([row])[self.feature_columns].astype(float)

        delay_prob = float(self.classifier.predict_proba(X)[0, 1])
        estimated_minutes = max(0.0, float(self.regressor.predict(X)[0]))

        return delay_prob, estimated_minutes

    # ------------------------------------------------------------------
    # Feature importances
    # ------------------------------------------------------------------

    def get_feature_importances(self) -> dict[str, float]:
        """Return feature name -> importance mapping from the classifier."""
        if self.classifier is None:
            raise RuntimeError("Model not trained or loaded.")
        importances = self.classifier.feature_importances_
        return {
            name: round(float(imp), 6)
            for name, imp in sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, model_dir: str = MODEL_DIR) -> None:
        """Save trained models, metadata, and evaluation curves."""
        if not self._trained:
            raise RuntimeError("Nothing to save - model has not been trained.")

        Path(model_dir).mkdir(parents=True, exist_ok=True)
        model_path = os.path.join(model_dir, "delay_model.joblib")
        columns_path = os.path.join(model_dir, "feature_columns.json")
        eval_path = os.path.join(model_dir, "evaluation.json")

        joblib.dump({"classifier": self.classifier, "regressor": self.regressor}, model_path)
        with open(columns_path, "w") as f:
            json.dump(self.feature_columns, f, indent=2)

        eval_data = {
            "cv_scores": self.cv_scores,
            "calibration": self.calibration_data,
            "pr_curve": self.pr_curve_data,
        }
        with open(eval_path, "w") as f:
            json.dump(eval_data, f, indent=2)

        logger.info("Model saved to %s", model_path)
        logger.info("Evaluation data saved to %s", eval_path)

    def load(self, model_dir: str = MODEL_DIR) -> None:
        """Load a previously saved model from *model_dir*."""
        model_path = os.path.join(model_dir, "delay_model.joblib")
        columns_path = os.path.join(model_dir, "feature_columns.json")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No saved model at {model_path}")
        if not os.path.exists(columns_path):
            raise FileNotFoundError(f"No feature columns at {columns_path}")

        data = joblib.load(model_path)
        self.classifier = data["classifier"]
        self.regressor = data["regressor"]

        with open(columns_path) as f:
            self.feature_columns = json.load(f)

        eval_path = os.path.join(model_dir, "evaluation.json")
        if os.path.exists(eval_path):
            with open(eval_path) as f:
                eval_data = json.load(f)
            self.cv_scores = eval_data.get("cv_scores", {})
            self.calibration_data = eval_data.get("calibration", {})
            self.pr_curve_data = eval_data.get("pr_curve", {})

        self._trained = True
        logger.info("Model loaded from %s (%d features)", model_path, len(self.feature_columns))
