"""
Generate sample data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Set seed for reproducibility
np.random.seed(42)

# Generate dates (3 years of monthly data)
dates = pd.date_range('2021-01-01', periods=36, freq='M')

# ===== Revenue Data =====
print("Generating sample revenue data...")

revenue_data = []

sales_units = ['ภาคกลาง', 'ภาคเหนือ', 'ภาคใต้', 'ภาคตะวันออกเฉียงเหนือ']
products = ['Fiber Internet', 'Mobile', 'Cloud Service', 'Data Center']
business_groups = ['Enterprise', 'SME', 'Consumer']

for date in dates:
    month_idx = date.month - 1

    for sales_unit in sales_units:
        for product in products:
            for business_group in business_groups:
                # Base revenue
                base = 500000

                # Trend (growth over time)
                trend = (dates.get_loc(date) * 5000)

                # Seasonality (higher in certain months)
                seasonality = 100000 * np.sin(month_idx * 2 * np.pi / 12)

                # Unit-specific factors
                if sales_unit == 'ภาคกลาง':
                    base *= 1.5
                elif sales_unit == 'ภาคเหนือ':
                    base *= 0.8

                # Product-specific factors
                if product == 'Fiber Internet':
                    base *= 1.3
                elif product == 'Cloud Service':
                    base *= 1.1

                # Business group factors
                if business_group == 'Enterprise':
                    base *= 1.4
                elif business_group == 'Consumer':
                    base *= 0.9

                # Random noise
                noise = np.random.normal(0, base * 0.1)

                revenue = max(0, base + trend + seasonality + noise)

                revenue_data.append({
                    'month': date,
                    'sales_unit': sales_unit,
                    'product': product,
                    'business_group': business_group,
                    'revenue': round(revenue, 2)
                })

df_revenue = pd.DataFrame(revenue_data)

# Save revenue data
df_revenue.to_csv('revenue_sample.csv', index=False)
print(f"✓ Revenue data saved: {len(df_revenue)} rows")

# Aggregated revenue (total)
df_revenue_total = df_revenue.groupby('month')['revenue'].sum().reset_index()
df_revenue_total.to_csv('revenue_total_sample.csv', index=False)
print(f"✓ Total revenue data saved: {len(df_revenue_total)} rows")

# ===== Expense Data =====
print("\nGenerating sample expense data...")

expense_data = []

gl_codes = {
    '5001': {'name': 'Salary', 'type': 'fixed', 'base': 800000},
    '5002': {'name': 'OT Pay', 'type': 'semi_variable', 'base': 50000},
    '5101': {'name': 'COGS', 'type': 'variable', 'base': 300000},
    '5201': {'name': 'Marketing', 'type': 'variable', 'base': 200000},
    '5301': {'name': 'Utilities', 'type': 'semi_variable', 'base': 100000},
    '6001': {'name': 'Depreciation', 'type': 'fixed', 'base': 150000}
}

departments = ['IT', 'Sales', 'Operations', 'Finance']

for date in dates:
    month_idx = date.month - 1

    # Get total revenue for this month (for variable costs)
    monthly_revenue = df_revenue_total[df_revenue_total['month'] == date]['revenue'].values[0]

    for gl_code, info in gl_codes.items():
        for department in departments:
            base = info['base']

            if info['type'] == 'fixed':
                # Fixed cost - very stable
                noise = np.random.normal(0, base * 0.02)
                expense = base + noise

            elif info['type'] == 'variable':
                # Variable cost - correlated with revenue
                ratio = base / df_revenue_total['revenue'].mean()
                expense = monthly_revenue * ratio
                noise = np.random.normal(0, expense * 0.1)
                expense = expense + noise

            else:  # semi_variable
                # Fixed component + variable component
                fixed_part = base * 0.6
                variable_part = base * 0.4 * (monthly_revenue / df_revenue_total['revenue'].mean())
                noise = np.random.normal(0, base * 0.05)
                expense = fixed_part + variable_part + noise

            # Department-specific adjustment
            if department == 'IT':
                expense *= 1.2
            elif department == 'Finance':
                expense *= 0.8

            expense = max(0, expense)

            expense_data.append({
                'month': date,
                'gl_code': gl_code,
                'gl_name': info['name'],
                'category': info['type'],
                'department': department,
                'expense': round(expense, 2)
            })

df_expense = pd.DataFrame(expense_data)

# Save expense data
df_expense.to_csv('expense_sample.csv', index=False)
print(f"✓ Expense data saved: {len(df_expense)} rows")

# Aggregated expense (total)
df_expense_total = df_expense.groupby('month')['expense'].sum().reset_index()
df_expense_total.to_csv('expense_total_sample.csv', index=False)
print(f"✓ Total expense data saved: {len(df_expense_total)} rows")

# ===== Summary =====
print("\n" + "="*50)
print("Sample Data Generation Complete!")
print("="*50)
print(f"\nFiles created:")
print(f"  - revenue_sample.csv ({len(df_revenue)} rows)")
print(f"  - revenue_total_sample.csv ({len(df_revenue_total)} rows)")
print(f"  - expense_sample.csv ({len(df_expense)} rows)")
print(f"  - expense_total_sample.csv ({len(df_expense_total)} rows)")

print(f"\nRevenue range: {df_revenue['revenue'].min():,.0f} - {df_revenue['revenue'].max():,.0f}")
print(f"Total monthly revenue: {df_revenue_total['revenue'].min():,.0f} - {df_revenue_total['revenue'].max():,.0f}")
print(f"Expense range: {df_expense['expense'].min():,.0f} - {df_expense['expense'].max():,.0f}")
print(f"Total monthly expense: {df_expense_total['expense'].min():,.0f} - {df_expense_total['expense'].max():,.0f}")
