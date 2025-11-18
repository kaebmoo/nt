# 2025/main_audit.py
import pandas as pd
import os
import numpy as np
from anomaly_engine import CrosstabGenerator, FullAuditEngine
from anomaly_reporter import ExcelReporter

# =============================================================================
# ⚙️ USER CONFIGURATION
# =============================================================================

# --- Input Mode Selection ---
INPUT_MODE = 'long'  # 'long' = Long Format (แบบเดิม) | 'crosstab' = Crosstab/Pivot Table (แบบใหม่)

# --- For Long Format (แบบเดิม) ---
INPUT_FILE_LONG = "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/Datasource/all/expense/EXPENSE_NT_REPORT_2024.csv"

# --- For Crosstab Format (แบบใหม่) ---
INPUT_FILE_CROSSTAB = "crosstab_data_example.csv"  # <-- ไฟล์ Crosstab ของคุณ
CROSSTAB_SHEET_NAME = 0                 # Sheet name หรือ index (สำหรับ Excel)
CROSSTAB_SKIPROWS = 0                   # จำนวนแถวที่ข้ามด้านบน
CROSSTAB_MODE = 'auto'                  # 'auto', 'date' (2025-01), 'sequential' (1,2,3 หรือ ม.ค.)
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]  # คอลัมน์ dimension
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"   # ชื่อคอลัมน์ค่า

# --- Common Configuration ---
OUTPUT_FILE = "data/Expense_Audit_Report_2024.xlsx"

COL_YEAR = "YEAR"
COL_MONTH = "MONTH"
TARGET_COL = "EXPENSE_VALUE"
DATE_COL_NAME = "__date_col__" 

# --- Configs ---
RUN_CROSSTAB_REPORT = True      # สร้าง Crosstab Report (Sheet 1)
RUN_FULL_AUDIT_LOG = True       # บันทึก Audit Log ลง Excel (Sheet 2, 3)

# --- Anomaly Detection Options ---
RUN_TIME_SERIES_ANALYSIS = True     # Time Series (Rolling Window) - เทียบกับอดีตของตัวเอง
RUN_PEER_GROUP_ANALYSIS = True     # Peer Group (IsolationForest) - เทียบกับกลุ่มเพื่อน ⚠️ ใช้เวลานาน

# Dimension สำหรับ Crosstab Report
# CROSSTAB_DIMENSIONS = ["PRODUCT_KEY", "SUB_PRODUCT_KEY", "GL_CODE"]
CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME"]
CROSSTAB_MIN_HISTORY = 3

# Dimension สำหรับ Full Audit (Rolling Window)
# AUDIT_TS_DIMENSIONS = ["PRODUCT_KEY", "SUB_PRODUCT_KEY", "GL_CODE", "COST_CENTER"]
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME"]
AUDIT_TS_WINDOW = 6

# Dimension สำหรับ Peer Group
# AUDIT_PEER_GROUP_BY = ["PRODUCT_KEY", "GL_CODE"]
AUDIT_PEER_GROUP_BY = ["GROUP_NAME", "GL_CODE", "GL_NAME"]
AUDIT_PEER_ITEM_ID  = "COST_CENTER"

# =============================================================================

def clean_numeric_column(series):
    """
    ทำความสะอาดคอลัมน์ตัวเลข รองรับรูปแบบบัญชี

    รองรับ:
    - Comma: 3,000.00 → 3000.00
    - Parentheses (negative): (3000) → -3000
    - Combined: (30,000.00) → -30000.00
    - Whitespace: " 3000 " → 3000
    - Currency: $3,000 หรือ ฿3,000 → 3000

    Examples:
    - "3,000.00" → 3000.00
    - "(3,000)" → -3000.00
    - "(30,000.00)" → -30000.00
    - "$ 1,234.56" → 1234.56
    """
    # แปลงเป็น string
    s = series.astype(str)

    # ตรวจสอบวงเล็บ (ค่าลบในระบบบัญชี)
    # วงเล็บในบัญชี เช่น (3000) หมายถึง -3000
    is_negative = s.str.contains(r'\(.*\)', regex=True, na=False)

    # ลบอักขระพิเศษ (เว้น . และ -)
    # ลบ: comma, วงเล็บ, ช่องว่าง, สกุลเงิน, เปอร์เซ็นต์
    s = s.str.replace(r'[,\(\)\s$฿%]', '', regex=True)

    # แปลงเป็นตัวเลข
    s = pd.to_numeric(s, errors='coerce').fillna(0)

    # ใส่เครื่องหมายลบสำหรับค่าที่อยู่ในวงเล็บ
    s.loc[is_negative] = -s.loc[is_negative].abs()

    return s

