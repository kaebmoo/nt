# 🔄 Joint Revenue & Expense Forecasting Guide

## Overview

Joint forecasting พิจารณาความสัมพันธ์ระหว่างรายได้และค่าใช้จ่าย ซึ่งส่งผลต่อ **profit margin** และการวางแผนทางการเงิน

### ทำไมต้องพยากรณ์ร่วมกัน?

1. **Causal Relationship** - รายได้สูง → ค่าใช้จ่ายผันแปรสูง (COGS, Commission)
2. **Feedback Loop** - การลงทุน Marketing → รายได้เพิ่ม → กำไรเพิ่ม → ลงทุนต่อ
3. **Budget Constraints** - ต้องควบคุมค่าใช้จ่ายไม่ให้เกิน % ของรายได้
4. **Profitability Analysis** - ต้องรู้ Profit Margin ล่วงหน้า

---

## 🎯 4 แนวทางการพยากรณ์

### 1. Sequential (พยากรณ์ตามลำดับ) ⭐ **แนะนำเริ่มต้น**

**ขั้นตอน:**
```
Revenue → Fixed Costs → Variable Costs → Semi-variable → Total Expense → Profit
```

**ข้อดี:**
- ✅ เข้าใจง่าย ตรงตามกระบวนการธุรกิจ
- ✅ แยกประเภทค่าใช้จ่ายชัดเจน
- ✅ ใช้ได้กับข้อมูลที่ไม่มากนัก

**ข้อเสีย:**
- ❌ ไม่จับ feedback loop
- ❌ สมมติว่ารายได้ไม่ถูกกระทบจากค่าใช้จ่าย

**ตัวอย่างโค้ด:**

```python
from src.engines.joint_engine import JointForecastEngine
import pandas as pd

# Load data
df_revenue = pd.read_csv('revenue.csv')
df_expense = pd.read_csv('expense.csv')

# Create engine
engine = JointForecastEngine()

# Forecast
result = engine.forecast_sequential(
    df_revenue=df_revenue,
    df_expense=df_expense,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12,
    revenue_model='prophet'  # or 'sarimax', 'xgboost'
)

# Results
print(result.profit_forecast)
print(f"Avg Margin: {result.metrics['avg_margin_pct']:.2f}%")
```

---

### 2. VAR (Simultaneous Forecasting) ⭐⭐ **Advanced**

**ทำงานอย่างไร:**
- พยากรณ์ revenue และ expense **พร้อมกัน**
- ใช้ Vector Autoregression (VAR) model
- จับความสัมพันธ์แบบ bidirectional

**เหมาะกับ:**
- มี feedback loop ระหว่าง revenue และ expense
- ข้อมูลมีความสัมพันธ์กันสูง
- ต้องการทดสอบ Granger Causality

**ตัวอย่างโค้ด:**

```python
from src.engines.joint_engine import JointForecastEngine

engine = JointForecastEngine()

# VAR forecasting
result = engine.forecast_simultaneous_var(
    df=df,  # DataFrame with both revenue and expense
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12,
    maxlags=12  # Auto-selected optimal lags
)

# Check causality
if result.component_results and 'causality' in result.component_results:
    print("\nGranger Causality Test:")
    print(result.component_results['causality'])

# Results
print(result.profit_forecast)
```

**Granger Causality Test:**
- ทดสอบว่า revenue ส่งผลต่อ expense หรือไม่
- p-value < 0.05 = มีความสัมพันธ์เชิงเหตุผล

---

### 3. Multi-output ML (XGBoost) ⭐⭐⭐ **High Accuracy**

**ทำงานอย่างไร:**
- ใช้ Machine Learning พยากรณ์ revenue และ expense พร้อมกัน
- สร้าง features จาก lags, rolling means, cross-variables
- Non-linear relationships

**เหมาะกับ:**
- ต้องการ accuracy สูงสุด
- มีข้อมูลเพียงพอ (>24 periods)
- Pattern ซับซ้อน, non-linear

**ตัวอย่างโค้ด:**

```python
from src.engines.joint_engine import JointForecastEngine

engine = JointForecastEngine()

# Multi-output ML
result = engine.forecast_multioutput_ml(
    df=df,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12,

    # Optional: XGBoost parameters
    n_estimators=1000,
    learning_rate=0.01,
    max_depth=5
)

# Feature importance
if result.component_results:
    rev_importance = result.component_results['revenue_feature_importance']
    exp_importance = result.component_results['expense_feature_importance']

    print("\nTop features for Revenue:")
    print(sorted(rev_importance.items(), key=lambda x: x[1], reverse=True)[:5])

    print("\nTop features for Expense:")
    print(sorted(exp_importance.items(), key=lambda x: x[1], reverse=True)[:5])
```

