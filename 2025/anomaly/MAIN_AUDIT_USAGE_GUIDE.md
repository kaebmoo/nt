# 📊 main_audit.py - คู่มือการใช้งาน v4.1

## 🎯 ความสามารถใหม่

**รองรับ 2 รูปแบบข้อมูล:**
1. **Long Format** (แบบเดิม) - อ่าน CSV ที่เป็น Long Format โดยตรง
2. **Crosstab Format** (แบบใหม่) - แปลง Crosstab/Pivot Table → Long Format อัตโนมัติ

---

## 🔧 Configuration

### 📋 ตัวเลือกหลัก

```python
# --- Input Mode Selection ---
INPUT_MODE = 'long'  # หรือ 'crosstab'
```

| Mode | คำอธิบาย | เหมาะกับ |
|------|----------|----------|
| `'long'` | อ่าน CSV/Excel ที่เป็น Long Format | ข้อมูลที่มี 1 แถว = 1 transaction ต่อเดือน |
| `'crosstab'` | แปลง Crosstab → Long แล้วประมวลผล | รายงานที่มี 1 แถว = 1 item, เดือนเป็นคอลัมน์ |

---

## 📝 วิธีใช้งาน

### 1️⃣ **Long Format Mode** (แบบเดิม)

#### ข้อมูลตัวอย่าง:
```csv
YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME_NT1,COST_CENTER,EXPENSE_VALUE
2025,1,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,24972.44
2025,2,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,248531.76
```

#### การตั้งค่า:
```python
# main_audit.py

INPUT_MODE = 'long'

INPUT_FILE_LONG = "/path/to/EXPENSE_NT_REPORT_2025.csv"
OUTPUT_FILE = "Expense_Audit_Report.xlsx"

TARGET_COL = "EXPENSE_VALUE"
COL_YEAR = "YEAR"
COL_MONTH = "MONTH"

CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_PEER_GROUP_BY = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_PEER_ITEM_ID = "COST_CENTER"
```

#### รันโปรแกรม:
```bash
python main_audit.py
```

---

### 2️⃣ **Crosstab Format Mode** (แบบใหม่)

#### ข้อมูลตัวอย่าง:
```csv
GROUP_NAME,GL_CODE,GL_NAME_NT1,2025-01,2025-02,2025-03,2025-04
ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44,248531.76,69566.08,1465986.98
```

#### การตั้งค่า:
```python
# main_audit.py

INPUT_MODE = 'crosstab'

# --- For Crosstab Format ---
INPUT_FILE_CROSSTAB = "crosstab_data_example.csv"
CROSSTAB_SHEET_NAME = 0                 # สำหรับ Excel: sheet name หรือ index
CROSSTAB_SKIPROWS = 0                   # ข้ามแถวบน (ถ้ามี header พิเศษ)
CROSSTAB_MODE = 'auto'                  # 'auto', 'date', 'sequential'
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"

# --- Common Configuration ---
OUTPUT_FILE = "Expense_Audit_Report.xlsx"
TARGET_COL = "EXPENSE_VALUE"

CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
```

#### รันโปรแกรม:
```bash
python main_audit.py
```

---

## 🎛️ Crosstab Mode Options

### `CROSSTAB_MODE` - เลือกประเภทคอลัมน์วันที่

| Mode | คอลัมน์วันที่ | ผลลัพธ์ |
|------|---------------|----------|
| `'auto'` | ตรวจสอบอัตโนมัติ | แนะนำ (ให้โปรแกรมเลือกเอง) |
| `'date'` | `2025-01`, `01/01/2025` | สร้าง YEAR, MONTH, DATE |
| `'sequential'` | `1,2,3` หรือ `ม.ค.,Jan` | ⚠️ ยังไม่รองรับใน main_audit.py |

**⚠️ หมายเหตุ:**
- ปัจจุบัน `main_audit.py` รองรับเฉพาะ **date mode** เท่านั้น
- ถ้าใช้ `sequential` mode จะได้ PERIOD แทน YEAR/MONTH และโปรแกรมจะ error

---

## 📂 โครงสร้างไฟล์

