# 📊 Forecast System - รายได้และค่าใช้จ่าย

ระบบพยากรณ์รายได้และค่าใช้จ่ายที่ครอบคลุม สามารถใช้งานง่ายผ่าน Web Interface

## ✨ Features

### 🎯 การพยากรณ์
- **รายได้ (Revenue)**: พยากรณ์ตาม Product, หน่วยงานขาย, กลุ่มบริการ, กลุ่มธุรกิจ
- **ค่าใช้จ่าย (Expenses)**: พยากรณ์ตาม GL Code, หมวดบัญชี, หน่วยงาน
- **Hierarchical Forecasting**: พยากรณ์หลายระดับพร้อม reconciliation

### 🤖 โมเดล
1. **Prophet** - เหมาะกับข้อมูลที่มี seasonality และ holidays
2. **SARIMAX** - Time series + External variables
3. **XGBoost** - Machine Learning สำหรับ accuracy สูง
4. **Holt-Winters** - Exponential smoothing สำหรับความเร็ว
5. **Ensemble** - รวมหลายโมเดลเพื่อความแม่นยำสูงสุด

### 📈 Capabilities
- Upload ข้อมูล CSV/Excel
- เลือกโมเดลและปรับ parameters
- Visualization แบบ interactive
- Export ผลลัพธ์ (CSV, Excel, PDF)
- Model comparison และ evaluation
- Confidence intervals

## 🚀 Quick Start

### Installation

```bash
# Clone repository
cd forecast-system

# Install dependencies
pip install -r requirements.txt

# Run web app
streamlit run src/web/app.py
```

### ใช้งานผ่าน Web Interface

```bash
streamlit run src/web/app.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8501`

### ใช้งานผ่าน Python

```python
from src.engines.revenue_engine import RevenueForecastEngine
import pandas as pd

# Load data
df = pd.read_csv('data/sample/revenue_sample.csv')

# Create engine
engine = RevenueForecastEngine()

# Forecast
result = engine.forecast(
    df=df,
    date_column='month',
    value_column='revenue',
    model_type='prophet',
    forecast_periods=12
)

# Show results
print(result.forecast_df)
print(f"MAPE: {result.metrics['mape']:.2%}")
```

## 📁 Project Structure

```
forecast-system/
├── src/
│   ├── core/              # Data processing & validation
│   ├── models/            # Forecast models
│   ├── engines/           # Revenue/Expense engines
│   ├── utils/             # Utilities
│   └── web/               # Web interface
├── data/
│   └── sample/            # Example data
├── config/                # Configuration
└── notebooks/             # Jupyter notebooks
```

## 📊 Data Format

### Revenue Data (รายได้)

| month      | sales_unit | product | business_group | revenue |
|------------|------------|---------|----------------|---------|
| 2023-01-01 | ภาคกลาง    | Fiber   | Enterprise     | 1000000 |
| 2023-01-01 | ภาคเหนือ   | Mobile  | SME            | 500000  |

### Expense Data (ค่าใช้จ่าย)

| month      | gl_code | category | department | expense |
|------------|---------|----------|------------|---------|
| 2023-01-01 | 5001    | Salary   | IT         | 800000  |
| 2023-01-01 | 5101    | COGS     | Sales      | 300000  |

## 🎓 Usage Examples

### 1. Revenue Forecast by Sales Unit

```python
from src.engines.revenue_engine import RevenueForecastEngine

engine = RevenueForecastEngine()

# Forecast by sales unit
results = engine.forecast_by_dimension(
    df=df_revenue,
    dimension='sales_unit',
    model_type='prophet',
    forecast_periods=12
)

# Visualize
results.plot()
```

### 2. Expense Forecast by Type

```python
from src.engines.expense_engine import ExpenseForecastEngine

engine = ExpenseForecastEngine()

# Classify expenses
df_classified = engine.classify_expense_type(df_expense)

# Forecast fixed costs
fixed_forecast = engine.forecast_fixed_costs(df_classified)

# Forecast variable costs with revenue
variable_forecast = engine.forecast_variable_costs(
    df_expense=df_classified,
    df_revenue=df_revenue
)
```

### 3. Hierarchical Forecast

```python
from src.engines.hierarchical_engine import HierarchicalForecastEngine

engine = HierarchicalForecastEngine()

# Define hierarchy
hierarchy = {
    'levels': ['total', 'sales_unit', 'product'],
    'aggregation': 'sum'
}

# Forecast with reconciliation
result = engine.forecast_hierarchical(
    df=df,
    hierarchy=hierarchy,
    model_type='prophet'
)

# Reconciled forecasts
print(result.reconciled_df)
```

## 📈 Model Selection Guide

| Use Case                          | Recommended Model | Why                           |
|-----------------------------------|-------------------|-------------------------------|
| Total Revenue/Expense             | Prophet           | Handles seasonality well      |
| With External Variables           | SARIMAX           | Supports exogenous variables  |
| High Accuracy Needed              | XGBoost           | Best for complex patterns     |
| Quick Forecasting                 | Holt-Winters      | Fast and simple               |
| Best Accuracy                     | Ensemble          | Combines multiple models      |
| Fixed Costs                       | Moving Average    | Stable and predictable        |
| Variable Costs (vs Revenue)       | Linear Regression | Simple correlation            |

## 🔧 Configuration

Edit `config/config.yaml` to customize:

```yaml
models:
  prophet:
    yearly_seasonality: true
    weekly_seasonality: false
    changepoint_prior_scale: 0.05

  sarimax:
    order: [1, 1, 1]
    seasonal_order: [1, 1, 1, 12]

  xgboost:
    n_estimators: 1000
    learning_rate: 0.01
    max_depth: 5
```

## 📊 Metrics

- **MAPE** (Mean Absolute Percentage Error)
- **MAE** (Mean Absolute Error)
- **RMSE** (Root Mean Squared Error)
- **R²** (Coefficient of Determination)
- **Coverage** (Confidence Interval Coverage)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

MIT License

## 📧 Contact

For questions or support, please open an issue.

---

**Developed for easy-to-use revenue and expense forecasting** 🚀
