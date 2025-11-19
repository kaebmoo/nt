# =============================================================================
# ตัวอย่าง Configuration สำหรับ Crosstab Format Mode
# =============================================================================
# วิธีใช้: Copy config นี้ไปแทนที่ใน main_audit.py (บรรทัดที่ 8-51)

# --- Input Mode Selection ---
INPUT_MODE = 'crosstab'  # Crosstab/Pivot Table Format (แบบใหม่)

# --- For Long Format (ไม่ใช้ใน crosstab mode) ---
INPUT_FILE_LONG = ""

# --- For Crosstab Format (แบบใหม่) ---
INPUT_FILE_CROSSTAB = "crosstab_data_example.csv"  # <-- ไฟล์ Crosstab ของคุณ
CROSSTAB_SHEET_NAME = 0                 # Sheet name หรือ index (สำหรับ Excel)
CROSSTAB_SKIPROWS = 0                   # จำนวนแถวที่ข้ามด้านบน
CROSSTAB_MODE = 'auto'                  # 'auto', 'date' (2025-01), 'sequential' (1,2,3 - ยังไม่รองรับ)
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]  # คอลัมน์ dimension
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"   # ชื่อคอลัมน์ค่า

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
# - ข้อมูล Crosstab Format ต้องมี:
#   * คอลัมน์ dimension (เช่น GROUP_NAME, GL_CODE)
#   * คอลัมน์วันที่เป็น column headers (เช่น 2025-01, 2025-02, 2025-03)
#
# - ตัวอย่างข้อมูล Crosstab:
#   GROUP_NAME,GL_CODE,GL_NAME_NT1,2025-01,2025-02,2025-03
#   ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44,248531.76,69566.08
#
# - โปรแกรมจะแปลงเป็น Long Format อัตโนมัติ:
#   YEAR,MONTH,DATE,GROUP_NAME,GL_CODE,GL_NAME_NT1,EXPENSE_VALUE
#   2025,1,2025-01-01,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44
#   2025,2,2025-02-01,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,248531.76
#
# - ไฟล์ชั่วคราว _temp_long_format.csv จะถูกสร้างขึ้น (สามารถลบได้)
#
# - ⚠️ CROSSTAB_MODE:
#   * 'auto' หรือ 'date' = คอลัมน์วันที่ที่ parse ได้ (แนะนำ)
#   * 'sequential' = คอลัมน์ 1,2,3 หรือ ม.ค.,Jan (ยังไม่รองรับใน main_audit.py)
# =============================================================================
