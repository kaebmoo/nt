"""
Feature engineering for time series
"""

import pandas as pd
import numpy as np
from typing import List, Optional


class FeatureEngineer:
    """Create features for time series forecasting"""

    @staticmethod
    def create_time_features(df: pd.DataFrame,
                            date_column: str = 'date') -> pd.DataFrame:
        """
        Create time-based features

        Args:
            df: Input DataFrame
            date_column: Name of date column

        Returns:
            DataFrame with time features added
        """
        df_feat = df.copy()
        df_feat[date_column] = pd.to_datetime(df_feat[date_column])

        # Extract time components
        df_feat['year'] = df_feat[date_column].dt.year
        df_feat['month'] = df_feat[date_column].dt.month
        df_feat['quarter'] = df_feat[date_column].dt.quarter
        df_feat['day'] = df_feat[date_column].dt.day
        df_feat['dayofweek'] = df_feat[date_column].dt.dayofweek
        df_feat['dayofyear'] = df_feat[date_column].dt.dayofyear
        df_feat['week'] = df_feat[date_column].dt.isocalendar().week

        # Is weekend
        df_feat['is_weekend'] = df_feat['dayofweek'].isin([5, 6]).astype(int)

        # Month/quarter start/end
        df_feat['is_month_start'] = df_feat[date_column].dt.is_month_start.astype(int)
        df_feat['is_month_end'] = df_feat[date_column].dt.is_month_end.astype(int)
        df_feat['is_quarter_start'] = df_feat[date_column].dt.is_quarter_start.astype(int)
        df_feat['is_quarter_end'] = df_feat[date_column].dt.is_quarter_end.astype(int)

        return df_feat

    @staticmethod
    def create_lag_features(df: pd.DataFrame,
                           value_column: str,
                           lags: List[int] = [1, 3, 6, 12]) -> pd.DataFrame:
        """
        Create lag features

        Args:
            df: Input DataFrame
            value_column: Column to create lags from
            lags: List of lag periods

        Returns:
            DataFrame with lag features
        """
        df_feat = df.copy()

        for lag in lags:
            df_feat[f'{value_column}_lag_{lag}'] = df_feat[value_column].shift(lag)

        return df_feat

    @staticmethod
    def create_rolling_features(df: pd.DataFrame,
                               value_column: str,
                               windows: List[int] = [3, 6, 12]) -> pd.DataFrame:
        """
        Create rolling window features

        Args:
            df: Input DataFrame
            value_column: Column to create rolling features from
            windows: List of window sizes

        Returns:
            DataFrame with rolling features
        """
        df_feat = df.copy()

        for window in windows:
            df_feat[f'{value_column}_rolling_mean_{window}'] = \
                df_feat[value_column].rolling(window).mean()

            df_feat[f'{value_column}_rolling_std_{window}'] = \
                df_feat[value_column].rolling(window).std()

            df_feat[f'{value_column}_rolling_min_{window}'] = \
                df_feat[value_column].rolling(window).min()

            df_feat[f'{value_column}_rolling_max_{window}'] = \
                df_feat[value_column].rolling(window).max()

        return df_feat

    @staticmethod
    def create_diff_features(df: pd.DataFrame,
                            value_column: str,
                            periods: List[int] = [1, 12]) -> pd.DataFrame:
        """
        Create difference features

        Args:
            df: Input DataFrame
            value_column: Column to create differences from
            periods: List of difference periods

        Returns:
            DataFrame with difference features
        """
        df_feat = df.copy()

        for period in periods:
            df_feat[f'{value_column}_diff_{period}'] = \
                df_feat[value_column].diff(period)

            df_feat[f'{value_column}_pct_change_{period}'] = \
                df_feat[value_column].pct_change(period)

        return df_feat
