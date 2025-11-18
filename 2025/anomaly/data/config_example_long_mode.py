# =============================================================================
# ตัวอย่าง Configuration สำหรับ Long Format Mode
# =============================================================================
# วิธีใช้: Copy config นี้ไปแทนที่ใน main_audit.py (บรรทัดที่ 8-51)

# --- Input Mode Selection ---
INPUT_MODE = 'long'  # Long Format (แบบเดิม)

# --- For Long Format (แบบเดิม) ---
INPUT_FILE_LONG = "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/Datasource/2025/expense/output/EXPENSE_NT_REPORT_2025.csv"

# --- For Crosstab Format (ไม่ใช้ใน long mode) ---
INPUT_FILE_CROSSTAB = ""
CROSSTAB_SHEET_NAME = 0
CROSSTAB_SKIPROWS = 0
CROSSTAB_MODE = 'auto'
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"

# --- Common Configuration ---
OUTPUT_FILE = "Expense_Audit_Report.xlsx"

COL_YEAR = "YEAR"
COL_MONTH = "MONTH"
TARGET_COL = "EXPENSE_VALUE"
DATE_COL_NAME = "__date_col__"

# --- Configs ---
RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True

# Dimension สำหรับ Crosstab Report
CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
CROSSTAB_MIN_HISTORY = 3

# Dimension สำหรับ Full Audit (Rolling Window)
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_WINDOW = 6

# Dimension สำหรับ Peer Group
AUDIT_PEER_GROUP_BY = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_PEER_ITEM_ID = "COST_CENTER"

# =============================================================================
# หมายเหตุ:
# - ข้อมูล Long Format ต้องมีคอลัมน์: YEAR, MONTH, EXPENSE_VALUE (หรือตาม TARGET_COL)
# - แต่ละแถว = 1 transaction ต่อเดือน
# - ตัวอย่างข้อมูล:
#   YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME_NT1,COST_CENTER,EXPENSE_VALUE
#   2025,1,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,24972.44
#   2025,2,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,248531.76
# =============================================================================
