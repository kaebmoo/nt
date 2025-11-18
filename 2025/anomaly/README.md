# 🔍 Anomaly Detection System for Financial Data

ระบบตรวจจับความผิดปกติในข้อมูลทางการเงิน (Revenue/Expense) รองรับทั้งข้อมูล **Long Format** และ **Crosstab Format**

**เวอร์ชัน:** v4.1 (Multi-Format Support)
**วันที่:** 2025-01-18
**ผู้พัฒนา:** Claude & seal

---

## 🎯 ความสามารถหลัก

✅ **รองรับ 2 รูปแบบข้อมูล:**
- **Long Format** - ข้อมูลแบบ 1 แถว = 1 transaction ต่อเดือน
- **Crosstab/Pivot Table** - ข้อมูลแบบ 1 แถว = 1 item, เดือนเป็นคอลัมน์

✅ **Data Cleaning:**
- **Accounting Format Support** - รองรับรูปแบบบัญชี
  - Comma: `3,000.00` → `3000.00`
  - Parentheses (negative): `(3000)` → `-3000`
  - Currency: `$1,000`, `฿2,500` → `1000`, `2500`
  - Combined: `(30,000.00)` → `-30000.00`

✅ **Anomaly Detection:**
- **Time Series Analysis** - ตรวจสอบประวัติย้อนหลัง (Rolling Window)
- **Peer Group Comparison** - เปรียบเทียบกับกลุ่มเพื่อน (IsolationForest)
- **IQR-based Detection** - ตรวจจับค่าผิดปกติ (High/Low Spike)

✅ **Excel Report:**
- Crosstab Report พร้อม Highlighting
- Full Audit Log (Time Series)
- Color-coded Anomaly Indicators

---

## 📂 โครงสร้างโปรเจค

```
2025/anomaly/
│
├── 📄 main_audit.py                      # โปรแกรมหลัก (v4.1)
├── 📄 crosstab_converter.py              # ตัวแปลง Crosstab → Long Format
├── 📄 anomaly_engine.py                  # Anomaly Detection Engine
├── 📄 anomaly_reporter.py                # Excel Report Generator
│
├── 📘 README.md                          # คู่มือนี้
├── 📘 QUICK_START.md                     # เริ่มต้นใช้งานอย่างรวดเร็ว
├── 📘 CONFIGURATION_GUIDE.md             # คู่มือการตั้งค่า (Flags, Options)
├── 📘 MAIN_AUDIT_USAGE_GUIDE.md          # คู่มือการใช้งาน main_audit.py
├── 📘 CROSSTAB_CONVERTER_GUIDE.md        # คู่มือการใช้งาน Crosstab Converter
├── 📘 DATA_CLEANING_GUIDE.md             # คู่มือการทำความสะอาดข้อมูล
│
├── 📋 config_example_long_mode.py        # Config สำหรับ Long Format
├── 📋 config_example_crosstab_mode.py    # Config สำหรับ Crosstab Format
│
├── 🧪 test_data_cleaning.py              # ทดสอบ Data Cleaning
│
├── 📊 crosstab_data_example.csv          # ตัวอย่างข้อมูล Crosstab (Date Mode)
├── 📊 example_sequential_numbers.csv     # ตัวอย่าง Sequential (1,2,3)
├── 📊 example_sequential_letters.csv     # ตัวอย่าง Sequential (A,B,C)
└── 📊 example_sequential_thai_months.csv # ตัวอย่าง Sequential (ม.ค., ก.พ.)
```

---

## 🚀 Quick Start

### 1. ติดตั้ง Dependencies

```bash
pip install pandas numpy openpyxl scikit-learn
```

### 2. เลือกโหมดที่ต้องการ

#### 🔹 **Long Format Mode**
```python
# แก้ไขใน main_audit.py
INPUT_MODE = 'long'
INPUT_FILE_LONG = "EXPENSE_NT_REPORT_2025.csv"
```

#### 🔹 **Crosstab Format Mode**
```python
# แก้ไขใน main_audit.py
INPUT_MODE = 'crosstab'
INPUT_FILE_CROSSTAB = "crosstab_data_example.csv"
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"
```

### 3. รันโปรแกรม

```bash
python main_audit.py
```

---

## 📊 รูปแบบข้อมูล

### 1. **Long Format** (แบบเดิม)

```csv
YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME_NT1,COST_CENTER,EXPENSE_VALUE
2025,1,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,24972.44
2025,2,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,248531.76
2025,3,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,CC001,69566.08
```

**ลักษณะ:**
- 1 แถว = 1 transaction ต่อเดือน
- มีคอลัมน์ YEAR, MONTH
- พร้อมใช้งานกับ main_audit.py ทันที

