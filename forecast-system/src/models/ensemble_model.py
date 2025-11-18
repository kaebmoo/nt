"""
Ensemble Forecast Model
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from .base_model import BaseForecastModel, ForecastResult
from .prophet_model import ProphetModel
from .sarimax_model import SARIMAXModel
from .xgboost_model import XGBoostModel
from .holt_winters_model import HoltWintersModel


class EnsembleModel(BaseForecastModel):
    """
    Ensemble of multiple forecast models

    Best for:
    - Maximum accuracy
    - Reducing model uncertainty
    - Robust predictions
    - Competition-winning forecasts
    """

    def __init__(self,
                 models: Optional[List[str]] = None,
                 weights: Optional[Dict[str, float]] = None,
                 method: str = 'weighted_average',
                 **kwargs):
        """
        Initialize Ensemble model

        Args:
            models: List of model names to include ['prophet', 'sarimax', 'xgboost', 'holt_winters']
            weights: Dictionary of weights for each model (must sum to 1)
            method: Ensemble method ('weighted_average', 'simple_average', 'median')
        """
        super().__init__(name="Ensemble", **kwargs)

        if models is None:
            self.model_names = ['prophet', 'xgboost']
        else:
            self.model_names = models

        self.weights = weights
        self.method = method

        self.models = {}
        self.results = {}

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_column: str = 'y',
            exog: Optional[pd.DataFrame] = None) -> 'EnsembleModel':
        """Fit all models in ensemble"""

        print(f"Fitting ensemble with models: {self.model_names}")

        # Initialize and fit each model
        for model_name in self.model_names:
            print(f"  Fitting {model_name}...")

            try:
                if model_name.lower() == 'prophet':
                    model = ProphetModel()
                elif model_name.lower() == 'sarimax':
                    model = SARIMAXModel()
                elif model_name.lower() == 'xgboost':
                    model = XGBoostModel()
                elif model_name.lower() == 'holt_winters':
                    model = HoltWintersModel()
                else:
                    print(f"  Unknown model: {model_name}, skipping")
                    continue

                model.fit(df, date_column, value_column, exog)
                self.models[model_name] = model
                print(f"  {model_name} fitted successfully")

            except Exception as e:
                print(f"  Error fitting {model_name}: {e}")
                continue

        if len(self.models) == 0:
            raise ValueError("No models fitted successfully")

        self.is_fitted = True
        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> ForecastResult:
        """Generate ensemble forecast"""

        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Get predictions from all models
        all_forecasts = []
        all_metrics = {}

        for model_name, model in self.models.items():
            print(f"  Predicting with {model_name}...")

            try:
                result = model.predict(periods, exog)
                self.results[model_name] = result

                all_forecasts.append(result.forecast_df['yhat'].values)
                all_metrics[model_name] = result.metrics

            except Exception as e:
                print(f"  Error predicting with {model_name}: {e}")
                continue

        if len(all_forecasts) == 0:
            raise ValueError("No models generated forecasts successfully")

        # Combine forecasts
        forecasts_array = np.array(all_forecasts)

        if self.method == 'simple_average':
            combined_forecast = np.mean(forecasts_array, axis=0)

        elif self.method == 'median':
            combined_forecast = np.median(forecasts_array, axis=0)

        elif self.method == 'weighted_average':
            if self.weights is None:
                # Use inverse MAPE as weights
                mapes = {name: metrics.get('mape', 1.0)
                        for name, metrics in all_metrics.items()}

                # Avoid division by zero
                mapes = {k: max(v, 0.001) for k, v in mapes.items()}

                # Inverse MAPE
                inv_mapes = {k: 1 / v for k, v in mapes.items()}
                total = sum(inv_mapes.values())

                # Normalize to sum to 1
                self.weights = {k: v / total for k, v in inv_mapes.items()}

            print(f"  Ensemble weights: {self.weights}")

            # Weighted average
            combined_forecast = np.zeros(periods)
            for i, (model_name, forecast) in enumerate(zip(self.models.keys(), all_forecasts)):
                weight = self.weights.get(model_name, 0)
                combined_forecast += weight * forecast

        else:
            raise ValueError(f"Unknown ensemble method: {self.method}")

        # Calculate confidence intervals (std across models)
        combined_lower = np.percentile(forecasts_array, 2.5, axis=0)
        combined_upper = np.percentile(forecasts_array, 97.5, axis=0)

        # Create forecast dataframe
        # Get dates from first model
        first_result = list(self.results.values())[0]
        future_dates = first_result.forecast_df['ds'].values

        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': combined_forecast,
            'yhat_lower': combined_lower,
            'yhat_upper': combined_upper
        })

        # Historical - use first model
        historical_df = first_result.historical_df.copy()

        # Confidence intervals
        confidence_df = forecast_df[['ds', 'yhat_lower', 'yhat_upper']].copy()

        # Average metrics across models
        avg_metrics = {}
        metric_keys = list(all_metrics.values())[0].keys()

        for key in metric_keys:
            values = [metrics[key] for metrics in all_metrics.values() if key in metrics]
            if values:
                avg_metrics[key] = np.mean(values)

        return ForecastResult(
            forecast_df=forecast_df,
            historical_df=historical_df,
            metrics=avg_metrics,
            model_params={
                'models': list(self.models.keys()),
                'weights': self.weights,
                'method': self.method,
                'individual_metrics': all_metrics
            },
            model_name=self.name,
            confidence_intervals=confidence_df
        )

    def compare_models(self) -> pd.DataFrame:
        """Compare performance of individual models"""

        if not self.results:
            raise ValueError("No predictions available. Run predict() first.")

        comparison = []

        for model_name, result in self.results.items():
            row = {'model': model_name}
            row.update(result.metrics)
            comparison.append(row)

        return pd.DataFrame(comparison)

    def plot_comparison(self):
        """Plot forecasts from all models"""

        if not self.results:
            raise ValueError("No predictions available. Run predict() first.")

        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(15, 8))

        # Plot each model's forecast
        for model_name, result in self.results.items():
            ax.plot(result.forecast_df['ds'],
                   result.forecast_df['yhat'],
                   label=model_name,
                   marker='o')

        ax.set_xlabel('Date')
        ax.set_ylabel('Forecast')
        ax.set_title('Model Comparison')
        ax.legend()
        ax.grid(True)

        plt.tight_layout()
        return fig
