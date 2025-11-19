# ⚙️ Configuration Guide - คู่มือการตั้งค่า

## 📋 ภาพรวม

ไฟล์ `main_audit.py` มี configuration flags ที่สามารถปรับแต่งได้ตามต้องการ

---

## 🎛️ Configuration Flags

### 1. **Input Mode Selection**

```python
INPUT_MODE = 'long'  # หรือ 'crosstab'
```

| Mode | คำอธิบาย | ใช้เมื่อไร |
|------|----------|-----------|
| `'long'` | อ่าน CSV แบบ Long Format | ข้อมูลมี YEAR, MONTH อยู่แล้ว |
| `'crosstab'` | แปลง Crosstab → Long ก่อน | ข้อมูลเป็น Pivot Table |

---

### 2. **Report Options**

```python
RUN_CROSSTAB_REPORT = True      # สร้าง Crosstab Report (Sheet 1)
RUN_FULL_AUDIT_LOG = True       # บันทึก Audit Log ลง Excel (Sheet 2, 3)
```

| Flag | คำอธิบาย | Output |
|------|----------|--------|
| `RUN_CROSSTAB_REPORT` | สร้าง Crosstab Report พร้อม Highlighting | Sheet 1: Crosstab Report |
| `RUN_FULL_AUDIT_LOG` | บันทึก Anomaly Log ลง Excel | Sheet 2-3: Audit Logs |

---

### 3. **Anomaly Detection Options** ⭐ **ใหม่!**

```python
RUN_TIME_SERIES_ANALYSIS = True     # Time Series (Rolling Window)
RUN_PEER_GROUP_ANALYSIS = False     # Peer Group (IsolationForest) ⚠️ ใช้เวลานาน
```

| Flag | วิธีวิเคราะห์ | เปรียบเทียบกับ | เวลา | แนะนำ |
|------|--------------|----------------|------|-------|
| `RUN_TIME_SERIES_ANALYSIS` | Rolling Window + IQR | อดีตของตัวเอง (6 เดือนก่อน) | ⚡ เร็ว | ✅ เปิดเสมอ |
| `RUN_PEER_GROUP_ANALYSIS` | IsolationForest | กลุ่มเพื่อนในเดือนเดียวกัน | ⏰ ช้า | ⚠️ เปิดเมื่อจำเป็น |

---

## 🎯 Scenarios การใช้งาน

### **Scenario 1: การใช้งานปกติ (เร็ว)** ⚡

```python
RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True
RUN_TIME_SERIES_ANALYSIS = True     # ✅ เปิด
RUN_PEER_GROUP_ANALYSIS = False     # ❌ ปิด (ประหยัดเวลา)
```

**ผลลัพธ์:**
- Sheet 1: Crosstab Report (พร้อม Highlighting)
- Sheet 2: Time Series Audit Log
- เวลา: **3-5 นาที** (ข้อมูล 10,000 rows)

---

### **Scenario 2: การวิเคราะห์แบบละเอียด (ช้า)** ⏰

```python
RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True
RUN_TIME_SERIES_ANALYSIS = True     # ✅ เปิด
RUN_PEER_GROUP_ANALYSIS = True      # ✅ เปิด (ใช้เวลานาน)
```

**ผลลัพธ์:**
- Sheet 1: Crosstab Report
- Sheet 2: Time Series Audit Log
- Sheet 3: Peer Group Audit Log
- เวลา: **10-30 นาที** (ข้อมูล 10,000 rows)

---

### **Scenario 3: เฉพาะ Crosstab Report (เร็วที่สุด)** ⚡⚡

```python
RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = False          # ❌ ปิด
RUN_TIME_SERIES_ANALYSIS = True     # ✅ เปิด (สำหรับ Highlighting)
RUN_PEER_GROUP_ANALYSIS = False     # ❌ ปิด
```

**ผลลัพธ์:**
- Sheet 1: Crosstab Report (มี Highlighting)
- ไม่มี Audit Log sheets
- เวลา: **2-3 นาที**

---

### **Scenario 4: เฉพาะ Peer Group (ทดสอบ)** 🧪

```python
RUN_CROSSTAB_REPORT = False
RUN_FULL_AUDIT_LOG = True
RUN_TIME_SERIES_ANALYSIS = False    # ❌ ปิด
RUN_PEER_GROUP_ANALYSIS = True      # ✅ เปิด
```

**ผลลัพธ์:**
- Sheet 1: Peer Group Audit Log
- ไม่มี Crosstab Report
- เวลา: **8-20 นาที**

---

## ⏱️ เวลาในการประมวลผล (ประมาณการ)

