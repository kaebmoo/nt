# Anomaly Detection Web Application

Web-based interface สำหรับตรวจหา Anomaly ในข้อมูลทางการเงิน โดยใช้ Hybrid Anomaly Detection Engine

## 🎯 คุณสมบัติหลัก

### 1. **Upload & Auto-Detection**
- รองรับไฟล์ CSV, Excel (.xlsx, .xls)
- รองรับทั้ง **Long Format** และ **Crosstab Format**
- Auto-detect columns และแนะนำการตั้งค่า
- แสดง preview ข้อมูล พร้อม statistics

### 2. **Interactive Configuration**
- เลือก input mode (Long/Crosstab)
- เลือก columns สำหรับ dimensions, date, value
- Auto-suggest numeric columns
- กำหนด parameters สำหรับ anomaly detection
- บันทึกและโหลด configuration templates

### 3. **Anomaly Detection**
- **Time Series Analysis**: Rolling Window method
- **Peer Group Analysis**: Isolation Forest (optional)
- Real-time progress tracking
- Crosstab report พร้อมการทาสีตาม anomaly

### 4. **Output Management**
- Auto-generate filename พร้อม timestamp
- Download Excel report
- Browse & manage input/output files
- เก็บประวัติการทำงาน

## 📦 Installation

### 1. Clone repository
```bash
cd /Users/seal/Documents/GitHub/nt/anomaly_web
```

### 2. สร้าง virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # สำหรับ Mac/Linux
# หรือ
venv\Scripts\activate  # สำหรับ Windows
```

### 3. ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

### 4. สร้าง directories ที่จำเป็น
```bash
mkdir -p data/uploads data/outputs data/configs
```

## 🚀 การใช้งาน

### เริ่มต้น Web Application

```bash
python app.py
```

เปิด browser ไปที่: `http://localhost:5000`

### ขั้นตอนการใช้งาน

#### **Step 1: Upload File**
1. เลือกไฟล์ CSV หรือ Excel
2. เลือก Input Mode:
   - **Long Format**: ข้อมูลที่มี columns แยก (YEAR, MONTH, VALUE, ...)
   - **Crosstab Format**: ข้อมูลรูปแบบ pivot table (rows เป็น items, columns เป็นเดือน)
3. ใส่รายละเอียด (optional) เช่น "Expense Data 2024"
4. กด Upload

#### **Step 2: Preview & Configure**
1. ดู preview ข้อมูล (100 แถวแรก)
2. ระบบจะ auto-detect:
   - **Numeric Columns**: แนะนำเป็น VALUE column
   - **Date Columns**: แนะนำเป็น YEAR/MONTH
   - **Text Columns**: แนะนำเป็น Dimensions
3. ปรับแต่ง configuration:
   - **Input Mode Settings**
     - Long: เลือก YEAR, MONTH columns
     - Crosstab: เลือก ID variables, date columns
   - **Target Column**: column ที่ต้องการตรวจหา anomaly
   - **Dimensions**: columns สำหรับจัดกลุ่มข้อมูล
   - **Detection Options**:
     - ✓ Time Series Analysis (แนะนำ)
     - ✓ Peer Group Analysis (ใช้เวลานาน)
   - **Parameters**:
     - Rolling Window: 3-12 เดือน (default: 6)
     - Min History: 3-6 เดือน (default: 3)

4. (Optional) บันทึก configuration เป็น template เพื่อใช้งานภายหลัง

#### **Step 3: Run Detection**
1. กด "Run Anomaly Detection"
2. ติดตามความคืบหน้า:
   - Loading data...
   - Preprocessing...
   - Time Series Analysis... (30-50%)
   - Peer Group Analysis... (50-70%) - ถ้าเปิดใช้งาน
   - Generating Report... (70-95%)
   - Saving... (95-100%)
3. รอจนเสร็จ (อาจใช้เวลา 1-10 นาที ขึ้นอยู่กับขนาดข้อมูล)

#### **Step 4: Download & Review**
1. Download Excel file
2. เปิดดู Report ที่มี sheets:
   - **Crosstab_Report**: ตารางสรุป พร้อมทาสีตาม anomaly
   - **Full_Audit_Log (Time)**: รายละเอียด Time Series anomalies
   - **Full_Audit_Log (Peer)**: รายละเอียด Peer Group anomalies (ถ้ามี)
   - **Peer_Crosstab_Report**: Peer Group crosstab (ถ้ามี)

#### **Step 5: History & Re-run**
1. เข้าหน้า "History"
2. ดู input files และ output files ทั้งหมด
3. สามารถ:
   - Re-run anomaly detection ด้วย config ใหม่
   - Download output files เก่า
   - ลบไฟล์ที่ไม่ต้องการ

