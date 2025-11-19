"""
Streamlit Web Application for Forecast System
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engines.revenue_engine import RevenueForecastEngine
from src.engines.expense_engine import ExpenseForecastEngine
from src.utils.visualization import ForecastVisualizer
from src.utils.export import ForecastExporter
from src.core.data_processor import DataProcessor

# Page config
st.set_page_config(
    page_title="Forecast System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">📊 Forecast System - รายได้และค่าใช้จ่าย</div>',
           unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Settings")

forecast_type = st.sidebar.radio(
    "Select Forecast Type",
    ["Revenue", "Expense", "Model Comparison"]
)

# Initialize processors
@st.cache_resource
def get_engines():
    return RevenueForecastEngine(), ExpenseForecastEngine()

revenue_engine, expense_engine = get_engines()
processor = DataProcessor()
visualizer = ForecastVisualizer()
exporter = ForecastExporter()

# Main content
if forecast_type == "Revenue":
    st.header("💰 Revenue Forecasting")

    # File upload
    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Upload Revenue Data (CSV or Excel)",
            type=['csv', 'xlsx', 'xls'],
            help="File should contain columns: date, revenue, and optional dimensions (sales_unit, product, etc.)"
        )

    # Sample data option
    if uploaded_file is None:
        use_sample = st.checkbox("Use sample data for demo")

        if use_sample:
            # Create sample data
            import numpy as np
            dates = pd.date_range('2020-01-01', periods=36, freq='M')
            revenue = 1000000 + np.random.normal(0, 50000, 36) + np.arange(36) * 10000

            # Add seasonality
            seasonality = 100000 * np.sin(np.arange(36) * 2 * np.pi / 12)
            revenue = revenue + seasonality

            df = pd.DataFrame({
                'month': dates,
                'revenue': revenue,
                'sales_unit': np.random.choice(['ภาคกลาง', 'ภาคเหนือ', 'ภาคใต้'], 36),
                'product': np.random.choice(['Fiber', 'Mobile', 'Cloud'], 36)
            })

            st.success("✅ Using sample data")
        else:
            st.info("👆 Please upload a data file to begin")
            df = None
    else:
        # Load uploaded file
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"✅ File uploaded successfully! {len(df)} rows loaded.")

        except Exception as e:
            st.error(f"❌ Error loading file: {e}")
            df = None

    if df is not None:
        # Show data preview
        with st.expander("📋 Data Preview"):
            st.dataframe(df.head(10))

            # Data info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", len(df))
            with col2:
                st.metric("Columns", len(df.columns))
            with col3:
                date_col = st.selectbox("Date Column", df.columns, index=0)

        # Configuration
        st.subheader("⚙️ Configuration")

        col1, col2, col3 = st.columns(3)

        with col1:
            value_col = st.selectbox("Value Column", df.columns,
                                    index=df.columns.get_loc('revenue') if 'revenue' in df.columns else 1)

        with col2:
            model_type = st.selectbox(
                "Model Type",
                ["sarimax", "xgboost", "holt_winters", "prophet", "ensemble"],
                help="Select forecasting model (SARIMAX recommended if Prophet has issues)"
            )

        with col3:
            forecast_periods = st.number_input("Forecast Periods", min_value=1, max_value=36, value=12)

        # Advanced options
        with st.expander("🔧 Advanced Options"):
            dimension = st.selectbox(
                "Forecast by Dimension (optional)",
                ["None"] + [col for col in df.columns if col not in [date_col, value_col]],
                help="Group forecasting by dimension (e.g., sales_unit, product)"
            )

            if dimension != "None":
                st.info(f"Will create separate forecasts for each {dimension}")

        # Forecast button
        if st.button("🚀 Run Forecast", type="primary"):
            with st.spinner("Training model and generating forecast..."):
                try:
                    if dimension == "None":
                        # Total forecast
                        result = revenue_engine.forecast(
                            df=df,
                            date_column=date_col,
                            value_column=value_col,
                            model_type=model_type,
                            forecast_periods=forecast_periods
                        )

                        # Display results
                        st.success("✅ Forecast completed successfully!")

                        # Metrics
                        st.subheader("📊 Performance Metrics")
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.metric("MAPE", f"{result.metrics.get('mape', 0):.2%}")
                        with col2:
                            st.metric("MAE", f"{result.metrics.get('mae', 0):,.0f}")
                        with col3:
                            st.metric("RMSE", f"{result.metrics.get('rmse', 0):,.0f}")
                        with col4:
                            st.metric("R²", f"{result.metrics.get('r2', 0):.3f}")

                        # Visualization
                        st.subheader("📈 Forecast Visualization")
                        fig = visualizer.plot_forecast_interactive(result, df.rename(columns={date_col: 'ds', value_col: 'y'}))
                        st.plotly_chart(fig, use_container_width=True)

                        # Forecast table
                        st.subheader("📋 Forecast Values")
                        st.dataframe(result.forecast_df.style.format({
                            'yhat': '{:,.0f}',
                            'yhat_lower': '{:,.0f}',
                            'yhat_upper': '{:,.0f}'
                        }))

                        # Export
                        st.subheader("💾 Export Results")
                        col1, col2 = st.columns(2)

                        with col1:
                            if st.button("Export to Excel"):
                                exporter.to_excel(result, "forecast_results.xlsx")
                                st.success("Exported to forecast_results.xlsx")

                        with col2:
                            if st.button("Export to CSV"):
                                exporter.to_csv(result, "forecast_results.csv")
                                st.success("Exported to forecast_results.csv")

                    else:
                        # Forecast by dimension
                        results = revenue_engine.forecast_by_dimension(
                            df=df,
                            dimension=dimension,
                            date_column=date_col,
                            value_column=value_col,
                            model_type=model_type,
                            forecast_periods=forecast_periods
                        )

                        st.success(f"✅ Forecast completed for {len(results)} {dimension} groups!")

                        # Show results for each dimension
                        for dim_value, result in results.items():
                            with st.expander(f"{dimension}: {dim_value}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("MAPE", f"{result.metrics.get('mape', 0):.2%}")
                                with col2:
                                    st.metric("MAE", f"{result.metrics.get('mae', 0):,.0f}")
                                with col3:
                                    total_forecast = result.forecast_df['yhat'].sum()
                                    st.metric("Total Forecast", f"{total_forecast:,.0f}")

                                # Plot
                                fig = visualizer.plot_forecast_interactive(result)
                                st.plotly_chart(fig, use_container_width=True)

                        # Summary
                        st.subheader("📊 Summary by Dimension")
                        summary_data = []
                        for dim_value, result in results.items():
                            summary_data.append({
                                dimension: dim_value,
                                'Total Forecast': result.forecast_df['yhat'].sum(),
                                'Avg Monthly': result.forecast_df['yhat'].mean(),
                                'MAPE': result.metrics.get('mape', 0)
                            })

                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df.style.format({
                            'Total Forecast': '{:,.0f}',
                            'Avg Monthly': '{:,.0f}',
                            'MAPE': '{:.2%}'
                        }))

                except Exception as e:
                    error_msg = str(e)

                    # Check for Prophet/polars compatibility error
                    if "schema_overrides" in error_msg or "cmdstanpy" in error_msg:
                        st.error("❌ Prophet Model Error: Dependency conflict detected")
                        st.warning("""
                        **Prophet ต้องการ polars เวอร์ชันเก่า**

                        วิธีแก้:

                        **Option 1: แก้ dependency (แนะนำ)**
                        ```bash
                        pip uninstall -y polars cmdstanpy prophet
                        pip install "polars<0.20.0"
                        pip install "cmdstanpy>=1.2.0"
                        pip install "prophet>=1.1.5"
                        ```

                        **Option 2: ใช้ Model อื่นแทน (ง่ายกว่า)**
                        - เลือก **SARIMAX** หรือ **XGBoost** จาก dropdown ด้านบน
                        - Model เหล่านี้ใช้งานได้ปกติ ไม่ต้องแก้อะไร
                        """)
                    else:
                        st.error(f"❌ Error during forecasting: {e}")

                    with st.expander("📋 Full Error Details"):
                        import traceback
                        st.code(traceback.format_exc())

elif forecast_type == "Expense":
    st.header("💸 Expense Forecasting")

    # File upload
    uploaded_file = st.file_uploader(
        "Upload Expense Data (CSV or Excel)",
        type=['csv', 'xlsx', 'xls']
    )

    # Sample data option
    if uploaded_file is None:
        use_sample = st.checkbox("Use sample expense data for demo")

        if use_sample:
            # Create sample data
            import numpy as np
            dates = pd.date_range('2020-01-01', periods=36, freq='M')

            # Fixed costs (stable)
            salary = 500000 + np.random.normal(0, 5000, 36)

            # Variable costs (correlated with revenue)
            cogs = 300000 + np.random.normal(0, 30000, 36) + np.arange(36) * 5000

            df = pd.DataFrame({
                'month': dates,
                'expense': salary + cogs,
                'gl_code': np.random.choice(['5001', '5101', '5201'], 36),
                'category': np.random.choice(['Salary', 'COGS', 'Marketing'], 36)
            })

            st.success("✅ Using sample expense data")
        else:
            st.info("👆 Please upload expense data")
            df = None
    else:
        # Load file
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"✅ File uploaded! {len(df)} rows loaded.")

        except Exception as e:
            st.error(f"❌ Error: {e}")
            df = None

    if df is not None:
        # Configuration
        col1, col2, col3 = st.columns(3)

        with col1:
            date_col = st.selectbox("Date Column", df.columns)
        with col2:
            value_col = st.selectbox("Expense Column", df.columns)
        with col3:
            forecast_periods = st.number_input("Forecast Periods", 1, 36, 12)

        # Expense type classification
        expense_type = st.radio(
            "Expense Type",
            ["Fixed Cost", "Variable Cost", "By GL Code"],
            help="Select expense classification"
        )

        if st.button("🚀 Run Expense Forecast", type="primary"):
            with st.spinner("Generating forecast..."):
                try:
                    if expense_type == "Fixed Cost":
                        result = expense_engine.forecast_fixed_costs(
                            df=df,
                            date_column=date_col,
                            value_column=value_col,
                            forecast_periods=forecast_periods
                        )

                        st.success("✅ Fixed cost forecast completed!")

                    elif expense_type == "By GL Code":
                        if 'gl_code' in df.columns:
                            results = expense_engine.forecast_by_gl_code(
                                df=df,
                                date_column=date_col,
                                value_column=value_col,
                                forecast_periods=forecast_periods
                            )

                            st.success(f"✅ Forecast completed for {len(results)} GL codes!")

                            # Show summary
                            summary_df = expense_engine.get_expense_summary()
                            st.dataframe(summary_df)

                            result = list(results.values())[0]  # Show first for demo
                        else:
                            st.error("GL code column not found")
                            result = None
                    else:
                        st.info("Variable cost forecasting requires revenue data")
                        result = None

                    if result:
                        # Show forecast
                        fig = visualizer.plot_forecast_interactive(result)
                        st.plotly_chart(fig, use_container_width=True)

                        st.dataframe(result.forecast_df)

                except Exception as e:
                    error_msg = str(e)

                    # Check for Prophet/polars compatibility error
                    if "schema_overrides" in error_msg or "cmdstanpy" in error_msg:
                        st.error("❌ Prophet Model Error: Dependency conflict detected")
                        st.warning("""
                        **Prophet ต้องการ polars เวอร์ชันเก่า**

                        วิธีแก้:
                        ```bash
                        pip uninstall -y polars cmdstanpy prophet
                        pip install "polars<0.20.0"
                        pip install "cmdstanpy>=1.2.0"
                        pip install "prophet>=1.1.5"
                        ```
                        """)
                    else:
                        st.error(f"❌ Error: {e}")

                    with st.expander("📋 Full Error Details"):
                        import traceback
                        st.code(traceback.format_exc())

else:  # Model Comparison
    st.header("🔍 Model Comparison")

    st.info("Upload data to compare different forecasting models")

    uploaded_file = st.file_uploader("Upload Data", type=['csv', 'xlsx'])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)

        col1, col2 = st.columns(2)
        with col1:
            date_col = st.selectbox("Date Column", df.columns)
        with col2:
            value_col = st.selectbox("Value Column", df.columns)

        if st.button("Compare Models"):
            with st.spinner("Training multiple models..."):
                comparison_df = revenue_engine.compare_models(
                    df=df,
                    date_column=date_col,
                    value_column=value_col,
                    models=['prophet', 'sarimax', 'xgboost', 'holt_winters']
                )

                st.subheader("Model Performance Comparison")
                st.dataframe(comparison_df.style.highlight_min(subset=['mape', 'mae', 'rmse'], color='lightgreen'))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Forecast System v1.0 | Built with Streamlit | 📊 Easy-to-use Revenue & Expense Forecasting</p>
</div>
""", unsafe_allow_html=True)
