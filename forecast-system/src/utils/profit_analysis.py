"""
Profit and Margin Analysis Utilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns


class ProfitAnalyzer:
    """Analyze profit and margins from joint forecasts"""

    @staticmethod
    def calculate_kpis(revenue_df: pd.DataFrame,
                      expense_df: pd.DataFrame,
                      revenue_col: str = 'revenue',
                      expense_col: str = 'expense') -> Dict[str, float]:
        """
        Calculate key profitability KPIs

        Args:
            revenue_df: Revenue forecast DataFrame
            expense_df: Expense forecast DataFrame
            revenue_col: Revenue column name
            expense_col: Expense column name

        Returns:
            Dictionary of KPIs
        """
        revenue = revenue_df[revenue_col].values
        expense = expense_df[expense_col].values

        profit = revenue - expense
        margin_pct = (profit / revenue) * 100

        kpis = {
            'total_revenue': revenue.sum(),
            'total_expense': expense.sum(),
            'total_profit': profit.sum(),
            'avg_revenue': revenue.mean(),
            'avg_expense': expense.mean(),
            'avg_profit': profit.mean(),
            'avg_margin_pct': margin_pct.mean(),
            'min_margin_pct': margin_pct.min(),
            'max_margin_pct': margin_pct.max(),
            'revenue_growth_pct': ((revenue[-1] - revenue[0]) / revenue[0] * 100) if len(revenue) > 1 else 0,
            'expense_growth_pct': ((expense[-1] - expense[0]) / expense[0] * 100) if len(expense) > 1 else 0,
            'profit_growth_pct': ((profit[-1] - profit[0]) / profit[0] * 100) if len(profit) > 1 and profit[0] != 0 else 0,
            'expense_to_revenue_ratio': expense.sum() / revenue.sum(),
            'breakeven_revenue': expense.sum(),  # Revenue needed to break even
        }

        return kpis

    @staticmethod
    def scenario_analysis(revenue_forecast: np.ndarray,
                         expense_forecast: np.ndarray,
                         revenue_scenarios: Dict[str, float] = None,
                         expense_scenarios: Dict[str, float] = None) -> pd.DataFrame:
        """
        Create scenario analysis

        Args:
            revenue_forecast: Base revenue forecast
            expense_forecast: Base expense forecast
            revenue_scenarios: Dict of {scenario_name: multiplier}
            expense_scenarios: Dict of {scenario_name: multiplier}

        Returns:
            DataFrame with scenarios
        """
        if revenue_scenarios is None:
            revenue_scenarios = {
                'pessimistic': 0.90,
                'base': 1.00,
                'optimistic': 1.10
            }

        if expense_scenarios is None:
            expense_scenarios = {
                'pessimistic': 1.10,
                'base': 1.00,
                'optimistic': 0.95
            }

        scenarios = []

        for rev_scenario, rev_mult in revenue_scenarios.items():
            for exp_scenario, exp_mult in expense_scenarios.items():
                revenue = revenue_forecast * rev_mult
                expense = expense_forecast * exp_mult
                profit = revenue - expense
                margin = (profit / revenue) * 100

                scenario_name = f"{rev_scenario}_revenue_{exp_scenario}_expense"

                scenarios.append({
                    'scenario': scenario_name,
                    'revenue_scenario': rev_scenario,
                    'expense_scenario': exp_scenario,
                    'total_revenue': revenue.sum(),
                    'total_expense': expense.sum(),
                    'total_profit': profit.sum(),
                    'avg_margin_pct': margin.mean(),
                    'min_profit': profit.min(),
                    'max_profit': profit.max()
                })

        return pd.DataFrame(scenarios)

    @staticmethod
    def sensitivity_analysis(base_revenue: float,
                           base_expense: float,
                           revenue_range: tuple = (-20, 20),
                           expense_range: tuple = (-20, 20),
                           steps: int = 10) -> pd.DataFrame:
        """
        Sensitivity analysis for profit margin

        Args:
            base_revenue: Base revenue value
            base_expense: Base expense value
            revenue_range: Tuple of (min_pct_change, max_pct_change)
            expense_range: Tuple of (min_pct_change, max_pct_change)
            steps: Number of steps

        Returns:
            DataFrame with sensitivity results
        """
        results = []

        revenue_changes = np.linspace(revenue_range[0], revenue_range[1], steps)
        expense_changes = np.linspace(expense_range[0], expense_range[1], steps)

        for rev_change in revenue_changes:
            for exp_change in expense_changes:
                revenue = base_revenue * (1 + rev_change / 100)
                expense = base_expense * (1 + exp_change / 100)
                profit = revenue - expense
                margin = (profit / revenue) * 100

                results.append({
                    'revenue_change_pct': rev_change,
                    'expense_change_pct': exp_change,
                    'revenue': revenue,
                    'expense': expense,
                    'profit': profit,
                    'margin_pct': margin
                })

        return pd.DataFrame(results)

    @staticmethod
    def plot_profit_waterfall(revenue: float,
                             fixed_expense: float,
                             variable_expense: float,
                             other_expense: float = 0,
                             title: str = "Profit Waterfall") -> plt.Figure:
        """
        Create profit waterfall chart

        Args:
            revenue: Total revenue
            fixed_expense: Fixed costs
            variable_expense: Variable costs
            other_expense: Other expenses
            title: Chart title

        Returns:
            matplotlib Figure
        """
        categories = ['Revenue', 'Fixed\nCosts', 'Variable\nCosts']
        values = [revenue, -fixed_expense, -variable_expense]

        if other_expense > 0:
            categories.append('Other\nCosts')
            values.append(-other_expense)

        categories.append('Profit')
        profit = revenue - fixed_expense - variable_expense - other_expense
        values.append(profit)

        # Calculate cumulative
        cumulative = np.cumsum([0] + values)

        fig, ax = plt.subplots(figsize=(12, 6))

        # Plot bars
        colors = ['green' if i == 0 else 'red' if i < len(values)-1 else 'blue'
                 for i in range(len(values))]

        for i, (cat, val) in enumerate(zip(categories, values)):
            if i == 0:
                # Revenue bar from 0
                ax.bar(i, val, color=colors[i], alpha=0.7)
            else:
                # Other bars from cumulative
                ax.bar(i, val, bottom=cumulative[i], color=colors[i], alpha=0.7)

            # Add value labels
            if val >= 0:
                ax.text(i, cumulative[i+1] + revenue*0.02, f'{val:,.0f}',
                       ha='center', va='bottom', fontweight='bold')
            else:
                ax.text(i, cumulative[i+1] - revenue*0.02, f'{val:,.0f}',
                       ha='center', va='top', fontweight='bold')

        # Connect bars with lines
        for i in range(len(values)-1):
            ax.plot([i+0.4, i+0.6], [cumulative[i+1], cumulative[i+1]],
                   'k--', linewidth=1, alpha=0.5)

        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, fontsize=11)
        ax.set_ylabel('Amount', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_sensitivity_heatmap(sensitivity_df: pd.DataFrame) -> plt.Figure:
        """
        Plot sensitivity analysis heatmap

        Args:
            sensitivity_df: DataFrame from sensitivity_analysis()

        Returns:
            matplotlib Figure
        """
        # Pivot for heatmap
        pivot = sensitivity_df.pivot(
            index='expense_change_pct',
            columns='revenue_change_pct',
            values='margin_pct'
        )

        fig, ax = plt.subplots(figsize=(12, 8))

        sns.heatmap(pivot,
                   annot=True,
                   fmt='.1f',
                   cmap='RdYlGn',
                   center=0,
                   ax=ax,
                   cbar_kws={'label': 'Profit Margin %'})

        ax.set_xlabel('Revenue Change %', fontsize=12)
        ax.set_ylabel('Expense Change %', fontsize=12)
        ax.set_title('Profit Margin Sensitivity Analysis', fontsize=14, fontweight='bold')

        plt.tight_layout()
        return fig

    @staticmethod
    def plot_margin_trend(dates: pd.Series,
                         revenue: np.ndarray,
                         expense: np.ndarray,
                         title: str = "Profit Margin Trend") -> plt.Figure:
        """
        Plot profit margin trend over time

        Args:
            dates: Date series
            revenue: Revenue values
            expense: Expense values
            title: Chart title

        Returns:
            matplotlib Figure
        """
        profit = revenue - expense
        margin_pct = (profit / revenue) * 100

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Plot 1: Revenue, Expense, Profit
        ax1.plot(dates, revenue, label='Revenue', linewidth=2, marker='o', color='green')
        ax1.plot(dates, expense, label='Expense', linewidth=2, marker='s', color='red')
        ax1.plot(dates, profit, label='Profit', linewidth=2, marker='^', color='blue')
        ax1.fill_between(dates, 0, profit, alpha=0.2, color='blue')
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax1.set_ylabel('Amount', fontsize=12)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)

        # Plot 2: Margin %
        ax2.plot(dates, margin_pct, linewidth=2, marker='D', color='purple')
        ax2.fill_between(dates, 0, margin_pct, alpha=0.3, color='purple')
        ax2.axhline(y=margin_pct.mean(), color='red', linestyle='--',
                   label=f'Avg: {margin_pct.mean():.1f}%', linewidth=1.5)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Profit Margin %', fontsize=12)
        ax2.set_title('Profit Margin Trend', fontsize=12, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig

    @staticmethod
    def breakeven_analysis(fixed_costs: float,
                          variable_cost_ratio: float,
                          target_margin: float = 0.0) -> Dict[str, float]:
        """
        Calculate breakeven revenue

        Args:
            fixed_costs: Monthly fixed costs
            variable_cost_ratio: Variable costs as % of revenue
            target_margin: Target profit margin % (0 for breakeven)

        Returns:
            Dictionary with breakeven metrics
        """
        # Breakeven Revenue = Fixed Costs / (1 - Variable Cost Ratio - Target Margin)
        denominator = 1 - variable_cost_ratio - (target_margin / 100)

        if denominator <= 0:
            return {
                'breakeven_revenue': float('inf'),
                'error': 'Target margin not achievable with current cost structure'
            }

        breakeven_revenue = fixed_costs / denominator

        return {
            'breakeven_revenue': breakeven_revenue,
            'fixed_costs': fixed_costs,
            'variable_cost_ratio': variable_cost_ratio,
            'target_margin_pct': target_margin,
            'variable_costs_at_breakeven': breakeven_revenue * variable_cost_ratio,
            'total_costs_at_breakeven': fixed_costs + (breakeven_revenue * variable_cost_ratio),
            'profit_at_breakeven': breakeven_revenue * (target_margin / 100)
        }

    @staticmethod
    def format_kpi_report(kpis: Dict[str, float]) -> str:
        """
        Format KPIs as a readable report

        Args:
            kpis: Dictionary of KPIs

        Returns:
            Formatted string report
        """
        report = []
        report.append("=" * 60)
        report.append("PROFITABILITY ANALYSIS")
        report.append("=" * 60)

        report.append("\n📊 Revenue & Expense")
        report.append(f"  Total Revenue:        {kpis.get('total_revenue', 0):>15,.0f}")
        report.append(f"  Total Expense:        {kpis.get('total_expense', 0):>15,.0f}")
        report.append(f"  Total Profit:         {kpis.get('total_profit', 0):>15,.0f}")

        report.append("\n📈 Averages")
        report.append(f"  Avg Revenue/period:   {kpis.get('avg_revenue', 0):>15,.0f}")
        report.append(f"  Avg Expense/period:   {kpis.get('avg_expense', 0):>15,.0f}")
        report.append(f"  Avg Profit/period:    {kpis.get('avg_profit', 0):>15,.0f}")

        report.append("\n💰 Margins")
        report.append(f"  Avg Margin:           {kpis.get('avg_margin_pct', 0):>14.2f}%")
        report.append(f"  Min Margin:           {kpis.get('min_margin_pct', 0):>14.2f}%")
        report.append(f"  Max Margin:           {kpis.get('max_margin_pct', 0):>14.2f}%")

        report.append("\n📊 Growth Rates")
        report.append(f"  Revenue Growth:       {kpis.get('revenue_growth_pct', 0):>14.2f}%")
        report.append(f"  Expense Growth:       {kpis.get('expense_growth_pct', 0):>14.2f}%")
        report.append(f"  Profit Growth:        {kpis.get('profit_growth_pct', 0):>14.2f}%")

        report.append("\n📉 Ratios")
        report.append(f"  Expense/Revenue:      {kpis.get('expense_to_revenue_ratio', 0):>14.2%}")

        report.append("=" * 60)

        return "\n".join(report)