## 📊 รูปแบบข้อมูลที่รองรับ

### Long Format (แนะนำ)
```csv
YEAR,MONTH,GROUP_NAME,GL_CODE,GL_NAME,EXPENSE_VALUE
2024,1,IT,5001,Software License,50000
2024,1,IT,5002,Hardware,30000
2024,2,IT,5001,Software License,52000
...
```

### Crosstab Format
```csv
GROUP_NAME,GL_CODE,GL_NAME,2024-01,2024-02,2024-03
IT,5001,Software License,50000,52000,51000
IT,5002,Hardware,30000,32000,31000
HR,6001,Salary,100000,105000,103000
...
```

## ⚙️ Configuration Parameters

### **Input Mode Settings**

#### Long Format
- `col_year`: Column ที่เก็บปี (default: "YEAR")
- `col_month`: Column ที่เก็บเดือน (default: "MONTH")

#### Crosstab Format
- `crosstab_id_vars`: Columns ที่เป็น dimensions (e.g., ["GROUP_NAME", "GL_CODE"])
- `crosstab_value_name`: ชื่อ column สำหรับค่า (default: "VALUE")
- `crosstab_mode`: วิธีแปลง date columns ("auto", "date", "sequential")
- `crosstab_skiprows`: จำนวนแถวที่ข้ามด้านบน (default: 0)

### **Detection Settings**

- `target_col`: Column ที่ต้องการตรวจหา anomaly
- `crosstab_dimensions`: Dimensions สำหรับ Crosstab Report
- `audit_ts_dimensions`: Dimensions สำหรับ Time Series Analysis
- `audit_peer_group_by`: Dimensions สำหรับ Peer Group
- `audit_peer_item_id`: Column ที่เป็น Item ID สำหรับ Peer Group

### **Analysis Options**

- `run_crosstab_report`: สร้าง Crosstab Report (default: true)
- `run_full_audit_log`: บันทึก Audit Logs (default: true)
- `run_time_series_analysis`: รัน Time Series Analysis (default: true)
- `run_peer_group_analysis`: รัน Peer Group Analysis (default: false)

### **Parameters**

- `crosstab_min_history`: จำนวนเดือนขั้นต่ำสำหรับ crosstab (default: 3)
- `audit_ts_window`: Rolling window สำหรับ time series (default: 6)
- `iqr_k`: ตัวคูณ IQR สำหรับ Time Series/Crosstab (default: 2.0; ค่าน้อย strict, ค่ามาก relaxed)
- `min_change_ratio`: % เปลี่ยนแปลงขั้นต่ำก่อนเริ่มจับ anomaly (default: 0.10 = 10%)
- `constant_change_ratio`: % เปลี่ยนแปลงขั้นต่ำเมื่อประวัติเดิมคงที่/IQR = 0 (default: 0.15 = 15%)
- `peer_contamination`: สัดส่วน candidate outlier ของ Isolation Forest (default: 0.05 = 5%)
- `peer_zscore_threshold`: z-score ขั้นต่ำหลังผ่าน Isolation Forest (default: 2.0)
- `peer_min_group_size`: จำนวนรายการขั้นต่ำต่อ peer group ก่อนวิเคราะห์ (default: 5)

### **PCT_CHANGE คำนวณอย่างไร**

ค่าเปลี่ยนแปลงของ "เดือนล่าสุด" เทียบกับ "ค่าเฉลี่ยของเดือนก่อนหน้า" มี 2 ที่ที่คำนวณต่างกัน:

| | Crosstab Report (`PCT_CHANGE` ในไฟล์) | Time Series Audit (ใช้ภายใน) |
|---|---|---|
| สูตร | `(LATEST_VALUE - AVG_HISTORICAL) / AVG_HISTORICAL * 100` | `abs(value - HIST_MEAN) / HIST_MEAN` |
| ฐานเทียบ | ค่าเฉลี่ยของ **ทุกเดือนก่อนหน้า** (ตัดค่า ≤ 0 และค่าที่ไม่ใช่ตัวเลขทิ้ง) | ค่าเฉลี่ยของ **`audit_ts_window` เดือนก่อนหน้า** (ไม่รวมเดือนปัจจุบัน) |
| หน่วย | เปอร์เซ็นต์ มีเครื่องหมาย (-20 = ลด 20%) | สัดส่วน ค่าสัมบูรณ์ (0.2 = เปลี่ยน 20%) |
| ฐานเป็น 0 | ได้ 0 | ได้ 0 |
| แสดงในรายงาน | ✅ column `PCT_CHANGE` | ❌ ใช้ตัดสินสถานะแล้วทิ้ง เหลือแค่ `COMPARED_WITH` (Avg Past N + Count) |

