# Revenue ETL System v2.0
## ระบบประมวลผลข้อมูลรายได้แบบ Modular

---

## 📋 ภาพรวมระบบ

Revenue ETL System เป็นระบบประมวลผลข้อมูลรายได้ที่ปรับปรุงใหม่ให้เป็น Modular Architecture พร้อมระบบ Configuration Management ภายนอก ทำให้สามารถปรับแต่งการทำงานได้โดยไม่ต้องแก้ไขโค้ด

### คุณสมบัติหลัก
- ✅ **Configuration Management** - จัดการ config ผ่านไฟล์ JSON ภายนอก
- ✅ **Modular Design** - แยก module ชัดเจน ง่ายต่อการบำรุงรักษา
- ✅ **Cross-Platform Support** - รองรับ Windows, macOS, Linux
- ✅ **Data Validation** - ตรวจสอบความถูกต้องด้วย Reconciliation
- ✅ **Anomaly Detection** - ตรวจจับความผิดปกติของข้อมูล
- ✅ **Web Application Ready** - พร้อมสำหรับการพัฒนา Web Interface

---

## 🏗️ โครงสร้างระบบ

```
revenue-etl-system/
│
├── config.json                 # ไฟล์ configuration หลัก
├── main.py                     # โปรแกรมหลัก
├── config_manager.py           # Module จัดการ configuration
├── fi_revenue_expense_module.py # Module ประมวลผลงบการเงิน
├── revenue_etl_report.py       # Module ETL Pipeline
├── revenue_reconciliation.py    # Module ตรวจสอบความถูกต้อง
├── requirements.txt            # Python dependencies
├── README.md                   # คู่มือการใช้งาน
└── web_app.py                  # Web Application (optional)
```

---

## 🔧 การติดตั้ง

### 1. System Requirements
- Python 3.8 หรือสูงกว่า
- RAM อย่างน้อย 4 GB
- พื้นที่ว่างอย่างน้อย 2 GB

### 2. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 3. ตั้งค่า Configuration

แก้ไขไฟล์ `config.json` ตามความต้องการ:

```json
{
  "processing_year": "2025",
  "paths": {
    "darwin": {
      "base_path": "/path/to/your/data",
      "master_path": "/path/to/master"
    }
  }
}
```

---

## 📖 วิธีการใช้งาน

### การใช้งานพื้นฐาน

#### 1. รันระบบทั้งหมด (FI + ETL)
```bash
python main.py
```

#### 2. รันเฉพาะ FI Module
```bash
python main.py --module fi
```

#### 3. รันเฉพาะ ETL Module
```bash
python main.py --module etl
```

#### 4. ระบุไฟล์ config
```bash
python main.py --config custom_config.json
```

#### 5. Override ปีที่ประมวลผล
```bash
python main.py --year 2024
```

### การใช้งานขั้นสูง

#### Import และใช้งานใน Python Script

```python
from config_manager import ConfigManager
from fi_revenue_expense_module import FIRevenueExpenseProcessor

# โหลด configuration
config_manager = ConfigManager("config.json")

# รัน FI Module
fi_config = config_manager.get_fi_config()
fi_processor = FIRevenueExpenseProcessor(fi_config)
fi_processor.run()
```

---

## ⚙️ Configuration

### โครงสร้าง config.json

#### 1. Processing Year
```json
"processing_year": "2025"
```

#### 2. Paths Configuration (ตาม OS)
```json
"paths": {
  "darwin": {  // macOS
    "base_path": "/Users/username/data",
    "master_path": "/Users/username/master"
  },
  "linux": {   // Linux
    "base_path": "/home/username/data",
    "master_path": "/home/username/master"
  },
  "windows": { // Windows
    "base_path": "C:\\Users\\username\\data",
    "master_path": "C:\\Users\\username\\master"
  }
}
```

#### 3. FI Module Configuration
```json
"fi_module": {
  "input_files": ["pld_nt_20251031.txt"],
  "master_files": {
    "expense": "MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv",
    "revenue": "MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv"
  },
  "output_files": {
    "excel": "pl_combined_output_202510.xlsx",
    "csv_expense": "pl_expense_nt_output_202510.csv",
    "csv_revenue": "pl_revenue_nt_output_202510.csv"
  }
}
```

#### 4. ETL Module Configuration
```json
"etl_module": {
  "reconciliation": {
    "enabled": true,
    "fi_month": "10",
    "tolerance": 0.00
  },
  "anomaly_detection": {
    "enabled": true,
    "iqr_multiplier": 1.5,
    "min_history": 3
  }
}
```

---

## 📊 ขั้นตอนการประมวลผล

