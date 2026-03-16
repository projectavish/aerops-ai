"""GradientBoosting-based delay prediction model for aviation operations.

Trains a classifier (P(delay > 15 min)) and a regressor (estimated delay
minutes) on historical flight data.  Features include temporal encodings,
route / airport / airline historical delay rates, distance, and optional
weather observations.
"""

import json
import logging
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
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
FLIGHT_CAT_MAP = {"VFR": 0, "MVFR": 1, "IFR": 2, "LIFR": 3}


class DelayPredictor:
    """Aviation delay prediction model backed by GradientBoosting."""

    def __init__(self):
        self.classifier: GradientBoostingClassifier | None = None
        self.regressor: GradientBoostingRegressor | None = None
        self.feature_columns: list[str] = []
        self.label_encoders: dict[str, LabelEncoder] = {}
        self._trained = False

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

        route_rate = df.groupby("route")["arr_del15"].transform("mean")
        df["route_delay_rate"] = route_rate

        origin_rate = df.groupby("origin")["arr_del15"].transform("mean")
        df["origin_delay_rate"] = origin_rate

        dest_rate = df.groupby("dest")["arr_del15"].transform("mean")
        df["dest_delay_rate"] = dest_rate

        airline_rate = df.groupby("airline")["arr_del15"].transform("mean")
        df["airline_delay_rate"] = airline_rate

        return df

    @staticmethod
    def _add_weather_features(
        df: pd.DataFrame, weather_df: pd.DataFrame | None
    ) -> pd.DataFrame:
        """Merge weather features when available; fill defaults otherwise."""
        df = df.copy()

        if weather_df is not None and not weather_df.empty:
            # Encode flight category
            weather_df = weather_df.copy()
            weather_df["origin_flight_cat"] = (
                weather_df["origin_flight_cat"]
                .map(FLIGHT_CAT_MAP)
                .fillna(0)
                .astype(int)
            )
            # De-duplicate per ICAO (take latest)
            weather_df = weather_df.drop_duplicates(
                subset=["icao_id"], keep="last"
            )
            # Map ICAO -> IATA (strip leading K for US airports)
            weather_df["origin"] = weather_df["icao_id"].str.replace(
                r"^K", "", regex=True
            )
            weather_df = weather_df.drop(columns=["icao_id"])

            df = df.merge(weather_df, on="origin", how="left")

        # Ensure columns exist with safe defaults
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
    # Training
    # ------------------------------------------------------------------

    def train(self, db_path: str = DB_PATH) -> dict:
        """Train classifier and regressor on historical flight data.

        Uses a temporal split: the most recent 30 days of data form the
        test set; everything before that is used for training.

        Returns a dict with evaluation metrics.
        """
        # 1. Load data ---------------------------------------------------
        df = self._load_flight_data(db_path)
        if df.empty or len(df) < 100:
            raise ValueError(
                f"Insufficient training data: only {len(df)} rows. "
                "Run demo_generator or load BTS data first."
            )

        weather_df = self._load_weather_data(db_path)

        # 2. Feature engineering -----------------------------------------
        df = self._engineer_features(df, weather_df)

        # 3. Define feature columns --------------------------------------
        self.feature_columns = [
            "dep_hour",
            "day_of_week",
            "month",
            "is_weekend",
            "distance",
            "crs_elapsed_time",
            "route_delay_rate",
            "origin_delay_rate",
            "dest_delay_rate",
            "airline_delay_rate",
            "dep_hour_sin",
            "dep_hour_cos",
            "month_sin",
            "month_cos",
            "origin_visibility",
            "origin_wind_speed",
            "origin_ceiling",
            "origin_flight_cat",
        ]

        # 4. Temporal train/test split -----------------------------------
        df["flight_date"] = pd.to_datetime(df["flight_date"])
        cutoff_date = df["flight_date"].max() - pd.Timedelta(days=30)
        train_df = df[df["flight_date"] <= cutoff_date].copy()
        test_df = df[df["flight_date"] > cutoff_date].copy()

        logger.info(
            "Temporal split  |  train: %d rows (up to %s)  |  test: %d rows (after %s)",
            len(train_df),
            cutoff_date.date(),
            len(test_df),
            cutoff_date.date(),
        )

        if len(train_df) < 50 or len(test_df) < 10:
            raise ValueError(
                "Not enough data for a meaningful temporal split. "
                f"Train={len(train_df)}, Test={len(test_df)}."
            )

        # 5. Prepare matrices -------------------------------------------
        X_train = train_df[self.feature_columns].astype(float)
        y_train_cls = train_df["arr_del15"].astype(int)

        X_test = test_df[self.feature_columns].astype(float)
        y_test_cls = test_df["arr_del15"].astype(int)

        # Handle any remaining NaN values
        X_train = X_train.fillna(0)
        X_test = X_test.fillna(0)

        # 6. Train classifier -------------------------------------------
        logger.info("Training GradientBoostingClassifier ...")
        self.classifier = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
        )
        self.classifier.fit(X_train, y_train_cls)

        # 7. Train regressor (only on delayed flights) -------------------
        delayed_train = train_df[train_df["arr_del15"] == 1]
        if len(delayed_train) < 20:
            logger.warning(
                "Only %d delayed flights in training data; regressor may be unreliable",
                len(delayed_train),
            )

        X_train_reg = delayed_train[self.feature_columns].astype(float).fillna(0)
        y_train_reg = delayed_train["arr_delay_minutes"].astype(float)

        logger.info(
            "Training GradientBoostingRegressor on %d delayed flights ...",
            len(delayed_train),
        )
        self.regressor = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
        )
        self.regressor.fit(X_train_reg, y_train_reg)

        # 8. Evaluate ---------------------------------------------------
        y_pred_cls = self.classifier.predict(X_test)
        y_pred_proba = self.classifier.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test_cls, y_pred_cls)
        precision = precision_score(y_test_cls, y_pred_cls, zero_division=0)
        recall = recall_score(y_test_cls, y_pred_cls, zero_division=0)
        auc = roc_auc_score(y_test_cls, y_pred_proba)

        metrics = {
            "accuracy": round(accuracy, 4),
            "auc": round(auc, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "train_size": len(train_df),
            "test_size": len(test_df),
            "delayed_train_size": len(delayed_train),
            "n_features": len(self.feature_columns),
        }

        print("\n" + "=" * 60)
        print("  DELAY PREDICTION MODEL - EVALUATION RESULTS")
        print("=" * 60)
        print(f"  Accuracy  : {accuracy:.4f}")
        print(f"  AUC-ROC   : {auc:.4f}")
        print(f"  Precision : {precision:.4f}")
        print(f"  Recall    : {recall:.4f}")
        print(f"  Train size: {len(train_df):,}  |  Test size: {len(test_df):,}")
        print("=" * 60)
        print("\n  Classification Report (test set):")
        print(classification_report(y_test_cls, y_pred_cls, target_names=["On-Time", "Delayed"]))

        self._trained = True
        return metrics

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, features_dict: dict) -> tuple[float, float]:
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
            raise RuntimeError(
                "Model not trained or loaded. Call train() or load() first."
            )

        row = {col: features_dict.get(col, 0) for col in self.feature_columns}
        X = pd.DataFrame([row])[self.feature_columns].astype(float)

        delay_prob = float(self.classifier.predict_proba(X)[0, 1])
        estimated_minutes = max(0.0, float(self.regressor.predict(X)[0]))

        return delay_prob, estimated_minutes

    # ------------------------------------------------------------------
    # Feature importances
    # ------------------------------------------------------------------

    def get_feature_importances(self) -> dict:
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
        """Save trained models and metadata to *model_dir*."""
        if not self._trained:
            raise RuntimeError("Nothing to save - model has not been trained.")

        Path(model_dir).mkdir(parents=True, exist_ok=True)

        model_path = os.path.join(model_dir, "delay_model.joblib")
        columns_path = os.path.join(model_dir, "feature_columns.json")

        joblib.dump(
            {
                "classifier": self.classifier,
                "regressor": self.regressor,
            },
            model_path,
        )

        with open(columns_path, "w") as f:
            json.dump(self.feature_columns, f, indent=2)

        logger.info("Model saved to %s", model_path)
        logger.info("Feature columns saved to %s", columns_path)
        print(f"\n  Model saved  -> {model_path}")
        print(f"  Columns saved -> {columns_path}")

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

        self._trained = True
        logger.info("Model loaded from %s (%d features)", model_path, len(self.feature_columns))
