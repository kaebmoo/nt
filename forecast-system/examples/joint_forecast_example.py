"""
Example: Joint Revenue & Expense Forecasting

This example demonstrates all 4 approaches:
1. Sequential (Revenue → Expense)
2. Simultaneous (VAR)
3. Multi-output ML (XGBoost)
4. Comparison of methods
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engines.joint_engine import JointForecastEngine
from src.utils.profit_analysis import ProfitAnalyzer
import matplotlib.pyplot as plt

# ==================================================
# Generate Sample Data
# ==================================================

print("="*60)
print("JOINT REVENUE & EXPENSE FORECASTING EXAMPLE")
print("="*60)

# Create sample data (3 years monthly)
np.random.seed(42)
dates = pd.date_range('2021-01-01', periods=36, freq='M')

# Revenue with trend and seasonality
base_revenue = 1000000
trend = np.arange(36) * 10000
seasonality = 100000 * np.sin(np.arange(36) * 2 * np.pi / 12)
noise_rev = np.random.normal(0, 30000, 36)
revenue = base_revenue + trend + seasonality + noise_rev

# Expense (70% of revenue + some fixed costs)
fixed_costs = 300000
variable_costs = revenue * 0.45  # 45% of revenue
semi_variable = 100000 + revenue * 0.05 + np.random.normal(0, 10000, 36)
expense = fixed_costs + variable_costs + semi_variable

# Create DataFrame
df = pd.DataFrame({
    'month': dates,
    'revenue': revenue,
    'expense': expense
})

# Also create separate revenue and expense DataFrames for sequential method
df_revenue = df[['month', 'revenue']].copy()
df_expense = df[['month', 'expense']].copy()
df_expense['cost_type'] = 'semi_variable'  # Will be auto-classified

print(f"\n📊 Sample Data: {len(df)} months")
print(f"   Revenue range: {df['revenue'].min():,.0f} - {df['revenue'].max():,.0f}")
print(f"   Expense range: {df['expense'].min():,.0f} - {df['expense'].max():,.0f}")

# ==================================================
# Initialize Engine
# ==================================================

engine = JointForecastEngine()
analyzer = ProfitAnalyzer()

# ==================================================
# Approach 1: Sequential Forecasting
# ==================================================

print("\n" + "="*60)
print("APPROACH 1: SEQUENTIAL FORECASTING")
print("="*60)

result_sequential = engine.forecast_sequential(
    df_revenue=df_revenue,
    df_expense=df_expense,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12,
    revenue_model='prophet'
)

print("\n📊 Sequential Results:")
print(result_sequential.profit_forecast[['ds', 'revenue', 'expense', 'profit', 'margin_pct']].to_string(index=False))

# ==================================================
# Approach 2: VAR Model
# ==================================================

print("\n" + "="*60)
print("APPROACH 2: VAR (SIMULTANEOUS)")
print("="*60)

result_var = engine.forecast_simultaneous_var(
    df=df,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12,
    maxlags=12
)

print("\n📊 VAR Results:")
print(result_var.profit_forecast[['ds', 'revenue', 'expense', 'profit', 'margin_pct']].head(12).to_string(index=False))

# ==================================================
# Approach 3: Multi-output ML
# ==================================================

print("\n" + "="*60)
print("APPROACH 3: MULTI-OUTPUT ML (XGBoost)")
print("="*60)

result_ml = engine.forecast_multioutput_ml(
    df=df,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12
)

print("\n📊 Multi-output ML Results:")
print(result_ml.profit_forecast[['ds', 'revenue', 'expense', 'profit', 'margin_pct']].head(12).to_string(index=False))

# ==================================================
# Compare Methods
# ==================================================

print("\n" + "="*60)
print("METHOD COMPARISON")
print("="*60)

comparison = pd.DataFrame({
    'Method': ['Sequential', 'VAR', 'MultiOutput ML'],
    'Avg Profit': [
        result_sequential.metrics['avg_profit'],
        result_var.metrics['avg_profit'],
        result_ml.metrics['avg_profit']
    ],
    'Avg Margin %': [
        result_sequential.metrics['avg_margin_pct'],
        result_var.metrics['avg_margin_pct'],
        result_ml.metrics['avg_margin_pct']
    ],
    'Revenue MAPE': [
        result_sequential.metrics.get('revenue_mape', 0),
        result_var.metrics.get('revenue_mape', 0),
        result_ml.metrics.get('revenue_mape', 0)
    ],
    'Expense MAPE': [
        0,  # Sequential doesn't have expense MAPE directly
        result_var.metrics.get('expense_mape', 0),
        result_ml.metrics.get('expense_mape', 0)
    ]
})

print("\n" + comparison.to_string(index=False))

# ==================================================
# Profit Analysis
# ==================================================

print("\n" + "="*60)
print("PROFIT ANALYSIS (Using Sequential Results)")
print("="*60)

# Calculate KPIs
kpis = analyzer.calculate_kpis(
    result_sequential.revenue_forecast,
    result_sequential.expense_forecast,
    revenue_col='revenue',
    expense_col='expense'
)

report = analyzer.format_kpi_report(kpis)
print(report)

# ==================================================
# Scenario Analysis
# ==================================================

print("\n" + "="*60)
print("SCENARIO ANALYSIS")
print("="*60)

scenarios_df = analyzer.scenario_analysis(
    revenue_forecast=result_sequential.revenue_forecast['revenue'].values,
    expense_forecast=result_sequential.expense_forecast['expense'].values
)

print("\n" + scenarios_df.to_string(index=False))

# ==================================================
# Visualization
# ==================================================

print("\n📊 Creating visualizations...")

# Plot 1: Comparison of all methods
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Sequential
axes[0, 0].plot(result_sequential.profit_forecast['ds'],
               result_sequential.profit_forecast['revenue'],
               label='Revenue', color='green', linewidth=2)
axes[0, 0].plot(result_sequential.profit_forecast['ds'],
               result_sequential.profit_forecast['expense'],
               label='Expense', color='red', linewidth=2)
axes[0, 0].set_title('Sequential Forecast', fontsize=14, fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# VAR
axes[0, 1].plot(result_var.profit_forecast['ds'],
               result_var.profit_forecast['revenue'],
               label='Revenue', color='green', linewidth=2)
axes[0, 1].plot(result_var.profit_forecast['ds'],
               result_var.profit_forecast['expense'],
               label='Expense', color='red', linewidth=2)
axes[0, 1].set_title('VAR (Simultaneous) Forecast', fontsize=14, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Multi-output ML
axes[1, 0].plot(result_ml.profit_forecast['ds'],
               result_ml.profit_forecast['revenue'],
               label='Revenue', color='green', linewidth=2)
axes[1, 0].plot(result_ml.profit_forecast['ds'],
               result_ml.profit_forecast['expense'],
               label='Expense', color='red', linewidth=2)
axes[1, 0].set_title('Multi-output ML Forecast', fontsize=14, fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

# Profit comparison
axes[1, 1].plot(result_sequential.profit_forecast['ds'],
               result_sequential.profit_forecast['profit'],
               label='Sequential', linewidth=2, marker='o')
axes[1, 1].plot(result_var.profit_forecast['ds'],
               result_var.profit_forecast['profit'],
               label='VAR', linewidth=2, marker='s')
axes[1, 1].plot(result_ml.profit_forecast['ds'],
               result_ml.profit_forecast['profit'],
               label='Multi-output ML', linewidth=2, marker='^')
axes[1, 1].set_title('Profit Comparison', fontsize=14, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('joint_forecast_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: joint_forecast_comparison.png")

# Plot 2: Margin trend
fig2 = analyzer.plot_margin_trend(
    dates=result_sequential.profit_forecast['ds'],
    revenue=result_sequential.profit_forecast['revenue'].values,
    expense=result_sequential.profit_forecast['expense'].values,
    title="12-Month Profit Margin Forecast"
)
plt.savefig('margin_trend.png', dpi=300, bbox_inches='tight')
print("✓ Saved: margin_trend.png")

# Plot 3: Waterfall
fig3 = analyzer.plot_profit_waterfall(
    revenue=result_sequential.revenue_forecast['revenue'].sum(),
    fixed_expense=result_sequential.expense_forecast['fixed'].sum(),
    variable_expense=result_sequential.expense_forecast['variable'].sum(),
    other_expense=result_sequential.expense_forecast['semi_variable'].sum(),
    title="Profit Waterfall (12-month total)"
)
plt.savefig('profit_waterfall.png', dpi=300, bbox_inches='tight')
print("✓ Saved: profit_waterfall.png")

print("\n" + "="*60)
print("✅ EXAMPLE COMPLETE!")
print("="*60)
print("\nCreated files:")
print("  - joint_forecast_comparison.png")
print("  - margin_trend.png")
print("  - profit_waterfall.png")
