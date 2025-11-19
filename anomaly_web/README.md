# Anomaly Detection Web Application

ระบบตรวจจับความผิดปกติทางการเงินผ่าน Web Interface

## คุณสมบัติหลัก

### 1. รองรับ 2 รูปแบบข้อมูล
- **Long Format**: ข้อมูลแบบแถว-คอลัมน์ (YEAR, MONTH, VALUE)
- **Crosstab Format**: ข้อมูลแบบ Pivot Table (GL_CODE | ม.ค. | ก.พ. | ...)

### 2. การวิเคราะห์อัตโนมัติ
- **Time Series Analysis**: เปรียบเทียบกับประวัติในอดีต
- **Peer Group Analysis**: เปรียบเทียบกับกลุ่มเพื่อน (IsolationForest)

### 3. ระบบจัดการไฟล์
- อัพโหลดไฟล์ CSV, Excel (XLSX, XLS)
- ตัวอย่างข้อมูลและวิเคราะห์อัตโนมัติ
- เก็บประวัติการทำงาน
- จัดการ Tags และคำอธิบาย

### 4. Configuration Templates
- บันทึกการตั้งค่าที่ใช้บ่อย
- โหลด Template ได้ทันที
- แชร์ Configuration ระหว่างโปรเจกต์

### 5. Progress Tracking
- แสดง Real-time Progress
- รายละเอียดการประมวลผลแต่ละขั้นตอน
- การจัดการ Error

## การติดตั้ง

### 1. Clone Repository
```bash
cd /path/to/anomaly_web
```

### 2. สร้าง Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies
```bash
pip install -r requirements.txt
```

### 4. ตั้งค่า Environment Variables (Optional)
สร้างไฟล์ `.env`:
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

## การรัน Application

### Development Mode
```bash
python app.py
```

หรือใช้ Flask CLI:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

เปิดเบราว์เซอร์ที่: `http://localhost:5000`

## โครงสร้างโฟลเดอร์

```
anomaly_web/
├── app.py                      # Main Flask application
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── README.md                   # คู่มือนี้
│
├── utils/                      # Utility modules
│   ├── __init__.py
│   ├── file_handler.py        # จัดการไฟล์
│   ├── data_analyzer.py       # วิเคราะห์ข้อมูล
│   ├── config_manager.py      # จัดการ config
│   └── audit_runner.py        # รัน anomaly detection
│
├── templates/                  # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── preview.html
│   ├── configure.html
│   ├── process.html
│   └── history.html
│
├── static/                     # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
│
├── uploads/                    # Uploaded files (auto-created)
├── outputs/                    # Generated reports (auto-created)
└── configs/                    # Saved configurations (auto-created)
```

## วิธีใช้งาน

### 1. อัพโหลดไฟล์
- คลิก "อัพโหลดไฟล์"
- เลือกไฟล์ CSV หรือ Excel
- เลือกรูปแบบข้อมูล (Long/Crosstab)
- เพิ่มคำอธิบาย (Optional)

### 2. ดูตัวอย่างข้อมูล
- ระบบจะแสดงตัวอย่างข้อมูล
- วิเคราะห์อัตโนมัติและแนะนำการตั้งค่า

### 3. กำหนดค่า
- เลือก Columns สำหรับวันที่และค่าตัวเลข
- เลือกมิติข้อมูล (Dimensions)
- เปิด/ปิดการวิเคราะห์แต่ละประเภท
- บันทึกเป็น Template (Optional)

### 4. รับรายงาน
- ระบบจะประมวลผลและแสดง Progress
- ดาวน์โหลดรายงาน Excel เมื่อเสร็จสิ้น

### 5. จัดการประวัติ
- ดูไฟล์ Input และ Output ทั้งหมด
- Re-run การวิเคราะห์ด้วยค่าใหม่
- ลบไฟล์ที่ไม่ต้องการ

## การรวม Main Audit Logic

**สำคัญ**: ไฟล์นี้เป็นเพียง **Framework** สำหรับ Web Application  
คุณต้องเพิ่ม Logic จาก `main_audit.py` ดั้งเดิมของคุณเข้ามา:

### ไฟล์ที่ต้อง Copy/Import:
1. `anomaly_engine.py` - CrosstabGenerator, FullAuditEngine
2. `anomaly_reporter.py` - ExcelReporter
3. `crosstab_converter.py` - CrosstabConverter

### ตำแหน่งที่ต้องแก้ไข:
- `utils/audit_runner.py` - เพิ่ม logic การรัน audit
- เปลี่ยนจาก placeholder → ใช้ engine จริง

### ตัวอย่างการแก้ไข:
```python
# ใน audit_runner.py
from anomaly_engine import FullAuditEngine
from anomaly_reporter import ExcelReporter

def _run_time_series(self, df, config, callback=None):
    engine = FullAuditEngine(df)
    return engine.audit_time_series_all_months(...)
```

## Configuration Schema

```json
{
  "input_mode": "long|crosstab",
  "col_year": "YEAR",
  "col_month": "MONTH",
  "target_col": "EXPENSE_VALUE",
  "crosstab_dimensions": ["GROUP_NAME", "GL_CODE"],
  "run_time_series_analysis": true,
  "run_peer_group_analysis": false,
  "audit_ts_window": 6,
  "crosstab_min_history": 3
}
```

## API Endpoints

### File Management
- `POST /upload` - อัพโหลดไฟล์
- `GET /preview/<file_id>` - ดูตัวอย่างข้อมูล
- `DELETE /api/delete-file/<file_id>` - ลบไฟล์

### Configuration
- `GET /configure/<file_id>` - หน้ากำหนดค่า
- `POST /configure/<file_id>` - บันทึกการตั้งค่า
- `POST /api/save-template` - บันทึก template
- `GET /api/load-template/<name>` - โหลด template

### Processing
- `POST /api/run-audit/<file_id>` - เริ่มประมวลผล
- `GET /api/progress/<file_id>` - ดู progress

### Download
- `GET /download/<output_id>` - ดาวน์โหลด report

## Troubleshooting

### ปัญหา: ไม่สามารถอัพโหลดไฟล์ขนาดใหญ่
- แก้ไข `MAX_CONTENT_LENGTH` ใน `config.py`

### ปัญหา: Progress ไม่อัปเดต
- ตรวจสอบ JavaScript Console
- ใช้ Redis สำหรับ Progress Tracking (แทน in-memory)

### ปัญหา: Peer Group Analysis ช้ามาก
- ลดขนาดข้อมูล
- ปิด Peer Group Analysis
- ใช้ Async Task Queue (Celery)

## TODO / Future Enhancements

- [ ] Async Task Processing (Celery + Redis)
- [ ] User Authentication
- [ ] Multi-user Support
- [ ] Email Notifications
- [ ] Scheduled Reports
- [ ] API Documentation (Swagger)
- [ ] Docker Support
- [ ] Cloud Storage Integration

## License

Internal Use Only - NT Organization

## ผู้พัฒนา

Pornthep (Seal)  
2024