---

### 2. **Crosstab Format** (แบบใหม่)

```csv
GROUP_NAME,GL_CODE,GL_NAME_NT1,2025-01,2025-02,2025-03,2025-04
ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44,248531.76,69566.08,1465986.98
```

**ลักษณะ:**
- 1 แถว = 1 item (Product/Service)
- เดือนเป็นคอลัมน์ (2025-01, 2025-02, ...)
- จะถูกแปลงเป็น Long Format อัตโนมัติ

**รองรับ 2 ประเภท:**

| Mode | Column Headers | ตัวอย่าง |
|------|----------------|----------|
| **Date** | วันที่จริง | `2025-01`, `01/01/2025` |
| **Sequential** | ไม่ใช่วันที่ | `1,2,3`, `A,B,C`, `ม.ค.,Jan` ⚠️ ยังไม่รองรับ |

---

## 🔧 การตั้งค่าหลัก

### พารามิเตอร์สำคัญ

```python
# --- Input Mode ---
INPUT_MODE = 'long' หรือ 'crosstab'

# --- Long Format ---
INPUT_FILE_LONG = "path/to/data.csv"
COL_YEAR = "YEAR"
COL_MONTH = "MONTH"
TARGET_COL = "EXPENSE_VALUE"

# --- Crosstab Format ---
INPUT_FILE_CROSSTAB = "path/to/crosstab.csv"
CROSSTAB_ID_VARS = ["DIM1", "DIM2", "DIM3"]  # คอลัมน์ dimension
CROSSTAB_VALUE_NAME = "EXPENSE_VALUE"
CROSSTAB_MODE = 'auto'  # 'auto', 'date', 'sequential'

# --- Anomaly Detection ---
CROSSTAB_DIMENSIONS = ["DIM1", "DIM2", "DIM3"]
AUDIT_TS_WINDOW = 6  # Rolling window (เดือน)
CROSSTAB_MIN_HISTORY = 3  # ประวัติย้อนหลังขั้นต่ำ
```

---

## 📖 เอกสารเพิ่มเติม

| ไฟล์ | คำอธิบาย |
|------|----------|
| [QUICK_START.md](QUICK_START.md) | เริ่มต้นใช้งานอย่างรวดเร็ว (3 ขั้นตอน) |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | คู่มือการตั้งค่า Flags และ Options |
| [MAIN_AUDIT_USAGE_GUIDE.md](MAIN_AUDIT_USAGE_GUIDE.md) | คู่มือการใช้งาน main_audit.py ฉบับสมบูรณ์ |
| [CROSSTAB_CONVERTER_GUIDE.md](CROSSTAB_CONVERTER_GUIDE.md) | คู่มือการแปลง Crosstab → Long Format |
| [DATA_CLEANING_GUIDE.md](DATA_CLEANING_GUIDE.md) | คู่มือการทำความสะอาดข้อมูลตัวเลข (comma, วงเล็บ) |
| [config_example_long_mode.py](config_example_long_mode.py) | ตัวอย่าง config สำหรับ Long Format |
| [config_example_crosstab_mode.py](config_example_crosstab_mode.py) | ตัวอย่าง config สำหรับ Crosstab Format |
| [test_data_cleaning.py](test_data_cleaning.py) | ทดสอบฟังก์ชัน Data Cleaning |

---

## 🎯 Use Cases

### 1. **Expense Audit (Long Format)**
```bash
# ข้อมูล: EXPENSE_NT_REPORT_2025.csv
INPUT_MODE = 'long'
TARGET_COL = "EXPENSE_VALUE"
```

### 2. **Revenue Audit (Crosstab Format)**
```bash
# ข้อมูล: revenue_crosstab_2025.xlsx
INPUT_MODE = 'crosstab'
CROSSTAB_VALUE_NAME = "REVENUE_VALUE"
```

### 3. **Multi-dimension Analysis**
```bash
# รองรับหลาย dimensions
CROSSTAB_ID_VARS = ["GROUP", "PRODUCT", "REGION", "CHANNEL"]
AUDIT_TS_DIMENSIONS = ["GROUP", "PRODUCT", "REGION"]
```

---

## 🔄 ขั้นตอนการทำงาน

### **Long Format Mode:**
```
1. อ่าน CSV → 2. Preprocess → 3. Anomaly Detection → 4. Excel Report
```

### **Crosstab Format Mode:**
```
1. อ่าน Crosstab
    ↓
2. แปลงเป็น Long Format (_temp_long_format.csv)
    ↓
3. Preprocess
    ↓
4. Anomaly Detection
    ↓
5. Excel Report
```

