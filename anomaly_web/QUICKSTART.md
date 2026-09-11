# Quick Start Guide - Anomaly Detection Web App

## การติดตั้งและเริ่มต้นใช้งาน (5 นาที)

### 1. ติดตั้ง Dependencies

```bash
cd /Users/seal/Documents/GitHub/nt/anomaly_web
pip install -r requirements.txt
```

### 2. เริ่มต้น Web Server

```bash
python app.py
```

### 3. เปิด Browser

```
http://localhost:5000
```

---

## การใช้งานพื้นฐาน

### 🔸 กรณีที่ 1: ไฟล์ Long Format (แนะนำสำหรับผู้เริ่มต้น)

#### ตัวอย่างข้อมูล:
```csv
YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME,EXPENSE_VALUE
2024,1,IT,5001,Software,50000
2024,2,IT,5001,Software,52000
2024,3,IT,5001,Software,180000
```

#### ขั้นตอน:
1. **Upload**
   - เลือกไฟล์
   - Input Mode: `Long Format`
   - กด Upload

2. **Configure** (ระบบจะ auto-detect ให้)
   - Year Column: `YEAR`
   - Month Column: `MONTH`
   - Target Column: `EXPENSE_VALUE` (ตัวเลขที่ต้องการตรวจสอบ)
   - Dimensions: เลือก `GROUP_NAME`, `GL_CODE`, `GL_NAME`

3. **Detection Options**
   - ✓ Time Series Analysis (แนะนำเปิด)
   - ☐ Peer Group Analysis (ปิดไว้ก่อนเพื่อความเร็ว)

4. **Run**
   - กด "Run Anomaly Detection"
   - รอ 1-3 นาที
   - Download Excel file

5. **ผลลัพธ์**
   - เปิดไฟล์ Excel
   - ดู sheet "Crosstab_Report"
   - เดือนที่มีปัญหาจะถูกทาสี:
     - 🟥 แดง = ยอดพุ่งสูงผิดปกติ
     - 🟨 เหลือง = ยอดต่ำผิดปกติ
     - 🔴 แดงเข้ม = ยอดติดลบ

---

### 🔸 กรณีที่ 2: ไฟล์ Crosstab Format

#### ตัวอย่างข้อมูล:
```csv
GROUP_NAME,GL_CODE,GL_NAME,2024-01,2024-02,2024-03
IT,5001,Software,50000,52000,180000
HR,6001,Salary,100000,105000,103000
```

#### ขั้นตอน:
1. **Upload**
   - เลือกไฟล์
   - Input Mode: `Crosstab Format`
   - กด Upload

2. **Configure**
   - ID Variables: เลือก `GROUP_NAME`, `GL_CODE`, `GL_NAME`
   - Date Columns: ระบบจะ detect อัตโนมัติ (2024-01, 2024-02, ...)
   - Value Name: `EXPENSE_VALUE`
   - Crosstab Mode: `auto` (ให้ระบบจัดการเอง)

3. **Detection & Run** (เหมือนกรณีที่ 1)

---

## เคล็ดลับการใช้งาน

### ✨ สำหรับมือใหม่
1. **เริ่มจาก Long Format** - ง่ายกว่าและควบคุมได้ดีกว่า
2. **ปิด Peer Group ก่อน** - ใช้เวลานาน ควรเปิดเมื่อจำเป็นจริงๆ
3. **ใช้ข้อมูลตัวอย่างก่อน** - ทดสอบด้วยข้อมูล 100-1000 แถว
4. **บันทึก Template** - เมื่อได้ config ที่ดีแล้ว บันทึกเป็น template

### ⚡ สำหรับผู้ใช้ขั้นสูง
1. **Optimize Dimensions** - เลือกเฉพาะ dimensions ที่จำเป็น
2. **Tune Parameters**:
   - `audit_ts_window`: 3-6 = sensitive, 6-12 = moderate
   - `crosstab_min_history`: 3 = strict, 6 = relaxed
   - `iqr_k`: 1.5 = strict, 2.0 = ปกติ, 3.0 = relaxed
   - `min_change_ratio`: 0.10 = ต้องเปลี่ยนอย่างน้อย 10% ก่อนจับ anomaly
   - `constant_change_ratio`: 0.15 = threshold เมื่อ history คงที่
   - `peer_contamination`: 0.05 = ให้ Isolation Forest หา candidate outlier ราว 5%
   - `peer_zscore_threshold`: 2.0 = กรอง candidate ด้วย z-score
   - `peer_min_group_size`: 5 = จำนวนรายการขั้นต่ำต่อ peer group
3. **Batch Processing** - ประมวลผลหลายไฟล์พร้อมกันด้วย configuration เดียวกัน

---

## การแก้ปัญหาเบื้องต้น

### ❌ ปัญหา: "Column not found"
**แก้ไข**: ตรวจสอบว่า column names ในไฟล์ตรงกับที่ระบุใน config

### ❌ ปัญหา: "ใช้เวลานานมาก"
**แก้ไข**: 
- ปิด Peer Group Analysis
- ลด dimensions
- แบ่งไฟล์เป็นชิ้นเล็กลง

### ❌ ปัญหา: "ไม่มี anomaly เลย"
**แก้ไข**:
- ลด `audit_ts_window` จาก 6 เป็น 3
- ลด `iqr_k` หรือ `peer_zscore_threshold`
- ลด `min_change_ratio` ถ้าอยากให้การเปลี่ยนแปลงเล็กลงถูกจับด้วย
- ตรวจสอบว่าข้อมูลมีความแปรปรวนเพียงพอ
- ดูใน sheet "Full_Audit_Log" ว่ามี anomaly ที่ไม่ critical

### ❌ ปัญหา: "Excel ไม่มีสี"
**แก้ไข**:
- ตรวจสอบว่าเปิด option `run_crosstab_report = true`
- ตรวจสอบว่า anomalies ที่พบเป็น critical types (High_Spike, Low_Spike, Negative_Value)

---

## ตัวอย่าง Configuration ที่ดี

### สำหรับ Expense Analysis
```json
{
  "input_mode": "long",
  "col_year": "YEAR",
  "col_month": "MONTH",
  "target_col": "EXPENSE_VALUE",
  "crosstab_dimensions": ["GROUP_NAME", "GL_CODE", "GL_NAME"],
  "audit_ts_dimensions": ["GROUP_NAME", "GL_CODE", "GL_NAME"],
  "audit_ts_window": 6,
  "crosstab_min_history": 3,
  "run_time_series_analysis": true,
  "run_peer_group_analysis": false
}
```

### สำหรับ Revenue Analysis (with Peer Group)
```json
{
  "input_mode": "long",
  "col_year": "YEAR",
  "col_month": "MONTH",
  "target_col": "REVENUE_VALUE",
  "crosstab_dimensions": ["PRODUCT", "REGION"],
  "audit_ts_dimensions": ["PRODUCT", "REGION"],
  "audit_peer_group_by": ["PRODUCT"],
  "audit_peer_item_id": "CUSTOMER_ID",
  "audit_ts_window": 6,
  "run_time_series_analysis": true,
  "run_peer_group_analysis": true
}
```

---

## Next Steps

1. **ลองใช้ด้วยข้อมูลจริง** - เริ่มจากไฟล์เล็กๆ
2. **ทดลองปรับ parameters** - ดูว่าผลลัพธ์เปลี่ยนแปลงอย่างไร
3. **บันทึก templates** - สำหรับงานที่ทำซ้ำ
4. **อ่าน README.md** - เพื่อทำความเข้าใจ features เพิ่มเติม

---

**Happy Anomaly Hunting! 🔍**
