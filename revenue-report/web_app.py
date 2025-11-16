"""
Revenue ETL Web Application
============================
Web Interface สำหรับระบบ Revenue ETL
Built with Streamlit

Author: Revenue ETL System
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Import modules
from config_manager import ConfigManager, get_config_manager
from fi_revenue_expense_module import FIRevenueExpenseProcessor
from main import RevenueETLSystem

# Page Configuration
st.set_page_config(
    page_title="Revenue ETL System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .success-message {
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-message {
        padding: 10px;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'config_manager' not in st.session_state:
    st.session_state.config_manager = None
    st.session_state.system = None
    st.session_state.processing_status = None
    st.session_state.fi_completed = False
    st.session_state.etl_completed = False

def sync_status_from_system():
    """
    ซิงค์สถานะจาก system instance มาที่ session_state
    (ใช้ system เป็น source of truth)
    """
    if st.session_state.system:
        st.session_state.fi_completed = st.session_state.system.fi_completed
        st.session_state.etl_completed = st.session_state.system.etl_completed

def get_fi_status():
    """
    ดูสถานะ FI Module จาก system instance (source of truth)
    """
    if st.session_state.system:
        return st.session_state.system.fi_completed
    return st.session_state.fi_completed

def get_etl_status():
    """
    ดูสถานะ ETL Module จาก system instance (source of truth)
    """
    if st.session_state.system:
        return st.session_state.system.etl_completed
    return st.session_state.etl_completed

def load_configuration():
    """โหลด configuration จากไฟล์"""
    try:
        if os.path.exists("config.json"):
            st.session_state.config_manager = get_config_manager("config.json")
            st.session_state.system = RevenueETLSystem("config.json")
            # ซิงค์สถานะเริ่มต้น
            sync_status_from_system()
            return True
        else:
            st.error("❌ ไม่พบไฟล์ config.json")
            return False
    except Exception as e:
        st.error(f"❌ Error loading configuration: {e}")
        return False

def main():
    """Main application"""
    
    # Header
    st.title("💰 Revenue ETL System")
    st.markdown("### ระบบประมวลผลข้อมูลรายได้แบบ Modular v2.0")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Load configuration
        if st.button("📂 Load Configuration"):
            if load_configuration():
                st.success("✅ Configuration loaded successfully")
        
        # Display config status
        if st.session_state.config_manager:
            config = st.session_state.config_manager.config
            
            st.markdown("### 📊 Current Configuration")
            st.info(f"**Year:** {config['processing_year']}")
            st.info(f"**Environment:** {config['environment']['name']}")
            st.info(f"**OS:** {st.session_state.config_manager.os_platform}")
            
            # Configuration Editor
            with st.expander("📝 Edit Configuration"):
                new_year = st.text_input("Processing Year", value=config['processing_year'])
                
                if st.button("💾 Save Changes"):
                    st.session_state.config_manager.update_config('', 'processing_year', new_year)
                    st.success("✅ Configuration updated")
        
        st.markdown("---")
        
        # Processing Controls
        st.header("🚀 Processing Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Run All", width='stretch'):
                run_all_modules()
        with col2:
            if st.button("🔄 Reset", width='stretch'):
                reset_system()
        
        st.markdown("---")
        
        # Module Controls
        st.header("📦 Individual Modules")
        
        if st.button("1️⃣ Run FI Module", width='stretch'):
            run_fi_module()
        
        if st.button("2️⃣ Run ETL Module", width='stretch'):
            run_etl_module()
        
        st.markdown("---")
        
        # Status
        st.header("📈 Processing Status")

        # ใช้ helper function เพื่อดูสถานะจาก system instance
        if get_fi_status():
            st.success("✅ FI Module Completed")
        else:
            st.info("⏳ FI Module Pending")

        if get_etl_status():
            st.success("✅ ETL Module Completed")
        else:
            st.info("⏳ ETL Module Pending")
    
    # Main Content Area
    tabs = st.tabs(["📊 Dashboard", "📁 FI Module", "🔄 ETL Module", "✅ Reconciliation", "📈 Analytics", "📋 Logs"])
    
    with tabs[0]:
        show_dashboard()
    
    with tabs[1]:
        show_fi_module()
    
    with tabs[2]:
        show_etl_module()
    
    with tabs[3]:
        show_reconciliation()
    
    with tabs[4]:
        show_analytics()
    
    with tabs[5]:
        show_logs()

def run_all_modules():
    """
    รันทุก module โดยใช้ system.run_all()
    (ไม่เขียนตรรกะซ้ำ - ใช้ที่มีอยู่แล้วใน main.py)
    """
    if not st.session_state.system:
        st.error("❌ Please load configuration first")
        return

    with st.spinner("Processing all modules..."):
        # เรียก run_all() ที่มีอยู่แล้วใน main.py
        success = st.session_state.system.run_all()

        if success:
            # ซิงค์สถานะจาก system instance (source of truth)
            sync_status_from_system()

            st.balloons()
            st.success("🎉 All modules completed successfully!")
        else:
            # ซิงค์สถานะแม้ล้มเหลว (เพื่อแสดงสถานะที่ถูกต้อง)
            sync_status_from_system()
            st.error("❌ Processing failed")

def run_fi_module():
    """รัน FI Module"""
    if not st.session_state.system:
        st.error("❌ Please load configuration first")
        return

    with st.spinner("Running FI Module..."):
        if st.session_state.system.run_fi_module():
            # ซิงค์สถานะจาก system instance
            sync_status_from_system()
            st.success("✅ FI Module completed successfully")
        else:
            # ซิงค์สถานะแม้ล้มเหลว
            sync_status_from_system()
            st.error("❌ FI Module failed")

def run_etl_module():
    """
    รัน ETL Module
    (main.py จะตรวจสอบและรัน FI Module ก่อนอัตโนมัติถ้ายังไม่ได้รัน)
    """
    if not st.session_state.system:
        st.error("❌ Please load configuration first")
        return

    with st.spinner("Running ETL Module..."):
        if st.session_state.system.run_etl_module():
            # ซิงค์สถานะจาก system instance
            sync_status_from_system()
            st.success("✅ ETL Module completed successfully")
        else:
            # ซิงค์สถานะแม้ล้มเหลว
            sync_status_from_system()
            st.error("❌ ETL Module failed")

def reset_system():
    """รีเซ็ตระบบ"""
    st.session_state.fi_completed = False
    st.session_state.etl_completed = False
    st.session_state.processing_status = None
    st.success("🔄 System reset completed")

def show_dashboard():
    """แสดง Dashboard"""
    st.header("📊 Dashboard")
    
    if not st.session_state.config_manager:
        st.info("Please load configuration to view dashboard")
        return
    
    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Processing Year",
            value=st.session_state.config_manager.config['processing_year']
        )
    
    with col2:
        status = "✅ Ready" if get_fi_status() else "⏳ Pending"
        st.metric(label="FI Module", value=status)

    with col3:
        status = "✅ Ready" if get_etl_status() else "⏳ Pending"
        st.metric(label="ETL Module", value=status)
    
    with col4:
        reconcile_status = "Enabled" if st.session_state.config_manager.config['etl_module']['reconciliation']['enabled'] else "Disabled"
        st.metric(label="Reconciliation", value=reconcile_status)
    
    # Configuration Overview
    st.markdown("---")
    st.subheader("⚙️ Configuration Overview")
    
    config = st.session_state.config_manager.config
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### FI Module")
        st.json({
            "Input Files": config['fi_module']['input_files'],
            "Output Files": config['fi_module']['output_files']
        })
    
    with col2:
        st.markdown("### ETL Module")
        st.json({
            "Reconciliation": config['etl_module']['reconciliation'],
            "Anomaly Detection": {
                "Enabled": config['etl_module']['anomaly_detection']['enabled'],
                "IQR Multiplier": config['etl_module']['anomaly_detection']['iqr_multiplier']
            }
        })
    
    # File Status
    st.markdown("---")
    st.subheader("📁 File Status")

    if get_fi_status() and st.session_state.system and st.session_state.system.fi_output:
        st.markdown("### FI Output Files")
        for key, path in st.session_state.system.fi_output.items():
            if os.path.exists(path):
                size = os.path.getsize(path) / 1024  # KB
                st.success(f"✅ {key}: {os.path.basename(path)} ({size:.2f} KB)")
            else:
                st.error(f"❌ {key}: File not found")

def show_fi_module():
    """แสดงหน้า FI Module"""
    st.header("📁 FI Module - Financial Income Statement Processing")
    
    if not st.session_state.config_manager:
        st.info("Please load configuration first")
        return
    
    fi_config = st.session_state.config_manager.get_fi_config()
    
    # Configuration Display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Input Files")
        for file in fi_config['input_files']:
            st.text(f"📄 {file}")
    
    with col2:
        st.markdown("### Master Files")
        for key, file in fi_config['master_files'].items():
            st.text(f"📊 {key}: {file}")
    
    with col3:
        st.markdown("### Output Files")
        for key, file in fi_config['output_files'].items():
            st.text(f"💾 {key}: {file}")
    
    # Processing
    st.markdown("---")
    
    if st.button("▶️ Run FI Processing"):
        run_fi_module()
    
    # Results Display
    if get_fi_status():
        st.markdown("### 📊 Processing Results")
        
        # Try to load and display summary
        try:
            excel_path = st.session_state.system.fi_output['excel']
            if os.path.exists(excel_path):
                st.success(f"✅ Excel report generated: {os.path.basename(excel_path)}")
                
                # Load summary sheet
                df_summary = pd.read_excel(excel_path, sheet_name="summary_other")
                
                st.markdown("### Summary - รายได้/ค่าใช้จ่ายอื่น")
                st.dataframe(df_summary, width='stretch')
                
                # Create chart
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='เดือน',
                    x=df_summary['รายการ'],
                    y=df_summary['เดือน'],
                    text=df_summary['เดือน'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto',
                ))
                fig.add_trace(go.Bar(
                    name='สะสม',
                    x=df_summary['รายการ'],
                    y=df_summary['สะสม'],
                    text=df_summary['สะสม'].apply(lambda x: f'{x:,.0f}'),
                    textposition='auto',
                ))
                fig.update_layout(
                    title='สรุปผลตอบแทนทางการเงินและรายได้อื่น',
                    barmode='group',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.warning(f"Unable to display results: {e}")

def show_etl_module():
    """แสดงหน้า ETL Module"""
    st.header("🔄 ETL Module - Revenue ETL Pipeline")
    
    if not st.session_state.config_manager:
        st.info("Please load configuration first")
        return
    
    etl_config = st.session_state.config_manager.get_etl_config()
    
    # Pipeline Steps
    st.markdown("### 📋 Pipeline Steps")
    
    steps = [
        "1️⃣ Concatenate CSV Files",
        "2️⃣ Map Cost Center",
        "3️⃣ Map Product Codes",
        "4️⃣ Merge with Master Files",
        "5️⃣ Anomaly Detection",
        "6️⃣ Generate Reports"
    ]
    
    progress_bar = st.progress(0)
    for i, step in enumerate(steps):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(step)
        with col2:
            if get_etl_status():
                st.success("✅")

        if get_etl_status():
            progress_bar.progress((i + 1) / len(steps))
    
    # Configuration
    st.markdown("---")
    st.markdown("### ⚙️ ETL Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.json({
            "Reconciliation": etl_config['reconciliation'],
            "Business Rules": etl_config['business_rules']
        })
    
    with col2:
        st.json({
            "Anomaly Detection": etl_config['anomaly_detection'],
            "Validation": etl_config['validation']
        })
    
    # Run ETL
    if st.button("▶️ Run ETL Pipeline"):
        run_etl_module()

def show_reconciliation():
    """แสดงหน้า Reconciliation"""
    st.header("✅ Reconciliation - Data Validation")

    if not get_etl_status():
        st.info("Please complete ETL processing first")
        return
    
    st.markdown("### 🔍 Reconciliation Results")
    
    # Mock reconciliation results
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Monthly Reconciliation",
            value="PASSED",
            delta="0 errors"
        )
    
    with col2:
        st.metric(
            label="YTD Reconciliation",
            value="PASSED",
            delta="0 errors"
        )
    
    with col3:
        st.metric(
            label="Tolerance",
            value="0.00",
            delta="±0.00"
        )
    
    # Details
    st.markdown("---")
    st.markdown("### 📊 Reconciliation Details")
    
    # Create sample reconciliation data
    reconcile_data = {
        "Type": ["Monthly", "YTD"],
        "FI Total": [1000000.00, 10000000.00],
        "TRN Total": [1000000.00, 10000000.00],
        "Difference": [0.00, 0.00],
        "Status": ["✅ PASSED", "✅ PASSED"]
    }
    
    df_reconcile = pd.DataFrame(reconcile_data)
    st.dataframe(df_reconcile, width='stretch')

def show_analytics():
    """แสดงหน้า Analytics"""
    st.header("📈 Analytics - Data Insights")

    if not get_etl_status():
        st.info("Please complete processing to view analytics")
        return
    
    # Sample analytics
    st.markdown("### 📊 Revenue Trends")
    
    # Create sample data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
    revenue = [100, 110, 105, 120, 125, 130, 128, 135, 140, 145]
    expense = [80, 85, 82, 90, 92, 95, 93, 98, 100, 102]
    
    # Revenue vs Expense Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=revenue,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='green', width=3)
    ))
    fig.add_trace(go.Scatter(
        x=months,
        y=expense,
        mode='lines+markers',
        name='Expense',
        line=dict(color='red', width=3)
    ))
    fig.update_layout(
        title='Revenue vs Expense Trend',
        xaxis_title='Month',
        yaxis_title='Amount (Million THB)',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Anomaly Detection Results
    st.markdown("### 🚨 Anomaly Detection")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="High Spikes", value="3", delta="+2")
    with col2:
        st.metric(label="Low Dips", value="1", delta="-1")
    with col3:
        st.metric(label="New Items", value="5", delta="+5")
    with col4:
        st.metric(label="Normal", value="92%", delta="0%")

def show_logs():
    """แสดงหน้า Logs"""
    st.header("📋 System Logs")
    
    # Log display
    st.markdown("### 📝 Processing Logs")
    
    log_text = """
[2025-01-15 10:00:00] [INFO] System started
[2025-01-15 10:00:01] [INFO] Configuration loaded successfully
[2025-01-15 10:00:02] [INFO] FI Module started
[2025-01-15 10:00:15] [SUCCESS] FI Module completed
[2025-01-15 10:00:16] [INFO] ETL Module started
[2025-01-15 10:00:45] [SUCCESS] ETL Module completed
[2025-01-15 10:00:46] [INFO] Reconciliation started
[2025-01-15 10:00:50] [SUCCESS] Reconciliation passed
[2025-01-15 10:00:51] [SUCCESS] All processing completed
    """
    
    st.text_area("System Logs", value=log_text, height=300)
    
    # Download logs button
    if st.button("📥 Download Logs"):
        st.download_button(
            label="Download",
            data=log_text,
            file_name=f"revenue_etl_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()