def prepare_data(df):
    print("   running: Data Preprocessing...")
    try:
        # 1. สร้าง Column วันที่
        # ตรวจสอบว่ามี YEAR, MONTH หรือไม่ (สำหรับ date mode)
        if COL_YEAR in df.columns and COL_MONTH in df.columns:
            df[DATE_COL_NAME] = pd.to_datetime(
                df[COL_YEAR].astype(str) + '-' +
                df[COL_MONTH].astype(int).astype(str).str.zfill(2) + '-01'
            )
            print(f"   ✓ Created date from YEAR, MONTH columns")

        # ถ้าไม่มี YEAR, MONTH แต่มี DATE (จาก crosstab date mode)
        elif 'DATE' in df.columns:
            df[DATE_COL_NAME] = pd.to_datetime(df['DATE'])
            # สร้าง YEAR, MONTH จาก DATE
            df[COL_YEAR] = df[DATE_COL_NAME].dt.year
            df[COL_MONTH] = df[DATE_COL_NAME].dt.month
            print(f"   ✓ Created YEAR, MONTH from DATE column")

        # ถ้ามี PERIOD (จาก crosstab sequential mode)
        elif 'PERIOD' in df.columns:
            print(f"   ⚠ Warning: Sequential mode detected (PERIOD column)")
            print(f"   ⚠ Cannot create date columns - PERIOD will be used as-is")
            print(f"   ⚠ Note: Some features may not work correctly")
            # ไม่สามารถสร้าง DATE ได้ - ต้องให้ผู้ใช้จัดการเอง
            # หรืออาจจะให้ error
            return None

        else:
            print(f"   ❌ Error: ไม่พบคอลัมน์ YEAR, MONTH, DATE, หรือ PERIOD")
            return None

        # 2. แปลงตัวเลข (รองรับรูปแบบบัญชี: comma, วงเล็บ)
        if TARGET_COL in df.columns:
            df[TARGET_COL] = clean_numeric_column(df[TARGET_COL])
            print(f"   ✓ Converted {TARGET_COL} to numeric (accounting format supported)")
        else:
            print(f"   ❌ Error: ไม่พบคอลัมน์ {TARGET_COL}")
            return None

    except Exception as e:
        print(f"   ❌ Error: {e}"); return None

    # 3. เติมค่าว่าง Dimension
    all_dims = set(CROSSTAB_DIMENSIONS + AUDIT_TS_DIMENSIONS + AUDIT_PEER_GROUP_BY + [AUDIT_PEER_ITEM_ID])
    for col in all_dims:
        if col in df.columns:
            df[col] = df[col].fillna('N/A')
    
    print("   ✓ Preprocessing complete.")
    return df

