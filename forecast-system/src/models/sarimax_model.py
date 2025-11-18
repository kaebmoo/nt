"""
SARIMAX Forecast Model
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple
from .base_model import BaseForecastModel, ForecastResult


class SARIMAXModel(BaseForecastModel):
    """
    SARIMAX (Seasonal ARIMA with eXogenous variables) model

    Best for:
    - Stationary or trend-stationary data
    - Data with external factors/variables
    - Financial time series
    - When you need statistical rigor
    """

    def __init__(self,
                 order: Tuple[int, int, int] = (1, 1, 1),
                 seasonal_order: Tuple[int, int, int, int] = (1, 1, 1, 12),
                 auto_arima: bool = True,
                 **kwargs):
        """
        Initialize SARIMAX model

        Args:
            order: (p, d, q) order of ARIMA
            seasonal_order: (P, D, Q, s) seasonal order
            auto_arima: Use auto_arima to find best parameters
        """
        super().__init__(name="SARIMAX", **kwargs)

        self.order = order
        self.seasonal_order = seasonal_order
        self.auto_arima = auto_arima

        self.model = None
        self.results = None

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'SARIMAXModel':
        """Fit SARIMAX model"""

        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAX
        except ImportError:
            raise ImportError("statsmodels not installed. Run: pip install statsmodels")

        # Prepare data
        df_prep = self.prepare_data(df, date_column, value_column)
        self.df_prep = df_prep

        # If auto_arima enabled, find best parameters
        if self.auto_arima:
            self.order, self.seasonal_order = self._auto_arima(
                df_prep['y'],
                exog=exog
            )

        # Fit SARIMAX
        try:
            self.model = SARIMAX(
                df_prep['y'],
                exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            self.results = self.model.fit(disp=False)
            self.is_fitted = True

        except Exception as e:
            # If seasonal order fails, try without seasonality
            print(f"SARIMAX fitting failed, trying without seasonality: {e}")
            self.seasonal_order = (0, 0, 0, 0)

            self.model = SARIMAX(
                df_prep['y'],
                exog=exog,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )

            self.results = self.model.fit(disp=False)
            self.is_fitted = True

        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """Generate forecast using SARIMAX"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Generate forecast
        forecast = self.results.forecast(steps=periods, exog=exog)

        # Get confidence intervals
        forecast_obj = self.results.get_forecast(steps=periods, exog=exog)
        conf_int = forecast_obj.conf_int()

        # Create future dates
        last_date = self.df_prep['ds'].iloc[-1]
        freq = pd.infer_freq(self.df_prep['ds'])
        if freq is None:
            freq = 'M'  # Default to monthly

        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=freq
        )[1:]  # Exclude start date

        # Create forecast dataframe
        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': forecast.values,
            'yhat_lower': conf_int.iloc[:, 0].values,
            'yhat_upper': conf_int.iloc[:, 1].values
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
                'order': self.order,
                'seasonal_order': self.seasonal_order
            },
            model_name=self.name,
            confidence_intervals=confidence_df
        )

    def _auto_arima(self,
                    y: pd.Series,
                    exog: Optional[pd.DataFrame] = None) -> Tuple[Tuple, Tuple]:
        """
        Find best ARIMA parameters using auto_arima

        Args:
            y: Time series data
            exog: Exogenous variables

        Returns:
            Tuple of (order, seasonal_order)
        """
        try:
            from pmdarima import auto_arima

            # Determine seasonal period
            freq = pd.infer_freq(self.df_prep['ds'])
            if freq == 'M' or freq == 'MS':
                m = 12
            elif freq == 'Q' or freq == 'QS':
                m = 4
            elif freq == 'W':
                m = 52
            else:
                m = 1  # No seasonality

            print(f"Running auto_arima (this may take a while)...")

            model = auto_arima(
                y,
                exogenous=exog,
                start_p=0, start_q=0,
                max_p=3, max_q=3,
                start_P=0, start_Q=0,
                max_P=2, max_Q=2,
                m=m,
                seasonal=True if m > 1 else False,
                d=None,  # Let auto_arima determine
                D=None,
                trace=False,
                error_action='ignore',
                suppress_warnings=True,
                stepwise=True
            )

            order = model.order
            seasonal_order = model.seasonal_order

            print(f"Best ARIMA order: {order}")
            print(f"Best seasonal order: {seasonal_order}")

            return order, seasonal_order

        except ImportError:
            print("pmdarima not installed. Using default parameters.")
            return self.order, self.seasonal_order
        except Exception as e:
            print(f"auto_arima failed: {e}. Using default parameters.")
            return self.order, self.seasonal_order

    def plot_diagnostics(self):
        """Plot model diagnostics"""
        if self.results is None:
            raise ValueError("Model not fitted yet")

        import matplotlib.pyplot as plt

        fig = self.results.plot_diagnostics(figsize=(15, 10))
        return fig