```
2025/anomaly/
├── main_audit.py              # โปรแกรมหลัก (v4.1)
├── crosstab_converter.py      # ตัวแปลง Crosstab → Long
├── anomaly_engine.py          # Anomaly detection engine
├── anomaly_reporter.py        # Excel reporter
├── crosstab_data_example.csv  # ตัวอย่างข้อมูล Crosstab
└── MAIN_AUDIT_USAGE_GUIDE.md  # คู่มือนี้
```

---

## 🔄 ขั้นตอนการทำงาน (Crosstab Mode)

```
1. อ่านไฟล์ Crosstab (Excel/CSV)
         ↓
2. แปลงเป็น Long Format (ใช้ crosstab_converter.py)
         ↓
3. บันทึกเป็น _temp_long_format.csv
         ↓
4. ประมวลผล Anomaly Detection
         ↓
5. สร้าง Excel Report
```

---

## 🧪 ตัวอย่างการใช้งาน

### ตัวอย่างที่ 1: Revenue Report (Crosstab)

```python
INPUT_MODE = 'crosstab'
INPUT_FILE_CROSSTAB = "revenue_crosstab_2025.xlsx"
CROSSTAB_SHEET_NAME = "Sheet1"
CROSSTAB_ID_VARS = ["SERVICE_GROUP", "SERVICE_CODE", "SERVICE_NAME"]
CROSSTAB_VALUE_NAME = "REVENUE_VALUE"
CROSSTAB_MODE = 'date'

TARGET_COL = "REVENUE_VALUE"
OUTPUT_FILE = "Revenue_Audit_Report.xlsx"
```

### ตัวอย่างที่ 2: Expense Report (Long Format)

```python
INPUT_MODE = 'long'
INPUT_FILE_LONG = "EXPENSE_NT_REPORT_2025.csv"
TARGET_COL = "EXPENSE_VALUE"
OUTPUT_FILE = "Expense_Audit_Report.xlsx"
```

---

## ⚙️ ข้อกำหนดเบื้องต้น

### ไฟล์ที่ต้องมี:
```bash
pip install pandas numpy openpyxl scikit-learn
```

### ไฟล์ Python ที่จำเป็น:
- `main_audit.py`
- `crosstab_converter.py` (สำหรับ Crosstab mode)
- `anomaly_engine.py`
- `anomaly_reporter.py`

---

## 🐛 Troubleshooting

### ปัญหา: `ModuleNotFoundError: No module named 'crosstab_converter'`
**วิธีแก้:** ตรวจสอบว่า `crosstab_converter.py` อยู่ในโฟลเดอร์เดียวกับ `main_audit.py`

### ปัญหา: `ไม่พบคอลัมน์ YEAR, MONTH, DATE`
**วิธีแก้:**
1. ตรวจสอบ `CROSSTAB_MODE` ว่าเป็น `'date'` หรือ `'auto'`
2. ตรวจสอบว่าคอลัมน์วันที่เป็นรูปแบบที่ parse ได้ (เช่น `2025-01`, `01/01/2025`)

### ปัญหา: `Sequential mode detected - Cannot create date columns`
**วิธีแก้:**
- Crosstab sequential mode (`1,2,3`, `ม.ค.`) ยังไม่รองรับใน `main_audit.py`
- ใช้ `CROSSTAB_MODE = 'date'` แทน
- หรือแปลงคอลัมน์ให้เป็นรูปแบบวันที่ก่อน

---

## 📊 Output

โปรแกรมจะสร้างไฟล์ Excel ที่ชื่อตาม `OUTPUT_FILE`:

### Sheet 1: Crosstab Report
- แสดงผล Crosstab พร้อม ANOMALY_STATUS
- Highlight สีตาม severity (สีแดง = High Spike, สีเหลือง = Low Spike)

### Sheet 2: Full_Audit_Log (Time)
- รายละเอียด Anomaly ทั้งหมดจาก Time Series analysis
- มีคอลัมน์: DATE, ISSUE_DESC, VALUE, COMPARED_WITH, dimensions

---

## 🔗 ดูเพิ่มเติม

- **crosstab_converter.py** - คู่มือการแปลง Crosstab → Long
- **CROSSTAB_CONVERTER_GUIDE.md** - คู่มือการใช้งาน Crosstab Converter
- **anomaly_engine.py** - เอกสาร API สำหรับ Anomaly Detection

---

**สร้างโดย:** Claude
**วันที่:** 2025-01-18
**เวอร์ชัน:** v4.1 (Multi-Format Support)