def load_data():
    """
    โหลดข้อมูลตาม INPUT_MODE
    - 'long': อ่าน CSV แบบ Long Format โดยตรง
    - 'crosstab': แปลง Crosstab → Long Format ก่อน
    """
    print("\n📂 Loading data...")

    if INPUT_MODE == 'crosstab':
        print(f"   Mode: Crosstab Format")
        print(f"   Converting: {INPUT_FILE_CROSSTAB} → Long Format...")

        # ตรวจสอบไฟล์
        if not os.path.exists(INPUT_FILE_CROSSTAB):
            print(f"❌ Error: ไม่พบไฟล์ '{INPUT_FILE_CROSSTAB}'")
            return None

        # Import crosstab_converter
        try:
            from crosstab_converter import CrosstabConverter
        except ImportError:
            print("❌ Error: ไม่พบ crosstab_converter.py")
            print("   กรุณาตรวจสอบว่าไฟล์อยู่ในโฟลเดอร์เดียวกัน")
            return None

        # แปลง Crosstab → Long
        temp_output = "_temp_long_format.csv"
        converter = CrosstabConverter(
            input_file=INPUT_FILE_CROSSTAB,
            output_file=temp_output
        )

        try:
            converter.convert(
                sheet_name=CROSSTAB_SHEET_NAME,
                skiprows=CROSSTAB_SKIPROWS,
                id_vars=CROSSTAB_ID_VARS,
                value_name=CROSSTAB_VALUE_NAME,
                mode=CROSSTAB_MODE
            )

            # อ่านไฟล์ที่แปลงแล้ว
            df = pd.read_csv(temp_output)
            print(f"   ✓ Converted successfully: {len(df):,} rows")

            # ลบไฟล์ temp (optional - comment out ถ้าต้องการเก็บไว้ดู)
            # os.remove(temp_output)

            return df

        except Exception as e:
            print(f"❌ Error during conversion: {e}")
            return None

    elif INPUT_MODE == 'long':
        print(f"   Mode: Long Format (Direct)")

        if not os.path.exists(INPUT_FILE_LONG):
            print(f"❌ Error: ไม่พบไฟล์ '{INPUT_FILE_LONG}'")
            return None

        print(f"   Loading: {INPUT_FILE_LONG}...")
        df = pd.read_csv(INPUT_FILE_LONG)
        print(f"   ✓ Loaded: {len(df):,} rows")
        return df

    else:
        print(f"❌ Error: INPUT_MODE ไม่ถูกต้อง (ต้องเป็น 'long' หรือ 'crosstab')")
        return None

