"""
ETL Admin Tab Module
====================
Web Interface สำหรับ ETL System (Admin Only)
Converted from revenue-report/web_app.py with etl_ session state prefixes

This module provides full ETL admin interface integrated into the main web app.
All session states use 'etl_' prefix to avoid collision.

Author: Revenue Report Web Integration
Version: 2.0.0 (Full Feature)
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
    create_etl_config_manager,
    create_etl_system,
    validate_etl_environment,
    get_etl_config_path
)
# Page Configuration (removed - managed by main app)
# Page config removed - managed by main app.py

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

# Session state is now initialized in app.py:init_session_state()
# No need to initialize here - just use the values

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
        # ไม่แสดง warning ที่นี่ เพื่อไม่ให้ซ้ำซ้อน
        return None

def load_configuration():
    """โหลด configuration จากไฟล์"""
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
        st.error(f"❌ Error loading configuration: {e}")
        return False

def show_etl_admin_tab():
    """Main ETL Admin interface - entry point from main app"""
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
        return

    # Auto-load ETL configuration on first access
    if st.session_state.etl_config_manager is None:
        with st.spinner("Loading ETL configuration..."):
            load_configuration()


    
    # Header
    st.title("💰 Revenue ETL System")
    st.markdown("### ระบบประมวลผลข้อมูลรายได้แบบ Modular v2.0")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Quick Settings")

        # Load configuration
        if st.button("📂 Load Configuration"):
            if load_configuration():
                st.success("✅ Configuration loaded successfully")

        # Display config status
        if st.session_state.etl_config_manager:
            config = st.session_state.etl_config_manager.config

            st.markdown("### 📊 Current Status")
            st.info(f"**Year:** {config['processing_year']}")
            st.info(f"**Environment:** {config['environment']['name']}")
            st.info(f"**OS:** {st.session_state.etl_config_manager.os_platform}")

            st.markdown("---")

            # Quick Settings
            st.markdown("### ⚡ Quick Controls")

            # Processing Month
            current_fi_month = config['processing_months']['fi_current_month']

            fi_month = st.number_input(
                "📅 Processing Month",
                min_value=1,
                max_value=12,
                value=current_fi_month,
                help="เดือนที่ทั้ง FI และ ETL จะประมวลผล (ต้องเท่ากันเสมอ)"
            )

            # Anomaly Detection - IQR Multiplier
            iqr_multiplier = st.number_input(
                "📊 IQR Multiplier",
                min_value=1.0,
                max_value=3.0,
                value=config['etl_module']['anomaly_detection']['iqr_multiplier'],
                step=0.1,
                format="%.1f",
                help="ค่าคูณสำหรับ Interquartile Range ในการหา anomaly"
            )

            # Anomaly Detection - Rolling Window
            rolling_window = st.number_input(
                "📈 Rolling Window",
                min_value=3,
                max_value=12,
                value=config['etl_module']['anomaly_detection']['rolling_window'],
                step=1,
                help="จำนวนเดือนสำหรับ rolling average"
            )

            if st.button("💾 Save Quick Settings", width='stretch'):
                # Update months (sync ทั้ง FI และ ETL ให้เท่ากันเสมอ)
                st.session_state.etl_config_manager.set_processing_month(fi_month, update_etl=True)

                # Update anomaly detection settings
                st.session_state.etl_config_manager.config['etl_module']['anomaly_detection']['iqr_multiplier'] = iqr_multiplier
                st.session_state.etl_config_manager.config['etl_module']['anomaly_detection']['rolling_window'] = rolling_window

                # Reload paths (เพราะ year อาจเปลี่ยน)
                st.session_state.etl_config_manager._setup_paths()

                # Reload config in system
                if st.session_state.etl_system:
                    st.session_state.etl_system.fi_config = st.session_state.etl_config_manager.get_fi_config()
                    st.session_state.etl_system.etl_config = st.session_state.etl_config_manager.get_etl_config()

                st.success(f"✅ Settings updated: Month {fi_month:02d}, IQR {iqr_multiplier:.1f}, Window {rolling_window}")

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
    tabs = st.tabs(["📊 Dashboard", "📁 FI Module", "🔄 ETL Module", "✅ Reconciliation", "📈 Analytics", "📋 Logs", "⚙️ Configuration"])

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

    with tabs[6]:
        show_configuration()

def run_all_modules():
    """
    รันทุก module โดยใช้ system.run_all()
    (ไม่เขียนตรรกะซ้ำ - ใช้ที่มีอยู่แล้วใน main.py)
    """
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
    """
    รัน ETL Module
    (main.py จะตรวจสอบและรัน FI Module ก่อนอัตโนมัติถ้ายังไม่ได้รัน)
    """
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

def reset_system():
    """รีเซ็ตระบบ"""
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

    st.success("🔄 System reset completed")

def show_dashboard():
    """แสดง Dashboard"""
    st.header("📊 Dashboard")
    
    if not st.session_state.etl_config_manager:
        st.info("Please load configuration to view dashboard")
        return
    
    # Check month sync
    fi_month = st.session_state.etl_config_manager.config['processing_months']['fi_current_month']
    etl_month = st.session_state.etl_config_manager.config['processing_months']['etl_end_month']

    if fi_month != etl_month:
        st.error(f"🚨 เดือนไม่ตรงกัน! FI: {fi_month:02d}, ETL: {etl_month:02d} → Reconciliation จะล้มเหลว")
        st.warning("💡 กรุณาแก้ไขที่ Sidebar → 📝 Edit Configuration → กด 🔄 Sync เดือนให้ตรงกัน")
        st.markdown("---")

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year = st.session_state.etl_config_manager.config['processing_year']
        month_display = f"{year}-{fi_month:02d}"
        if fi_month != etl_month:
            month_display = f"{year}-{fi_month:02d}⚠️"
        st.metric(
            label="Processing Year/Month",
            value=month_display,
            delta="Month mismatch!" if fi_month != etl_month else None,
            delta_color="inverse" if fi_month != etl_month else "normal"
        )
    
    with col2:
        status = "✅ Ready" if get_fi_status() else "⏳ Pending"
        st.metric(label="FI Module", value=status)

    with col3:
        status = "✅ Ready" if get_etl_status() else "⏳ Pending"
        st.metric(label="ETL Module", value=status)
    
    with col4:
        reconcile_status = "Enabled" if st.session_state.etl_config_manager.config['etl_module']['reconciliation']['enabled'] else "Disabled"
        st.metric(label="Reconciliation", value=reconcile_status)
    
    # Configuration Overview
    st.markdown("---")
    st.subheader("⚙️ Configuration Overview")
    
    config = st.session_state.etl_config_manager.config
    
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
        fi_config = st.session_state.etl_config_manager.get_fi_config()
        master_path = fi_config['paths']['master']
        master_source = fi_config['paths']['master_source']  # master_path/source

        for key, filename in st.session_state.etl_config_manager.config['fi_module']['master_files'].items():
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
        if get_fi_status() and st.session_state.etl_system and st.session_state.etl_system.fi_output:
            st.markdown("### FI Output Files")
            for key, path in st.session_state.etl_system.fi_output.items():
                file_info = check_file_exists(path)
                if file_info['exists']:
                    st.success(f"✅ {key}: {os.path.basename(path)} ({file_info['size_kb']:.1f} KB)")
                else:
                    st.error(f"❌ {key}: File not found")

    # ETL Output Files
    if get_etl_status() and st.session_state.etl_system:
        st.markdown("---")
        st.markdown("### ETL Output Files")

        etl_config = st.session_state.etl_config_manager.get_etl_config()
        output_path = etl_config['paths']['output']
        final_output_path = etl_config['paths']['final_output']

        # Get output_files with defaults
        output_files = etl_config.get('output_files', {})
        year = st.session_state.etl_config_manager.config.get('processing_year', '2026')

        # Define default filenames if not in config
        default_files = {
            'concat': f'trn_revenue_nt_{year}.csv',
            'mapped_cc': f'revenue_new_cc_{year}.csv',
            'mapped_product': f'revenue_mapped_product_{year}_.csv',
            'final_report': f'REVENUE_NT_REPORT_{year}.csv',
            'error_gl': f'error_gl_REVENUE_NT_REPORT_{year}.csv',
            'error_product': f'error_product_REVENUE_NT_REPORT_{year}.csv'
        }

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Intermediate Files**")
            for key in ['concat', 'mapped_cc', 'mapped_product']:
                filename = output_files.get(key, default_files.get(key, ''))
                if filename:
                    file_path = os.path.join(output_path, filename)
                    file_info = check_file_exists(file_path)
                    if file_info['exists']:
                        st.success(f"✅ {key}")
                        st.caption(f"{file_info['size_kb']:.1f} KB")
                    else:
                        st.warning(f"⚠️ {key}")

        with col2:
            st.markdown("**Final Report**")
            filename = output_files.get('final_report', default_files.get('final_report', ''))
            if filename:
                final_file = os.path.join(final_output_path, filename)
                file_info = check_file_exists(final_file)
                if file_info['exists']:
                    st.success(f"✅ Final Report")
                    st.caption(f"{file_info['size_kb']:.1f} KB")
                else:
                    st.warning(f"⚠️ Final Report")

        with col3:
            st.markdown("**Error Files**")
            for key in ['error_gl', 'error_product']:
                filename = output_files.get(key, default_files.get(key, ''))
                if filename:
                    file_path = os.path.join(final_output_path, filename)
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
    
    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return
    
    fi_config = st.session_state.etl_config_manager.get_fi_config()
    
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
        st.markdown("---")
        st.markdown("### 📊 Processing Results")

        # Download Section - แสดงก่อนเพื่อให้เห็นชัดเจน
        if st.session_state.etl_system and st.session_state.etl_system.fi_output:
            st.markdown("#### 📥 Download Output Files")

            output_files = st.session_state.etl_system.fi_output

            # สร้าง columns สำหรับแต่ละไฟล์
            cols = st.columns(len(output_files))

            for idx, (key, file_path) in enumerate(output_files.items()):
                with cols[idx]:
                    if file_path and os.path.exists(file_path):
                        file_name = os.path.basename(file_path)
                        file_size = os.path.getsize(file_path) / 1024  # KB
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))

                        # แสดงข้อมูลไฟล์
                        st.markdown(f"**{key.upper()}**")
                        st.caption(f"📄 {file_name}")
                        st.caption(f"📦 {file_size:.1f} KB")
                        st.caption(f"🕐 {file_time.strftime('%H:%M:%S')}")

                        # ปุ่ม Download
                        with open(file_path, 'rb') as f:
                            file_ext = os.path.splitext(file_name)[1]
                            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if file_ext == '.xlsx' else 'text/csv'

                            st.download_button(
                                label=f"⬇️ Download",
                                data=f.read(),
                                file_name=file_name,
                                mime=mime_type,
                                key=f"download_fi_{key}",
                                width='stretch'
                            )
                    else:
                        st.warning(f"❌ {key}: File not found")

            st.markdown("---")

        # Summary Display
        try:
            excel_path = st.session_state.etl_system.fi_output.get('excel')
            if excel_path and os.path.exists(excel_path):
                st.success(f"✅ Excel report generated: {os.path.basename(excel_path)}")

                # Load summary sheet
                df_summary = pd.read_excel(excel_path, sheet_name="summary_other")

                st.markdown("#### Summary - รายได้/ค่าใช้จ่ายอื่น")

                # Format numbers with comma separator
                df_display = df_summary.copy()
                for col in df_display.columns:
                    if col != 'รายการ' and df_display[col].dtype in ['int64', 'float64']:
                        df_display[col] = df_display[col].apply(lambda x: f'{x:,.2f}' if pd.notna(x) else '')

                st.dataframe(df_display, width='stretch')

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
    
    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return
    
    etl_config = st.session_state.etl_config_manager.get_etl_config()
    
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
    reconcile_result = get_reconciliation_results(st.session_state.etl_config_manager)

    if not reconcile_result:
        st.warning("⚠️ No reconciliation results found. Reconciliation may be disabled or logs not available.")

        # แสดง config
        config = st.session_state.etl_config_manager.config
        st.info(f"Reconciliation Enabled: {config['etl_module']['reconciliation']['enabled']}")
        st.info(f"Tolerance: {config['etl_module']['reconciliation']['tolerance']}")
        return

    st.markdown("### 🔍 Reconciliation Results")

    # แสดง FI Month ที่ใช้
    config = st.session_state.etl_config_manager.config
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

    st.dataframe(df_reconcile, width='stretch')

    # Validation Results
    st.markdown("---")
    st.markdown("### 🔍 Validation Results")

    if st.session_state.etl_system and st.session_state.etl_system.etl_final_df is not None:
        df = st.session_state.etl_system.etl_final_df

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

    if st.session_state.etl_system and st.session_state.etl_system.etl_anomaly_results:
        anomaly_results = st.session_state.etl_system.etl_anomaly_results

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
                                    width='stretch'
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

    if st.session_state.etl_system and st.session_state.etl_system.etl_final_df is not None:
        df = st.session_state.etl_system.etl_final_df

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

def show_configuration():
    """แสดงหน้า Configuration - Comprehensive Config Editor"""
    st.header("⚙️ Configuration Editor")

    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return

    config = st.session_state.etl_config_manager.config

    st.warning("⚠️ การแก้ไข configuration จะมีผลชั่วคราว และจะหายเมื่อรีสตาร์ทโปรแกรม")
    st.info("💡 เพื่อบันทึกถาวร ให้แก้ไขไฟล์ config.json โดยตรง")

    # Section 1: Environment & Paths
    st.markdown("---")
    st.markdown("## 1️⃣ Environment & Paths")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("### Environment")
        env_name = st.text_input("Environment Name", value=config['environment']['name'], key="env_name")
        env_desc = st.text_input("Description", value=config['environment']['description'], key="env_desc")

        st.markdown("### Processing Period")
        new_year = st.text_input("Processing Year", value=config['processing_year'], key="proc_year")

        current_fi_month = config['processing_months']['fi_current_month']
        current_etl_month = config['processing_months']['etl_end_month']

        if current_fi_month != current_etl_month:
            st.error(f"🚨 เดือนไม่ตรงกัน! FI: {current_fi_month:02d}, ETL: {current_etl_month:02d}")

        new_fi_month = st.number_input("FI Current Month", min_value=1, max_value=12, value=current_fi_month, key="fi_month")
        new_etl_month = st.number_input("ETL End Month", min_value=1, max_value=12, value=current_etl_month, key="etl_month")

        if new_fi_month != new_etl_month:
            st.warning("⚠️ FI และ ETL ควรเป็นเดือนเดียวกัน!")

    with col2:
        st.markdown("### OS-Specific Paths")

        # Current OS
        current_os = st.session_state.etl_config_manager.os_platform
        st.info(f"Current OS: **{current_os}**")

        # Darwin (macOS) paths
        with st.expander("🍎 macOS (Darwin) Paths", expanded=(current_os == 'darwin')):
            darwin_base = st.text_input(
                "Base Path",
                value=config['paths']['darwin']['base_path'],
                key="darwin_base"
            )
            darwin_master = st.text_input(
                "Master Path",
                value=config['paths']['darwin']['master_path'],
                key="darwin_master"
            )

        # Linux paths
        with st.expander("🐧 Linux Paths", expanded=(current_os == 'linux')):
            linux_base = st.text_input(
                "Base Path",
                value=config['paths']['linux']['base_path'],
                key="linux_base"
            )
            linux_master = st.text_input(
                "Master Path",
                value=config['paths']['linux']['master_path'],
                key="linux_master"
            )

        # Windows paths
        with st.expander("🪟 Windows Paths", expanded=(current_os == 'windows')):
            windows_base = st.text_input(
                "Base Path",
                value=config['paths']['windows']['base_path'],
                key="windows_base"
            )
            windows_master = st.text_input(
                "Master Path",
                value=config['paths']['windows']['master_path'],
                key="windows_master"
            )

    # Section 2: FI Module Configuration
    st.markdown("---")
    st.markdown("## 2️⃣ FI Module Configuration")

    st.warning("⚠️ **คำเตือน**: การเปลี่ยนแปลง Master Files และ Input Files อาจส่งผลกระทบต่อการประมวลผลข้อมูล กรุณาตรวจสอบให้แน่ใจว่าไฟล์มีอยู่จริงและ format ถูกต้อง")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🟠 :orange[Input Files] *(Important)*")
        st.caption("📥 ระบุชื่อไฟล์ input ที่ต้องการประมวลผล - รองรับ template {YYYYMMDD}")
        fi_input_files = config['fi_module']['input_files']
        for idx, filename in enumerate(fi_input_files):
            st.text_input(f"Input File {idx+1}", value=filename, key=f"fi_input_{idx}")

    with col2:
        st.markdown("### 🔵 :blue[Master Files] *(Critical)*")
        st.caption("📚 ไฟล์ Master สำหรับ mapping GL codes - เปลี่ยนแปลงเฉพาะเมื่อมีไฟล์ Master ใหม่")
        fi_master_expense = st.text_input("Expense", value=config['fi_module']['master_files']['expense'], key="fi_master_expense")
        fi_master_revenue = st.text_input("Revenue", value=config['fi_module']['master_files']['revenue'], key="fi_master_revenue")
        fi_master_other = st.text_input("Other Revenue", value=config['fi_module']['master_files']['other_revenue'], key="fi_master_other")
        fi_master_net = st.text_input("Revenue Expense Net", value=config['fi_module']['master_files']['revenue_expense_net'], key="fi_master_net")

    with col3:
        st.markdown("### 🟢 :green[Output Files] *(Info)*")
        st.caption("💾 ชื่อไฟล์ผลลัพธ์ที่จะถูกสร้างขึ้น - รองรับ template {YYYYMM}")
        fi_output_excel = st.text_input("Excel Output", value=config['fi_module']['output_files']['excel'], key="fi_output_excel")
        fi_output_csv_expense = st.text_input("CSV Expense", value=config['fi_module']['output_files']['csv_expense'], key="fi_output_csv_expense")
        fi_output_csv_revenue = st.text_input("CSV Revenue", value=config['fi_module']['output_files']['csv_revenue'], key="fi_output_csv_revenue")

    # Section 3: ETL Module Configuration
    st.markdown("---")
    st.markdown("## 3️⃣ ETL Module Configuration")

    st.warning("⚠️ **คำเตือน**: Master Files และ Input Patterns มีความสำคัญต่อการ mapping และ transformation ของข้อมูล")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔵 :blue[Master Files] *(Critical)*")
        st.caption("📚 ไฟล์ Master สำหรับ mapping products, GL codes และ cost centers")
        etl_master_product = st.text_input("Product Master", value=config['etl_module']['master_files']['product'], key="etl_master_product")
        etl_master_gl = st.text_input("GL Code Master", value=config['etl_module']['master_files']['gl_code'], key="etl_master_gl")
        etl_master_mapping_cc = st.text_input("Mapping Cost Center", value=config['etl_module']['master_files']['mapping_cc'], key="etl_master_mapping_cc")
        etl_master_mapping_product = st.text_input("Mapping Product", value=config['etl_module']['master_files']['mapping_product'], key="etl_master_mapping_product")

        st.markdown("### 🟠 :orange[Input Patterns] *(Important)*")
        st.caption("📥 Pattern สำหรับค้นหาไฟล์ input - รองรับ wildcards (*)")
        etl_input_main = st.text_area(
            "Main Files (comma-separated)",
            value=", ".join(config['etl_module']['input_patterns']['main_files']),
            key="etl_input_main",
            help="รายการไฟล์หลัก เช่น TRN_REVENUE_NT1_*.csv, TRN_REVENUE_ADJ_GL_NT1_*.csv"
        )
        etl_input_adj_monthly = st.text_input("Adj Monthly", value=config['etl_module']['input_patterns']['adj_monthly'], key="etl_input_adj_monthly", help="ไฟล์ปรับปรุงรายเดือน")
        etl_input_adj_ytd = st.text_input("Adj YTD", value=config['etl_module']['input_patterns']['adj_ytd'], key="etl_input_adj_ytd", help="ไฟล์ปรับปรุงสะสม")

    with col2:
        st.markdown("### 🟢 :green[Output Files] *(Info)*")
        st.caption("💾 ชื่อไฟล์ผลลัพธ์จาก ETL pipeline - รองรับ template variables")

        # Get output_files with defaults based on processing_year
        output_files = config['etl_module'].get('output_files', {})
        year = config.get('processing_year', '2026')

        etl_output_concat = st.text_input("Concat File", value=output_files.get('concat', f'trn_revenue_nt_{year}.csv'), key="etl_output_concat")
        etl_output_mapped_cc = st.text_input("Mapped Cost Center", value=output_files.get('mapped_cc', f'revenue_new_cc_{year}.csv'), key="etl_output_mapped_cc")
        etl_output_mapped_product = st.text_input("Mapped Product", value=output_files.get('mapped_product', f'revenue_mapped_product_{year}_.csv'), key="etl_output_mapped_product")
        etl_output_final = st.text_input("Final Report", value=output_files.get('final_report', f'REVENUE_NT_REPORT_{year}.csv'), key="etl_output_final")

        st.markdown("#### Error Files")
        st.caption("🚨 ไฟล์ที่บันทึก records ที่ mapping ไม่สำเร็จ")
        etl_output_error_gl = st.text_input("Error GL", value=output_files.get('error_gl', f'error_gl_REVENUE_NT_REPORT_{year}.csv'), key="etl_output_error_gl")
        etl_output_error_product = st.text_input("Error Product", value=output_files.get('error_product', f'error_product_REVENUE_NT_REPORT_{year}.csv'), key="etl_output_error_product")

    # Section 4: Business Rules
    st.markdown("---")
    st.markdown("## 4️⃣ Business Rules")

    col1, col2 = st.columns(2)

    with col1:
        br_exclude_bg = st.text_input("Exclude Business Group", value=config['etl_module']['business_rules']['exclude_business_group'], key="br_exclude_bg")
        br_non_telecom = st.text_input("Non-Telecom Service Group", value=config['etl_module']['business_rules']['non_telecom_service_group'], key="br_non_telecom")
        br_new_adj_bg = st.text_input("New Adj Business Group", value=config['etl_module']['business_rules']['new_adj_business_group'], key="br_new_adj_bg")

    with col2:
        br_financial_income = st.text_input("Financial Income Name", value=config['etl_module']['business_rules']['financial_income_name'], key="br_financial_income")
        br_other_revenue = st.text_input("Other Revenue Adj Name", value=config['etl_module']['business_rules']['other_revenue_adj_name'], key="br_other_revenue")

    # Section 5: Reconciliation & Validation
    st.markdown("---")
    st.markdown("## 5️⃣ Reconciliation & Validation")

    st.info("ℹ️ Reconciliation ตรวจสอบความถูกต้องระหว่าง FI และ TRN data - Tolerance ถูก lock ที่ 0.0 (ต้องตรงทุกหลัก)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Reconciliation")
        st.caption("🔍 ตรวจสอบความสอดคล้องระหว่างข้อมูล FI และ Transaction")
        reconcile_enabled = st.checkbox(
            "Enable Reconciliation",
            value=config['etl_module']['reconciliation']['enabled'],
            key="reconcile_enabled"
        )
        st.warning("⚠️ **Tolerance = 0.0** (ถาวร) - ข้อมูลต้องตรงกันทุกหลัก")

    with col2:
        st.markdown("### ✅ Validation")
        st.caption("🔍 ตรวจสอบความถูกต้องของข้อมูลก่อนสร้างรายงาน")
        validation_threshold = st.number_input(
            "Grand Total Diff Threshold",
            min_value=0.0,
            max_value=1.0,
            value=config['etl_module']['validation']['grand_total_diff_threshold'],
            step=0.01,
            format="%.2f",
            key="validation_threshold",
            help="ค่าความแตกต่างสูงสุดที่ยอมรับได้ (0.01 = 1%)"
        )

    # Section 6: Anomaly Detection
    st.markdown("---")
    st.markdown("## 6️⃣ Anomaly Detection")

    st.info("ℹ️ Anomaly Detection ใช้ IQR (Interquartile Range) วิเคราะห์ค่าผิดปกติในรายได้แต่ละเดือน - ปรับค่าพารามิเตอร์ได้ตามต้องการ")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🚨 Detection Settings")
        st.caption("เปิด/ปิด การตรวจจับความผิดปกติ")
        anomaly_enabled = st.checkbox(
            "Enable Anomaly Detection",
            value=config['etl_module']['anomaly_detection']['enabled'],
            key="anomaly_enabled"
        )
        anomaly_iqr = st.number_input(
            "IQR Multiplier",
            min_value=1.0,
            max_value=3.0,
            value=config['etl_module']['anomaly_detection']['iqr_multiplier'],
            step=0.1,
            format="%.1f",
            key="anomaly_iqr",
            help="ค่าคูณ IQR สำหรับกำหนด outliers (1.5 = standard, 3.0 = conservative)"
        )

    with col2:
        st.markdown("### 📊 Historical Settings")
        st.caption("จำนวนเดือนสำหรับการวิเคราะห์")
        anomaly_min_history = st.number_input(
            "Min History",
            min_value=2,
            max_value=12,
            value=config['etl_module']['anomaly_detection']['min_history'],
            step=1,
            key="anomaly_min_history",
            help="จำนวนเดือนขั้นต่ำที่ต้องมีก่อนเริ่มตรวจจับ anomaly"
        )
        anomaly_rolling_window = st.number_input(
            "Rolling Window",
            min_value=3,
            max_value=12,
            value=config['etl_module']['anomaly_detection']['rolling_window'],
            step=1,
            key="anomaly_rolling_window",
            help="จำนวนเดือนสำหรับคำนวณ rolling average"
        )

    with col3:
        anomaly_historical = st.checkbox(
            "Enable Historical Highlight",
            value=config['etl_module']['anomaly_detection']['enable_historical_highlight'],
            key="anomaly_historical"
        )

    # Section 7: Special Mappings
    st.markdown("---")
    st.markdown("## 7️⃣ Special Mappings")

    with st.expander("🔄 View/Edit Special Mappings (JSON)", expanded=False):
        special_mappings_json = json.dumps(config['etl_module']['special_mappings'], indent=2, ensure_ascii=False)
        special_mappings_edited = st.text_area(
            "Special Mappings (JSON format)",
            value=special_mappings_json,
            height=200,
            key="special_mappings"
        )

    # Section 8: Logging
    st.markdown("---")
    st.markdown("## 8️⃣ Logging Configuration")

    col1, col2, col3 = st.columns(3)

    with col1:
        log_level = st.selectbox(
            "Log Level",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config['logging']['level']),
            key="log_level"
        )

    with col2:
        log_enable_file = st.checkbox(
            "Enable File Logging",
            value=config['logging']['enable_file_logging'],
            key="log_enable_file"
        )

    with col3:
        log_directory = st.text_input(
            "Log Directory",
            value=config['logging']['log_directory'],
            key="log_directory"
        )

    # Save Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("💾 Save All Configuration Changes", width='stretch', type="primary"):
            try:
                # Update environment
                config['environment']['name'] = env_name
                config['environment']['description'] = env_desc

                # Update processing period
                config['processing_year'] = new_year
                config['processing_months']['fi_current_month'] = new_fi_month
                config['processing_months']['etl_end_month'] = new_etl_month

                # Update paths
                config['paths']['darwin']['base_path'] = darwin_base
                config['paths']['darwin']['master_path'] = darwin_master
                config['paths']['linux']['base_path'] = linux_base
                config['paths']['linux']['master_path'] = linux_master
                config['paths']['windows']['base_path'] = windows_base
                config['paths']['windows']['master_path'] = windows_master

                # Update FI module
                config['fi_module']['master_files']['expense'] = fi_master_expense
                config['fi_module']['master_files']['revenue'] = fi_master_revenue
                config['fi_module']['master_files']['other_revenue'] = fi_master_other
                config['fi_module']['master_files']['revenue_expense_net'] = fi_master_net
                config['fi_module']['output_files']['excel'] = fi_output_excel
                config['fi_module']['output_files']['csv_expense'] = fi_output_csv_expense
                config['fi_module']['output_files']['csv_revenue'] = fi_output_csv_revenue

                # Update ETL module - master files
                config['etl_module']['master_files']['product'] = etl_master_product
                config['etl_module']['master_files']['gl_code'] = etl_master_gl
                config['etl_module']['master_files']['mapping_cc'] = etl_master_mapping_cc
                config['etl_module']['master_files']['mapping_product'] = etl_master_mapping_product

                # Update ETL module - input patterns
                config['etl_module']['input_patterns']['main_files'] = [f.strip() for f in etl_input_main.split(',')]
                config['etl_module']['input_patterns']['adj_monthly'] = etl_input_adj_monthly
                config['etl_module']['input_patterns']['adj_ytd'] = etl_input_adj_ytd

                # Update ETL module - output files (ensure output_files exists)
                if 'output_files' not in config['etl_module']:
                    config['etl_module']['output_files'] = {}

                config['etl_module']['output_files']['concat'] = etl_output_concat
                config['etl_module']['output_files']['mapped_cc'] = etl_output_mapped_cc
                config['etl_module']['output_files']['mapped_product'] = etl_output_mapped_product
                config['etl_module']['output_files']['final_report'] = etl_output_final
                config['etl_module']['output_files']['error_gl'] = etl_output_error_gl
                config['etl_module']['output_files']['error_product'] = etl_output_error_product

                # Update business rules
                config['etl_module']['business_rules']['exclude_business_group'] = br_exclude_bg
                config['etl_module']['business_rules']['non_telecom_service_group'] = br_non_telecom
                config['etl_module']['business_rules']['new_adj_business_group'] = br_new_adj_bg
                config['etl_module']['business_rules']['financial_income_name'] = br_financial_income
                config['etl_module']['business_rules']['other_revenue_adj_name'] = br_other_revenue

                # Update reconciliation & validation
                config['etl_module']['reconciliation']['enabled'] = reconcile_enabled
                # Tolerance is always 0.0
                config['etl_module']['reconciliation']['tolerance'] = 0.0
                config['etl_module']['validation']['grand_total_diff_threshold'] = validation_threshold

                # Update anomaly detection
                config['etl_module']['anomaly_detection']['enabled'] = anomaly_enabled
                config['etl_module']['anomaly_detection']['iqr_multiplier'] = anomaly_iqr
                config['etl_module']['anomaly_detection']['min_history'] = anomaly_min_history
                config['etl_module']['anomaly_detection']['rolling_window'] = anomaly_rolling_window
                config['etl_module']['anomaly_detection']['enable_historical_highlight'] = anomaly_historical

                # Update special mappings
                try:
                    special_mappings_parsed = json.loads(special_mappings_edited)
                    config['etl_module']['special_mappings'] = special_mappings_parsed
                except json.JSONDecodeError as e:
                    st.error(f"❌ Special Mappings JSON is invalid: {e}")
                    return

                # Update logging
                config['logging']['level'] = log_level
                config['logging']['enable_file_logging'] = log_enable_file
                config['logging']['log_directory'] = log_directory

                # **CRITICAL: Save config to file!**
                st.session_state.etl_config_manager.save_config(backup=True)

                # Reload paths
                st.session_state.etl_config_manager._setup_paths()

                # Reload config in system
                if st.session_state.etl_system:
                    st.session_state.etl_system.fi_config = st.session_state.etl_config_manager.get_fi_config()
                    st.session_state.etl_system.etl_config = st.session_state.etl_config_manager.get_etl_config()

                st.success("✅ Configuration updated and saved to file successfully!")
                st.info(f"💾 Config saved to: {st.session_state.etl_config_manager.config_path}")
                st.balloons()

                if new_fi_month != new_etl_month:
                    st.warning("⚠️ Warning: FI และ ETL เดือนไม่ตรงกัน - Reconciliation อาจล้มเหลว")

            except Exception as e:
                st.error(f"❌ Error saving configuration: {e}")

def show_logs():
    """แสดงหน้า Logs"""
    st.header("📋 System Logs")

    # Check if config_manager is available
    if not st.session_state.etl_config_manager:
        st.info("Please load configuration first")
        return

    # Log directory
    log_dir = st.session_state.etl_config_manager.config['logging'].get('log_directory', 'logs')

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
        etl_config = st.session_state.etl_config_manager.get_etl_config()
        final_output_path = etl_config['paths']['final_output']
        # Get output_files with defaults
        output_files = etl_config.get('output_files', {})
        year = st.session_state.etl_config_manager.config.get('processing_year', '2026')

        default_files = {
            'error_gl': f'error_gl_REVENUE_NT_REPORT_{year}.csv',
            'error_product': f'error_product_REVENUE_NT_REPORT_{year}.csv'
        }

        error_files = {}
        for key in ['error_gl', 'error_product']:
            filename = output_files.get(key, default_files.get(key, ''))
            if filename:
                file_path = os.path.join(final_output_path, filename)
                if os.path.exists(file_path):
                    error_files[key] = file_path

        if error_files:
            for error_type, error_path in error_files.items():
                with st.expander(f"📄 {error_type.replace('_', ' ').title()}", expanded=False):
                    try:
                        df_error = pd.read_csv(error_path)

                        if len(df_error) > 0:
                            st.warning(f"Found {len(df_error)} error records")
                            st.dataframe(df_error.head(100), width='stretch')

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


# ========== Export for Main App ==========
# Main function: show_etl_admin_tab()
# Call from app.py ETL Admin tab
