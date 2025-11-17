# Revenue ETL System v2.1

## ระบบประมวลผลข้อมูลรายได้แบบ Modular พร้อม Web Interface

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Version](https://img.shields.io/badge/version-2.1.0-green.svg)]()

---

## 📋 ภาพรวมระบบ

Revenue ETL System เป็นระบบประมวลผลข้อมูลรายได้ที่ออกแบบมาเป็น **Modular Architecture** พร้อมระบบ **Configuration Management** ที่ยืดหยุ่น และ **Web Interface** ที่ใช้งานง่าย ทำให้สามารถปรับแต่งและใช้งานได้โดยไม่ต้องแก้ไขโค้ด

### ✨ คุณสมบัติหลัก

#### 🎯 Core Features
- ✅ **Configuration Management** - จัดการ config ผ่านไฟล์ JSON แบบ centralized
- ✅ **Modular Design** - แยก module ชัดเจน (FI, ETL, Reconciliation) ง่ายต่อการบำรุงรักษา
- ✅ **Cross-Platform Support** - รองรับ Windows, macOS, Linux อัตโนมัติ
- ✅ **Web Application** - UI ที่ใช้งานง่าย สร้างด้วย Streamlit
- ✅ **Command Line Interface** - รองรับการรันผ่าน CLI พร้อม options ต่างๆ

#### 📊 Data Processing Features
- ✅ **FI Module** - ประมวลผลงบการเงิน (Financial Income Statement)
- ✅ **ETL Pipeline** - ประมวลผล Transaction Revenue แบบ end-to-end
- ✅ **Data Reconciliation** - ตรวจสอบความถูกต้องระหว่าง FI และ Transaction
- ✅ **Anomaly Detection** - ตรวจจับความผิดปกติของข้อมูล 4 ระดับ
- ✅ **Business Rules Engine** - กฎทางธุรกิจที่ปรับแต่งได้

#### 🔧 Advanced Features
- ✅ **Logging System** - บันทึก log แบบ structured พร้อม rotation
- ✅ **Error Handling** - จัดการ errors อย่างเป็นระบบ พร้อม error files
- ✅ **Template Support** - ชื่อไฟล์แบบ dynamic (YYYY, MM, DD)
- ✅ **Month Sync** - ตรวจสอบและ sync เดือนระหว่าง FI และ ETL อัตโนมัติ
- ✅ **Progress Tracking** - แสดงความคืบหน้าแบบ real-time

---

## 🏗️ โครงสร้างระบบ

### System Architecture

```
Revenue ETL System v2.1
│
├─── Configuration Layer
│    └── config.json (Centralized Configuration)
│
├─── Core Modules
│    ├── FI Module (Financial Income Statement Processing)
│    ├── ETL Module (Revenue ETL Pipeline)
│    └── Reconciliation Module (Data Validation)
│
├─── Interface Layer
│    ├── CLI (main.py)
│    └── Web UI (web_app.py)
│
└─── Support Layer
     ├── Config Manager (Configuration Management)
     ├── Logger Utils (Logging System)
     └── Error Handling (Exception Management)
```

### ไฟล์ในระบบ

```
revenue-report/
│
├── 📋 Configuration
│   └── config.json                    # ไฟล์ configuration หลัก
│
├── 🎮 Main Applications
│   ├── main.py                        # CLI Application
│   └── web_app.py                     # Web Application (Streamlit)
│
├── 🔧 Core Modules
│   ├── config_manager.py              # Configuration Manager
│   ├── fi_revenue_expense_module.py   # FI Processing Module
│   ├── revenue_etl_report.py          # ETL Pipeline Module
│   ├── revenue_reconciliation.py      # Reconciliation Module
│   └── logger_utils.py                # Logging Utilities
│
├── 📚 Documentation
│   ├── README.md                      # คู่มือหลัก (ไฟล์นี้)
│   └── SETUP_GUIDE.md                 # คู่มือการติดตั้งและตั้งค่า
│
├── 📦 Dependencies
│   └── requirements.txt               # Python packages
│
└── 📁 Runtime (Generated)
    └── logs/                          # Log files
        ├── system_YYYYMMDD.log
        ├── fi_module_YYYYMMDD.log
        ├── etl_module_YYYYMMDD.log
        └── config_manager_YYYYMMDD.log
```

---

## 🚀 Quick Start

### ข้อกำหนดระบบ

- **Python:** 3.8 หรือสูงกว่า
- **RAM:** อย่างน้อย 4 GB
- **Disk Space:** อย่างน้อย 2 GB สำหรับข้อมูลและ logs
- **OS:** Windows 10+, macOS 10.14+, หรือ Linux

### การติดตั้งแบบเร็ว

```bash
# 1. Clone หรือ download repository
cd revenue-report

# 2. ติดตั้ง dependencies
pip install -r requirements.txt

# 3. แก้ไข config.json ตามระบบของคุณ
# (ดู SETUP_GUIDE.md สำหรับรายละเอียด)

# 4. รันระบบ
python main.py
```

---

## 💻 การใช้งาน

### 1. Command Line Interface (CLI)

#### รันระบบทั้งหมด (FI + ETL)
```bash
python main.py
```

#### รันเฉพาะ FI Module
```bash
python main.py --module fi
```

#### รันเฉพาะ ETL Module
```bash
python main.py --module etl
```

#### ระบุไฟล์ config
```bash
python main.py --config custom_config.json
```

#### Override เดือน
```bash
python main.py --month 10
```
> **Note:** เดือนจะถูก sync ระหว่าง FI และ ETL อัตโนมัติ

### 2. Web Application

#### เริ่มต้น Web Server
```bash
streamlit run web_app.py
```

#### เปิด Browser
```
http://localhost:8501
```

#### คุณสมบัติใน Web App

**📊 Dashboard Tab**
- แสดงสถานะระบบแบบ real-time
- ตรวจสอบ master files และ output files
- เตือนเมื่อเดือน FI และ ETL ไม่ตรงกัน
- แสดง configuration overview

**📁 FI Module Tab**
- แสดง configuration ของ FI module
- รัน FI processing ผ่าน UI
- แสดงผลลัพธ์พร้อมกราฟ Summary
- ดู FI output files

**🔄 ETL Module Tab**
- แสดง pipeline steps และความคืบหน้า
- แสดง business rules และ special mappings
- แสดง reconciliation และ anomaly detection settings
- รัน ETL processing ผ่าน UI

**✅ Reconciliation Tab**
- แสดงผล reconciliation จาก log files จริง
- เปรียบเทียบ FI vs TRN (Monthly และ YTD)
- แสดง validation results
- ดาวน์โหลด error files

**📈 Analytics Tab**
- แสดง Anomaly Detection Results (4 levels)
- กราฟ Revenue Trends จากข้อมูลจริง
- กราฟ Revenue by Business Group
- สถิติข้อมูลโดยรวม

**📋 Logs Tab**
- แสดง log files แบบ real-time
- กรอง logs ตาม level (ERROR, WARNING, INFO, etc.)
- ค้นหาใน logs
- แสดง error files พร้อมดาวน์โหลด

**⚙️ Configuration Editor (Sidebar)**
- แก้ไข Processing Year/Month
- ปรับ Reconciliation settings
- ปรับ Anomaly Detection parameters
- Sync เดือนระหว่าง FI และ ETL

---

## ⚙️ Configuration

### Overview

ระบบใช้ไฟล์ `config.json` เป็น central configuration โดยแบ่งเป็น sections หลักๆ ดังนี้:

1. **Environment & Paths** - การตั้งค่าพื้นฐานและ paths ตาม OS
2. **Processing Settings** - ปีและเดือนที่ประมวลผล
3. **FI Module** - การตั้งค่าสำหรับ FI processing
4. **ETL Module** - การตั้งค่าสำหรับ ETL pipeline
5. **Logging** - การตั้งค่า logging system

> **สำหรับรายละเอียดครบถ้วนของ config.json โปรดดูที่ [SETUP_GUIDE.md](SETUP_GUIDE.md#-configuration-reference)**

---

## 📊 ขั้นตอนการประมวลผล

### Phase 1: FI Revenue Expense Processing

```
┌─────────────────────────────────────────────────────┐
│  1. Load Master Files                               │
│     ├── MASTER_EXPENSE_GL_CODE                      │
│     ├── MASTER_REVENUE_GL_CODE                      │
│     ├── MASTER_OTHER_REVENUE_NET                    │
│     └── master_revenue_expense_net                  │
├─────────────────────────────────────────────────────┤
│  2. Read Input File                                 │
│     └── pld_nt_{YYYYMMDD}.txt (TIS-620 encoding)   │
├─────────────────────────────────────────────────────┤
│  3. Process Expense                                 │
│     ├── Filter GL codes (51, 53, 54, 59, 52)       │
│     ├── Map with MASTER_EXPENSE                     │
│     └── Group by CODE_GROUP                         │
├─────────────────────────────────────────────────────┤
│  4. Process Revenue                                 │
│     ├── Filter GL codes (4x)                        │
│     ├── Map with MASTER_REVENUE                     │
│     ├── Separate Other Revenue                      │
│     └── Process Financial Income                    │
├─────────────────────────────────────────────────────┤
│  5. Generate Excel Report                           │
│     └── pl_combined_output_{YYYYMM}.xlsx            │
│         ├── Sheet: expense_nt                       │
│         ├── Sheet: revenue_nt                       │
│         └── Sheet: summary_other                    │
└─────────────────────────────────────────────────────┘
```

**Output Files:**
- `pl_combined_output_{YYYYMM}.xlsx` - รายงาน Excel รวม
- `pl_expense_nt_output_{YYYYMM}.csv` - ข้อมูล Expense (UTF-8)
- `pl_revenue_nt_output_{YYYYMM}.csv` - ข้อมูล Revenue (UTF-8)

### Phase 2: Revenue ETL Pipeline

```
┌─────────────────────────────────────────────────────┐
│  STEP 0: Reconciliation (Optional)                  │
│     ├── Compare FI vs TRN (Monthly)                 │
│     ├── Compare FI vs TRN (YTD)                     │
│     └── Generate reconciliation logs                │
│         ├── reconcile_summary_{timestamp}.txt       │
│         ├── reconcile_monthly_errors_{timestamp}.csv│
│         └── reconcile_ytd_errors_{timestamp}.csv    │
├─────────────────────────────────────────────────────┤
│  STEP 1: Concatenate CSV Files                      │
│     ├── TRN_REVENUE_NT1_*.csv                       │
│     ├── TRN_REVENUE_ADJ_GL_NT1_*.csv                │
│     ├── TRN_REVENUE_ADJ_*.csv                       │
│     └── Output: trn_revenue_nt_2025.csv             │
├─────────────────────────────────────────────────────┤
│  STEP 2: Map Cost Center                            │
│     ├── Read MAPPING_CC.csv                         │
│     ├── Map COST_CENTER_OLD → COST_CENTER_NEW       │
│     └── Output: revenue_new_cc_2025.csv             │
├─────────────────────────────────────────────────────┤
│  STEP 3: Map Product Codes                          │
│     ├── Read MAP_PRODUCT_NT_NEW_2024.csv            │
│     ├── Apply Special Mappings                      │
│     │   └── GSaaS to Other Revenue                  │
│     └── Output: revenue_mapped_product_2025.csv     │
├─────────────────────────────────────────────────────┤
│  STEP 4: Merge with Master Files                    │
│     ├── Merge with MASTER_PRODUCT                   │
│     ├── Merge with MASTER_REVENUE_GL_CODE           │
│     ├── Apply Business Rules                        │
│     └── Generate error files                        │
│         ├── error_gl_REVENUE_NT_REPORT_2025.csv     │
│         └── error_product_REVENUE_NT_REPORT_2025.csv│
├─────────────────────────────────────────────────────┤
│  STEP 5: Anomaly Detection (4 Levels)               │
│     ├── Product Level                               │
│     ├── Service Group Level                         │
│     ├── Business Group Level                        │
│     └── Grand Total Level                           │
├─────────────────────────────────────────────────────┤
│  STEP 6: Generate Excel Report                      │
│     └── REVENUE_NT_REPORT_2025.xlsx                 │
│         ├── All sheets with anomaly highlighting    │
│         └── Pivot tables and charts                 │
└─────────────────────────────────────────────────────┘
```

**Output Files:**
- `REVENUE_NT_REPORT_2025.xlsx` - รายงานหลัก (Multi-sheet)
- `REVENUE_NT_REPORT_2025.csv` - ข้อมูล CSV รวม
- `trn_revenue_nt_2025.csv` - ข้อมูล transaction รวม
- `error_gl_*.csv` - GL codes ที่มีปัญหา
- `error_product_*.csv` - Product codes ที่มีปัญหา

---

## 🚨 Troubleshooting

### Common Issues และวิธีแก้ไข

#### 1. ❌ Month Mismatch Error
```
🚨 เดือนไม่ตรงกัน! FI: 09, ETL: 10 → Reconciliation จะล้มเหลว
```
**สาเหตุ:** FI และ ETL ใช้เดือนไม่เท่ากัน
**วิธีแก้:**
- **CLI:** ใช้ `--month 10` เพื่อ sync ทั้งคู่
- **Web App:** ไปที่ Configuration Editor → กด "🔄 Sync เดือนให้ตรงกัน"

#### 2. ❌ Reconciliation Failed
```
❌ Reconciliation ล้มเหลว - หยุดการทำงาน
```
**สาเหตุ:** ยอดรวม FI และ TRN ไม่ตรงกัน
**วิธีแก้:**
1. ตรวจสอบว่าใช้เดือนเดียวกัน
2. ดู log files ใน `revenue/output/reconcile_logs/`
3. ตรวจสอบ tolerance ใน config
4. พิจารณาปิด reconciliation ชั่วคราว (`"enabled": false`)

#### 3. ❌ Master File Not Found
```
❌ expense: MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv (Not found)
```
**สาเหตุ:** Path ไม่ถูกต้องหรือไฟล์ไม่มี
**วิธีแก้:**
1. ตรวจสอบว่าไฟล์อยู่ใน `master_path/source/` (สำหรับไฟล์ที่ไม่มี "/" ในชื่อ)
2. ตรวจสอบชื่อไฟล์ให้ตรงกับใน `config.json`
3. ดู expected path ใน Web App Dashboard

#### 4. ❌ Encoding Error
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
**สาเหตุ:** Encoding ของไฟล์ไม่ตรงกับที่ระบุ
**วิธีแก้:**
- ไฟล์ FI input ควรเป็น `tis-620`
- Master files ควรเป็น `utf-8`
- ตรวจสอบ `fi_module.encoding` ใน config

#### 5. ❌ Permission Denied
```
PermissionError: [Errno 13] Permission denied
```
**วิธีแก้:**
- ตรวจสอบสิทธิ์การเข้าถึง folder
- ปิดไฟล์ Excel ที่เปิดอยู่
- ใช้ sudo (Linux/Mac) หรือ Run as Administrator (Windows) ถ้าจำเป็น

---

## 📁 Output Files Reference

### FI Module Outputs

**Location:** `{base_path}/{year}/fi/output/`

| ไฟล์ | รายละเอียด |
|------|-----------|
| `pl_combined_output_{YYYYMM}.xlsx` | รายงาน Excel รวม 3 sheets |
| `pl_expense_nt_output_{YYYYMM}.csv` | ข้อมูล Expense (UTF-8) |
| `pl_revenue_nt_output_{YYYYMM}.csv` | ข้อมูล Revenue (UTF-8) สำหรับ reconciliation |

### ETL Module Outputs

**Location:** `{base_path}/{year}/revenue/output/`

| ไฟล์ | รายละเอียด |
|------|-----------|
| `trn_revenue_nt_{YYYY}.csv` | ข้อมูล transaction รวมทุกเดือน |
| `revenue_new_cc_{YYYY}.csv` | หลัง map cost center |
| `revenue_mapped_product_{YYYY}_.csv` | หลัง map product |

**Location:** `{base_path}/all/revenue/{year}/`

| ไฟล์ | รายละเอียด |
|------|-----------|
| `REVENUE_NT_REPORT_{YYYY}.xlsx` | รายงานหลัก (Multi-sheet) พร้อม anomaly detection |
| `REVENUE_NT_REPORT_{YYYY}.csv` | ข้อมูล CSV รวม |
| `error_gl_REVENUE_NT_REPORT_{YYYY}.csv` | GL codes ที่ไม่พบใน master |
| `error_product_REVENUE_NT_REPORT_{YYYY}.csv` | Product codes ที่ไม่พบใน master |

### Reconciliation Outputs

**Location:** `{base_path}/{year}/revenue/output/reconcile_logs/`

| ไฟล์ | รายละเอียด |
|------|-----------|
| `reconcile_summary_{YYYY}_{timestamp}.txt` | สรุปผลการ reconcile |
| `reconcile_monthly_errors_{YYYY}_{timestamp}.csv` | รายการที่แตกต่าง (Monthly) |
| `reconcile_ytd_errors_{YYYY}_{timestamp}.csv` | รายการที่แตกต่าง (YTD) |

---

## 🔄 Version History

### v2.1.0 (Current - November 2025)
- ✨ เพิ่ม Web Application พร้อม UI ที่สมบูรณ์
- ✨ ระบบตรวจสอบและ sync เดือนอัตโนมัติ
- ✨ แสดง Reconciliation Results จาก log files จริง
- ✨ แสดง Anomaly Detection Results แบบ interactive
- ✨ Configuration Editor ใน Web UI
- ✨ Real-time progress tracking
- 🐛 แก้ไข path handling สำหรับ master files
- 🐛 แก้ไข reconciliation parsing
- 📚 ปรับปรุงเอกสารให้ครบถ้วน

### v2.0.0
- ✨ ปรับโครงสร้างเป็น Modular Architecture
- ✨ เพิ่ม Configuration Management
- ✨ รองรับ Cross-platform
- ✨ เพิ่ม Command Line Interface
- ✨ ปรับปรุง Error Handling

### v1.0.0
- 🎉 Initial release
- ✅ FI Revenue Expense Processing
- ✅ Revenue ETL Pipeline
- ✅ Basic Reconciliation

---

## 📞 Support & Contact

### การรายงานปัญหา
หากพบปัญหาหรือต้องการความช่วยเหลือ:

1. ตรวจสอบ [Troubleshooting](#-troubleshooting) ด้านบน
2. ดู log files ใน `logs/` directory
3. ดู reconciliation logs ใน `revenue/output/reconcile_logs/`
4. ติดต่อทีมพัฒนา

### การขอ Feature ใหม่
- เปิด issue ใน repository
- ติดต่อทีมพัฒนาโดยตรง

---

## 📄 License

Copyright © 2025 Revenue ETL System. All rights reserved.

**Proprietary Software** - ห้ามทำซ้ำ แจกจ่าย หรือดัดแปลงโดยไม่ได้รับอนุญาต

---

## 🙏 Acknowledgments

พัฒนาโดย Revenue ETL Team
**Version:** 2.1.0
**Last Updated:** November 2025
