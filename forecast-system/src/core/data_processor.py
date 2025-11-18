"""
Data processing and validation
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict
from datetime import datetime


class DataProcessor:
    """Process and validate time series data"""

    @staticmethod
    def load_data(filepath: str,
                 date_column: str = 'date',
                 value_column: str = 'value',
                 **kwargs) -> pd.DataFrame:
        """
        Load data from file

        Args:
            filepath: Path to data file (CSV, Excel)
            date_column: Name of date column
            value_column: Name of value column
            **kwargs: Additional arguments for pd.read_csv/read_excel

        Returns:
            DataFrame
        """
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath, **kwargs)
        elif filepath.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {filepath}")

        # Validate columns exist
        if date_column not in df.columns:
            raise ValueError(f"Date column '{date_column}' not found")
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found")

        return df

    @staticmethod
    def validate_data(df: pd.DataFrame,
                     date_column: str = 'date',
                     value_column: str = 'value') -> Dict[str, any]:
        """
        Validate time series data

        Args:
            df: Input DataFrame
            date_column: Name of date column
            value_column: Name of value column

        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []

        # Check for missing values
        if df[date_column].isna().any():
            issues.append(f"Missing values in {date_column}")

        missing_values = df[value_column].isna().sum()
        if missing_values > 0:
            warnings.append(f"{missing_values} missing values in {value_column}")

        # Check for duplicates
        duplicates = df[date_column].duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{duplicates} duplicate dates found")

        # Check for negative values
        if (df[value_column] < 0).any():
            warnings.append("Negative values found")

        # Check for outliers (> 3 std)
        mean = df[value_column].mean()
        std = df[value_column].std()
        outliers = ((df[value_column] - mean).abs() > 3 * std).sum()
        if outliers > 0:
            warnings.append(f"{outliers} potential outliers detected (>3 std)")

        # Check date continuity
        df_sorted = df.sort_values(date_column)
        dates = pd.to_datetime(df_sorted[date_column])
        freq = pd.infer_freq(dates)

        if freq is None:
            warnings.append("Unable to infer frequency (irregular dates)")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'n_rows': len(df),
            'date_range': (df[date_column].min(), df[date_column].max()),
            'missing_values': missing_values,
            'duplicates': duplicates,
            'outliers': outliers,
            'frequency': freq
        }

    @staticmethod
    def clean_data(df: pd.DataFrame,
                  date_column: str = 'date',
                  value_column: str = 'value',
                  handle_missing: str = 'interpolate',
                  handle_duplicates: str = 'last',
                  remove_outliers: bool = False) -> pd.DataFrame:
        """
        Clean time series data

        Args:
            df: Input DataFrame
            date_column: Name of date column
            value_column: Name of value column
            handle_missing: How to handle missing values ('interpolate', 'forward_fill', 'drop')
            handle_duplicates: How to handle duplicates ('last', 'first', 'mean')
            remove_outliers: Remove outliers (>3 std)

        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()

        # Convert date to datetime
        df_clean[date_column] = pd.to_datetime(df_clean[date_column])

        # Sort by date
        df_clean = df_clean.sort_values(date_column).reset_index(drop=True)

        # Handle duplicates
        if handle_duplicates == 'last':
            df_clean = df_clean.drop_duplicates(subset=date_column, keep='last')
        elif handle_duplicates == 'first':
            df_clean = df_clean.drop_duplicates(subset=date_column, keep='first')
        elif handle_duplicates == 'mean':
            df_clean = df_clean.groupby(date_column)[value_column].mean().reset_index()

        # Handle missing values
        if handle_missing == 'interpolate':
            df_clean[value_column] = df_clean[value_column].interpolate(method='linear')
        elif handle_missing == 'forward_fill':
            df_clean[value_column] = df_clean[value_column].fillna(method='ffill')
        elif handle_missing == 'drop':
            df_clean = df_clean.dropna(subset=[value_column])

        # Remove outliers
        if remove_outliers:
            mean = df_clean[value_column].mean()
            std = df_clean[value_column].std()
            df_clean = df_clean[
                (df_clean[value_column] - mean).abs() <= 3 * std
            ]

        return df_clean

    @staticmethod
    def aggregate_data(df: pd.DataFrame,
                      date_column: str = 'date',
                      value_column: str = 'value',
                      freq: str = 'M',
                      agg_func: str = 'sum') -> pd.DataFrame:
        """
        Aggregate data to different frequency

        Args:
            df: Input DataFrame
            date_column: Name of date column
            value_column: Name of value column
            freq: Target frequency ('D', 'W', 'M', 'Q', 'Y')
            agg_func: Aggregation function ('sum', 'mean', 'median')

        Returns:
            Aggregated DataFrame
        """
        df_agg = df.copy()
        df_agg[date_column] = pd.to_datetime(df_agg[date_column])

        # Set date as index
        df_agg = df_agg.set_index(date_column)

        # Resample
        if agg_func == 'sum':
            df_result = df_agg[value_column].resample(freq).sum()
        elif agg_func == 'mean':
            df_result = df_agg[value_column].resample(freq).mean()
        elif agg_func == 'median':
            df_result = df_agg[value_column].resample(freq).median()
        else:
            raise ValueError(f"Unsupported aggregation function: {agg_func}")

        return df_result.reset_index()

    @staticmethod
    def split_train_test(df: pd.DataFrame,
                        test_size: int = 12,
                        date_column: str = 'date') -> tuple:
        """
        Split data into train and test sets

        Args:
            df: Input DataFrame
            test_size: Number of periods for test set
            date_column: Name of date column

        Returns:
            Tuple of (train_df, test_df)
        """
        df_sorted = df.sort_values(date_column).reset_index(drop=True)

        split_idx = len(df_sorted) - test_size
        train_df = df_sorted.iloc[:split_idx]
        test_df = df_sorted.iloc[split_idx:]

        return train_df, test_df

    @staticmethod
    def detect_seasonality(df: pd.DataFrame,
                          value_column: str = 'value',
                          max_lag: int = 24) -> Dict[str, any]:
        """
        Detect seasonality in data

        Args:
            df: Input DataFrame
            value_column: Name of value column
            max_lag: Maximum lag to check

        Returns:
            Dictionary with seasonality information
        """
        from scipy import stats

        # ACF analysis
        values = df[value_column].values

        autocorr = []
        for lag in range(1, max_lag + 1):
            if len(values) > lag:
                corr = np.corrcoef(values[:-lag], values[lag:])[0, 1]
                autocorr.append(corr)
            else:
                autocorr.append(0)

        # Find significant peaks
        autocorr = np.array(autocorr)
        peaks = []

        # Check common seasonalities
        common_periods = {
            7: 'Weekly',
            12: 'Monthly (yearly)',
            4: 'Quarterly',
            52: 'Weekly (yearly)'
        }

        for period, name in common_periods.items():
            if period <= max_lag and period <= len(autocorr):
                if autocorr[period - 1] > 0.3:  # Threshold for significance
                    peaks.append({
                        'period': period,
                        'name': name,
                        'correlation': autocorr[period - 1]
                    })

        return {
            'has_seasonality': len(peaks) > 0,
            'detected_periods': peaks,
            'autocorrelation': autocorr.tolist()
        }