ทั้งสองแบบใช้เป็นด่านแรกก่อนเช็ค IQR: ถ้าน้อยกว่า `min_change_ratio` → Normal ทันที และถ้าประวัตินิ่ง (IQR = 0) จะเทียบกับ `constant_change_ratio` แทน

## 🎨 Color Legend

### Crosstab Report
- 🔴 **แดง (Negative_Value)**: ยอดติดลบ
- 🟥 **แดงอ่อน (High_Spike)**: ยอดพุ่งสูงผิดปกติ
- 🟨 **เหลือง (Low_Spike)**: ยอดตกต่ำผิดปกติ
- 🟢 **เขียว (New_Item)**: รายการใหม่ (ข้อมูลไม่พอ)

### Peer Group Crosstab
- 🟥 **แดงอ่อน**: ค่าสูงผิดปกติเทียบกับกลุ่มเพื่อน
- 🟨 **เหลือง**: ค่าต่ำผิดปกติเทียบกับกลุ่มเพื่อน

## 📁 โครงสร้าง Project

```
anomaly_web/
├── app.py                      # Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── README.md                   # เอกสารนี้
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── anomaly_engine.py       # Anomaly detection engine
│   ├── anomaly_reporter.py     # Excel report generator
│   ├── audit_runner.py         # Main audit runner
│   ├── file_handler.py         # File management
│   ├── data_analyzer.py        # Data analysis utilities
│   └── config_manager.py       # Configuration management
├── templates/                  # HTML templates
│   ├── index.html
│   ├── upload.html
│   ├── preview.html
│   ├── configure.html
│   ├── process.html
│   └── history.html
├── static/                     # Static files (CSS, JS)
│   ├── css/
│   └── js/
└── data/                       # Data storage
    ├── uploads/                # Input files
    ├── outputs/                # Output files
    └── configs/                # Saved configurations
```

## 🔧 Troubleshooting

### ปัญหา: "Module not found"
```bash
# ตรวจสอบว่าติดตั้ง dependencies ครบแล้ว
pip install -r requirements.txt
```

### ปัญหา: "Permission denied"
```bash
# ตรวจสอบ permissions ของ directories
chmod -R 755 data/
```

### ปัญหา: Peer Group ใช้เวลานานมาก
- ปิดการใช้งาน Peer Group Analysis ในกรณีที่ข้อมูลมีขนาดใหญ่ (>100,000 rows)
- หรือลดจำนวน dimensions ที่ใช้ใน `audit_peer_group_by`

### ปัญหา: Memory Error
- ลดขนาดไฟล์ input โดยกรองเฉพาะข้อมูลที่จำเป็น
- เพิ่ม memory limit สำหรับ Python
- ปิดการใช้งาน Peer Group Analysis

## 📝 Notes

1. **ความเร็ว**:
   - Time Series: ~1,000-10,000 rows/second
   - Peer Group: ~100-1,000 rows/second (ช้ากว่ามาก)

2. **ขนาดไฟล์แนะนำ**:
   - < 1 MB: รวดเร็วมาก
   - 1-10 MB: ใช้เวลาปานกลาง (1-3 นาที)
   - 10-100 MB: ใช้เวลานาน (3-10 นาที)
   - > 100 MB: ควรแบ่งไฟล์หรือใช้ command line version

3. **Best Practices**:
   - ใช้ Long Format สำหรับข้อมูลที่มีหลาย dimensions
   - ใช้ Crosstab Format สำหรับข้อมูลที่ต้องการดูแนวโน้มตามเวลา
   - เปิด Peer Group เฉพาะเมื่อต้องการเปรียบเทียบกับกลุ่มเพื่อน
   - บันทึก configuration เป็น template สำหรับงานที่ทำซ้ำ

## 🤝 การพัฒนาเพิ่มเติม

### Features ที่อาจเพิ่มในอนาคต
- [ ] Async processing with Celery/Redis
- [ ] Email notification เมื่อเสร็จ
- [ ] Dashboard สำหรับดู statistics
- [ ] Export to PDF
- [ ] Multi-user support with authentication
- [ ] Schedule automated runs
- [ ] API endpoints for integration

## 📞 Support

หากพบปัญหาหรือมีข้อสงสัย สามารถ:
1. ตรวจสอบ logs ใน console
2. อ่าน error messages ใน UI
3. ตรวจสอบ input file format
4. ลอง configuration ใหม่

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-19  
**Author**: Pornthep (seal)
