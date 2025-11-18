"""
VAR (Vector Autoregression) Model for Simultaneous Forecasting
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from .base_model import BaseForecastModel, ForecastResult


class VARModel(BaseForecastModel):
    """
    Vector Autoregression (VAR) model for multivariate time series

    Best for:
    - Forecasting multiple related variables simultaneously
    - Revenue and Expense that influence each other
    - Capturing interdependencies
    - Feedback loops between variables
    """

    def __init__(self,
                 maxlags: int = 12,
                 ic: str = 'aic',
                 trend: str = 'c',
                 **kwargs):
        """
        Initialize VAR model

        Args:
            maxlags: Maximum number of lags to consider
            ic: Information criterion ('aic', 'bic', 'hqic', 'fpe')
            trend: Trend parameter ('c', 'ct', 'ctt', 'n')
        """
        super().__init__(name="VAR", **kwargs)

        self.maxlags = maxlags
        self.ic = ic
        self.trend = trend

        self.model = None
        self.results = None
        self.variable_names = []

    def fit(self,
            df: pd.DataFrame,
            date_column: str = 'ds',
            value_columns: List[str] = None,
            exog: Optional[pd.DataFrame] = None) -> 'VARModel':
        """
        Fit VAR model

        Args:
            df: DataFrame with multiple time series
            date_column: Name of date column
            value_columns: List of column names to forecast (e.g., ['revenue', 'expense'])
            exog: External variables (optional)

        Returns:
            self
        """
        try:
            from statsmodels.tsa.vector_ar.var_model import VAR
        except ImportError:
            raise ImportError("statsmodels not installed. Run: pip install statsmodels")

        if value_columns is None:
            # Use all numeric columns except date
            value_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        self.variable_names = value_columns

        # Prepare data
        df_sorted = df.sort_values(date_column).reset_index(drop=True)
        self.df_prep = df_sorted[[date_column] + value_columns].copy()

        # Extract values for VAR
        data = df_sorted[value_columns].values

        # Initialize and fit VAR
        self.model = VAR(data)

        # Fit with automatic lag selection
        self.results = self.model.fit(
            maxlags=self.maxlags,
            ic=self.ic,
            trend=self.trend
        )

        self.is_fitted = True

        print(f"VAR model fitted with {self.results.k_ar} lags")
        print(f"Variables: {', '.join(self.variable_names)}")

        return self

    def predict(self,
                periods: int = 12,
                exog: Optional[pd.DataFrame] = None) -> Dict[str, ForecastResult]:
        """
        Generate forecast for all variables

        Args:
            periods: Number of periods to forecast
            exog: External variables (not supported in basic VAR)

        Returns:
            Dictionary of {variable_name: ForecastResult}
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")

        # Get historical data for forecasting
        lag_order = self.results.k_ar
        historical_values = self.df_prep[self.variable_names].values

        # Forecast
        forecast_values = self.results.forecast(
            historical_values[-lag_order:],
            steps=periods
        )

        # Create future dates
        last_date = pd.to_datetime(self.df_prep['ds'].iloc[-1])
        freq = pd.infer_freq(pd.to_datetime(self.df_prep['ds']))
        if freq is None:
            freq = 'M'

        future_dates = pd.date_range(
            start=last_date,
            periods=periods + 1,
            freq=freq
        )[1:]

        # Calculate forecast errors (approximate confidence intervals)
        forecast_errors = self.results.forecast_interval(
            historical_values[-lag_order:],
            steps=periods,
            alpha=0.05  # 95% confidence
        )

        # Create results for each variable
        results = {}

        for i, var_name in enumerate(self.variable_names):
            # Forecast dataframe
            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': forecast_values[:, i],
                'yhat_lower': forecast_errors[0][:, i],
                'yhat_upper': forecast_errors[1][:, i]
            })

            # Historical fitted values
            fitted_values = self.results.fittedvalues[:, i]
            historical_df = pd.DataFrame({
                'ds': pd.to_datetime(self.df_prep['ds'].iloc[:len(fitted_values)]),
                'yhat': fitted_values
            })

            # Confidence intervals
            confidence_df = forecast_df[['ds', 'yhat_lower', 'yhat_upper']].copy()

            # Calculate metrics
            from src.utils.metrics import calculate_metrics
            actual = self.df_prep[var_name].values[:len(fitted_values)]
            predicted = fitted_values
            metrics = calculate_metrics(actual, predicted)

            # Add VAR-specific metrics
            metrics['aic'] = self.results.aic
            metrics['bic'] = self.results.bic

            results[var_name] = ForecastResult(
                forecast_df=forecast_df,
                historical_df=historical_df,
                metrics=metrics,
                model_params={
                    'lag_order': self.results.k_ar,
                    'ic': self.ic,
                    'trend': self.trend
                },
                model_name=f"VAR_{var_name}",
                confidence_intervals=confidence_df
            )

        return results

    def granger_causality(self, maxlag: int = 12) -> pd.DataFrame:
        """
        Test Granger causality between variables

        Args:
            maxlag: Maximum lag to test

        Returns:
            DataFrame with causality test results
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        from statsmodels.tsa.stattools import grangercausalitytests

        results = []

        # Test each pair of variables
        for i, var1 in enumerate(self.variable_names):
            for j, var2 in enumerate(self.variable_names):
                if i != j:
                    # Test if var2 Granger-causes var1
                    data = self.df_prep[[var1, var2]].values

                    try:
                        test_result = grangercausalitytests(
                            data,
                            maxlag=maxlag,
                            verbose=False
                        )

                        # Get p-value from first lag
                        p_value = test_result[1][0]['ssr_ftest'][1]

                        results.append({
                            'cause': var2,
                            'effect': var1,
                            'p_value': p_value,
                            'significant': p_value < 0.05
                        })

                    except Exception as e:
                        print(f"Warning: Granger test failed for {var2} -> {var1}: {e}")
                        continue

        return pd.DataFrame(results)

    def impulse_response(self, periods: int = 10) -> Dict:
        """
        Calculate impulse response functions

        Args:
            periods: Number of periods for IRF

        Returns:
            Dictionary with IRF results
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        irf = self.results.irf(periods)

        return {
            'irf': irf.irfs,
            'lower': irf.ci[:, :, :, 0],
            'upper': irf.ci[:, :, :, 1],
            'variable_names': self.variable_names
        }

    def forecast_error_variance_decomposition(self, periods: int = 10) -> pd.DataFrame:
        """
        Forecast error variance decomposition

        Args:
            periods: Number of periods

        Returns:
            DataFrame with FEVD results
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted first")

        fevd = self.results.fevd(periods)

        # Convert to DataFrame
        results = []
        for i, var_name in enumerate(self.variable_names):
            for period in range(periods):
                for j, source_var in enumerate(self.variable_names):
                    results.append({
                        'variable': var_name,
                        'period': period + 1,
                        'source': source_var,
                        'contribution': fevd.decomp[period, i, j]
                    })

        return pd.DataFrame(results)

    def summary(self) -> str:
        """Get model summary"""
        if not self.is_fitted:
            return "Model not fitted yet"

        return str(self.results.summary())
