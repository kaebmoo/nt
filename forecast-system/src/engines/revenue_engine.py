"""
Revenue Forecast Engine
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from src.models import (ProphetModel, SARIMAXModel, XGBoostModel,
                        HoltWintersModel, EnsembleModel, ForecastResult)
from src.core.data_processor import DataProcessor


class RevenueForecastEngine:
    """
    High-level engine for revenue forecasting

    Handles:
    - Total revenue forecasting
    - Revenue by sales unit / product / business group
    - Hierarchical revenue forecasting
    """

    def __init__(self):
        self.processor = DataProcessor()
        self.models = {}
        self.results = {}

    def forecast(self,
                df: pd.DataFrame,
                date_column: str = 'month',
                value_column: str = 'revenue',
                model_type: str = 'prophet',
                forecast_periods: int = 12,
                exog: Optional[pd.DataFrame] = None,
                **model_params) -> ForecastResult:
        """
        Forecast total revenue

        Args:
            df: DataFrame with historical revenue data
            date_column: Name of date column
            value_column: Name of revenue column
            model_type: Type of model ('prophet', 'sarimax', 'xgboost', 'holt_winters', 'ensemble')
            forecast_periods: Number of periods to forecast
            exog: External variables (optional)
            **model_params: Additional parameters for the model

        Returns:
            ForecastResult object
        """
        # Clean data
        df_clean = self.processor.clean_data(
            df,
            date_column=date_column,
            value_column=value_column
        )

        # Select and initialize model
        model = self._get_model(model_type, **model_params)

        # Fit and predict
        result = model.fit_predict(
            df_clean,
            date_column=date_column,
            value_column=value_column,
            periods=forecast_periods,
            exog=exog
        )

        self.models['total'] = model
        self.results['total'] = result

        return result

    def forecast_by_dimension(self,
                             df: pd.DataFrame,
                             dimension: str,
                             date_column: str = 'month',
                             value_column: str = 'revenue',
                             model_type: str = 'prophet',
                             forecast_periods: int = 12,
                             **model_params) -> Dict[str, ForecastResult]:
        """
        Forecast revenue by dimension (e.g., sales_unit, product, business_group)

        Args:
            df: DataFrame with revenue data
            dimension: Column name to group by
            date_column: Name of date column
            value_column: Name of revenue column
            model_type: Type of model
            forecast_periods: Number of periods to forecast
            **model_params: Additional model parameters

        Returns:
            Dictionary of {dimension_value: ForecastResult}
        """
        if dimension not in df.columns:
            raise ValueError(f"Dimension '{dimension}' not found in DataFrame")

        results = {}
        dimension_values = df[dimension].unique()

        print(f"Forecasting for {len(dimension_values)} {dimension} groups...")

        for dim_value in dimension_values:
            print(f"  Processing {dimension}={dim_value}...")

            # Filter data for this dimension
            df_subset = df[df[dimension] == dim_value].copy()

            # Aggregate by date
            df_agg = df_subset.groupby(date_column)[value_column].sum().reset_index()

            try:
                # Get model
                model = self._get_model(model_type, **model_params)

                # Forecast
                result = model.fit_predict(
                    df_agg,
                    date_column=date_column,
                    value_column=value_column,
                    periods=forecast_periods
                )

                results[dim_value] = result
                print(f"    ✓ Success (MAPE: {result.metrics.get('mape', 0):.2%})")

            except Exception as e:
                print(f"    ✗ Failed: {e}")
                continue

        self.results[f'by_{dimension}'] = results
        return results

    def forecast_hierarchical(self,
                             df: pd.DataFrame,
                             hierarchy: List[str],
                             date_column: str = 'month',
                             value_column: str = 'revenue',
                             model_type: str = 'prophet',
                             forecast_periods: int = 12,
                             reconciliation_method: str = 'bottom_up',
                             **model_params) -> Dict[str, any]:
        """
        Hierarchical revenue forecasting with reconciliation

        Args:
            df: DataFrame with revenue data
            hierarchy: List of hierarchy levels (e.g., ['total', 'sales_unit', 'product'])
            date_column: Name of date column
            value_column: Name of revenue column
            model_type: Type of model
            forecast_periods: Number of periods to forecast
            reconciliation_method: 'bottom_up', 'top_down', or 'middle_out'
            **model_params: Additional model parameters

        Returns:
            Dictionary with forecasts at each level
        """
        results = {
            'forecasts': {},
            'method': reconciliation_method
        }

        # Forecast at each level
        for level in hierarchy:
            if level == 'total':
                # Aggregate all revenue
                df_total = df.groupby(date_column)[value_column].sum().reset_index()

                model = self._get_model(model_type, **model_params)
                result = model.fit_predict(
                    df_total,
                    date_column=date_column,
                    value_column=value_column,
                    periods=forecast_periods
                )

                results['forecasts']['total'] = result

            else:
                # Forecast by dimension
                level_results = self.forecast_by_dimension(
                    df,
                    dimension=level,
                    date_column=date_column,
                    value_column=value_column,
                    model_type=model_type,
                    forecast_periods=forecast_periods,
                    **model_params
                )

                results['forecasts'][level] = level_results

        # Reconciliation (simple version)
        if reconciliation_method == 'bottom_up':
            # Sum bottom level to get top level
            bottom_level = hierarchy[-1]
            if bottom_level in results['forecasts']:
                bottom_forecasts = results['forecasts'][bottom_level]

                # Sum all bottom forecasts
                all_forecasts = []
                for result in bottom_forecasts.values():
                    all_forecasts.append(result.forecast_df['yhat'].values)

                reconciled_total = np.sum(all_forecasts, axis=0)

                # Update total forecast
                if 'total' in results['forecasts']:
                    results['forecasts']['total'].forecast_df['yhat_reconciled'] = reconciled_total

        return results

    def compare_models(self,
                      df: pd.DataFrame,
                      date_column: str = 'month',
                      value_column: str = 'revenue',
                      models: List[str] = ['prophet', 'sarimax', 'xgboost'],
                      forecast_periods: int = 12) -> pd.DataFrame:
        """
        Compare different models

        Args:
            df: DataFrame with revenue data
            date_column: Name of date column
            value_column: Name of revenue column
            models: List of model types to compare
            forecast_periods: Number of periods to forecast

        Returns:
            DataFrame with comparison
        """
        results = {}

        for model_type in models:
            print(f"Training {model_type}...")

            try:
                model = self._get_model(model_type)
                result = model.fit_predict(
                    df,
                    date_column=date_column,
                    value_column=value_column,
                    periods=forecast_periods
                )

                results[model_type] = result

            except Exception as e:
                print(f"  Failed: {e}")
                continue

        # Create comparison DataFrame
        comparison = []
        for model_name, result in results.items():
            row = {'Model': model_name}
            row.update(result.metrics)
            comparison.append(row)

        return pd.DataFrame(comparison)

    def _get_model(self, model_type: str, **params):
        """Get model instance by type"""
        model_type = model_type.lower()

        if model_type == 'prophet':
            return ProphetModel(**params)
        elif model_type == 'sarimax':
            return SARIMAXModel(**params)
        elif model_type == 'xgboost':
            return XGBoostModel(**params)
        elif model_type == 'holt_winters':
            return HoltWintersModel(**params)
        elif model_type == 'ensemble':
            return EnsembleModel(**params)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def get_forecast_summary(self, dimension: Optional[str] = None) -> pd.DataFrame:
        """Get summary of forecasts"""
        if dimension is None:
            # Total forecast
            if 'total' in self.results:
                return self.results['total'].forecast_df
        else:
            # By dimension
            key = f'by_{dimension}'
            if key in self.results:
                all_forecasts = []

                for dim_value, result in self.results[key].items():
                    df = result.forecast_df.copy()
                    df[dimension] = dim_value
                    all_forecasts.append(df)

                return pd.concat(all_forecasts, ignore_index=True)

        return pd.DataFrame()
