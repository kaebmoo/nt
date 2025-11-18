"""
Metrics calculation utilities
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def calculate_metrics(actual: np.ndarray,
                     predicted: np.ndarray,
                     confidence_lower: Optional[np.ndarray] = None,
                     confidence_upper: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Calculate forecast accuracy metrics

    Args:
        actual: Actual values
        predicted: Predicted values
        confidence_lower: Lower confidence bound
        confidence_upper: Upper confidence bound

    Returns:
        Dictionary of metrics
    """
    # Ensure arrays are the same length
    min_len = min(len(actual), len(predicted))
    actual = actual[:min_len]
    predicted = predicted[:min_len]

    # Remove NaN values
    mask = ~(np.isnan(actual) | np.isnan(predicted))
    actual = actual[mask]
    predicted = predicted[mask]

    if len(actual) == 0:
        return {
            'mape': 0.0,
            'mae': 0.0,
            'rmse': 0.0,
            'r2': 0.0
        }

    metrics = {}

    # MAPE (Mean Absolute Percentage Error)
    # Avoid division by zero
    non_zero_mask = actual != 0
    if np.sum(non_zero_mask) > 0:
        mape = np.mean(np.abs((actual[non_zero_mask] - predicted[non_zero_mask]) / actual[non_zero_mask]))
        metrics['mape'] = mape
    else:
        metrics['mape'] = 0.0

    # MAE (Mean Absolute Error)
    mae = np.mean(np.abs(actual - predicted))
    metrics['mae'] = mae

    # RMSE (Root Mean Squared Error)
    mse = np.mean((actual - predicted) ** 2)
    rmse = np.sqrt(mse)
    metrics['rmse'] = rmse

    # R² (Coefficient of Determination)
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    if ss_tot > 0:
        r2 = 1 - (ss_res / ss_tot)
        metrics['r2'] = r2
    else:
        metrics['r2'] = 0.0

    # SMAPE (Symmetric Mean Absolute Percentage Error)
    smape = np.mean(2 * np.abs(actual - predicted) / (np.abs(actual) + np.abs(predicted) + 1e-10))
    metrics['smape'] = smape

    # Coverage (if confidence intervals provided)
    if confidence_lower is not None and confidence_upper is not None:
        confidence_lower = confidence_lower[:min_len][mask]
        confidence_upper = confidence_upper[:min_len][mask]

        in_interval = (actual >= confidence_lower) & (actual <= confidence_upper)
        coverage = np.mean(in_interval)
        metrics['coverage'] = coverage

    return metrics


class MetricsCalculator:
    """Helper class for calculating and tracking metrics"""

    def __init__(self):
        self.metrics_history = []

    def add_metrics(self, actual: np.ndarray, predicted: np.ndarray, label: str = None):
        """Add metrics to history"""
        metrics = calculate_metrics(actual, predicted)
        if label:
            metrics['label'] = label
        self.metrics_history.append(metrics)

    def get_summary(self) -> pd.DataFrame:
        """Get summary of all metrics"""
        return pd.DataFrame(self.metrics_history)

    def compare_models(self, results: Dict) -> pd.DataFrame:
        """
        Compare metrics across multiple models

        Args:
            results: Dictionary of {model_name: ForecastResult}

        Returns:
            DataFrame with comparison
        """
        comparison = []

        for model_name, result in results.items():
            row = {'model': model_name}
            row.update(result.metrics)
            comparison.append(row)

        df = pd.DataFrame(comparison)

        # Sort by MAPE (lower is better)
        if 'mape' in df.columns:
            df = df.sort_values('mape')

        return df

    @staticmethod
    def format_metrics(metrics: Dict[str, float]) -> str:
        """Format metrics as readable string"""
        output = []
        for key, value in metrics.items():
            if key in ['mape', 'smape', 'coverage']:
                output.append(f"{key.upper()}: {value:.2%}")
            else:
                output.append(f"{key.upper()}: {value:,.2f}")

        return ", ".join(output)


def calculate_forecast_bias(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Calculate forecast bias metrics

    Returns:
        Dictionary with bias metrics
    """
    bias = np.mean(predicted - actual)
    bias_pct = bias / np.mean(actual) if np.mean(actual) != 0 else 0

    return {
        'bias': bias,
        'bias_pct': bias_pct,
        'over_forecast': np.sum(predicted > actual) / len(actual),
        'under_forecast': np.sum(predicted < actual) / len(actual)
    }
