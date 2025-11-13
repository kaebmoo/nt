# 2025/main_audit.py
import pandas as pd
import os
import numpy as np
from anomaly_engine import CrosstabGenerator, FullAuditEngine
from anomaly_reporter import ExcelReporter

# =============================================================================
# ⚙️ USER CONFIGURATION
# =============================================================================

INPUT_FILE = "/Users/seal/Documents/GitHub/nt/2025/data/revenue_mapped_product_2025_.csv"  # <-- เปลี่ยนชื่อไฟล์ข้อมูลของคุณที่นี่
OUTPUT_FILE = "Final_Audit_Report.xlsx"

COL_YEAR = "YEAR"
COL_MONTH = "MONTH"
TARGET_COL = "REVENUE_VALUE"
DATE_COL_NAME = "__date_col__" 

# --- Configs ---
RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True

# Dimension สำหรับ Crosstab Report
# CROSSTAB_DIMENSIONS = ["PRODUCT_KEY", "SUB_PRODUCT_KEY", "GL_CODE"]
CROSSTAB_DIMENSIONS = ["PRODUCT_KEY"]
CROSSTAB_MIN_HISTORY = 3

# Dimension สำหรับ Full Audit (Rolling Window)
# AUDIT_TS_DIMENSIONS = ["PRODUCT_KEY", "SUB_PRODUCT_KEY", "GL_CODE", "COST_CENTER"]
AUDIT_TS_DIMENSIONS = ["PRODUCT_KEY"]
AUDIT_TS_WINDOW = 6

# Dimension สำหรับ Peer Group
# AUDIT_PEER_GROUP_BY = ["PRODUCT_KEY", "GL_CODE"]
AUDIT_PEER_GROUP_BY = ["PRODUCT_KEY"]
AUDIT_PEER_ITEM_ID  = "COST_CENTER"

# =============================================================================

def prepare_data(df):
    print("   running: Data Preprocessing...")
    try:
        # 1. สร้าง Column วันที่
        df[DATE_COL_NAME] = pd.to_datetime(
            df[COL_YEAR].astype(str) + '-' + 
            df[COL_MONTH].astype(int).astype(str).str.zfill(2) + '-01'
        )
        
        # 2. แปลงตัวเลข (รองรับทั้งแบบมี Comma และไม่มี)
        # แปลงเป็น String ก่อน -> ลบ Comma -> แปลงเป็น Numeric
        if df[TARGET_COL].dtype == 'object':
            df[TARGET_COL] = df[TARGET_COL].astype(str).str.replace(',', '', regex=False)
            
        df[TARGET_COL] = pd.to_numeric(df[TARGET_COL], errors='coerce').fillna(0)
        
        print(f"   ✓ Created date & converted numeric.")
    except Exception as e:
        print(f"   ❌ Error: {e}"); return None

    # 3. เติมค่าว่าง Dimension
    all_dims = set(CROSSTAB_DIMENSIONS + AUDIT_TS_DIMENSIONS + AUDIT_PEER_GROUP_BY + [AUDIT_PEER_ITEM_ID])
    for col in all_dims:
        if col in df.columns:
            df[col] = df[col].fillna('N/A')
    
    print("   ✓ Preprocessing complete.")
    return df

def main():
    print("="*60)
    print("🔎 HYBRID ANOMALY AUDIT (v4.0 - With History Highlighting)")
    print("="*60)

    # 1. Load Data
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: ไม่พบไฟล์ '{INPUT_FILE}'"); return
    
    print(f"📂 Loading data: {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    df_clean = prepare_data(df)
    if df_clean is None: return
    
    # 2. Initialize Reporter
    reporter = ExcelReporter(OUTPUT_FILE)
    
    # ตัวแปรเก็บ Log สำหรับนำไปทาสี
    df_ts_log = pd.DataFrame()
    df_peer_log = pd.DataFrame()

    # 3. รัน Full Audit (Scanning ทุกเดือน)
    # จำเป็นต้องรันก่อน เพื่อเอาข้อมูลไป Highlight ใน Crosstab
    if RUN_FULL_AUDIT_LOG or RUN_CROSSTAB_REPORT:
        print("\n--- (Job 1/2) Running Full Audit Engine (All Months) ---")
        full_audit_gen = FullAuditEngine(df_clean.copy())
        
        # 3.1 Time Series (Rolling Window)
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
            print(f"   ✓ Filtered to {len(df_ts_log)} critical anomalies for highlighting")

        # 🔍 DEBUG: แสดง anomalies ทั้งหมด
        '''print("\n📊 DEBUG: Anomaly Details:")
        for idx, row in df_ts_log.iterrows():
            print(f"  - {row[DATE_COL_NAME].strftime('%Y-%m')}: "
                f"{row['PRODUCT_KEY']} = {row[TARGET_COL]:,.2f} "
                f"[{row['ISSUE_DESC']}]")'''
        # 3.2 Peer Group (IsolationForest)
        # df_peer_log = full_audit_gen.audit_peer_group_all_months(
        #     target_col=TARGET_COL,
        #     date_col=DATE_COL_NAME,
        #     group_dims=AUDIT_PEER_GROUP_BY,
        #     item_id_col=AUDIT_PEER_ITEM_ID
        # )
        

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
    # เพิ่ม Log ลง Excel (Sheet 2, 3)
    if RUN_FULL_AUDIT_LOG:
        reporter.add_audit_log_sheet(df_ts_log, "Full_Audit_Log (Time)",
            cols_to_show=[DATE_COL_NAME, 'ISSUE_DESC', TARGET_COL, 'COMPARED_WITH'] + AUDIT_TS_DIMENSIONS)
        # reporter.add_audit_log_sheet(df_peer_log, "Full_Audit_Log (Peer)",
        #     cols_to_show=[DATE_COL_NAME, 'ISSUE_DESC', TARGET_COL, 'COMPARED_WITH'] + AUDIT_PEER_GROUP_BY + [AUDIT_PEER_ITEM_ID])

    # 5. Save Final Report
    reporter.save()
    print("="*60)
    print("✅ DONE! Process finished successfully.")
    print(f"   Report file: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()