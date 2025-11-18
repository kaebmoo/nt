"""
XGBoost Forecast Model
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from .base_model import BaseForecastModel, ForecastResult


class XGBoostModel(BaseForecastModel):
    """
    XGBoost model for time series forecasting

    Best for:
    - Non-linear relationships
    - Multiple features/variables
    - High accuracy requirements
    - Complex patterns
    """

    def __init__(self,
                 n_estimators: int = 1000,
                 learning_rate: float = 0.01,
                 max_depth: int = 5,
                 subsample: float = 0.8,
                 colsample_bytree: float = 0.8,
                 lag_features: List[int] = [1, 3, 6, 12],
                 rolling_features: List[int] = [3, 6, 12],
                 **kwargs):
        """
        Initialize XGBoost model

        Args:
            n_estimators: Number of boosting rounds
            learning_rate: Learning rate
            max_depth: Maximum tree depth
            subsample: Subsample ratio of training instances
            colsample_bytree: Subsample ratio of columns
            lag_features: List of lag periods to create features
            rolling_features: List of rolling window sizes
        """
        super().__init__(name="XGBoost", **kwargs)

        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.lag_features = lag_features
        self.rolling_features = rolling_features

        self.model = None
        self.feature_names = []

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'XGBoostModel':
        """Fit XGBoost model"""

        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("xgboost not installed. Run: pip install xgboost")

        # Prepare data
        df_prep = self.prepare_data(df, date_column, value_column)
        self.df_prep = df_prep

        # Create features
        df_features = self._create_features(df_prep, exog)

        # Remove rows with NaN (from lag features)
        df_features = df_features.dropna()

        # Prepare X and y
        feature_cols = [col for col in df_features.columns if col not in ['ds', 'y']]
        self.feature_names = feature_cols

        X = df_features[feature_cols]
        y = df_features['y']

        # Store last rows for recursive forecasting
        self.last_values = df_prep.copy()
        self.last_features = df_features.copy()

        # Initialize and fit XGBoost
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            objective='reg:squarederror',
            random_state=42
        )

        self.model.fit(X, y,
                       eval_set=[(X, y)],
                       early_stopping_rounds=50,
                       verbose=False)

        self.is_fitted = True
        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """Generate forecast using XGBoost (recursive forecasting)"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Generate forecast recursively
        forecasts = []
        current_df = self.last_values.copy()

        for i in range(periods):
            # Create features for next period
            features_dict = self._create_single_period_features(
                current_df,
                exog.iloc[i] if exog is not None and i < len(exog) else None
            )

            # Predict
            X_pred = pd.DataFrame([features_dict])[self.feature_names]
            y_pred = self.model.predict(X_pred)[0]

            # Store forecast
            forecasts.append(y_pred)

            # Update current_df for next iteration
            last_date = current_df['ds'].iloc[-1]
            freq = pd.infer_freq(current_df['ds'])
            if freq is None:
                freq = 'M'

            next_date = last_date + pd.DateOffset(months=1) if freq == 'M' else last_date + pd.Timedelta(days=1)

            new_row = pd.DataFrame({
                'ds': [next_date],
                'y': [y_pred]
            })

            current_df = pd.concat([current_df, new_row], ignore_index=True)

        # Create forecast dataframe
        last_date = self.df_prep['ds'].iloc[-1]
        freq = pd.infer_freq(self.df_prep['ds'])
        if freq is None:
            freq = 'M'

        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=freq
        )[1:]

        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecasts
        })

        # Calculate confidence intervals (using historical error std)
        historical_pred = self.model.predict(self.last_features[self.feature_names].dropna())
        historical_actual = self.last_features['y'].dropna()
        residuals = historical_actual.values - historical_pred[:len(historical_actual)]
        std_error = np.std(residuals)

        forecast_df['yhat_lower'] = forecast_df['yhat'] - 1.96 * std_error
        forecast_df['yhat_upper'] = forecast_df['yhat'] + 1.96 * std_error

        # Historical fitted values
        historical_df = pd.DataFrame({
            'ds': self.df_prep['ds'].iloc[-len(historical_pred):],
            'yhat': historical_pred
        })

        # Confidence intervals
        confidence_df = forecast_df[['ds', 'yhat_lower', 'yhat_upper']].copy()

        # Calculate metrics
        from src.utils.metrics import calculate_metrics
        metrics = calculate_metrics(historical_actual.values, historical_pred[:len(historical_actual)])

        # Feature importance
        feature_importance = dict(zip(
            self.feature_names,
            self.model.feature_importances_
        ))

        return ForecastResult(
            forecast_df=forecast_df,
            historical_df=historical_df,
            metrics=metrics,
            model_params=self.get_params(),
            model_name=self.name,
            confidence_intervals=confidence_df,
            feature_importance=feature_importance
        )

    def _create_features(self,
                        df: pd.DataFrame,
                        exog: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Create time series features"""

        df_feat = df.copy()

        # Time-based features
        df_feat['month'] = df_feat['ds'].dt.month
        df_feat['quarter'] = df_feat['ds'].dt.quarter
        df_feat['year'] = df_feat['ds'].dt.year
        df_feat['dayofweek'] = df_feat['ds'].dt.dayofweek
        df_feat['dayofyear'] = df_feat['ds'].dt.dayofyear

        # Lag features
        for lag in self.lag_features:
            df_feat[f'lag_{lag}'] = df_feat['y'].shift(lag)

        # Rolling mean features
        for window in self.rolling_features:
            df_feat[f'rolling_mean_{window}'] = df_feat['y'].rolling(window).mean()
            df_feat[f'rolling_std_{window}'] = df_feat['y'].rolling(window).std()

        # Expanding features
        df_feat['expanding_mean'] = df_feat['y'].expanding().mean()

        # YoY growth (if data >= 12 months)
        if len(df_feat) >= 12:
            df_feat['yoy_growth'] = df_feat['y'].pct_change(12)

        # Add exogenous variables
        if exog is not None:
            for col in exog.columns:
                df_feat[col] = exog[col].values[:len(df_feat)]

        return df_feat

    def _create_single_period_features(self,
                                       df: pd.DataFrame,
                                       exog_row: Optional[pd.Series] = None) -> dict:
        """Create features for a single forecast period"""

        features = {}

        # Get last date
        last_date = df['ds'].iloc[-1]
        freq = pd.infer_freq(df['ds'])
        if freq is None:
            freq = 'M'

        next_date = last_date + pd.DateOffset(months=1) if freq == 'M' else last_date + pd.Timedelta(days=1)

        # Time-based features
        features['month'] = next_date.month
        features['quarter'] = next_date.quarter
        features['year'] = next_date.year
        features['dayofweek'] = next_date.dayofweek
        features['dayofyear'] = next_date.dayofyear

        # Lag features
        for lag in self.lag_features:
            if lag <= len(df):
                features[f'lag_{lag}'] = df['y'].iloc[-lag]
            else:
                features[f'lag_{lag}'] = df['y'].mean()

        # Rolling features
        for window in self.rolling_features:
            if window <= len(df):
                features[f'rolling_mean_{window}'] = df['y'].iloc[-window:].mean()
                features[f'rolling_std_{window}'] = df['y'].iloc[-window:].std()
            else:
                features[f'rolling_mean_{window}'] = df['y'].mean()
                features[f'rolling_std_{window}'] = df['y'].std()

        # Expanding mean
        features['expanding_mean'] = df['y'].mean()

        # YoY growth
        if len(df) >= 12:
            features['yoy_growth'] = (df['y'].iloc[-1] - df['y'].iloc[-12]) / df['y'].iloc[-12]
        else:
            features['yoy_growth'] = 0

        # Exogenous variables
        if exog_row is not None:
            for col, val in exog_row.items():
                features[col] = val

        return features

    def plot_feature_importance(self, top_n: int = 15):
        """Plot feature importance"""
        if self.model is None:
            raise ValueError("Model not fitted yet")

        import matplotlib.pyplot as plt
        import xgboost as xgb

        fig, ax = plt.subplots(figsize=(10, 8))
        xgb.plot_importance(self.model, max_num_features=top_n, ax=ax)
        plt.tight_layout()
        return fig
