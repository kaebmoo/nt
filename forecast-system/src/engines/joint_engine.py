"""
Joint Revenue & Expense Forecast Engine
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

from src.models import ProphetModel, SARIMAXModel, XGBoostModel, ForecastResult
from src.models.var_model import VARModel
from src.models.multioutput_model import MultiOutputXGBoostModel
from src.engines.revenue_engine import RevenueForecastEngine
from src.engines.expense_engine import ExpenseForecastEngine
from sklearn.linear_model import LinearRegression


@dataclass
class JointForecastResult:
    """Container for joint forecast results"""
    revenue_forecast: pd.DataFrame
    expense_forecast: pd.DataFrame
    profit_forecast: pd.DataFrame
    metrics: Dict[str, float]
    method: str
    scenarios: Optional[Dict[str, pd.DataFrame]] = None
    component_results: Optional[Dict] = None


class JointForecastEngine:
    """
    High-level engine for joint revenue and expense forecasting

    Supports 4 approaches:
    1. Sequential (Revenue → Expense)
    2. Simultaneous (VAR)
    3. Multi-output ML (XGBoost)
    4. Optimization-based
    """

    def __init__(self):
        self.revenue_engine = RevenueForecastEngine()
        self.expense_engine = ExpenseForecastEngine()

        self.results = {}
        self.classification = {}

    # ==================================================
    # Approach 1: Sequential Forecasting
    # ==================================================

    def forecast_sequential(self,
                           df_revenue: pd.DataFrame,
                           df_expense: pd.DataFrame,
                           date_column: str = 'month',
                           revenue_column: str = 'revenue',
                           expense_column: str = 'expense',
                           forecast_periods: int = 12,
                           revenue_model: str = 'prophet',
                           expense_classification: Optional[Dict[str, str]] = None,
                           **kwargs) -> JointForecastResult:
        """
        Sequential approach: Revenue first, then Expense based on Revenue

        Args:
            df_revenue: Revenue DataFrame
            df_expense: Expense DataFrame
            date_column: Date column name
            revenue_column: Revenue column name
            expense_column: Expense column name
            forecast_periods: Number of periods to forecast
            revenue_model: Model for revenue ('prophet', 'sarimax', 'xgboost')
            expense_classification: Dict mapping expense types to cost types
                                  {'gl_code': 'fixed/variable/semi_variable'}

        Returns:
            JointForecastResult
        """
        print("="*60)
        print("SEQUENTIAL JOINT FORECASTING")
        print("="*60)

        # Step 1: Forecast Revenue
        print("\n📈 Step 1: Forecasting Revenue...")
        revenue_result = self.revenue_engine.forecast(
            df=df_revenue,
            date_column=date_column,
            value_column=revenue_column,
            model_type=revenue_model,
            forecast_periods=forecast_periods,
            **kwargs
        )

        print(f"✓ Revenue forecast complete (MAPE: {revenue_result.metrics.get('mape', 0):.2%})")

        # Step 2: Classify Expenses
        print("\n💰 Step 2: Classifying Expenses...")

        if expense_classification is None:
            # Auto-classify
            expense_classification = self._auto_classify_expenses(
                df_expense,
                df_revenue,
                date_column,
                expense_column,
                revenue_column
            )

        print(f"✓ Classified {len(expense_classification)} expense categories")

        # Step 3: Forecast each expense type
        print("\n💸 Step 3: Forecasting Expenses by Type...")

        # Prepare expense data by type
        df_expense_merged = df_expense.copy()
        if 'cost_type' not in df_expense_merged.columns and expense_classification:
            # Map classification
            df_expense_merged['cost_type'] = df_expense_merged.apply(
                lambda row: self._determine_cost_type(row, expense_classification),
                axis=1
            )

        # Aggregate by cost type
        expense_forecasts = {}

        # Fixed costs
        df_fixed = df_expense_merged[
            df_expense_merged.get('cost_type', 'semi_variable') == 'fixed'
        ]

        if len(df_fixed) > 0:
            df_fixed_agg = df_fixed.groupby(date_column)[expense_column].sum().reset_index()

            fixed_result = self.expense_engine.forecast_fixed_costs(
                df=df_fixed_agg,
                date_column=date_column,
                value_column=expense_column,
                forecast_periods=forecast_periods,
                method='moving_average'
            )

            expense_forecasts['fixed'] = fixed_result.forecast_df['yhat'].values
            print(f"  ✓ Fixed costs: avg {fixed_result.forecast_df['yhat'].mean():,.0f}/month")

        else:
            expense_forecasts['fixed'] = np.zeros(forecast_periods)

        # Variable costs (based on revenue forecast)
        df_variable = df_expense_merged[
            df_expense_merged.get('cost_type', 'semi_variable') == 'variable'
        ]

        if len(df_variable) > 0:
            df_variable_agg = df_variable.groupby(date_column)[expense_column].sum().reset_index()
            df_revenue_agg = df_revenue.groupby(date_column)[revenue_column].sum().reset_index()

            variable_result = self.expense_engine.forecast_variable_costs(
                df_expense=df_variable_agg,
                df_revenue=df_revenue_agg,
                date_column=date_column,
                expense_column=expense_column,
                revenue_column=revenue_column,
                forecast_periods=forecast_periods,
                revenue_forecast=revenue_result.forecast_df['yhat'].values
            )

            expense_forecasts['variable'] = variable_result.forecast_df['yhat'].values

            ratio = variable_result.metrics.get('expense_ratio', 0)
            print(f"  ✓ Variable costs: {ratio:.2%} of revenue")

        else:
            expense_forecasts['variable'] = np.zeros(forecast_periods)

        # Semi-variable costs
        df_semi = df_expense_merged[
            df_expense_merged.get('cost_type', 'semi_variable') == 'semi_variable'
        ]

        if len(df_semi) > 0:
            df_semi_agg = df_semi.groupby(date_column)[expense_column].sum().reset_index()

            semi_model = ProphetModel(
                yearly_seasonality=True,
                seasonality_mode='additive'
            )

            semi_result = semi_model.fit_predict(
                df=df_semi_agg,
                date_column=date_column,
                value_column=expense_column,
                periods=forecast_periods
            )

            expense_forecasts['semi_variable'] = semi_result.forecast_df['yhat'].values
            print(f"  ✓ Semi-variable costs: avg {semi_result.forecast_df['yhat'].mean():,.0f}/month")

        else:
            expense_forecasts['semi_variable'] = np.zeros(forecast_periods)

        # Step 4: Combine total expenses
        print("\n💵 Step 4: Combining Total Expenses...")

        total_expense = (
            expense_forecasts.get('fixed', 0) +
            expense_forecasts.get('variable', 0) +
            expense_forecasts.get('semi_variable', 0)
        )

        # Step 5: Calculate profit and margin
        print("\n💰 Step 5: Calculating Profit & Margin...")

        # Create final dataframes
        revenue_df = revenue_result.forecast_df.copy()
        revenue_df.rename(columns={'yhat': 'revenue'}, inplace=True)

        expense_df = pd.DataFrame({
            'ds': revenue_df['ds'],
            'expense': total_expense,
            'fixed': expense_forecasts.get('fixed', 0),
            'variable': expense_forecasts.get('variable', 0),
            'semi_variable': expense_forecasts.get('semi_variable', 0)
        })

        profit_df = pd.DataFrame({
            'ds': revenue_df['ds'],
            'revenue': revenue_df['revenue'],
            'expense': expense_df['expense'],
            'profit': revenue_df['revenue'] - expense_df['expense'],
            'margin_pct': ((revenue_df['revenue'] - expense_df['expense']) / revenue_df['revenue'] * 100)
        })

        # Scenarios (best/worst case)
        scenarios = self._create_scenarios(revenue_result, expense_df)

        # Metrics
        metrics = {
            'revenue_mape': revenue_result.metrics.get('mape', 0),
            'avg_revenue': revenue_df['revenue'].mean(),
            'avg_expense': expense_df['expense'].mean(),
            'avg_profit': profit_df['profit'].mean(),
            'avg_margin_pct': profit_df['margin_pct'].mean(),
            'fixed_expense_ratio': expense_forecasts.get('fixed', np.array([0])).sum() / total_expense.sum(),
            'variable_expense_ratio': expense_forecasts.get('variable', np.array([0])).sum() / total_expense.sum(),
        }

        print(f"\n✅ Sequential forecast complete!")
        print(f"   Avg Profit: {metrics['avg_profit']:,.0f}")
        print(f"   Avg Margin: {metrics['avg_margin_pct']:.2f}%")

        return JointForecastResult(
            revenue_forecast=revenue_df,
            expense_forecast=expense_df,
            profit_forecast=profit_df,
            metrics=metrics,
            method='sequential',
            scenarios=scenarios,
            component_results={
                'revenue': revenue_result,
                'expense_by_type': expense_forecasts
            }
        )

    # ==================================================
    # Approach 2: Simultaneous (VAR)
    # ==================================================

    def forecast_simultaneous_var(self,
                                  df: pd.DataFrame,
                                  date_column: str = 'month',
                                  revenue_column: str = 'revenue',
                                  expense_column: str = 'expense',
                                  forecast_periods: int = 12,
                                  maxlags: int = 12,
                                  **kwargs) -> JointForecastResult:
        """
        Simultaneous forecasting using VAR model

        Args:
            df: DataFrame with both revenue and expense columns
            date_column: Date column name
            revenue_column: Revenue column name
            expense_column: Expense column name
            forecast_periods: Number of periods to forecast
            maxlags: Maximum lags for VAR

        Returns:
            JointForecastResult
        """
        print("="*60)
        print("SIMULTANEOUS FORECASTING (VAR)")
        print("="*60)

        # Prepare data
        df_combined = df[[date_column, revenue_column, expense_column]].copy()
        df_combined = df_combined.groupby(date_column)[[revenue_column, expense_column]].sum().reset_index()
        df_combined.columns = ['ds', 'revenue', 'expense']

        # Fit VAR model
        print("\n🔄 Fitting VAR model...")

        var_model = VARModel(maxlags=maxlags, **kwargs)
        var_model.fit(
            df=df_combined,
            date_column='ds',
            value_columns=['revenue', 'expense']
        )

        print(f"✓ VAR model fitted with {var_model.results.k_ar} lags")

        # Granger causality test
        print("\n📊 Testing Granger Causality...")
        try:
            causality = var_model.granger_causality(maxlag=6)
            print(causality.to_string(index=False))
        except Exception as e:
            print(f"Warning: Causality test failed: {e}")

        # Forecast
        print(f"\n🔮 Forecasting {forecast_periods} periods...")

        results = var_model.predict(periods=forecast_periods)

        revenue_result = results['revenue']
        expense_result = results['expense']

        # Create profit forecast
        profit_df = pd.DataFrame({
            'ds': revenue_result.forecast_df['ds'],
            'revenue': revenue_result.forecast_df['yhat'],
            'expense': expense_result.forecast_df['yhat'],
            'profit': revenue_result.forecast_df['yhat'] - expense_result.forecast_df['yhat'],
            'margin_pct': ((revenue_result.forecast_df['yhat'] - expense_result.forecast_df['yhat']) /
                          revenue_result.forecast_df['yhat'] * 100)
        })

        # Metrics
        metrics = {
            'revenue_mape': revenue_result.metrics.get('mape', 0),
            'expense_mape': expense_result.metrics.get('mape', 0),
            'avg_revenue': profit_df['revenue'].mean(),
            'avg_expense': profit_df['expense'].mean(),
            'avg_profit': profit_df['profit'].mean(),
            'avg_margin_pct': profit_df['margin_pct'].mean(),
            'var_aic': revenue_result.metrics.get('aic', 0),
            'var_bic': revenue_result.metrics.get('bic', 0),
        }

        print(f"\n✅ VAR forecast complete!")
        print(f"   Revenue MAPE: {metrics['revenue_mape']:.2%}")
        print(f"   Expense MAPE: {metrics['expense_mape']:.2%}")
        print(f"   Avg Margin: {metrics['avg_margin_pct']:.2f}%")

        return JointForecastResult(
            revenue_forecast=revenue_result.forecast_df.rename(columns={'yhat': 'revenue'}),
            expense_forecast=expense_result.forecast_df.rename(columns={'yhat': 'expense'}),
            profit_forecast=profit_df,
            metrics=metrics,
            method='var',
            component_results={
                'var_model': var_model,
                'causality': causality if 'causality' in locals() else None
            }
        )

    # ==================================================
    # Approach 3: Multi-output ML
    # ==================================================

    def forecast_multioutput_ml(self,
                                df: pd.DataFrame,
                                date_column: str = 'month',
                                revenue_column: str = 'revenue',
                                expense_column: str = 'expense',
                                forecast_periods: int = 12,
                                exog: Optional[pd.DataFrame] = None,
                                **kwargs) -> JointForecastResult:
        """
        Multi-output XGBoost forecasting

        Args:
            df: DataFrame with revenue and expense
            date_column: Date column name
            revenue_column: Revenue column name
            expense_column: Expense column name
            forecast_periods: Number of periods to forecast
            exog: External variables

        Returns:
            JointForecastResult
        """
        print("="*60)
        print("MULTI-OUTPUT MACHINE LEARNING (XGBoost)")
        print("="*60)

        # Prepare data
        df_combined = df[[date_column, revenue_column, expense_column]].copy()
        df_combined = df_combined.groupby(date_column)[[revenue_column, expense_column]].sum().reset_index()
        df_combined.columns = ['ds', 'revenue', 'expense']

        # Fit model
        print("\n🤖 Training Multi-output XGBoost...")

        ml_model = MultiOutputXGBoostModel(**kwargs)
        ml_model.fit(
            df=df_combined,
            date_column='ds',
            target_columns=['revenue', 'expense'],
            exog=exog
        )

        print("✓ Model trained successfully")

        # Forecast
        print(f"\n🔮 Forecasting {forecast_periods} periods...")

        results = ml_model.predict(periods=forecast_periods, exog=exog)

        revenue_result = results['revenue']
        expense_result = results['expense']

        # Create profit forecast
        profit_df = pd.DataFrame({
            'ds': revenue_result.forecast_df['ds'],
            'revenue': revenue_result.forecast_df['yhat'],
            'expense': expense_result.forecast_df['yhat'],
            'profit': revenue_result.forecast_df['yhat'] - expense_result.forecast_df['yhat'],
            'margin_pct': ((revenue_result.forecast_df['yhat'] - expense_result.forecast_df['yhat']) /
                          revenue_result.forecast_df['yhat'] * 100)
        })

        # Metrics
        metrics = {
            'revenue_mape': revenue_result.metrics.get('mape', 0),
            'expense_mape': expense_result.metrics.get('mape', 0),
            'revenue_r2': revenue_result.metrics.get('r2', 0),
            'expense_r2': expense_result.metrics.get('r2', 0),
            'avg_revenue': profit_df['revenue'].mean(),
            'avg_expense': profit_df['expense'].mean(),
            'avg_profit': profit_df['profit'].mean(),
            'avg_margin_pct': profit_df['margin_pct'].mean(),
        }

        print(f"\n✅ Multi-output ML forecast complete!")
        print(f"   Revenue MAPE: {metrics['revenue_mape']:.2%}")
        print(f"   Expense MAPE: {metrics['expense_mape']:.2%}")
        print(f"   Revenue R²: {metrics['revenue_r2']:.3f}")
        print(f"   Expense R²: {metrics['expense_r2']:.3f}")

        return JointForecastResult(
            revenue_forecast=revenue_result.forecast_df.rename(columns={'yhat': 'revenue'}),
            expense_forecast=expense_result.forecast_df.rename(columns={'yhat': 'expense'}),
            profit_forecast=profit_df,
            metrics=metrics,
            method='multioutput_ml',
            component_results={
                'ml_model': ml_model,
                'revenue_feature_importance': revenue_result.feature_importance,
                'expense_feature_importance': expense_result.feature_importance
            }
        )

    # ==================================================
    # Helper Methods
    # ==================================================

    def _auto_classify_expenses(self,
                                df_expense: pd.DataFrame,
                                df_revenue: pd.DataFrame,
                                date_column: str,
                                expense_column: str,
                                revenue_column: str) -> Dict[str, str]:
        """Auto-classify expenses as fixed/variable/semi-variable"""

        classification = {}

        # Aggregate
        df_exp_agg = df_expense.groupby(date_column)[expense_column].sum().reset_index()
        df_rev_agg = df_revenue.groupby(date_column)[revenue_column].sum().reset_index()

        df_merged = df_exp_agg.merge(df_rev_agg, on=date_column)

        # Calculate coefficient of variation
        cv = df_merged[expense_column].std() / df_merged[expense_column].mean()

        # Calculate correlation with revenue
        correlation = df_merged[expense_column].corr(df_merged[revenue_column])

        # Classify
        if cv < 0.1:
            cost_type = 'fixed'
        elif abs(correlation) > 0.7:
            cost_type = 'variable'
        else:
            cost_type = 'semi_variable'

        classification['total'] = cost_type

        print(f"  Auto-classification: {cost_type} (CV={cv:.2f}, Corr={correlation:.2f})")

        return classification

    def _determine_cost_type(self, row, classification: Dict) -> str:
        """Determine cost type for a row"""
        # Can be extended to check GL code, category, etc.
        return classification.get('total', 'semi_variable')

    def _create_scenarios(self,
                         revenue_result: ForecastResult,
                         expense_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Create best/worst case scenarios"""

        scenarios = {}

        # Pessimistic scenario
        scenarios['pessimistic'] = pd.DataFrame({
            'ds': revenue_result.forecast_df['ds'],
            'revenue': revenue_result.forecast_df.get('yhat_lower', revenue_result.forecast_df['yhat'] * 0.9),
            'expense': expense_df['expense'] * 1.1,
        })
        scenarios['pessimistic']['profit'] = scenarios['pessimistic']['revenue'] - scenarios['pessimistic']['expense']
        scenarios['pessimistic']['margin_pct'] = (scenarios['pessimistic']['profit'] / scenarios['pessimistic']['revenue'] * 100)

        # Base scenario
        scenarios['base'] = pd.DataFrame({
            'ds': revenue_result.forecast_df['ds'],
            'revenue': revenue_result.forecast_df['yhat'],
            'expense': expense_df['expense'],
        })
        scenarios['base']['profit'] = scenarios['base']['revenue'] - scenarios['base']['expense']
        scenarios['base']['margin_pct'] = (scenarios['base']['profit'] / scenarios['base']['revenue'] * 100)

        # Optimistic scenario
        scenarios['optimistic'] = pd.DataFrame({
            'ds': revenue_result.forecast_df['ds'],
            'revenue': revenue_result.forecast_df.get('yhat_upper', revenue_result.forecast_df['yhat'] * 1.1),
            'expense': expense_df['expense'] * 0.95,
        })
        scenarios['optimistic']['profit'] = scenarios['optimistic']['revenue'] - scenarios['optimistic']['expense']
        scenarios['optimistic']['margin_pct'] = (scenarios['optimistic']['profit'] / scenarios['optimistic']['revenue'] * 100)

        return scenarios

    def compare_methods(self,
                       df: pd.DataFrame,
                       date_column: str = 'month',
                       revenue_column: str = 'revenue',
                       expense_column: str = 'expense',
                       forecast_periods: int = 12) -> pd.DataFrame:
        """
        Compare all forecasting methods

        Returns:
            DataFrame with comparison
        """
        print("\n" + "="*60)
        print("COMPARING ALL METHODS")
        print("="*60)

        results_all = {}

        # Sequential
        try:
            df_rev = df[[date_column, revenue_column]].copy()
            df_exp = df[[date_column, expense_column]].copy()
            df_exp['cost_type'] = 'semi_variable'

            result_seq = self.forecast_sequential(
                df_revenue=df_rev,
                df_expense=df_exp,
                date_column=date_column,
                revenue_column=revenue_column,
                expense_column=expense_column,
                forecast_periods=forecast_periods
            )
            results_all['Sequential'] = result_seq.metrics

        except Exception as e:
            print(f"\nSequential failed: {e}")

        # VAR
        try:
            result_var = self.forecast_simultaneous_var(
                df=df,
                date_column=date_column,
                revenue_column=revenue_column,
                expense_column=expense_column,
                forecast_periods=forecast_periods
            )
            results_all['VAR'] = result_var.metrics

        except Exception as e:
            print(f"\nVAR failed: {e}")

        # Multi-output ML
        try:
            result_ml = self.forecast_multioutput_ml(
                df=df,
                date_column=date_column,
                revenue_column=revenue_column,
                expense_column=expense_column,
                forecast_periods=forecast_periods
            )
            results_all['MultiOutput_ML'] = result_ml.metrics

        except Exception as e:
            print(f"\nMulti-output ML failed: {e}")

        # Create comparison DataFrame
        comparison = pd.DataFrame(results_all).T
        comparison = comparison[['revenue_mape', 'expense_mape', 'avg_profit', 'avg_margin_pct']]

        return comparison
