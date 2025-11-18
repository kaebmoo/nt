"""
Expense Forecast Engine
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from src.models import (ProphetModel, SARIMAXModel, XGBoostModel,
                        HoltWintersModel, ForecastResult)
from src.core.data_processor import DataProcessor
from sklearn.linear_model import LinearRegression


class ExpenseForecastEngine:
    """
    High-level engine for expense forecasting

    Handles:
    - Fixed cost forecasting (salary, rent, etc.)
    - Variable cost forecasting (COGS, commission, etc.)
    - Semi-variable costs
    - Expense by GL code / department / category
    """

    def __init__(self):
        self.processor = DataProcessor()
        self.models = {}
        self.results = {}
        self.expense_classification = {}

    def classify_expense_type(self,
                              df: pd.DataFrame,
                              value_column: str = 'expense',
                              revenue_column: Optional[str] = None,
                              cv_threshold: float = 0.1,
                              correlation_threshold: float = 0.7) -> pd.DataFrame:
        """
        Classify expenses as Fixed, Variable, or Semi-variable

        Args:
            df: DataFrame with expense data
            value_column: Name of expense column
            revenue_column: Name of revenue column (for correlation analysis)
            cv_threshold: Coefficient of variation threshold for fixed costs
            correlation_threshold: Correlation threshold for variable costs

        Returns:
            DataFrame with expense_type column added
        """
        df_classified = df.copy()

        # Calculate coefficient of variation (CV)
        cv = df[value_column].std() / df[value_column].mean()

        # Default classification
        expense_type = 'semi_variable'

        # Fixed cost: low variation
        if cv < cv_threshold:
            expense_type = 'fixed'

        # Variable cost: high correlation with revenue
        elif revenue_column and revenue_column in df.columns:
            correlation = df[value_column].corr(df[revenue_column])

            if abs(correlation) > correlation_threshold:
                expense_type = 'variable'

        df_classified['expense_type'] = expense_type
        self.expense_classification[value_column] = expense_type

        return df_classified

    def forecast_fixed_costs(self,
                            df: pd.DataFrame,
                            date_column: str = 'month',
                            value_column: str = 'expense',
                            forecast_periods: int = 12,
                            method: str = 'moving_average',
                            window: int = 6) -> ForecastResult:
        """
        Forecast fixed costs (salary, rent, etc.)

        Args:
            df: DataFrame with expense data
            date_column: Name of date column
            value_column: Name of expense column
            forecast_periods: Number of periods to forecast
            method: 'moving_average', 'last_value', or 'prophet'
            window: Window size for moving average

        Returns:
            ForecastResult object
        """
        df_clean = self.processor.clean_data(df, date_column, value_column)

        if method == 'moving_average':
            # Simple moving average
            last_values = df_clean[value_column].tail(window)
            forecast_value = last_values.mean()

            # Create forecast dataframe
            last_date = pd.to_datetime(df_clean[date_column].iloc[-1])
            future_dates = pd.date_range(start=last_date, periods=forecast_periods + 1, freq='M')[1:]

            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': [forecast_value] * forecast_periods,
                'yhat_lower': [forecast_value * 0.95] * forecast_periods,
                'yhat_upper': [forecast_value * 1.05] * forecast_periods
            })

            # Historical
            historical_df = pd.DataFrame({
                'ds': pd.to_datetime(df_clean[date_column]),
                'yhat': df_clean[value_column].rolling(window).mean()
            })

            # Metrics
            from src.utils.metrics import calculate_metrics
            actual = df_clean[value_column].iloc[window:].values
            predicted = historical_df['yhat'].iloc[window:].values
            metrics = calculate_metrics(actual, predicted)

            result = ForecastResult(
                forecast_df=forecast_df,
                historical_df=historical_df,
                metrics=metrics,
                model_params={'method': method, 'window': window},
                model_name='FixedCost_MovingAverage'
            )

        elif method == 'last_value':
            # Use last value
            forecast_value = df_clean[value_column].iloc[-1]

            last_date = pd.to_datetime(df_clean[date_column].iloc[-1])
            future_dates = pd.date_range(start=last_date, periods=forecast_periods + 1, freq='M')[1:]

            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': [forecast_value] * forecast_periods
            })

            result = ForecastResult(
                forecast_df=forecast_df,
                historical_df=df_clean.rename(columns={date_column: 'ds', value_column: 'yhat'}),
                metrics={'method': method},
                model_params={'method': method},
                model_name='FixedCost_LastValue'
            )

        else:  # prophet
            model = ProphetModel(
                yearly_seasonality=False,
                seasonality_mode='additive',
                changepoint_prior_scale=0.01  # Low flexibility for fixed costs
            )

            result = model.fit_predict(
                df_clean,
                date_column=date_column,
                value_column=value_column,
                periods=forecast_periods
            )

        self.results['fixed_cost'] = result
        return result

    def forecast_variable_costs(self,
                               df_expense: pd.DataFrame,
                               df_revenue: pd.DataFrame,
                               date_column: str = 'month',
                               expense_column: str = 'expense',
                               revenue_column: str = 'revenue',
                               forecast_periods: int = 12,
                               revenue_forecast: Optional[np.ndarray] = None) -> ForecastResult:
        """
        Forecast variable costs (COGS, commission, etc.) based on revenue

        Args:
            df_expense: DataFrame with expense data
            df_revenue: DataFrame with revenue data
            date_column: Name of date column
            expense_column: Name of expense column
            revenue_column: Name of revenue column
            forecast_periods: Number of periods to forecast
            revenue_forecast: Forecasted revenue values (if None, will forecast revenue first)

        Returns:
            ForecastResult object
        """
        # Merge expense and revenue
        df_merged = pd.merge(
            df_expense[[date_column, expense_column]],
            df_revenue[[date_column, revenue_column]],
            on=date_column,
            how='inner'
        )

        # Linear regression: expense = f(revenue)
        X = df_merged[[revenue_column]].values
        y = df_merged[expense_column].values

        model = LinearRegression()
        model.fit(X, y)

        # Coefficient (expense ratio)
        expense_ratio = model.coef_[0]
        intercept = model.intercept_

        print(f"Expense ratio: {expense_ratio:.2%}")
        print(f"Intercept: {intercept:,.2f}")

        # Forecast revenue if not provided
        if revenue_forecast is None:
            # Simple forecast: use mean of last 3 months
            revenue_forecast = np.array([df_merged[revenue_column].tail(3).mean()] * forecast_periods)

        # Forecast expense
        expense_forecast = model.predict(revenue_forecast.reshape(-1, 1))

        # Create forecast dataframe
        last_date = pd.to_datetime(df_merged[date_column].iloc[-1])
        future_dates = pd.date_range(start=last_date, periods=forecast_periods + 1, freq='M')[1:]

        # Calculate prediction intervals (using residual std)
        residuals = y - model.predict(X)
        std_error = np.std(residuals)

        forecast_df = pd.DataFrame({
            'ds': future_dates,
            'yhat': expense_forecast,
            'yhat_lower': expense_forecast - 1.96 * std_error,
            'yhat_upper': expense_forecast + 1.96 * std_error
        })

        # Historical fitted values
        historical_df = pd.DataFrame({
            'ds': pd.to_datetime(df_merged[date_column]),
            'yhat': model.predict(X)
        })

        # Metrics
        from src.utils.metrics import calculate_metrics
        metrics = calculate_metrics(y, model.predict(X))
        metrics['expense_ratio'] = expense_ratio
        metrics['r2_revenue'] = model.score(X, y)

        result = ForecastResult(
            forecast_df=forecast_df,
            historical_df=historical_df,
            metrics=metrics,
            model_params={
                'expense_ratio': expense_ratio,
                'intercept': intercept
            },
            model_name='VariableCost_LinearRegression'
        )

        self.results['variable_cost'] = result
        return result

    def forecast_by_gl_code(self,
                           df: pd.DataFrame,
                           gl_column: str = 'gl_code',
                           date_column: str = 'month',
                           value_column: str = 'expense',
                           forecast_periods: int = 12,
                           model_type: str = 'auto') -> Dict[str, ForecastResult]:
        """
        Forecast expenses by GL code

        Args:
            df: DataFrame with expense data
            gl_column: Name of GL code column
            date_column: Name of date column
            value_column: Name of expense column
            forecast_periods: Number of periods to forecast
            model_type: 'auto', 'prophet', or 'moving_average'

        Returns:
            Dictionary of {gl_code: ForecastResult}
        """
        results = {}
        gl_codes = df[gl_column].unique()

        print(f"Forecasting for {len(gl_codes)} GL codes...")

        for gl_code in gl_codes:
            print(f"  Processing GL code: {gl_code}...")

            # Filter data
            df_gl = df[df[gl_column] == gl_code].copy()

            # Aggregate by date
            df_agg = df_gl.groupby(date_column)[value_column].sum().reset_index()

            # Classify expense type
            cv = df_agg[value_column].std() / df_agg[value_column].mean()

            # Auto-select model based on variation
            if model_type == 'auto':
                if cv < 0.1:
                    # Fixed cost - use moving average
                    selected_model = 'moving_average'
                else:
                    # Variable/semi-variable - use Prophet
                    selected_model = 'prophet'
            else:
                selected_model = model_type

            try:
                if selected_model == 'moving_average':
                    result = self.forecast_fixed_costs(
                        df_agg,
                        date_column=date_column,
                        value_column=value_column,
                        forecast_periods=forecast_periods,
                        method='moving_average'
                    )
                else:
                    model = ProphetModel(
                        yearly_seasonality=True,
                        seasonality_mode='additive'
                    )

                    result = model.fit_predict(
                        df_agg,
                        date_column=date_column,
                        value_column=value_column,
                        periods=forecast_periods
                    )

                results[gl_code] = result
                print(f"    ✓ Success ({selected_model}, CV: {cv:.2f})")

            except Exception as e:
                print(f"    ✗ Failed: {e}")
                continue

        self.results['by_gl_code'] = results
        return results

    def get_expense_summary(self) -> pd.DataFrame:
        """Get summary of expense forecasts"""
        summary = []

        for key, result in self.results.items():
            if isinstance(result, dict):
                # Multiple forecasts (e.g., by GL code)
                for sub_key, sub_result in result.items():
                    total_forecast = sub_result.forecast_df['yhat'].sum()
                    summary.append({
                        'category': key,
                        'item': sub_key,
                        'total_forecast': total_forecast,
                        'avg_monthly': total_forecast / len(sub_result.forecast_df),
                        'mape': sub_result.metrics.get('mape', None)
                    })
            else:
                # Single forecast
                total_forecast = result.forecast_df['yhat'].sum()
                summary.append({
                    'category': key,
                    'item': 'total',
                    'total_forecast': total_forecast,
                    'avg_monthly': total_forecast / len(result.forecast_df),
                    'mape': result.metrics.get('mape', None)
                })

        return pd.DataFrame(summary)
