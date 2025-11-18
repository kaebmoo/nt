"""
Holt-Winters Exponential Smoothing Model
"""

import pandas as pd
import numpy as np
from typing import Optional
from .base_model import BaseForecastModel, ForecastResult


class HoltWintersModel(BaseForecastModel):
    """
    Holt-Winters Exponential Smoothing model

    Best for:
    - Quick forecasting
    - Data with trend and seasonality
    - Simple baseline models
    - Fast computation
    """

    def __init__(self,
                 seasonal: str = 'add',
                 trend: str = 'add',
                 seasonal_periods: int = 12,
                 damped_trend: bool = False,
                 **kwargs):
        """
        Initialize Holt-Winters model

        Args:
            seasonal: 'add' (additive) or 'mul' (multiplicative)
            trend: 'add', 'mul', or None
            seasonal_periods: Number of periods in a season (12 for monthly data)
            damped_trend: Whether to use damped trend
        """
        super().__init__(name="Holt-Winters", **kwargs)

        self.seasonal = seasonal
        self.trend = trend
        self.seasonal_periods = seasonal_periods
        self.damped_trend = damped_trend

        self.model = None
        self.results = None

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'HoltWintersModel':
        """Fit Holt-Winters model"""

        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
        except ImportError:
            raise ImportError("statsmodels not installed. Run: pip install statsmodels")

        # Prepare data
        df_prep = self.prepare_data(df, date_column, value_column)
        self.df_prep = df_prep

        # Check if we have enough data for seasonality
        if len(df_prep) < 2 * self.seasonal_periods:
            print(f"Warning: Not enough data for seasonal_periods={self.seasonal_periods}")
            print(f"Setting seasonal to None")
            self.seasonal = None

        # Fit model
        try:
            self.model = ExponentialSmoothing(
                df_prep['y'],
                seasonal=self.seasonal,
                trend=self.trend,
                seasonal_periods=self.seasonal_periods if self.seasonal else None,
                damped_trend=self.damped_trend
            )

            self.results = self.model.fit(optimized=True)
            self.is_fitted = True

        except Exception as e:
            # Try simpler model if fails
            print(f"Holt-Winters fitting failed: {e}")
            print("Trying simpler model (additive, no damping)")

            self.seasonal = 'add'
            self.trend = 'add'
            self.damped_trend = False

            self.model = ExponentialSmoothing(
                df_prep['y'],
                seasonal=self.seasonal,
                trend=self.trend,
                seasonal_periods=self.seasonal_periods if self.seasonal else None,
                damped_trend=False
            )

            self.results = self.model.fit(optimized=True)
            self.is_fitted = True

        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """Generate forecast using Holt-Winters"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Generate forecast
        forecast = self.results.forecast(steps=periods)

        # Create future dates
        last_date = self.df_prep['ds'].iloc[-1]
        freq = pd.infer_freq(self.df_prep['ds'])
        if freq is None:
            freq = 'M'

        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=freq
        )[1:]

        # Calculate confidence intervals (using residual std)
        residuals = self.results.resid
        std_error = np.std(residuals)

        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecast.values,
            'yhat_lower': forecast.values - 1.96 * std_error,
            'yhat_upper': forecast.values + 1.96 * std_error
        })

        # Historical fitted values
        historical_df = pd.DataFrame({
            'ds': self.df_prep['ds'],
            'yhat': self.results.fittedvalues
        })

        # Confidence intervals
        confidence_df = forecast_df[['ds', 'yhat_lower', 'yhat_upper']].copy()

        # Calculate metrics
        from src.utils.metrics import calculate_metrics
        actual = self.df_prep['y'].values
        predicted = self.results.fittedvalues.values
        metrics = calculate_metrics(actual, predicted)

        # Add model-specific metrics
        metrics['aic'] = self.results.aic
        metrics['bic'] = self.results.bic

        return ForecastResult(
            forecast_df=forecast_df,
            historical_df=historical_df,
            metrics=metrics,
            model_params={
                'seasonal': self.seasonal,
                'trend': self.trend,
                'seasonal_periods': self.seasonal_periods,
                'damped_trend': self.damped_trend
            },
            model_name=self.name,
            confidence_intervals=confidence_df
        )

    def plot_components(self):
        """Plot level, trend, and seasonal components"""
        if self.results is None:
            raise ValueError("Model not fitted yet")

        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(3, 1, figsize=(12, 10))

        # Level
        axes[0].plot(self.df_prep['ds'], self.results.level)
        axes[0].set_title('Level Component')
        axes[0].set_ylabel('Level')
        axes[0].grid(True)

        # Trend (if exists)
        if self.trend:
            axes[1].plot(self.df_prep['ds'], self.results.trend)
            axes[1].set_title('Trend Component')
            axes[1].set_ylabel('Trend')
            axes[1].grid(True)

        # Seasonal (if exists)
        if self.seasonal:
            axes[2].plot(self.df_prep['ds'], self.results.season)
            axes[2].set_title('Seasonal Component')
            axes[2].set_ylabel('Seasonal')
            axes[2].grid(True)

        plt.tight_layout()
        return fig