---

### 4. Comparison (เปรียบเทียบทุกวิธี)

```python
from src.engines.joint_engine import JointForecastEngine

engine = JointForecastEngine()

# Compare all methods
comparison = engine.compare_methods(
    df=df,
    date_column='month',
    revenue_column='revenue',
    expense_column='expense',
    forecast_periods=12
)

print(comparison)
```

**Output:**
```
           Method  Revenue MAPE  Expense MAPE  Avg Profit  Avg Margin %
      Sequential          5.2%          7.3%     350,000         30.5%
             VAR          5.8%          6.9%     345,000         29.8%
MultiOutput ML          4.1%          5.2%     360,000         31.2%
```

---

## 💰 Profit & Margin Analysis

### Calculate KPIs

```python
from src.utils.profit_analysis import ProfitAnalyzer

analyzer = ProfitAnalyzer()

# Calculate KPIs
kpis = analyzer.calculate_kpis(
    revenue_df=result.revenue_forecast,
    expense_df=result.expense_forecast,
    revenue_col='revenue',
    expense_col='expense'
)

# Print report
report = analyzer.format_kpi_report(kpis)
print(report)
```

**Output:**
```
============================================================
PROFITABILITY ANALYSIS
============================================================

📊 Revenue & Expense
  Total Revenue:            12,500,000
  Total Expense:             8,750,000
  Total Profit:              3,750,000

📈 Averages
  Avg Revenue/period:        1,041,667
  Avg Expense/period:          729,167
  Avg Profit/period:           312,500

💰 Margins
  Avg Margin:                    30.00%
  Min Margin:                    28.50%
  Max Margin:                    31.80%

📊 Growth Rates
  Revenue Growth:                 8.50%
  Expense Growth:                 7.20%
  Profit Growth:                 12.30%

📉 Ratios
  Expense/Revenue:               70.00%
============================================================
```

---

## 📊 Scenario Analysis

### Create Scenarios

```python
from src.utils.profit_analysis import ProfitAnalyzer

analyzer = ProfitAnalyzer()

# Scenario analysis
scenarios = analyzer.scenario_analysis(
    revenue_forecast=result.revenue_forecast['revenue'].values,
    expense_forecast=result.expense_forecast['expense'].values,
    revenue_scenarios={
        'pessimistic': 0.90,  # -10%
        'base': 1.00,
        'optimistic': 1.10   # +10%
    },
    expense_scenarios={
        'pessimistic': 1.10,  # +10%
        'base': 1.00,
        'optimistic': 0.95   # -5%
    }
)

print(scenarios)
```

**Output:**
```
                        scenario  total_revenue  total_expense  total_profit  avg_margin_pct
pessimistic_revenue_pessimistic_expense     11,250,000      9,625,000     1,625,000           14.4%
          base_revenue_base_expense     12,500,000      8,750,000     3,750,000           30.0%
  optimistic_revenue_optimistic_expense     13,750,000      8,312,500     5,437,500           39.5%
```

---

## 🎨 Visualization

### Profit Margin Trend

```python
from src.utils.profit_analysis import ProfitAnalyzer

analyzer = ProfitAnalyzer()

# Plot margin trend
fig = analyzer.plot_margin_trend(
    dates=result.profit_forecast['ds'],
    revenue=result.profit_forecast['revenue'].values,
    expense=result.profit_forecast['expense'].values,
    title="12-Month Profit Margin Forecast"
)

fig.savefig('margin_trend.png')
```

### Profit Waterfall

```python
# Waterfall chart
fig = analyzer.plot_profit_waterfall(
    revenue=result.revenue_forecast['revenue'].sum(),
    fixed_expense=result.expense_forecast['fixed'].sum(),
    variable_expense=result.expense_forecast['variable'].sum(),
    other_expense=result.expense_forecast['semi_variable'].sum(),
    title="12-Month Profit Waterfall"
)

fig.savefig('profit_waterfall.png')
```

### Sensitivity Analysis

```python
# Sensitivity heatmap
sensitivity_df = analyzer.sensitivity_analysis(
    base_revenue=result.revenue_forecast['revenue'].mean(),
    base_expense=result.expense_forecast['expense'].mean(),
    revenue_range=(-20, 20),
    expense_range=(-20, 20),
    steps=10
)

fig = analyzer.plot_sensitivity_heatmap(sensitivity_df)
fig.savefig('sensitivity_heatmap.png')
```

