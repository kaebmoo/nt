"""
Multi-output XGBoost Model for Joint Forecasting
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from .base_model import BaseForecastModel, ForecastResult


class MultiOutputXGBoostModel(BaseForecastModel):
    """
    Multi-output XGBoost model for forecasting multiple variables simultaneously

    Best for:
    - Forecasting Revenue and Expense together
    - Capturing complex non-linear relationships
    - Feature engineering across multiple variables
    - High accuracy requirements
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
        """Initialize Multi-output XGBoost model"""
        super().__init__(name="MultiOutputXGBoost", **kwargs)

        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.lag_features = lag_features
        self.rolling_features = rolling_features

        self.model = None
        self.feature_names = []
        self.target_names = []

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            target_columns: List[str] = None,
            exog: Optional[pd.DataFrame] = None) -> 'MultiOutputXGBoostModel':
        """
        Fit multi-output XGBoost model

        Args:
            df: DataFrame with time series data
            date_column: Name of date column
            target_columns: List of target columns (e.g., ['revenue', 'expense'])
            exog: External variables

        Returns:
            self
        """
        try:
            import xgboost as xgb
            from sklearn.multioutput import MultiOutputRegressor
        except ImportError:
            raise ImportError("xgboost not installed. Run: pip install xgboost scikit-learn")

        if target_columns is None:
            raise ValueError("target_columns must be specified")

        self.target_names = target_columns

        # Prepare data
        df_sorted = df.sort_values(date_column).reset_index(drop=True)
        self.df_prep = df_sorted.copy()

        # Create features
        df_features = self._create_features(df_sorted, target_columns, exog)

        # Remove rows with NaN
        df_features = df_features.dropna()

        # Prepare X and y
        feature_cols = [col for col in df_features.columns
                       if col not in [date_column] + target_columns]
        self.feature_names = feature_cols

        X = df_features[feature_cols]
        y = df_features[target_columns]

        # Store last data for forecasting
        self.last_features = df_features.copy()
        self.last_values = df_sorted.copy()

        # Initialize multi-output XGBoost
        base_model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            objective='reg:squarederror',
            random_state=42
        )

        self.model = MultiOutputRegressor(base_model)

        # Fit
        self.model.fit(X, y)

        self.is_fitted = True
        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> Dict[str, ForecastResult]:
        """
        Generate forecast for all target variables

        Args:
            periods: Number of periods to forecast
            exog: External variables for forecast period

        Returns:
            Dictionary of {variable_name: ForecastResult}
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Recursive forecasting
        forecasts = {name: [] for name in self.target_names}
        current_df = self.last_values.copy()

        for i in range(periods):
            # Create features for next period
            features_dict = self._create_single_period_features(
                current_df,
                self.target_names,
                exog.iloc[i] if exog is not None and i < len(exog) else None
            )

            # Predict all outputs
            X_pred = pd.DataFrame([features_dict])[self.feature_names]
            y_pred = self.model.predict(X_pred)[0]

            # Store forecasts
            for j, name in enumerate(self.target_names):
                forecasts[name].append(y_pred[j])

            # Update current_df for next iteration
            last_date = current_df['ds'].iloc[-1]
            freq = pd.infer_freq(current_df['ds'])
            if freq is None:
                freq = 'M'

            next_date = last_date + pd.DateOffset(months=1) if freq == 'M' else last_date + pd.Timedelta(days=1)

            new_row = pd.DataFrame({
                'ds': [next_date]
            })

            for j, name in enumerate(self.target_names):
                new_row[name] = y_pred[j]

            current_df = pd.concat([current_df, new_row], ignore_index=True)

        # Create forecast dataframes
        last_date = self.df_prep['ds'].iloc[-1]
        freq = pd.infer_freq(self.df_prep['ds'])
        if freq is None:
            freq = 'M'

        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=freq
        )[1:]

        results = {}

        # Calculate historical predictions
        X_hist = self.last_features[self.feature_names].dropna()
        y_hist_pred = self.model.predict(X_hist)

        for i, name in enumerate(self.target_names):
            # Forecast DataFrame
            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': forecasts[name]
            })

            # Calculate confidence intervals using historical error
            historical_actual = self.last_features[name].dropna().values
            historical_pred = y_hist_pred[:len(historical_actual), i]
            residuals = historical_actual - historical_pred
            std_error = np.std(residuals)

            forecast_df['yhat_lower'] = forecast_df['yhat'] - 1.96 * std_error
            forecast_df['yhat_upper'] = forecast_df['yhat'] + 1.96 * std_error

            # Historical fitted values
            historical_df = pd.DataFrame({
                'ds': self.df_prep['ds'].iloc[-len(historical_pred):].values,
                'yhat': historical_pred
            })

            # Metrics
            from src.utils.metrics import calculate_metrics
            metrics = calculate_metrics(historical_actual, historical_pred)

            # Feature importance
            feature_importance = dict(zip(
                self.feature_names,
                self.model.estimators_[i].feature_importances_
            ))

            results[name] = ForecastResult(
                forecast_df=forecast_df,
                historical_df=historical_df,
                metrics=metrics,
                model_params=self.get_params(),
                model_name=f"MultiOutputXGBoost_{name}",
                confidence_intervals=forecast_df[['ds', 'yhat_lower', 'yhat_upper']],
                feature_importance=feature_importance
            )

        return results

    def _create_features(self,
                        df: pd.DataFrame,
                        target_columns: List[str],
                        exog: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Create features for all target variables"""

        df_feat = df.copy()

        # Time features
        df_feat['month'] = df_feat['ds'].dt.month
        df_feat['quarter'] = df_feat['ds'].dt.quarter
        df_feat['year'] = df_feat['ds'].dt.year

        # Create lag and rolling features for each target
        for target in target_columns:
            # Lag features
            for lag in self.lag_features:
                df_feat[f'{target}_lag_{lag}'] = df_feat[target].shift(lag)

            # Rolling features
            for window in self.rolling_features:
                df_feat[f'{target}_rolling_mean_{window}'] = df_feat[target].rolling(window).mean()
                df_feat[f'{target}_rolling_std_{window}'] = df_feat[target].rolling(window).std()

            # YoY growth
            if len(df_feat) >= 12:
                df_feat[f'{target}_yoy_growth'] = df_feat[target].pct_change(12)

        # Cross-variable features (if multiple targets)
        if len(target_columns) >= 2:
            # Example: revenue/expense ratio
            if 'revenue' in target_columns and 'expense' in target_columns:
                df_feat['expense_revenue_ratio'] = df_feat['expense'] / (df_feat['revenue'] + 1)
                df_feat['profit'] = df_feat['revenue'] - df_feat['expense']
                df_feat['profit_lag1'] = df_feat['profit'].shift(1)
                df_feat['margin'] = df_feat['profit'] / (df_feat['revenue'] + 1)
                df_feat['margin_lag1'] = df_feat['margin'].shift(1)

        # Add exogenous variables
        if exog is not None:
            for col in exog.columns:
                df_feat[col] = exog[col].values[:len(df_feat)]

        return df_feat

    def _create_single_period_features(self,
                                       df: pd.DataFrame,
                                       target_columns: List[str],
                                       exog_row: Optional[pd.Series] = None) -> dict:
        """Create features for single forecast period"""

        features = {}

        # Time features
        last_date = df['ds'].iloc[-1]
        freq = pd.infer_freq(df['ds'])
        if freq is None:
            freq = 'M'

        next_date = last_date + pd.DateOffset(months=1) if freq == 'M' else last_date + pd.Timedelta(days=1)

        features['month'] = next_date.month
        features['quarter'] = next_date.quarter
        features['year'] = next_date.year

        # Lag and rolling features for each target
        for target in target_columns:
            for lag in self.lag_features:
                if lag <= len(df):
                    features[f'{target}_lag_{lag}'] = df[target].iloc[-lag]
                else:
                    features[f'{target}_lag_{lag}'] = df[target].mean()

            for window in self.rolling_features:
                if window <= len(df):
                    features[f'{target}_rolling_mean_{window}'] = df[target].iloc[-window:].mean()
                    features[f'{target}_rolling_std_{window}'] = df[target].iloc[-window:].std()
                else:
                    features[f'{target}_rolling_mean_{window}'] = df[target].mean()
                    features[f'{target}_rolling_std_{window}'] = df[target].std()

            if len(df) >= 12:
                features[f'{target}_yoy_growth'] = (df[target].iloc[-1] - df[target].iloc[-12]) / (df[target].iloc[-12] + 1)
            else:
                features[f'{target}_yoy_growth'] = 0

        # Cross-variable features
        if 'revenue' in target_columns and 'expense' in target_columns:
            revenue = df['revenue'].iloc[-1]
            expense = df['expense'].iloc[-1]

            features['expense_revenue_ratio'] = expense / (revenue + 1)
            features['profit'] = revenue - expense
            features['profit_lag1'] = df['revenue'].iloc[-2] - df['expense'].iloc[-2] if len(df) > 1 else 0
            features['margin'] = (revenue - expense) / (revenue + 1)
            features['margin_lag1'] = ((df['revenue'].iloc[-2] - df['expense'].iloc[-2]) /
                                      (df['revenue'].iloc[-2] + 1) if len(df) > 1 else 0)

        # Exogenous variables
        if exog_row is not None:
            for col, val in exog_row.items():
                features[col] = val

        return features