---

## 📊 Output

### **Excel Report** (`Expense_Audit_Report.xlsx`)

#### Sheet 1: **Crosstab Report**
- Pivot table พร้อมสถานะความผิดปกติ
- Color-coded highlighting:
  - 🔴 สีแดง = High Spike
  - 🟡 สีเหลือง = Low Spike
  - ⚪ สีขาว = Normal

#### Sheet 2: **Full_Audit_Log (Time)**
- รายละเอียด anomalies ทั้งหมด
- คอลัมน์: DATE, ISSUE_DESC, VALUE, COMPARED_WITH, dimensions

---

## ⚠️ ข้อจำกัด

1. **Sequential Mode** (`1,2,3`, `ม.ค.`) ยังไม่รองรับใน `main_audit.py`
   - ใช้ได้เฉพาะใน `crosstab_converter.py`
   - main_audit.py ต้องการ YEAR, MONTH

2. **ไฟล์ชั่วคราว** `_temp_long_format.csv`
   - สร้างขึ้นเมื่อใช้ Crosstab mode
   - สามารถลบได้หลังจากรันเสร็จ

3. **Excel File Size**
   - ข้อมูลขนาดใหญ่มากอาจทำให้ไฟล์ Excel ช้า

---

## 🐛 Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'crosstab_converter'`
**วิธีแก้:** ตรวจสอบว่า `crosstab_converter.py` อยู่ในโฟลเดอร์เดียวกับ `main_audit.py`

### ❌ `ไม่พบคอลัมน์ YEAR, MONTH, DATE`
**วิธีแก้:**
- ตรวจสอบ `CROSSTAB_MODE` = `'date'` หรือ `'auto'`
- คอลัมน์วันที่ต้องเป็นรูปแบบที่ parse ได้ (เช่น `2025-01`)

### ❌ `Sequential mode detected - Cannot create date columns`
**วิธีแก้:**
- ใช้ `CROSSTAB_MODE = 'date'` แทน
- หรือแปลงคอลัมน์ให้เป็นรูปแบบวันที่ก่อน

---

## 🔗 เทคโนโลยีที่ใช้

- **Python 3.x**
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **scikit-learn** - IsolationForest (Peer Group Detection)
- **openpyxl** - Excel report generation

---

## 📞 ติดต่อ / สนับสนุน

- ดูคู่มือเพิ่มเติมใน `MAIN_AUDIT_USAGE_GUIDE.md`
- ดูตัวอย่าง config ใน `config_example_*.py`
- ตรวจสอบไฟล์ตัวอย่างใน `example_*.csv`

---

## 📝 License

Internal use only - National Telecom (NT)

---

## 🎉 Version History

### v4.1.2 (2025-01-18) - **Configurable Analysis**
- ⚙️ เพิ่ม **Configuration Flags** สำหรับควบคุมการวิเคราะห์
  - `RUN_TIME_SERIES_ANALYSIS` - เปิด/ปิด Time Series Analysis
  - `RUN_PEER_GROUP_ANALYSIS` - เปิด/ปิด Peer Group Analysis (ช่วยประหยัดเวลา)
- 📘 สร้าง `CONFIGURATION_GUIDE.md` - คู่มือการตั้งค่า
- 📘 สร้าง `QUICK_START.md` - คู่มือเริ่มต้นใช้งาน
- 🐛 แก้ไข bug: `mode='auto'` ใน crosstab_converter.py

### v4.1.1 (2025-01-18) - **Data Cleaning Enhancement**
- 🧹 เพิ่ม **Accounting Format Support**
  - รองรับ comma: `3,000.00` → `3000.00`
  - รองรับวงเล็บ (ค่าลบ): `(3000)` → `-3000`
  - รองรับสกุลเงิน: `$1,000`, `฿2,500`
  - รองรับรวมกัน: `(30,000.00)` → `-30000.00`
- 📘 สร้าง `DATA_CLEANING_GUIDE.md`
- 🧪 สร้าง `test_data_cleaning.py`

### v4.1 (2025-01-18) - **Multi-Format Support**
- ✨ เพิ่มรองรับ **Crosstab Format**
- ✨ สร้าง `crosstab_converter.py` (Date + Sequential modes)
- ✨ เพิ่ม `INPUT_MODE` configuration
- 📘 สร้างคู่มือการใช้งานครบถ้วน

### v4.0 - **Hybrid Detection**
- ✨ Hybrid Anomaly Detection (Time Series + Peer Group)
- 📊 Excel Report พร้อม Color Highlighting

---

**Happy Auditing! 🚀**