---

## 🔧 Advanced Features

### Breakeven Analysis

```python
from src.utils.profit_analysis import ProfitAnalyzer

analyzer = ProfitAnalyzer()

# Calculate breakeven
breakeven = analyzer.breakeven_analysis(
    fixed_costs=300000,
    variable_cost_ratio=0.45,
    target_margin=30.0  # Target 30% margin
)

print(f"Breakeven Revenue: {breakeven['breakeven_revenue']:,.0f}")
print(f"Required for 30% margin: {breakeven['breakeven_revenue']:,.0f}")
```

---

## 📋 Best Practices

### 1. Data Preparation

```python
from src.core.data_processor import DataProcessor

processor = DataProcessor()

# Validate data
validation = processor.validate_data(df, 'month', 'revenue')
print(validation)

# Clean data
df_clean = processor.clean_data(
    df,
    date_column='month',
    value_column='revenue',
    handle_missing='interpolate',
    handle_duplicates='last'
)
```

### 2. Model Selection

| Situation | Recommended Method |
|-----------|-------------------|
| First time forecasting | Sequential |
| Have correlation data | VAR |
| Need highest accuracy | Multi-output ML |
| Want to compare | All methods |

### 3. Validation

```python
# Cross-validation
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=3, test_size=12)

for train_idx, test_idx in tscv.split(df):
    df_train = df.iloc[train_idx]
    df_test = df.iloc[test_idx]

    # Train and evaluate
    result = engine.forecast_sequential(...)

    # Calculate metrics
    actual_profit = df_test['revenue'] - df_test['expense']
    forecast_profit = result.profit_forecast['profit']

    # Compare
    mape = np.mean(np.abs((actual_profit - forecast_profit) / actual_profit))
    print(f"MAPE: {mape:.2%}")
```

---

## 🚀 Quick Start Example

```python
from src.engines.joint_engine import JointForecastEngine
from src.utils.profit_analysis import ProfitAnalyzer
import pandas as pd

# Load data
df = pd.read_csv('data.csv')  # Must have: month, revenue, expense

# 1. Create engine
engine = JointForecastEngine()

# 2. Forecast (choose one method)
result = engine.forecast_sequential(
    df_revenue=df[['month', 'revenue']],
    df_expense=df[['month', 'expense']],
    forecast_periods=12
)

# 3. Analyze
analyzer = ProfitAnalyzer()
kpis = analyzer.calculate_kpis(
    result.revenue_forecast,
    result.expense_forecast
)

# 4. Print results
print(analyzer.format_kpi_report(kpis))
print("\nForecast:")
print(result.profit_forecast)

# 5. Visualize
fig = analyzer.plot_margin_trend(
    result.profit_forecast['ds'],
    result.profit_forecast['revenue'].values,
    result.profit_forecast['expense'].values
)
fig.savefig('forecast_result.png')
```

---

## 📖 Complete Example

See `examples/joint_forecast_example.py` for a comprehensive example that demonstrates all 4 approaches.

Run it:
```bash
cd forecast-system
python examples/joint_forecast_example.py
```

---

## ❓ FAQ

**Q: ควรใช้วิธีไหน?**

A:
- เริ่มต้น: Sequential
- มีข้อมูลดี + เวลา: ลอง VAR และ Multi-output ML
- Production: Ensemble หลายวิธี

**Q: ข้อมูลต้องมีอย่างน้อยกี่ periods?**

A:
- Sequential: 24+ periods
- VAR: 36+ periods
- Multi-output ML: 36+ periods

**Q: จะรู้ได้ไงว่า revenue และ expense มีความสัมพันธ์?**

A:
```python
correlation = df['revenue'].corr(df['expense'])
print(f"Correlation: {correlation:.3f}")

# > 0.7 = High correlation → Use VAR or Multi-output ML
# < 0.3 = Low correlation → Sequential might be better
```

---

## 📚 References

- [VAR Model Theory](https://en.wikipedia.org/wiki/Vector_autoregression)
- [Granger Causality](https://en.wikipedia.org/wiki/Granger_causality)
- [Multi-output ML](https://scikit-learn.org/stable/modules/multioutput.html)

---

**Created by Forecast System v1.0** | [GitHub](https://github.com/kaebmoo/nt)
