# 🚀 Quick Start Guide - เริ่มต้นใช้งานอย่างรวดเร็ว

## ⚡ ติดตั้งและใช้งานใน 3 ขั้นตอน

### 1️⃣ ติดตั้ง Dependencies
```bash
pip install pandas numpy openpyxl scikit-learn
```

### 2️⃣ เตรียมข้อมูล

เลือก 1 จาก 2 รูปแบบ:

#### **รูปแบบที่ 1: Long Format** (แบบเดิม)
```csv
YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME_NT1,EXPENSE_VALUE
2025,1,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44
2025,2,ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,248531.76
```

#### **รูปแบบที่ 2: Crosstab Format** (แบบใหม่)
```csv
GROUP_NAME,GL_CODE,GL_NAME_NT1,2025-01,2025-02,2025-03
ค่าซ่อมแซม,51642102,ต-ค่าซ่อม...,24972.44,248531.76,69566.08
```

### 3️⃣ แก้ไข Config และรัน

#### สำหรับ **Long Format:**
```python
# main_audit.py (บรรทัด 13)
INPUT_MODE = 'long'
INPUT_FILE_LONG = "path/to/your/data.csv"
```

#### สำหรับ **Crosstab Format:**
```python
# main_audit.py (บรรทัด 13)
INPUT_MODE = 'crosstab'
INPUT_FILE_CROSSTAB = "path/to/your/crosstab.csv"
CROSSTAB_ID_VARS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
```

#### รันโปรแกรม:
```bash
python main_audit.py
```

---

## 📊 ข้อมูลที่รองรับ

### ✅ รูปแบบตัวเลข (Data Cleaning)
| รูปแบบ | ผลลัพธ์ | หมายเหตุ |
|--------|---------|----------|
| `3,000.00` | `3000.00` | ลบ comma |
| `(3000)` | `-3000.00` | วงเล็บ = ค่าลบ |
| `(30,000)` | `-30000.00` | รวมกัน |
| `$1,000` | `1000.00` | ลบสกุลเงิน |
| `฿2,500` | `2500.00` | รองรับบาท |

### ✅ รูปแบบ Column (Crosstab)
| Mode | Column Headers | รองรับ |
|------|----------------|--------|
| `date` | `2025-01`, `01/01/2025` | ✅ |
| `sequential` | `1,2,3`, `A,B,C`, `ม.ค.` | ⚠️ ยังไม่รองรับใน main_audit.py |

---

## 📤 Output

ไฟล์ Excel ที่ชื่อ `Expense_Audit_Report.xlsx`:
- **Sheet 1:** Crosstab Report (พร้อม Anomaly Highlighting)
- **Sheet 2:** Full Audit Log (Time Series)

---

## 🔍 ตัวอย่างการใช้งาน

### ตัวอย่างที่ 1: Expense Audit (Long Format)
```bash
# 1. เปิด main_audit.py
# 2. แก้ไข:
INPUT_MODE = 'long'
INPUT_FILE_LONG = "EXPENSE_NT_REPORT_2025.csv"
TARGET_COL = "EXPENSE_VALUE"

# 3. รัน:
python main_audit.py
```

### ตัวอย่างที่ 2: Revenue Audit (Crosstab)
```bash
# 1. เปิด main_audit.py
# 2. แก้ไข:
INPUT_MODE = 'crosstab'
INPUT_FILE_CROSSTAB = "revenue_crosstab_2025.xlsx"
CROSSTAB_ID_VARS = ["SERVICE_GROUP", "SERVICE_CODE"]
CROSSTAB_VALUE_NAME = "REVENUE_VALUE"
TARGET_COL = "REVENUE_VALUE"

# 3. รัน:
python main_audit.py
```

---

## ⚙️ Configuration ที่สำคัญ

### ต้องแก้ไขเสมอ:
```python
INPUT_MODE = 'long'  # หรือ 'crosstab'
INPUT_FILE_LONG = "your_file.csv"  # (สำหรับ long mode)
INPUT_FILE_CROSSTAB = "your_file.csv"  # (สำหรับ crosstab mode)
TARGET_COL = "EXPENSE_VALUE"  # หรือ "REVENUE_VALUE"
```

### อาจปรับแต่ง (Optional):
```python
# Dimension columns
CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]

# Detection parameters
AUDIT_TS_WINDOW = 6  # Rolling window (เดือน)
CROSSTAB_MIN_HISTORY = 3  # ประวัติย้อนหลังขั้นต่ำ
```

---

## 🐛 แก้ปัญหาพื้นฐาน

### ❌ `ไม่พบไฟล์`
**วิธีแก้:** ตรวจสอบ path ของไฟล์ให้ถูกต้อง
```python
# ใช้ absolute path
INPUT_FILE_LONG = "/Users/seal/data/EXPENSE_2025.csv"
```

### ❌ `ModuleNotFoundError`
**วิธีแก้:** ติดตั้ง dependencies
```bash
pip install pandas numpy openpyxl scikit-learn
```

### ❌ `ไม่พบคอลัมน์ YEAR, MONTH`
**วิธีแก้:**
- ตรวจสอบข้อมูลมีคอลัมน์ YEAR, MONTH
- หรือใช้ Crosstab mode แทน

### ❌ `Sequential mode detected`
**วิธีแก้:**
- ใช้ `CROSSTAB_MODE = 'date'` แทน 'sequential'
- หรือแปลง column headers เป็นรูปแบบวันที่

---

## 📘 เอกสารเพิ่มเติม

| เอกสาร | เหมาะสำหรับ |
|--------|-------------|
| [README.md](README.md) | ภาพรวมโปรเจค |
| [MAIN_AUDIT_USAGE_GUIDE.md](MAIN_AUDIT_USAGE_GUIDE.md) | การใช้งาน main_audit.py แบบละเอียด |
| [CROSSTAB_CONVERTER_GUIDE.md](CROSSTAB_CONVERTER_GUIDE.md) | การแปลง Crosstab → Long |
| [DATA_CLEANING_GUIDE.md](DATA_CLEANING_GUIDE.md) | การทำความสะอาดข้อมูล |

---

## 🧪 ทดสอบฟังก์ชัน

```bash
# ทดสอบ Data Cleaning
python test_data_cleaning.py

# ทดสอบกับข้อมูลตัวอย่าง
python main_audit.py  # (ใช้ crosstab_data_example.csv)
```

---

## 💡 Tips

1. **ใช้ Long Format** ถ้าข้อมูลมี YEAR, MONTH อยู่แล้ว → เร็วกว่า
2. **ใช้ Crosstab Mode** ถ้าข้อมูลเป็น Pivot Table จาก Excel
3. **ตรวจสอบ Output** ที่ `_temp_long_format.csv` (สำหรับ Crosstab mode)
4. **ปรับ Dimensions** ให้ตรงกับข้อมูลของคุณ
5. **อ่าน Error Message** - โปรแกรมจะบอกว่าขาดอะไร

---

**Happy Auditing! 🚀**

*สร้างโดย: Claude | วันที่: 2025-01-18 | เวอร์ชัน: v4.1.1*
