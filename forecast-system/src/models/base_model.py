"""
Base Forecast Model
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


@dataclass
class ForecastResult:
    """Container for forecast results"""

    forecast_df: pd.DataFrame  # Forecast values with dates
    historical_df: pd.DataFrame  # Historical data used for training
    metrics: Dict[str, float]  # Performance metrics (MAPE, MAE, RMSE, etc.)
    model_params: Dict[str, Any]  # Model parameters used
    model_name: str  # Name of the model
    confidence_intervals: Optional[pd.DataFrame] = None  # Upper/lower bounds
    feature_importance: Optional[Dict[str, float]] = None  # For ML models
    components: Optional[pd.DataFrame] = None  # Trend, seasonality components

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            'forecast': self.forecast_df.to_dict('records'),
            'metrics': self.metrics,
            'model_name': self.model_name,
            'model_params': self.model_params
        }

    def summary(self) -> str:
        """Generate summary text"""
        summary = f"=== {self.model_name} Forecast Summary ===\n"
        summary += f"Forecast periods: {len(self.forecast_df)}\n"
        summary += f"Historical periods: {len(self.historical_df)}\n"
        summary += "\nMetrics:\n"
        for metric, value in self.metrics.items():
            if 'pct' in metric.lower() or 'mape' in metric.lower():
                summary += f"  {metric.upper()}: {value:.2%}\n"
            else:
                summary += f"  {metric.upper()}: {value:,.2f}\n"
        return summary


class BaseForecastModel(ABC):
    """Abstract base class for all forecast models"""

    def __init__(self, name: str = "BaseForecast", **kwargs):
        """
        Initialize forecast model

        Args:
            name: Model name
            **kwargs: Additional model-specific parameters
        """
        self.name = name
        self.params = kwargs
        self.model = None
        self.is_fitted = False

    @abstractmethod
    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'BaseForecastModel':
        """
        Fit the forecast model

        Args:
            df: DataFrame with historical data
            date_column: Name of date column
            value_column: Name of value column to forecast
            exog: External variables (if supported)

        Returns:
            self
        """
        pass

    @abstractmethod
    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """
        Generate forecast

        Args:
            periods: Number of periods to forecast
            exog: External variables for forecast period (if supported)

        Returns:
            ForecastResult object
        """
        pass

    def fit_predict(self,
                    df: pd.DataFrame,
                    date_column: str = 'ds',
                    value_column: str = 'y',
                    periods: int = 12,
                    exog: Optional[pd.DataFrame] = None,
                    exog_future: Optional[pd.DataFrame] = None) -> ForecastResult:
        """
        Fit model and generate forecast in one step

        Args:
            df: DataFrame with historical data
            date_column: Name of date column
            value_column: Name of value column
            periods: Number of periods to forecast
            exog: External variables for training
            exog_future: External variables for forecast period

        Returns:
            ForecastResult object
        """
        self.fit(df, date_column, value_column, exog)
        return self.predict(periods, exog_future)

    def cross_validate(self,
                       df: pd.DataFrame,
                       date_column: str = 'ds',
                       value_column: str = 'y',
                       n_splits: int = 3,
                       test_size: int = 12) -> Dict[str, List[float]]:
        """
        Perform time series cross-validation

        Args:
            df: DataFrame with historical data
            date_column: Name of date column
            value_column: Name of value column
            n_splits: Number of CV splits
            test_size: Size of test set

        Returns:
            Dictionary of metrics across splits
        """
        from sklearn.model_selection import TimeSeriesSplit
        from .metrics import calculate_metrics

        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)

        metrics_list = {
            'mape': [],
            'mae': [],
            'rmse': [],
            'r2': []
        }

        df_sorted = df.sort_values(date_column)

        for train_idx, test_idx in tscv.split(df_sorted):
            # Split data
            train_df = df_sorted.iloc[train_idx]
            test_df = df_sorted.iloc[test_idx]

            # Fit and predict
            self.fit(train_df, date_column, value_column)
            result = self.predict(len(test_df))

            # Calculate metrics
            actual = test_df[value_column].values
            predicted = result.forecast_df['yhat'].values[:len(actual)]

            metrics = calculate_metrics(actual, predicted)

            for key in metrics_list:
                if key in metrics:
                    metrics_list[key].append(metrics[key])

        return metrics_list

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters"""
        return self.params.copy()

    def set_params(self, **params) -> 'BaseForecastModel':
        """Set model parameters"""
        self.params.update(params)
        return self

    @staticmethod
    def prepare_data(df: pd.DataFrame,
                     date_column: str = 'ds',
                     value_column: str = 'y') -> pd.DataFrame:
        """
        Prepare data for forecasting

        Args:
            df: Input DataFrame
            date_column: Name of date column
            value_column: Name of value column

        Returns:
            Prepared DataFrame with 'ds' and 'y' columns
        """
        df_prep = df[[date_column, value_column]].copy()
        df_prep.columns = ['ds', 'y']

        # Ensure datetime
        df_prep['ds'] = pd.to_datetime(df_prep['ds'])

        # Sort by date
        df_prep = df_prep.sort_values('ds').reset_index(drop=True)

        # Remove duplicates
        df_prep = df_prep.drop_duplicates(subset='ds', keep='last')

        return df_prep
