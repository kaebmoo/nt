# 📦 Revenue ETL System v2.0 - Setup Guide

## รายการไฟล์ทั้งหมด (File List)

### ✅ ไฟล์หลักที่จำเป็น (Core Files)
1. **config.json** - ไฟล์ configuration หลัก
2. **main.py** - โปรแกรมหลักสำหรับรันระบบ
3. **config_manager.py** - Module จัดการ configuration
4. **fi_revenue_expense_module.py** - Module ประมวลผลงบการเงิน (FI)
5. **revenue_etl_report.py** - Module ETL Pipeline
6. **revenue_reconciliation.py** - Module ตรวจสอบความถูกต้อง

### 📚 ไฟล์เอกสารและเครื่องมือ (Documentation & Tools)
7. **requirements.txt** - Python dependencies
8. **README.md** - คู่มือการใช้งานระบบ
9. **web_app.py** - Web Application (Streamlit)
10. **run.sh** - Shell script สำหรับรันระบบ

---

## 🚀 ขั้นตอนการติดตั้ง (Quick Setup)

### Step 1: แตกไฟล์ (Extract Files)
```bash
unzip revenue_etl_system_v2.zip
cd revenue_etl_system
```

### Step 2: ติดตั้ง Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: ปรับแต่ง Configuration
แก้ไขไฟล์ `config.json` ตามความต้องการ:

```json
{
  "processing_year": "2025",  // <- เปลี่ยนปีที่ต้องการ
  "paths": {
    "darwin": {  // macOS
      "base_path": "/path/to/your/data",  // <- แก้ไข path
      "master_path": "/path/to/master"     // <- แก้ไข path
    }
  }
}
```

### Step 4: จัดโครงสร้าง Folder
สร้างโครงสร้าง folder ตามนี้:

```
your-data-folder/
├── 2025/                    # ปีที่ประมวลผล
│   ├── fi/                  # สำหรับไฟล์ FI input
│   │   ├── pld_nt_*.txt    # ไฟล์ input
│   │   └── output/          # folder output (จะสร้างอัตโนมัติ)
│   └── revenue/             # สำหรับไฟล์ Revenue
│       ├── TRN_*.csv       # ไฟล์ transaction
│       └── output/          # folder output (จะสร้างอัตโนมัติ)
│
master-folder/
├── source/                  # Master files สำหรับ FI
│   ├── MASTER_EXPENSE_*.csv
│   └── MASTER_REVENUE_*.csv
├── MASTER_PRODUCT_*.csv     # Master product
├── MAPPING_CC.csv           # Mapping cost center
└── clean/                   # Clean master files
    └── MAP_PRODUCT_*.csv
```

---

## ▶️ วิธีการรันระบบ (How to Run)

### Option 1: ใช้ Command Line
```bash
# รันทุก module
python main.py

# รันเฉพาะ FI
python main.py --module fi

# รันเฉพาะ ETL
python main.py --module etl
```

### Option 2: ใช้ Shell Script (Linux/Mac)
```bash
chmod +x run.sh
./run.sh
```

### Option 3: ใช้ Web Interface
```bash
streamlit run web_app.py
# เปิด browser ที่ http://localhost:8501
```

---

## 🔧 การปรับแต่งเพิ่มเติม (Customization)

### เปลี่ยนปีประมวลผล
1. แก้ไข `processing_year` ใน config.json
2. อัพเดทชื่อไฟล์ master ให้ตรงกับปีใหม่
3. อัพเดทชื่อไฟล์ output ในส่วน `fi_module.output_files`

### เพิ่มไฟล์ Input
1. สำหรับ FI: เพิ่มใน `fi_module.input_files`
2. สำหรับ ETL: ไฟล์จะถูกค้นหาอัตโนมัติตาม pattern

### ปรับ Reconciliation
```json
"reconciliation": {
  "enabled": true,      // true=เปิด, false=ปิด
  "fi_month": "10",    // เดือนของไฟล์ FI
  "tolerance": 0.00    // ความคลาดเคลื่อนที่ยอมรับได้
}
```

---

## 📊 ไฟล์ Output ที่จะได้

### จาก FI Module:
- `pl_combined_output_YYYYMM.xlsx` - รายงาน Excel รวม
- `pl_expense_nt_output_YYYYMM.csv` - ข้อมูล Expense
- `pl_revenue_nt_output_YYYYMM.csv` - ข้อมูล Revenue

### จาก ETL Module:
- `REVENUE_NT_REPORT_YYYY.xlsx` - รายงานหลักพร้อม Anomaly
- `trn_revenue_nt_YYYY.csv` - ข้อมูล transaction รวม
- `error_*.csv` - รายการที่มีปัญหา

### จาก Reconciliation:
- `reconcile_summary_*.txt` - สรุปผลการตรวจสอบ
- `reconcile_*_errors_*.csv` - รายการที่แตกต่าง

---

## ❓ Troubleshooting

### Problem: ไม่พบไฟล์ Master
- ตรวจสอบ path ใน config.json
- ตรวจสอบชื่อไฟล์ให้ตรงกับที่ระบุใน config

### Problem: Encoding Error
- ตรวจสอบ encoding ของไฟล์ input (ปกติใช้ tis-620)
- สามารถแก้ไขใน `fi_module.encoding`

### Problem: Reconciliation Failed
- ตรวจสอบว่าเดือนใน config ตรงกับไฟล์ FI
- ดูรายละเอียดใน reconcile_logs/

---

## 📞 Support

หากมีปัญหาการใช้งาน:
1. ตรวจสอบ error messages
2. ดู log files
3. ตรวจสอบ configuration
4. ติดต่อทีมพัฒนา

---

## ✨ Features ที่จะพัฒนาต่อ

- [ ] Database connection
- [ ] Email notifications
- [ ] API endpoints
- [ ] Docker support
- [ ] Automated scheduling
- [ ] Advanced analytics dashboard

---

**Version:** 2.0.0  
**Last Updated:** January 2025  
**Developed by:** Revenue ETL Team