def main():
    print("="*60)
    print("🔎 HYBRID ANOMALY AUDIT (v4.1 - Multi-Format Support)")
    print("="*60)

    # 1. Load Data (รองรับทั้ง Long และ Crosstab)
    df = load_data()
    if df is None: return

    df_clean = prepare_data(df)
    if df_clean is None: return
    
    # 2. Initialize Reporter
    reporter = ExcelReporter(OUTPUT_FILE)
    
    # ตัวแปรเก็บ Log สำหรับนำไปทาสี
    df_ts_log = pd.DataFrame()
    df_peer_log = pd.DataFrame()

    # 3. รัน Full Audit (Scanning ทุกเดือน)
    # จำเป็นต้องรันก่อน เพื่อเอาข้อมูลไป Highlight ใน Crosstab
    if RUN_TIME_SERIES_ANALYSIS or RUN_PEER_GROUP_ANALYSIS:
        print("\n--- (Job 1/2) Running Full Audit Engine (All Months) ---")
        full_audit_gen = FullAuditEngine(df_clean.copy())

        # 3.1 Time Series (Rolling Window)
        if RUN_TIME_SERIES_ANALYSIS:
            print("   🔄 Running Time Series Analysis (Rolling Window)...")
            df_ts_log = full_audit_gen.audit_time_series_all_months(
                target_col=TARGET_COL,
                date_col=DATE_COL_NAME,
                dimensions=AUDIT_TS_DIMENSIONS,
                window=AUDIT_TS_WINDOW
            )
            # ✅ กรองเฉพาะปัญหาสำคัญ
            if not df_ts_log.empty:
                # เอาเฉพาะ Critical
                df_ts_log = df_ts_log[
                    df_ts_log['ISSUE_DESC'].isin([
                        'High_Spike', 'Low_Spike', 'Negative_Value'
                    ])
                ].copy()
                print(f"   ✓ Time Series: Found {len(df_ts_log)} critical anomalies")
            else:
                print(f"   ✓ Time Series: No anomalies detected")
        else:
            print("   ⏭️  Time Series Analysis: Skipped (RUN_TIME_SERIES_ANALYSIS = False)")

        # 3.2 Peer Group (IsolationForest)
        if RUN_PEER_GROUP_ANALYSIS:
            print("   🔄 Running Peer Group Analysis (IsolationForest)...")
            print("   ⚠️  This may take a while for large datasets...")
            df_peer_log = full_audit_gen.audit_peer_group_all_months(
                target_col=TARGET_COL,
                date_col=DATE_COL_NAME,
                group_dims=AUDIT_PEER_GROUP_BY,
                item_id_col=AUDIT_PEER_ITEM_ID
            )
            if not df_peer_log.empty:
                print(f"   ✓ Peer Group: Found {len(df_peer_log)} anomalies")
            else:
                print(f"   ✓ Peer Group: No anomalies detected")
        else:
            print("   ⏭️  Peer Group Analysis: Skipped (RUN_PEER_GROUP_ANALYSIS = False)")
    else:
        print("\n--- Anomaly Detection: Skipped (All analysis disabled) ---")
        

    # 4. รัน Crosstab Report (Sheet 1)
    if RUN_CROSSTAB_REPORT:
        print("\n--- (Job 2/2) Running Crosstab Report (Latest Month) ---")
        crosstab_gen = CrosstabGenerator(df_clean.copy(), CROSSTAB_MIN_HISTORY)
        
        df_crosstab = crosstab_gen.create_report(
            target_col=TARGET_COL,
            date_col=DATE_COL_NAME,
            dimensions=CROSSTAB_DIMENSIONS
        )
        
        # [สำคัญ] ส่ง df_ts_log เข้าไปเพื่อช่วยทาสี Cell ในอดีต
        reporter.add_crosstab_sheet(
            df_report=df_crosstab,
            df_anomaly_log=df_ts_log,
            dimensions=CROSSTAB_DIMENSIONS,
            date_col_name=DATE_COL_NAME,
            date_cols_sorted=crosstab_gen.date_cols_sorted
        )

    # 5. รัน Peer Group Crosstab Report (ถ้ามีข้อมูล Peer Anomaly)
    if RUN_PEER_GROUP_ANALYSIS and not df_peer_log.empty:
        print("\n--- (Job 2.5/2) Adding Peer Group Crosstab Report ---")
        reporter.add_peer_crosstab_sheet(
            df_clean=df_clean,
            df_peer_log=df_peer_log,
            group_dims=AUDIT_PEER_GROUP_BY,
            item_id_col=AUDIT_PEER_ITEM_ID,
            target_col=TARGET_COL,
            date_col=DATE_COL_NAME
        )
        print(f"   ✓ Added Peer Group Crosstab sheet")

    # เพิ่ม Log ลง Excel (Sheet 2, 3)
    if RUN_FULL_AUDIT_LOG:
        # Time Series Log
        if RUN_TIME_SERIES_ANALYSIS and not df_ts_log.empty:
            reporter.add_audit_log_sheet(df_ts_log, "Full_Audit_Log (Time)",
                cols_to_show=[DATE_COL_NAME, 'ISSUE_DESC', TARGET_COL, 'COMPARED_WITH'] + AUDIT_TS_DIMENSIONS)
            print(f"   ✓ Added Time Series Log sheet ({len(df_ts_log)} rows)")

        # Peer Group Log
        if RUN_PEER_GROUP_ANALYSIS and not df_peer_log.empty:
            reporter.add_audit_log_sheet(df_peer_log, "Full_Audit_Log (Peer)",
                cols_to_show=[DATE_COL_NAME, 'ISSUE_DESC', TARGET_COL, 'COMPARED_WITH'] + AUDIT_PEER_GROUP_BY + [AUDIT_PEER_ITEM_ID])
            print(f"   ✓ Added Peer Group Log sheet ({len(df_peer_log)} rows)")

    # 5. Save Final Report
    reporter.save()
    print("="*60)
    print("✅ DONE! Process finished successfully.")
    print(f"   Report file: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()