| ข้อมูล | Time Series | Peer Group | รวม |
|--------|-------------|------------|-----|
| 1,000 rows | 30 วินาที | 2-3 นาที | 2-3 นาที |
| 5,000 rows | 1-2 นาที | 5-10 นาที | 6-12 นาที |
| 10,000 rows | 3-5 นาที | 10-20 นาที | 13-25 นาที |
| 50,000 rows | 10-15 นาที | 30-60 นาที | 40-75 นาที |

---

## 💡 คำแนะนำ

### ✅ **แนะนำให้เปิด:**
- `RUN_TIME_SERIES_ANALYSIS = True` - เร็ว แม่นยำ จับ anomaly ได้ดี
- `RUN_CROSSTAB_REPORT = True` - มี Highlighting สวย ดูง่าย

### ⚠️ **ระวังเมื่อเปิด:**
- `RUN_PEER_GROUP_ANALYSIS = True` - ใช้เวลานาน ✋ เปิดเมื่อ:
  - ต้องการหา outliers เทียบกับกลุ่มเพื่อน
  - มีเวลาประมวลผล
  - ข้อมูลมี item หลายรายการในแต่ละกลุ่ม

### 🚫 **สามารถปิดได้:**
- `RUN_FULL_AUDIT_LOG = False` - ถ้าต้องการแค่ Crosstab Report

---

## 🔧 Dimensions Configuration

### **Time Series Dimensions**
```python
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_WINDOW = 6  # เทียบกับ 6 เดือนก่อน
```

### **Peer Group Dimensions**
```python
AUDIT_PEER_GROUP_BY = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]  # กลุ่มที่เทียบ
AUDIT_PEER_ITEM_ID = "COST_CENTER"  # รายการที่เทียบในกลุ่ม
```

### **Crosstab Dimensions**
```python
CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
CROSSTAB_MIN_HISTORY = 3  # ต้องมีประวัติอย่างน้อย 3 เดือน
```

---

## 📊 ตัวอย่างการตั้งค่า

### **ตัวอย่าง 1: Expense Audit (ใช้งานประจำ)**
```python
INPUT_MODE = 'long'
INPUT_FILE_LONG = "EXPENSE_NT_REPORT_2025.csv"
TARGET_COL = "EXPENSE_VALUE"

RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True
RUN_TIME_SERIES_ANALYSIS = True      # ✅ เปิด
RUN_PEER_GROUP_ANALYSIS = False      # ❌ ปิด (ประหยัดเวลา)

CROSSTAB_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
AUDIT_TS_DIMENSIONS = ["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"]
```

### **ตัวอย่าง 2: Revenue Audit (วิเคราะห์แบบละเอียด)**
```python
INPUT_MODE = 'crosstab'
INPUT_FILE_CROSSTAB = "revenue_crosstab_2025.xlsx"
CROSSTAB_VALUE_NAME = "REVENUE_VALUE"
TARGET_COL = "REVENUE_VALUE"

RUN_CROSSTAB_REPORT = True
RUN_FULL_AUDIT_LOG = True
RUN_TIME_SERIES_ANALYSIS = True      # ✅ เปิด
RUN_PEER_GROUP_ANALYSIS = True       # ✅ เปิด (วิเคราะห์แบบละเอียด)

CROSSTAB_DIMENSIONS = ["SERVICE_GROUP", "SERVICE_CODE"]
AUDIT_PEER_GROUP_BY = ["SERVICE_GROUP"]
AUDIT_PEER_ITEM_ID = "SERVICE_CODE"
```

---

## 🐛 Troubleshooting

### ❓ **Peer Group ใช้เวลานานมาก**
**วิธีแก้:**
- ปิด Peer Group: `RUN_PEER_GROUP_ANALYSIS = False`
- ลด dimensions: ใช้น้อยกว่า 3 dimensions
- แบ่งข้อมูล: รันแยกตามช่วงเวลา

### ❓ **ไม่มี Audit Log sheet**
**ตรวจสอบ:**
- `RUN_FULL_AUDIT_LOG = True` หรือไม่
- มี anomalies หรือไม่ (ถ้าไม่มีจะไม่สร้าง sheet)

### ❓ **Crosstab Report ไม่มี Highlighting**
**ตรวจสอบ:**
- `RUN_TIME_SERIES_ANALYSIS = True` หรือไม่
- มีข้อมูลอดีตมากพอหรือไม่ (`CROSSTAB_MIN_HISTORY = 3`)

---

## 📖 ดูเพิ่มเติม

- [README.md](README.md) - ภาพรวมโปรเจค
- [MAIN_AUDIT_USAGE_GUIDE.md](MAIN_AUDIT_USAGE_GUIDE.md) - คู่มือการใช้งานแบบละเอียด
- [QUICK_START.md](QUICK_START.md) - เริ่มต้นใช้งานอย่างรวดเร็ว

---

**สร้างโดย:** Claude
**วันที่:** 2025-01-18
**เวอร์ชัน:** v4.1.2 (Configurable Analysis)
