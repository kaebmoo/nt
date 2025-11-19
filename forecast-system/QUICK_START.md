# 🚀 Quick Start Guide

## Installation

```bash
# Navigate to project directory
cd forecast-system

# Install dependencies
pip install -r requirements.txt

# Generate sample data
cd data/sample
python generate_sample_data.py
cd ../..
```

## Usage

### 1. Web Interface (Easiest)

```bash
streamlit run src/web/app.py
```

Then open your browser at `http://localhost:8501`

### 2. Python API

#### Revenue Forecasting

```python
from src.engines.revenue_engine import RevenueForecastEngine
import pandas as pd

# Load data
df = pd.read_csv('data/sample/revenue_total_sample.csv')

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
print(result.summary())
print(result.forecast_df)
```

#### Expense Forecasting

```python
from src.engines.expense_engine import ExpenseForecastEngine
import pandas as pd

# Load data
df = pd.read_csv('data/sample/expense_sample.csv')

# Create engine
engine = ExpenseForecastEngine()

# Forecast by GL code
results = engine.forecast_by_gl_code(
    df=df,
    date_column='month',
    value_column='expense',
    forecast_periods=12
)

# Show summary
summary = engine.get_expense_summary()
print(summary)
```

## Examples

### Forecast Revenue by Sales Unit

```python
from src.engines.revenue_engine import RevenueForecastEngine
import pandas as pd

df = pd.read_csv('data/sample/revenue_sample.csv')
engine = RevenueForecastEngine()

# Forecast by sales unit
results = engine.forecast_by_dimension(
    df=df,
    dimension='sales_unit',
    date_column='month',
    value_column='revenue',
    model_type='prophet',
    forecast_periods=12
)

# Show results for each unit
for unit, result in results.items():
    print(f"\n{unit}:")
    print(f"  MAPE: {result.metrics['mape']:.2%}")
    print(f"  Total Forecast: {result.forecast_df['yhat'].sum():,.0f}")
```

### Compare Models

```python
comparison = engine.compare_models(
    df=df,
    date_column='month',
    value_column='revenue',
    models=['prophet', 'sarimax', 'xgboost', 'holt_winters']
)

print(comparison)
```

### Export Results

```python
from src.utils.export import ForecastExporter

exporter = ForecastExporter()

# Export to Excel
exporter.to_excel(result, 'forecast_output.xlsx')

# Export to CSV
exporter.to_csv(result, 'forecast_output.csv')

# Export HTML report
exporter.to_html_report(result, 'forecast_report.html', historical_data=df)
```

### Visualize Results

```python
from src.utils.visualization import ForecastVisualizer

viz = ForecastVisualizer()

# Plot forecast
fig = viz.plot_forecast(result, historical_data=df)
fig.savefig('forecast_plot.png')

# Interactive plot
fig_interactive = viz.plot_forecast_interactive(result, historical_data=df)
fig_interactive.show()
```

## Available Models

1. **Prophet** - Best for data with strong seasonality
2. **SARIMAX** - Time series with external variables
3. **XGBoost** - Machine learning for high accuracy
4. **Holt-Winters** - Fast exponential smoothing
5. **Ensemble** - Combines multiple models

## Tips

- **Revenue**: Start with Prophet model
- **Fixed Costs**: Use moving_average method
- **Variable Costs**: Use linear regression with revenue
- **High Accuracy**: Try ensemble model
- **Multiple Dimensions**: Use forecast_by_dimension()

## Troubleshooting

### ImportError: No module named 'prophet'

```bash
pip install prophet
```

### SARIMAX taking too long

Set `auto_arima=False` in SARIMAXModel or use simpler order parameters.

### Data validation errors

Use DataProcessor to clean your data first:

```python
from src.core.data_processor import DataProcessor

processor = DataProcessor()

# Validate
validation = processor.validate_data(df, 'date', 'value')
print(validation)

# Clean
df_clean = processor.clean_data(df, 'date', 'value')
```

## Next Steps

- Check `notebooks/` for detailed examples
- Read `README.md` for full documentation
- Modify `config/config.yaml` for custom settings
- Explore the web interface for interactive forecasting

Happy Forecasting! 📊