### Phase 1: FI Revenue Expense Processing
1. **โหลด Master Files** - อ่านไฟล์ master สำหรับ mapping
2. **ประมวลผล Expense** - จัดกลุ่มและคำนวณค่าใช้จ่าย
3. **ประมวลผล Revenue** - จัดกลุ่มและคำนวณรายได้
4. **วิเคราะห์รายได้/ค่าใช้จ่ายอื่น** - แยกประเภทพิเศษ
5. **สร้างรายงาน Excel** - บันทึกผลลัพธ์

### Phase 2: Revenue ETL Pipeline
1. **รวมไฟล์ CSV** - รวมไฟล์ transaction ทั้งหมด
2. **Mapping Cost Center** - แปลง cost center
3. **Mapping Product** - แปลง product codes
4. **Merge กับ Master** - รวมข้อมูลและสร้างรายงาน
5. **Anomaly Detection** - ตรวจจับความผิดปกติ

### Phase 3: Reconciliation (Optional)
1. **เปรียบเทียบ FI vs TRN** - ตรวจสอบยอดรวม
2. **ตรวจสอบระดับ GL Code** - เทียบรายละเอียด
3. **สร้าง Reconciliation Report** - บันทึกผลการตรวจสอบ

---

## 📁 Output Files

### FI Module Outputs
- `pl_combined_output_YYYYMM.xlsx` - รายงาน Excel รวม
- `pl_expense_nt_output_YYYYMM.csv` - ข้อมูล Expense
- `pl_revenue_nt_output_YYYYMM.csv` - ข้อมูล Revenue

### ETL Module Outputs
- `REVENUE_NT_REPORT_YYYY.xlsx` - รายงานหลัก พร้อม Anomaly Detection
- `trn_revenue_nt_YYYY.csv` - ข้อมูล transaction รวม
- `error_gl_REVENUE_NT_REPORT_YYYY.csv` - GL codes ที่มีปัญหา
- `error_product_REVENUE_NT_REPORT_YYYY.csv` - Product codes ที่มีปัญหา

### Reconciliation Outputs
- `reconcile_summary_YYYY_timestamp.txt` - สรุปผลการ reconcile
- `reconcile_monthly_errors_YYYY_timestamp.csv` - รายการที่แตกต่างรายเดือน
- `reconcile_ytd_errors_YYYY_timestamp.csv` - รายการที่แตกต่าง YTD

---

## 🚨 Error Handling

### Common Errors และวิธีแก้ไข

#### 1. ไม่พบไฟล์ Configuration
```
Error: ไม่พบไฟล์ configuration: config.json
```
**แก้ไข:** ตรวจสอบว่ามีไฟล์ config.json อยู่ใน directory เดียวกับ main.py

#### 2. Path ไม่ถูกต้อง
```
Error: ไม่พบไฟล์ Master: MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv
```
**แก้ไข:** ตรวจสอบ paths ใน config.json ให้ตรงกับระบบของคุณ

#### 3. Reconciliation ล้มเหลว
```
Error: RECONCILIATION FAILED - พบความแตกต่างที่ไม่ยอมรับได้
```
**แก้ไข:** ตรวจสอบ log file ใน reconcile_logs/ เพื่อดูรายละเอียด

---

## 🔄 การอัพเดทและบำรุงรักษา

### การเปลี่ยนปีประมวลผล
1. แก้ไข `processing_year` ใน config.json
2. อัพเดทชื่อไฟล์ input/output ตามปีใหม่
3. รันระบบใหม่

### การเพิ่มไฟล์ Input
1. เพิ่มชื่อไฟล์ใน `fi_module.input_files` หรือ `etl_module.input_patterns`
2. วางไฟล์ใน directory ที่กำหนด
3. รันระบบใหม่

### การแก้ไข Business Rules
1. แก้ไขค่าใน `etl_module.business_rules`
2. รันระบบใหม่

---

## 📞 การสนับสนุน

หากพบปัญหาหรือต้องการความช่วยเหลือ:

1. ตรวจสอบ log files ใน directory `logs/`
2. ตรวจสอบ error messages และ common errors ด้านบน
3. ติดต่อทีมพัฒนา

---

## 📝 Change Log

### Version 2.0.0 (Current)
- ✨ ปรับโครงสร้างเป็น Modular Architecture
- ✨ เพิ่ม Configuration Management
- ✨ รองรับ Cross-platform
- ✨ เพิ่ม Command Line Interface
- ✨ ปรับปรุง Error Handling

### Version 1.0.0
- 🎉 Initial release
- ✅ FI Revenue Expense Processing
- ✅ Revenue ETL Pipeline
- ✅ Basic Reconciliation

---

## 📄 License

Copyright © 2025 Revenue ETL System. All rights reserved.