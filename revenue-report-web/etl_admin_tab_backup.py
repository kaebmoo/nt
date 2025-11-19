"""
ETL Admin Tab Module
====================
Web Interface สำหรับ ETL System (Admin Only)
Refactored from revenue-report/web_app.py

This module provides ETL admin interface integrated into the main web app.
All session states use 'etl_' prefix to avoid collision.

Author: Revenue Report Web Integration
Version: 1.0.0
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import glob

# Import ETL modules from integration layer
from etl_integration import (
    ETLConfigManager,
    RevenueETLSystem,
    FIRevenueExpenseProcessor,
    ETLLogger,
    create_etl_config_manager,
    create_etl_system,
    validate_etl_environment,
    get_etl_config_path
)


# ========== Session State Management ==========
def init_etl_session_state():
    """Initialize ETL-specific session state with etl_ prefix"""
    if 'etl_config_manager' not in st.session_state:
        st.session_state.etl_config_manager = None
    if 'etl_system' not in st.session_state:
        st.session_state.etl_system = None
    if 'etl_processing_status' not in st.session_state:
        st.session_state.etl_processing_status = None
    if 'etl_fi_completed' not in st.session_state:
        st.session_state.etl_fi_completed = False
    if 'etl_etl_completed' not in st.session_state:
        st.session_state.etl_etl_completed = False


def sync_status_from_system():
    """
    ซิงค์สถานะจาก system instance มาที่ session_state
    (ใช้ system เป็น source of truth)
    """
    if st.session_state.etl_system:
        st.session_state.etl_fi_completed = st.session_state.etl_system.fi_completed
        st.session_state.etl_etl_completed = st.session_state.etl_system.etl_completed


def get_fi_status():
    """
    ดูสถานะ FI Module จาก system instance (source of truth)
    """
    if st.session_state.etl_system:
        return st.session_state.etl_system.fi_completed
    return st.session_state.etl_fi_completed


def get_etl_status():
    """
    ดูสถานะ ETL Module จาก system instance (source of truth)
    """
    if st.session_state.etl_system:
        return st.session_state.etl_system.etl_completed
    return st.session_state.etl_etl_completed


# ========== Helper Functions ==========
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


def get_reconciliation_results(config_manager) -> dict:
    """
    อ่านผล reconciliation จาก summary files ใน reconcile_logs

    Args:
        config_manager: ConfigManager instance

    Returns:
        dict: ผล reconciliation หรือ None ถ้าไม่พบ
    """
    try:
        # หา reconcile_logs path จาก ETL config
        etl_config = config_manager.get_etl_config()
        reconcile_logs_dir = os.path.join(etl_config['paths']['output'], 'reconcile_logs')

        # หาไฟล์ summary ล่าสุด (.txt ไม่ใช่ .log)
        reconcile_logs = glob.glob(f"{reconcile_logs_dir}/reconcile_summary_*.txt")
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
            'log_file': os.path.basename(latest_log),
            'log_path': latest_log
        }

        with open(latest_log, 'r', encoding='utf-8') as f:
            content = f.read()

            # Parse ตามรูปแบบของ reconciliation log
            lines = content.split('\n')

            in_monthly_section = False
            in_ytd_section = False

            for line in lines:
                # Detect sections
                if 'RECONCILE รายเดือน' in line or 'MONTHLY' in line:
                    in_monthly_section = True
                    in_ytd_section = False
                elif 'RECONCILE ยอดสะสม' in line or 'YTD' in line:
                    in_monthly_section = False
                    in_ytd_section = True
                elif 'OVERALL STATUS' in line:
                    in_monthly_section = False
                    in_ytd_section = False

                # Parse values based on section
                if 'Status:' in line:
                    if 'PASSED' in line:
                        if in_monthly_section:
                            result['monthly_passed'] = True
                        elif in_ytd_section:
                            result['ytd_passed'] = True

                if 'FI Total:' in line:
                    try:
                        value = line.split('FI Total:')[-1].strip().replace(',', '')
                        if in_monthly_section:
                            result['fi_total_monthly'] = float(value)
                        elif in_ytd_section:
                            result['fi_total_ytd'] = float(value)
                    except:
                        pass

                if 'TRN Total:' in line:
                    try:
                        value = line.split('TRN Total:')[-1].strip().replace(',', '')
                        if in_monthly_section:
                            result['trn_total_monthly'] = float(value)
                        elif in_ytd_section:
                            result['trn_total_ytd'] = float(value)
                    except:
                        pass

                if 'Diff:' in line:
                    try:
                        value = line.split('Diff:')[-1].strip().replace(',', '')
                        if in_monthly_section:
                            result['monthly_diff'] = float(value)
                        elif in_ytd_section:
                            result['ytd_diff'] = float(value)
                    except:
                        pass

        return result
    except Exception as e:
        return None


def load_etl_configuration():
    """โหลด ETL configuration"""
    try:
        config_path = get_etl_config_path()
        if os.path.exists(config_path):
            st.session_state.etl_config_manager = create_etl_config_manager()
            st.session_state.etl_system = create_etl_system()
            # ซิงค์สถานะเริ่มต้น
            sync_status_from_system()
            return True
        else:
            st.error(f"❌ ไม่พบไฟล์ config.json ที่ {config_path}")
            return False
    except Exception as e:
        st.error(f"❌ Error loading ETL configuration: {e}")
        return False


# ========== Processing Functions ==========
def run_all_modules():
    """รันทุก module โดยใช้ system.run_all()"""
    if not st.session_state.etl_system:
        st.error("❌ Please load configuration first")
        return

    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: FI Module
        status_text.text("⏳ Running FI Module...")
        progress_bar.progress(10)

        if not st.session_state.etl_system.run_fi_module():
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

        if not st.session_state.etl_system.run_etl_module():
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
    if not st.session_state.etl_system:
        st.error("❌ Please load configuration first")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("⏳ Initializing FI Module...")
        progress_bar.progress(20)

        status_text.text("⏳ Processing FI data...")
        progress_bar.progress(40)

        if st.session_state.etl_system.run_fi_module():
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
    """รัน ETL Module"""
    if not st.session_state.etl_system:
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

        if st.session_state.etl_system.run_etl_module():
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


def reset_etl_system():
    """รีเซ็ต ETL system"""
    # รีเซ็ต session state
    st.session_state.etl_fi_completed = False
    st.session_state.etl_etl_completed = False
    st.session_state.etl_processing_status = None

    # รีเซ็ต system instance ถ้ามี
    if st.session_state.etl_system:
        st.session_state.etl_system.fi_completed = False
        st.session_state.etl_system.etl_completed = False
        st.session_state.etl_system.fi_output = None
        st.session_state.etl_system.etl_final_df = None
        st.session_state.etl_system.etl_anomaly_results = None

    st.success("🔄 ETL System reset completed")


# ========== Main ETL Admin Tab Function ==========
def show_etl_admin_tab():
    """
    Main function to display ETL Admin interface
    This is the entry point called from the main app
    """
    # Initialize session state
    init_etl_session_state()

    # Security check - Admin only
    if not st.session_state.get('user_data', {}).get('is_admin', False):
        st.error("❌ Access Denied: ETL Admin is available for administrators only")
        st.info("💡 Please contact your system administrator if you need access")
        return

    # Validate ETL environment
    validation = validate_etl_environment()

    if not validation['valid']:
        st.error("❌ ETL System Integration Error")
        st.markdown("### 🔍 Validation Issues:")
        for error in validation['errors']:
            st.error(f"• {error}")

        st.markdown("---")
        st.markdown("### 💡 Troubleshooting:")
        st.info(
            "1. ตรวจสอบว่า revenue-report directory อยู่ที่ `/Users/seal/Documents/GitHub/nt/revenue-report`\n"
            "2. ตรวจสอบว่ามีไฟล์ `config.json` ใน revenue-report/\n"
            "3. ตรวจสอบว่า ETL modules สามารถ import ได้"
        )
        return

    # Auto-load ETL configuration on first access
    if st.session_state.etl_config_manager is None:
        with st.spinner("Loading ETL configuration..."):
            load_etl_configuration()

    # Header
    st.markdown("## 🔧 ETL Admin - Revenue ETL System")
    st.caption("ระบบประมวลผลข้อมูลรายได้แบบ Modular")
    st.markdown("---")

    # Sidebar for ETL controls
    with st.sidebar:
        st.markdown("### 🔧 ETL Controls")

        # Reload configuration (config auto-loads on first access)
        reload_label = "🔄 Reload Configuration" if st.session_state.etl_config_manager else "📂 Load Configuration"
        if st.button(reload_label, key="etl_load_config"):
            if load_etl_configuration():
                st.success("✅ Configuration reloaded")

        # Display config status
        if st.session_state.etl_config_manager:
            config = st.session_state.etl_config_manager.config

            st.markdown("#### 📊 Current Status")
            st.info(f"**Year:** {config['processing_year']}")
            st.info(f"**Environment:** {config['environment']['name']}")

            st.markdown("---")

            # Quick Settings
            st.markdown("#### ⚡ Quick Controls")

            # Processing Month
            current_fi_month = config['processing_months']['fi_current_month']

            fi_month = st.number_input(
                "📅 Processing Month",
                min_value=1,
                max_value=12,
                value=current_fi_month,
                key="etl_fi_month_input"
            )

            if st.button("💾 Save Month", key="etl_save_month"):
                st.session_state.etl_config_manager.set_processing_month(fi_month, update_etl=True)
                if st.session_state.etl_system:
                    st.session_state.etl_system.fi_config = st.session_state.etl_config_manager.get_fi_config()
                    st.session_state.etl_system.etl_config = st.session_state.etl_config_manager.get_etl_config()
                st.success(f"✅ Month updated: {fi_month:02d}")

        st.markdown("---")

        # Processing Controls
        st.markdown("#### 🚀 Processing")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Run All", key="etl_run_all"):
                run_all_modules()
        with col2:
            if st.button("🔄 Reset", key="etl_reset"):
                reset_etl_system()

        st.markdown("---")

        # Module Controls
        if st.button("1️⃣ Run FI Module", key="etl_run_fi", use_container_width=True):
            run_fi_module()

        if st.button("2️⃣ Run ETL Module", key="etl_run_etl", use_container_width=True):
            run_etl_module()

        st.markdown("---")

        # Status
        st.markdown("#### 📈 Status")

        if get_fi_status():
            st.success("✅ FI Completed")
        else:
            st.info("⏳ FI Pending")

        if get_etl_status():
            st.success("✅ ETL Completed")
        else:
            st.info("⏳ ETL Pending")

    # Main Content - Import tab functions
    # Due to file size, we'll create a simplified version
    # The full version would include all tabs from web_app.py

    # Create tabs
    tabs = st.tabs([
        "📊 Dashboard",
        "📁 FI Module",
        "🔄 ETL Module",
        "✅ Reconciliation",
        "📋 Logs"
    ])

    with tabs[0]:
        show_etl_dashboard()

    with tabs[1]:
        show_etl_fi_module()

    with tabs[2]:
        show_etl_etl_module()

    with tabs[3]:
        show_etl_reconciliation()

    with tabs[4]:
        show_etl_logs()


# ========== Tab Display Functions ==========
# Note: These are simplified versions. Full implementation would include
# all functions from web_app.py with etl_ prefixes

def show_etl_dashboard():
    """แสดง ETL Dashboard"""
    st.header("📊 ETL Dashboard")

    if not st.session_state.etl_config_manager:
        st.warning("⚠️ ETL Configuration not loaded. Reloading...")
        load_etl_configuration()
        st.rerun()
        return

    config = st.session_state.etl_config_manager.config

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year = config['processing_year']
        fi_month = config['processing_months']['fi_current_month']
        st.metric("Processing Period", f"{year}-{fi_month:02d}")

    with col2:
        status = "✅ Ready" if get_fi_status() else "⏳ Pending"
        st.metric("FI Module", status)

    with col3:
        status = "✅ Ready" if get_etl_status() else "⏳ Pending"
        st.metric("ETL Module", status)

    with col4:
        reconcile_status = "Enabled" if config['etl_module']['reconciliation']['enabled'] else "Disabled"
        st.metric("Reconciliation", reconcile_status)

    # File Status
    st.markdown("---")
    st.subheader("📁 File Status")

    if get_fi_status() and st.session_state.etl_system and st.session_state.etl_system.fi_output:
        st.markdown("### FI Output Files")
        for key, path in st.session_state.etl_system.fi_output.items():
            file_info = check_file_exists(path)
            if file_info['exists']:
                st.success(f"✅ {key}: {os.path.basename(path)} ({file_info['size_kb']:.1f} KB)")
            else:
                st.error(f"❌ {key}: File not found")


def show_etl_fi_module():
    """แสดง FI Module Tab"""
    st.header("📁 FI Module")

    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return

    fi_config = st.session_state.etl_config_manager.get_fi_config()

    # Configuration Display
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Input Files")
        for file in fi_config['input_files']:
            st.text(f"📄 {file}")

    with col2:
        st.markdown("### Output Files")
        for key, file in fi_config['output_files'].items():
            st.text(f"💾 {key}: {file}")

    st.markdown("---")

    if st.button("▶️ Run FI Processing", key="fi_tab_run"):
        run_fi_module()

    # Results Display
    if get_fi_status() and st.session_state.etl_system and st.session_state.etl_system.fi_output:
        st.markdown("### 📊 Processing Results")
        excel_path = st.session_state.etl_system.fi_output.get('excel')
        if excel_path and os.path.exists(excel_path):
            st.success(f"✅ Excel report generated: {os.path.basename(excel_path)}")


def show_etl_etl_module():
    """แสดง ETL Module Tab"""
    st.header("🔄 ETL Module")

    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return

    st.markdown("### 📋 Pipeline Steps")

    steps = [
        "1️⃣ Concatenate CSV Files",
        "2️⃣ Map Cost Center",
        "3️⃣ Map Product Codes",
        "4️⃣ Merge with Master Files",
        "5️⃣ Anomaly Detection",
        "6️⃣ Generate Reports"
    ]

    for step in steps:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.text(step)
        with col2:
            if get_etl_status():
                st.success("✅")

    st.markdown("---")

    if st.button("▶️ Run ETL Pipeline", key="etl_tab_run"):
        run_etl_module()


def show_etl_reconciliation():
    """แสดง Reconciliation Tab"""
    st.header("✅ Reconciliation")

    if not get_etl_status():
        st.info("Please complete ETL processing first")
        return

    # อ่านผลจาก log files
    reconcile_result = get_reconciliation_results(st.session_state.etl_config_manager)

    if not reconcile_result:
        st.warning("⚠️ No reconciliation results found")
        return

    st.markdown("### 🔍 Reconciliation Results")

    # Summary Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        monthly_status = "PASSED ✅" if reconcile_result['monthly_passed'] else "FAILED ❌"
        st.metric("Monthly", monthly_status, f"{reconcile_result['monthly_diff']:,.2f}")

    with col2:
        ytd_status = "PASSED ✅" if reconcile_result['ytd_passed'] else "FAILED ❌"
        st.metric("YTD", ytd_status, f"{reconcile_result['ytd_diff']:,.2f}")

    with col3:
        config = st.session_state.etl_config_manager.config
        tolerance = config['etl_module']['reconciliation']['tolerance']
        st.metric("Tolerance", f"±{tolerance:.2f}")


def show_etl_logs():
    """แสดง Logs Tab"""
    st.header("📋 System Logs")

    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return

    log_dir = st.session_state.etl_config_manager.config['logging'].get('log_directory', 'logs')

    log_files = glob.glob(f"{log_dir}/*.log")

    if not log_files:
        st.warning(f"No log files found in {log_dir}/")
        return

    # Sort by modification time
    log_files.sort(key=os.path.getmtime, reverse=True)

    selected_log = st.selectbox(
        "Select Log File",
        options=[os.path.basename(f) for f in log_files],
        key="etl_log_select"
    )

    if selected_log:
        log_path = os.path.join(log_dir, selected_log)

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()

            max_lines = st.number_input("Max Lines", min_value=10, max_value=1000, value=200, key="etl_log_lines")

            lines = log_content.split('\n')
            display_lines = lines[-max_lines:] if len(lines) > max_lines else lines

            st.text_area(
                "Log Content",
                value='\n'.join(display_lines),
                height=400,
                key="etl_log_content"
            )

        except Exception as e:
            st.error(f"Error reading log file: {e}")
