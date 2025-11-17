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
from logger_utils import ETLLogger
import glob

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

def check_file_exists(file_path: str) -> dict:
    """
    ตรวจสอบว่าไฟล์มีอยู่จริงและคืนข้อมูล

    Returns:
        dict: {'exists': bool, 'size_kb': float, 'path': str}
    """
    if os.path.exists(file_path):
        size_kb = os.path.getsize(file_path) / 1024
        return {'exists': True, 'size_kb': size_kb, 'path': file_path}
    return {'exists': False, 'size_kb': 0, 'path': file_path}

def get_latest_log_content(log_dir: str = "logs", max_lines: int = 100) -> str:
    """
    อ่าน log files ล่าสุด

    Args:
        log_dir: โฟลเดอร์ log
        max_lines: จำนวนบรรทัดสูงสุด

    Returns:
        str: เนื้อหา log
    """
    try:
        log_files = glob.glob(f"{log_dir}/*.log")
        if not log_files:
            return "No log files found"

        # หาไฟล์ล่าสุด
        latest_log = max(log_files, key=os.path.getmtime)

        with open(latest_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # คืน n บรรทัดสุดท้าย
            return ''.join(lines[-max_lines:])
    except Exception as e:
        return f"Error reading logs: {e}"

def get_reconciliation_results(log_dir: str = "logs") -> dict:
    """
    อ่านผล reconciliation จาก log files

    Returns:
        dict: ผล reconciliation
    """
    try:
        # หา reconciliation log files
        reconcile_logs = glob.glob(f"{log_dir}/reconcile_*.log")
        if not reconcile_logs:
            return None

        latest_log = max(reconcile_logs, key=os.path.getmtime)

        result = {
            'monthly_passed': False,
            'ytd_passed': False,
            'monthly_diff': 0.0,
            'ytd_diff': 0.0,
            'fi_total_monthly': 0.0,
            'trn_total_monthly': 0.0,
            'fi_total_ytd': 0.0,
            'trn_total_ytd': 0.0,
            'log_file': os.path.basename(latest_log)
        }

        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()

            # Parse log content (simple parsing)
            if 'Monthly Reconciliation: PASSED' in content:
                result['monthly_passed'] = True
            if 'YTD Reconciliation: PASSED' in content:
                result['ytd_passed'] = True

            # ค้นหาตัวเลข (simplified - อาจต้อง regex ที่ดีกว่า)
            lines = content.split('\n')
            for line in lines:
                if 'FI Total (Monthly)' in line:
                    try:
                        result['fi_total_monthly'] = float(line.split(':')[-1].strip().replace(',', ''))
                    except:
                        pass
                elif 'TRN Total (Monthly)' in line:
                    try:
                        result['trn_total_monthly'] = float(line.split(':')[-1].strip().replace(',', ''))
                    except:
                        pass
                elif 'FI Total (YTD)' in line:
                    try:
                        result['fi_total_ytd'] = float(line.split(':')[-1].strip().replace(',', ''))
                    except:
                        pass
                elif 'TRN Total (YTD)' in line:
                    try:
                        result['trn_total_ytd'] = float(line.split(':')[-1].strip().replace(',', ''))
                    except:
                        pass

        result['monthly_diff'] = result['fi_total_monthly'] - result['trn_total_monthly']
        result['ytd_diff'] = result['fi_total_ytd'] - result['trn_total_ytd']

        return result
    except Exception as e:
        st.warning(f"Unable to read reconciliation results: {e}")
        return None

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

                # Processing Months
                st.markdown("**Processing Months**")
                fi_month = st.number_input(
                    "FI Current Month",
                    min_value=1,
                    max_value=12,
                    value=config['processing_months']['fi_current_month']
                )
                etl_month = st.number_input(
                    "ETL End Month",
                    min_value=1,
                    max_value=12,
                    value=config['processing_months']['etl_end_month']
                )

                # Reconciliation Settings
                st.markdown("**Reconciliation**")
                reconcile_enabled = st.checkbox(
                    "Enable Reconciliation",
                    value=config['etl_module']['reconciliation']['enabled']
                )
                reconcile_tolerance = st.number_input(
                    "Tolerance",
                    min_value=0.0,
                    max_value=100.0,
                    value=config['etl_module']['reconciliation']['tolerance'],
                    format="%.2f"
                )

                # Anomaly Detection Settings
                st.markdown("**Anomaly Detection**")
                anomaly_enabled = st.checkbox(
                    "Enable Anomaly Detection",
                    value=config['etl_module']['anomaly_detection']['enabled']
                )
                iqr_multiplier = st.number_input(
                    "IQR Multiplier",
                    min_value=1.0,
                    max_value=3.0,
                    value=config['etl_module']['anomaly_detection']['iqr_multiplier'],
                    step=0.1,
                    format="%.1f"
                )

                if st.button("💾 Save All Changes"):
                    # Update year (root level)
                    st.session_state.config_manager.config['processing_year'] = new_year

                    # Update months
                    st.session_state.config_manager.set_processing_month(fi_month, update_etl=False)
                    if etl_month != fi_month:
                        st.session_state.config_manager.config['processing_months']['etl_end_month'] = etl_month

                    # Update reconciliation
                    st.session_state.config_manager.config['etl_module']['reconciliation']['enabled'] = reconcile_enabled
                    st.session_state.config_manager.config['etl_module']['reconciliation']['tolerance'] = reconcile_tolerance

                    # Update anomaly detection
                    st.session_state.config_manager.config['etl_module']['anomaly_detection']['enabled'] = anomaly_enabled
                    st.session_state.config_manager.config['etl_module']['anomaly_detection']['iqr_multiplier'] = iqr_multiplier

                    # Reload paths (เพราะ year อาจเปลี่ยน)
                    st.session_state.config_manager._setup_paths()

                    # Reload config in system
                    if st.session_state.system:
                        st.session_state.system.fi_config = st.session_state.config_manager.get_fi_config()
                        st.session_state.system.etl_config = st.session_state.config_manager.get_etl_config()

                    st.success("✅ Configuration updated successfully")
                    st.info("💡 Note: Changes are temporary and will be lost on restart unless saved to file")
        
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

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: FI Module
        status_text.text("⏳ Running FI Module...")
        progress_bar.progress(10)

        if not st.session_state.system.run_fi_module():
            sync_status_from_system()
            status_text.text("❌ FI Module failed")
            st.error("❌ FI Module processing failed")
            return

        sync_status_from_system()
        progress_bar.progress(50)
        status_text.text("✅ FI Module completed")

        # Step 2: ETL Module
        status_text.text("⏳ Running ETL Module...")
        progress_bar.progress(60)

        if not st.session_state.system.run_etl_module():
            sync_status_from_system()
            status_text.text("❌ ETL Module failed")
            st.error("❌ ETL Module processing failed")
            return

        sync_status_from_system()
        progress_bar.progress(100)
        status_text.text("✅ All modules completed!")

        st.balloons()
        st.success("🎉 All modules completed successfully!")

    except Exception as e:
        sync_status_from_system()
        status_text.text(f"❌ Error: {str(e)}")
        st.error(f"❌ Processing failed: {e}")
    finally:
        progress_bar.empty()
        status_text.empty()

def run_fi_module():
    """รัน FI Module"""
    if not st.session_state.system:
        st.error("❌ Please load configuration first")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("⏳ Initializing FI Module...")
        progress_bar.progress(20)

        status_text.text("⏳ Processing FI data...")
        progress_bar.progress(40)

        if st.session_state.system.run_fi_module():
            sync_status_from_system()
            progress_bar.progress(100)
            status_text.text("✅ FI Module completed!")
            st.success("✅ FI Module completed successfully")
        else:
            sync_status_from_system()
            status_text.text("❌ FI Module failed")
            st.error("❌ FI Module failed")

    except Exception as e:
        sync_status_from_system()
        status_text.text(f"❌ Error: {str(e)}")
        st.error(f"❌ FI Module failed: {e}")
    finally:
        progress_bar.empty()
        status_text.empty()

def run_etl_module():
    """
    รัน ETL Module
    (main.py จะตรวจสอบและรัน FI Module ก่อนอัตโนมัติถ้ายังไม่ได้รัน)
    """
    if not st.session_state.system:
        st.error("❌ Please load configuration first")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Check if FI module needs to run first
        if not get_fi_status():
            status_text.text("⏳ FI Module not completed. Running FI Module first...")
            progress_bar.progress(10)

        status_text.text("⏳ Initializing ETL Module...")
        progress_bar.progress(20)

        status_text.text("⏳ Processing revenue data...")
        progress_bar.progress(40)

        status_text.text("⏳ Running reconciliation...")
        progress_bar.progress(60)

        status_text.text("⏳ Detecting anomalies...")
        progress_bar.progress(80)

        status_text.text("⏳ Generating reports...")
        progress_bar.progress(90)

        if st.session_state.system.run_etl_module():
            sync_status_from_system()
            progress_bar.progress(100)
            status_text.text("✅ ETL Module completed!")
            st.success("✅ ETL Module completed successfully")
        else:
            sync_status_from_system()
            status_text.text("❌ ETL Module failed")
            st.error("❌ ETL Module failed")

    except Exception as e:
        sync_status_from_system()
        status_text.text(f"❌ Error: {str(e)}")
        st.error(f"❌ ETL Module failed: {e}")
    finally:
        progress_bar.empty()
        status_text.empty()

def reset_system():
    """รีเซ็ตระบบ"""
    # รีเซ็ต session state
    st.session_state.fi_completed = False
    st.session_state.etl_completed = False
    st.session_state.processing_status = None

    # รีเซ็ต system instance ถ้ามี
    if st.session_state.system:
        st.session_state.system.fi_completed = False
        st.session_state.system.etl_completed = False
        st.session_state.system.fi_output = None
        st.session_state.system.etl_final_df = None
        st.session_state.system.etl_anomaly_results = None

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
        year = st.session_state.config_manager.config['processing_year']
        fi_month = st.session_state.config_manager.config['processing_months']['fi_current_month']
        st.metric(
            label="Processing Year/Month",
            value=f"{year}-{fi_month:02d}"
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

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Master Files")
        # Check FI master files
        fi_config = st.session_state.config_manager.get_fi_config()
        master_path = fi_config['paths']['master']
        master_source = fi_config['paths']['master_source']  # master_path/source

        for key, filename in st.session_state.config_manager.config['fi_module']['master_files'].items():
            # Handle files with 'source/' prefix
            # ถ้ามี '/' ในชื่อไฟล์ แสดงว่าเป็น relative path จาก master_path
            # ถ้าไม่มี '/' แสดงว่าอยู่ใน master_source (master_path/source/)
            if '/' in filename:
                full_path = os.path.join(master_path, filename)
            else:
                full_path = os.path.join(master_source, filename)

            file_info = check_file_exists(full_path)
            if file_info['exists']:
                st.success(f"✅ {key}: {os.path.basename(filename)} ({file_info['size_kb']:.1f} KB)")
            else:
                st.error(f"❌ {key}: {os.path.basename(filename)} (Not found)")
                st.caption(f"Expected path: {full_path}")

    with col2:
        if get_fi_status() and st.session_state.system and st.session_state.system.fi_output:
            st.markdown("### FI Output Files")
            for key, path in st.session_state.system.fi_output.items():
                file_info = check_file_exists(path)
                if file_info['exists']:
                    st.success(f"✅ {key}: {os.path.basename(path)} ({file_info['size_kb']:.1f} KB)")
                else:
                    st.error(f"❌ {key}: File not found")

    # ETL Output Files
    if get_etl_status() and st.session_state.system:
        st.markdown("---")
        st.markdown("### ETL Output Files")

        etl_config = st.session_state.config_manager.get_etl_config()
        output_path = etl_config['paths']['output']
        final_output_path = etl_config['paths']['final_output']

        output_files = etl_config['output_files']

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Intermediate Files**")
            for key in ['concat', 'mapped_cc', 'mapped_product']:
                if key in output_files:
                    file_path = os.path.join(output_path, output_files[key])
                    file_info = check_file_exists(file_path)
                    if file_info['exists']:
                        st.success(f"✅ {key}")
                        st.caption(f"{file_info['size_kb']:.1f} KB")
                    else:
                        st.warning(f"⚠️ {key}")

        with col2:
            st.markdown("**Final Report**")
            final_file = os.path.join(final_output_path, output_files['final_report'])
            file_info = check_file_exists(final_file)
            if file_info['exists']:
                st.success(f"✅ Final Report")
                st.caption(f"{file_info['size_kb']:.1f} KB")
            else:
                st.warning(f"⚠️ Final Report")

        with col3:
            st.markdown("**Error Files**")
            for key in ['error_gl', 'error_product']:
                if key in output_files:
                    file_path = os.path.join(final_output_path, output_files[key])
                    file_info = check_file_exists(file_path)
                    if file_info['exists']:
                        if file_info['size_kb'] > 1:  # มี errors
                            st.error(f"⚠️ {key}")
                            st.caption(f"{file_info['size_kb']:.1f} KB")
                        else:
                            st.success(f"✅ {key} (empty)")
                    else:
                        st.info(f"ℹ️ {key}")

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

                # Format numbers with comma separator
                df_display = df_summary.copy()
                for col in df_display.columns:
                    if col != 'รายการ' and df_display[col].dtype in ['int64', 'float64']:
                        df_display[col] = df_display[col].apply(lambda x: f'{x:,.2f}' if pd.notna(x) else '')

                st.dataframe(df_display, use_container_width=True)
                
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

    # Business Rules
    with st.expander("📋 Business Rules", expanded=False):
        rules = etl_config['business_rules']
        st.markdown("""
        **Revenue Classification Rules:**
        """)
        st.info(f"**Exclude Business Group:** {rules['exclude_business_group']}")
        st.info(f"**Non-Telecom Service Group:** {rules['non_telecom_service_group']}")
        st.info(f"**New Adjustment Business Group:** {rules['new_adj_business_group']}")
        st.info(f"**Financial Income Name:** {rules['financial_income_name']}")
        st.info(f"**Other Revenue Adj Name:** {rules['other_revenue_adj_name']}")

    # Special Mappings
    with st.expander("🔄 Special Mappings", expanded=False):
        if 'special_mappings' in etl_config and etl_config['special_mappings']:
            for idx, mapping in enumerate(etl_config['special_mappings'], 1):
                st.markdown(f"**Mapping {idx}: {mapping['name']}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*Condition:*")
                    st.json(mapping['condition'])
                with col2:
                    st.markdown("*Maps to:*")
                    st.json(mapping['mapping'])
                st.markdown("---")
        else:
            st.info("No special mappings configured")

    # Reconciliation & Validation
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("✅ Reconciliation Settings"):
            st.json(etl_config['reconciliation'])

        with st.expander("🔍 Validation Rules"):
            validation = etl_config['validation']
            st.markdown(f"**Grand Total Diff Threshold:** {validation['grand_total_diff_threshold']}")
            st.markdown("**Required Columns:**")
            for col in validation['required_columns']:
                st.text(f"• {col}")

    with col2:
        with st.expander("🚨 Anomaly Detection Settings"):
            anomaly_cfg = etl_config['anomaly_detection']
            st.markdown(f"**Enabled:** {anomaly_cfg['enabled']}")
            st.markdown(f"**IQR Multiplier:** {anomaly_cfg['iqr_multiplier']}")
            st.markdown(f"**Min History:** {anomaly_cfg['min_history']}")
            st.markdown(f"**Rolling Window:** {anomaly_cfg['rolling_window']}")
            st.markdown(f"**Historical Highlight:** {anomaly_cfg['enable_historical_highlight']}")

            st.markdown("**Detection Levels:**")
            for level, config in anomaly_cfg['levels'].items():
                with st.container():
                    st.markdown(f"*{level.replace('_', ' ').title()}*")
                    if config['group_by']:
                        st.caption(f"Group by: {', '.join(config['group_by'])}")
                    else:
                        st.caption("Group by: Grand Total")
    
    # Run ETL
    if st.button("▶️ Run ETL Pipeline"):
        run_etl_module()

def show_reconciliation():
    """แสดงหน้า Reconciliation"""
    st.header("✅ Reconciliation - Data Validation")

    if not get_etl_status():
        st.info("Please complete ETL processing first")
        return

    # อ่านผลจาก log files
    reconcile_result = get_reconciliation_results()

    if not reconcile_result:
        st.warning("⚠️ No reconciliation results found. Reconciliation may be disabled or logs not available.")

        # แสดง config
        config = st.session_state.config_manager.config
        st.info(f"Reconciliation Enabled: {config['etl_module']['reconciliation']['enabled']}")
        st.info(f"Tolerance: {config['etl_module']['reconciliation']['tolerance']}")
        return

    st.markdown("### 🔍 Reconciliation Results")

    # แสดง FI Month ที่ใช้
    config = st.session_state.config_manager.config
    fi_month = config['processing_months']['fi_current_month']
    st.info(f"📅 Reconciliation Month: {fi_month:02d} (FI Current Month)")

    # Summary Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        monthly_status = "PASSED ✅" if reconcile_result['monthly_passed'] else "FAILED ❌"
        st.metric(
            label="Monthly Reconciliation",
            value=monthly_status,
            delta=f"{reconcile_result['monthly_diff']:,.2f}"
        )

    with col2:
        ytd_status = "PASSED ✅" if reconcile_result['ytd_passed'] else "FAILED ❌"
        st.metric(
            label="YTD Reconciliation",
            value=ytd_status,
            delta=f"{reconcile_result['ytd_diff']:,.2f}"
        )

    with col3:
        tolerance = config['etl_module']['reconciliation']['tolerance']
        st.metric(
            label="Tolerance",
            value=f"±{tolerance:.2f}",
            delta=f"Log: {reconcile_result['log_file']}"
        )

    # Details
    st.markdown("---")
    st.markdown("### 📊 Reconciliation Details")

    # Create reconciliation data
    reconcile_data = {
        "Type": ["Monthly", "YTD"],
        "FI Total": [
            reconcile_result['fi_total_monthly'],
            reconcile_result['fi_total_ytd']
        ],
        "TRN Total": [
            reconcile_result['trn_total_monthly'],
            reconcile_result['trn_total_ytd']
        ],
        "Difference": [
            reconcile_result['monthly_diff'],
            reconcile_result['ytd_diff']
        ],
        "Status": [
            "✅ PASSED" if reconcile_result['monthly_passed'] else "❌ FAILED",
            "✅ PASSED" if reconcile_result['ytd_passed'] else "❌ FAILED"
        ]
    }

    df_reconcile = pd.DataFrame(reconcile_data)

    # Format numbers
    df_reconcile['FI Total'] = df_reconcile['FI Total'].apply(lambda x: f"{x:,.2f}")
    df_reconcile['TRN Total'] = df_reconcile['TRN Total'].apply(lambda x: f"{x:,.2f}")
    df_reconcile['Difference'] = df_reconcile['Difference'].apply(lambda x: f"{x:,.2f}")

    st.dataframe(df_reconcile, use_container_width=True)

    # Validation Results
    st.markdown("---")
    st.markdown("### 🔍 Validation Results")

    if st.session_state.system and st.session_state.system.etl_final_df is not None:
        df = st.session_state.system.etl_final_df

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Records", f"{len(df):,}")

        with col2:
            # Count unique products
            if 'PRODUCT_KEY' in df.columns:
                st.metric("Unique Products", f"{df['PRODUCT_KEY'].nunique():,}")

        with col3:
            # Total Revenue
            if 'REVENUE_VALUE' in df.columns:
                total_revenue = df['REVENUE_VALUE'].sum()
                st.metric("Total Revenue", f"{total_revenue:,.2f}")

        # Required columns check
        validation_config = config['etl_module']['validation']
        required_cols = validation_config['required_columns']

        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        else:
            st.success(f"✅ All required columns present ({len(required_cols)} columns)")
    else:
        st.info("ETL data not available in session")

def show_analytics():
    """แสดงหน้า Analytics"""
    st.header("📈 Analytics - Data Insights")

    if not get_etl_status():
        st.info("Please complete processing to view analytics")
        return

    # Anomaly Detection Results
    st.markdown("### 🚨 Anomaly Detection Results")

    if st.session_state.system and st.session_state.system.etl_anomaly_results:
        anomaly_results = st.session_state.system.etl_anomaly_results

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        total_anomalies = 0
        high_spikes = 0
        low_dips = 0
        new_items = 0

        # Count anomalies from all levels
        for level_name, level_data in anomaly_results.items():
            if 'summary' in level_data:
                total_anomalies += level_data['summary'].get('total_anomalies', 0)
                high_spikes += level_data['summary'].get('high_spikes', 0)
                low_dips += level_data['summary'].get('low_dips', 0)
                new_items += level_data['summary'].get('new_items', 0)

        with col1:
            st.metric("Total Anomalies", f"{total_anomalies:,}")
        with col2:
            st.metric("High Spikes ↗️", f"{high_spikes:,}")
        with col3:
            st.metric("Low Dips ↘️", f"{low_dips:,}")
        with col4:
            st.metric("New Items 🆕", f"{new_items:,}")

        # แสดงรายละเอียดแต่ละ level
        st.markdown("---")

        for level_name, level_data in anomaly_results.items():
            with st.expander(f"📊 {level_name.replace('_', ' ').title()} Level", expanded=False):
                if 'dataframe' in level_data and level_data['dataframe'] is not None:
                    df = level_data['dataframe']

                    # Filter เฉพาะแถวที่มี anomaly
                    if 'ANOMALY_FLAG' in df.columns:
                        anomalies_df = df[df['ANOMALY_FLAG'].notna() & (df['ANOMALY_FLAG'] != '')]

                        if len(anomalies_df) > 0:
                            st.warning(f"Found {len(anomalies_df)} anomalies")

                            # แสดงตาราง
                            display_cols = [col for col in df.columns if col in [
                                'BUSINESS_GROUP', 'SERVICE_GROUP', 'PRODUCT_KEY', 'PRODUCT_NAME',
                                'MONTH', 'REVENUE_VALUE', 'ANOMALY_FLAG', 'ANOMALY_TYPE'
                            ]]

                            if display_cols:
                                st.dataframe(
                                    anomalies_df[display_cols].head(20),
                                    use_container_width=True
                                )
                        else:
                            st.success("No anomalies detected")
                    else:
                        st.info("Anomaly detection not performed for this level")

                if 'summary' in level_data:
                    st.json(level_data['summary'])

    else:
        st.info("Anomaly detection results not available. Make sure anomaly detection is enabled in configuration.")

    # Revenue Trends (from actual data)
    st.markdown("---")
    st.markdown("### 📊 Revenue Trends")

    if st.session_state.system and st.session_state.system.etl_final_df is not None:
        df = st.session_state.system.etl_final_df

        # Check if we have required columns
        if 'MONTH' in df.columns and 'REVENUE_VALUE' in df.columns:
            # Aggregate by month
            monthly_revenue = df.groupby('MONTH')['REVENUE_VALUE'].sum().reset_index()
            monthly_revenue = monthly_revenue.sort_values('MONTH')

            # Create line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_revenue['MONTH'],
                y=monthly_revenue['REVENUE_VALUE'],
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#00CC96', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title='Monthly Revenue Trend',
                xaxis_title='Month',
                yaxis_title='Revenue (THB)',
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Revenue by Business Group (if available)
            if 'BUSINESS_GROUP' in df.columns:
                st.markdown("### 📊 Revenue by Business Group")

                business_revenue = df.groupby('BUSINESS_GROUP')['REVENUE_VALUE'].sum().reset_index()
                business_revenue = business_revenue.sort_values('REVENUE_VALUE', ascending=False)

                fig = go.Figure(data=[go.Bar(
                    x=business_revenue['BUSINESS_GROUP'],
                    y=business_revenue['REVENUE_VALUE'],
                    marker_color='#636EFA'
                )])
                fig.update_layout(
                    title='Revenue by Business Group',
                    xaxis_title='Business Group',
                    yaxis_title='Revenue (THB)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("Required columns (MONTH, REVENUE_VALUE) not found in data")

        # Data Summary
        st.markdown("---")
        st.markdown("### 📋 Data Summary")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Dataset Overview**")
            st.info(f"Total Records: {len(df):,}")
            st.info(f"Columns: {len(df.columns)}")
            st.info(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

        with col2:
            st.markdown("**Revenue Statistics**")
            if 'REVENUE_VALUE' in df.columns:
                st.info(f"Total Revenue: {df['REVENUE_VALUE'].sum():,.2f}")
                st.info(f"Average Revenue: {df['REVENUE_VALUE'].mean():,.2f}")
                st.info(f"Max Revenue: {df['REVENUE_VALUE'].max():,.2f}")

    else:
        st.info("ETL data not available. Please run ETL processing first.")

def show_logs():
    """แสดงหน้า Logs"""
    st.header("📋 System Logs")

    # Check if config_manager is available
    if not st.session_state.config_manager:
        st.info("Please load configuration first")
        return

    # Log directory
    log_dir = st.session_state.config_manager.config['logging'].get('log_directory', 'logs')

    # Get log files
    log_files = glob.glob(f"{log_dir}/*.log")

    if not log_files:
        st.warning(f"No log files found in {log_dir}/")
        return

    # Sort by modification time (newest first)
    log_files.sort(key=os.path.getmtime, reverse=True)

    # Log file selector
    selected_log = st.selectbox(
        "Select Log File",
        options=[os.path.basename(f) for f in log_files],
        index=0
    )

    if selected_log:
        log_path = os.path.join(log_dir, selected_log)

        # Display options
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### 📝 {selected_log}")

        with col2:
            # File info
            file_size = os.path.getsize(log_path) / 1024  # KB
            st.caption(f"Size: {file_size:.1f} KB")
            st.caption(f"Modified: {datetime.fromtimestamp(os.path.getmtime(log_path)).strftime('%Y-%m-%d %H:%M:%S')}")

        # Read log file
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()

            # Display options
            col1, col2, col3 = st.columns(3)

            with col1:
                max_lines = st.number_input("Max Lines to Display", min_value=10, max_value=10000, value=500, step=10)

            with col2:
                filter_level = st.selectbox("Filter by Level", ["All", "ERROR", "WARNING", "INFO", "SUCCESS", "DEBUG"])

            with col3:
                search_text = st.text_input("Search in Logs", "")

            # Process log content
            lines = log_content.split('\n')

            # Apply filter
            if filter_level != "All":
                lines = [line for line in lines if f"[{filter_level}]" in line]

            # Apply search
            if search_text:
                lines = [line for line in lines if search_text.lower() in line.lower()]

            # Limit lines
            display_lines = lines[-max_lines:] if len(lines) > max_lines else lines

            # Display
            st.text_area(
                "Log Content",
                value='\n'.join(display_lines),
                height=400,
                help=f"Showing {len(display_lines)} of {len(lines)} lines"
            )

            # Statistics
            st.markdown("---")
            st.markdown("### 📊 Log Statistics")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                error_count = sum(1 for line in lines if '[ERROR]' in line)
                st.metric("Errors", error_count)

            with col2:
                warning_count = sum(1 for line in lines if '[WARNING]' in line)
                st.metric("Warnings", warning_count)

            with col3:
                info_count = sum(1 for line in lines if '[INFO]' in line)
                st.metric("Info", info_count)

            with col4:
                success_count = sum(1 for line in lines if '[SUCCESS]' in line or '✓' in line)
                st.metric("Success", success_count)

            with col5:
                st.metric("Total Lines", len(lines))

            # Download button
            st.download_button(
                label="📥 Download Full Log",
                data=log_content,
                file_name=selected_log,
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Error reading log file: {e}")

    # Error Files Section
    st.markdown("---")
    st.markdown("### ⚠️ Error Files")

    if get_etl_status():
        etl_config = st.session_state.config_manager.get_etl_config()
        final_output_path = etl_config['paths']['final_output']
        output_files = etl_config['output_files']

        error_files = {}
        for key in ['error_gl', 'error_product']:
            if key in output_files:
                file_path = os.path.join(final_output_path, output_files[key])
                if os.path.exists(file_path):
                    error_files[key] = file_path

        if error_files:
            for error_type, error_path in error_files.items():
                with st.expander(f"📄 {error_type.replace('_', ' ').title()}", expanded=False):
                    try:
                        df_error = pd.read_csv(error_path)

                        if len(df_error) > 0:
                            st.warning(f"Found {len(df_error)} error records")
                            st.dataframe(df_error.head(100), use_container_width=True)

                            # Download button
                            st.download_button(
                                label=f"📥 Download {error_type}",
                                data=df_error.to_csv(index=False),
                                file_name=os.path.basename(error_path),
                                mime="text/csv"
                            )
                        else:
                            st.success("No errors found")

                    except Exception as e:
                        st.error(f"Error reading {error_type}: {e}")
        else:
            st.info("No error files found. Run ETL processing first.")
    else:
        st.info("Complete ETL processing to view error files")

if __name__ == "__main__":
    main()