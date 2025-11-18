"""
Prophet Forecast Model
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
from .base_model import BaseForecastModel, ForecastResult


class ProphetModel(BaseForecastModel):
    """
    Facebook Prophet model for time series forecasting

    Best for:
    - Data with strong seasonality
    - Multiple seasonality patterns
    - Handling holidays and special events
    - Trend changes
    """

    def __init__(self,
                 yearly_seasonality: bool = True,
                 weekly_seasonality: bool = False,
                 daily_seasonality: bool = False,
                 seasonality_mode: str = 'multiplicative',
                 changepoint_prior_scale: float = 0.05,
                 seasonality_prior_scale: float = 10.0,
                 holidays: Optional[pd.DataFrame] = None,
                 country_holidays: Optional[str] = None,
                 **kwargs):
        """
        Initialize Prophet model

        Args:
            yearly_seasonality: Enable yearly seasonality
            weekly_seasonality: Enable weekly seasonality
            daily_seasonality: Enable daily seasonality
            seasonality_mode: 'additive' or 'multiplicative'
            changepoint_prior_scale: Flexibility of trend changes
            seasonality_prior_scale: Strength of seasonality
            holidays: DataFrame with holiday dates
            country_holidays: Country code for holidays (e.g., 'TH' for Thailand)
        """
        super().__init__(name="Prophet", **kwargs)

        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.seasonality_mode = seasonality_mode
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        self.holidays = holidays
        self.country_holidays = country_holidays

        self.model = None
        self.freq = None

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'ProphetModel':
        """Fit Prophet model"""

        try:
            from prophet import Prophet
        except ImportError:
            raise ImportError("Prophet not installed. Run: pip install prophet")

        # Prepare data
        df_prep = self.prepare_data(df, date_column, value_column)

        # Detect frequency
        self.freq = pd.infer_freq(df_prep['ds'])
        if self.freq is None:
            # Calculate median difference
            diff = df_prep['ds'].diff().median()
            if diff.days >= 28 and diff.days <= 31:
                self.freq = 'M'
            elif diff.days >= 89 and diff.days <= 92:
                self.freq = 'Q'
            elif diff.days >= 365 and diff.days <= 366:
                self.freq = 'Y'
            else:
                self.freq = 'D'

        # Initialize Prophet
        self.model = Prophet(
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            seasonality_mode=self.seasonality_mode,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale,
            holidays=self.holidays
        )

        # Add country holidays
        if self.country_holidays:
            try:
                self.model.add_country_holidays(country_name=self.country_holidays)
            except:
                pass  # Country not supported

        # Add exogenous variables
        if exog is not None:
            for col in exog.columns:
                self.model.add_regressor(col)
            df_prep = pd.concat([df_prep, exog], axis=1)

        # Fit model
        with pd.option_context('mode.chained_assignment', None):
            self.model.fit(df_prep)

        self.is_fitted = True
        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """Generate forecast using Prophet"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Create future dataframe
        future = self.model.make_future_dataframe(periods=periods, freq=self.freq)

        # Add exogenous variables
        if exog is not None:
            # Ensure exog has same length as future
            if len(exog) < len(future):
                # Extend with last values
                last_row = exog.iloc[-1:].copy()
                for _ in range(len(future) - len(exog)):
                    exog = pd.concat([exog, last_row], ignore_index=True)
            future = pd.concat([future.reset_index(drop=True), exog.reset_index(drop=True)], axis=1)

        # Predict
        forecast_full = self.model.predict(future)

        # Extract forecast period only
        forecast_df = forecast_full.iloc[-periods:][['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        forecast_df = forecast_df.reset_index(drop=True)

        # Extract historical
        historical_df = forecast_full.iloc[:-periods][['ds', 'yhat']].copy()

        # Confidence intervals
        confidence_df = forecast_df[['ds', 'yhat_lower', 'yhat_upper']].copy()

        # Components
        components_df = None
        if hasattr(self.model, 'predict_components'):
            try:
                components_df = self.model.predict(future)[['ds', 'trend', 'yearly', 'weekly']].iloc[-periods:]
            except:
                pass

        # Calculate metrics (in-sample)
        from src.utils.metrics import calculate_metrics
        actual = self.model.history['y'].values
        predicted = forecast_full.iloc[:len(actual)]['yhat'].values
        metrics = calculate_metrics(actual, predicted)

        return ForecastResult(
            forecast_df=forecast_df,
            historical_df=historical_df,
            metrics=metrics,
            model_params=self.get_params(),
            model_name=self.name,
            confidence_intervals=confidence_df,
            components=components_df
        )

    def plot_components(self):
        """Plot forecast components (trend, seasonality)"""
        if self.model is None:
            raise ValueError("Model not fitted yet")

        try:
            from prophet.plot import plot_components
            import matplotlib.pyplot as plt

            future = self.model.make_future_dataframe(periods=12, freq=self.freq)
            forecast = self.model.predict(future)

            fig = plot_components(self.model, forecast)
            return fig
        except Exception as e:
            print(f"Could not plot components: {e}")
            return None
