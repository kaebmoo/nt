# Revenue ETL System v2.2

## ระบบประมวลผลข้อมูลรายได้แบบ Modular พร้อม Multi-tier GL Validation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![Version](https://img.shields.io/badge/version-2.2.0-green.svg)]()

---

## ภาพรวมระบบ

Revenue ETL System เป็นระบบประมวลผลข้อมูลรายได้ที่ออกแบบมาเป็น **Modular Architecture** พร้อมระบบ **Configuration Management** ที่ยืดหยุ่น, **Multi-tier GL Validation** สำหรับตรวจสอบความถูกต้องของข้อมูล และ **Web Interface** ที่ใช้งานง่าย

### คุณสมบัติหลัก

#### Core Features
- **Configuration Management** - จัดการ config ผ่านไฟล์ JSON แบบ centralized
- **Modular Design** - แยก module ชัดเจน (FI, ETL, Reconciliation) ง่ายต่อการบำรุงรักษา
- **Cross-Platform Support** - รองรับ Windows, macOS, Linux อัตโนมัติ
- **Web Application** - UI ที่ใช้งานง่าย สร้างด้วย Streamlit (อยู่ใน `revenue-report-web`)
- **Command Line Interface** - รองรับการรันผ่าน CLI พร้อม options ต่างๆ

#### Data Processing Features
- **FI Module** - ประมวลผลงบการเงิน (Financial Income Statement) จาก SAP
- **ETL Pipeline** - ประมวลผล Transaction Revenue แบบ end-to-end (Step 0-5)
- **Data Reconciliation** - ตรวจสอบความถูกต้องระหว่าง FI และ Transaction (ทุก GL)
- **Multi-tier GL Validation** - ตรวจสอบ GL 4 ระดับใน Step 4 พร้อม graceful stop
- **Anomaly Detection** - ตรวจจับความผิดปกติของข้อมูล 4 ระดับ
- **Business Rules Engine** - กฎทางธุรกิจที่ปรับแต่งได้

#### Advanced Features
- **Logging System** - บันทึก log แบบ structured พร้อม rotation
- **Graceful Pipeline Control** - หยุดการทำงานอย่างสวยงาม (ไม่มี error traceback)
- **Financial Statement Validation** - เทียบยอดกับงบการเงิน Excel
- **Template Support** - ชื่อไฟล์แบบ dynamic (YYYY, MM, DD)
- **Month Sync** - ตรวจสอบและ sync เดือนระหว่าง FI และ ETL อัตโนมัติ

---

## โครงสร้างระบบ

### System Architecture

```
Revenue ETL System v2.2
│
├─── Configuration Layer
│    └── config.json (Centralized Configuration)
│
├─── Core Modules
│    ├── FI Module (Financial Income Statement Processing)
│    ├── ETL Module (Revenue ETL Pipeline + GL Validation)
│    └── Reconciliation Module (Step 0 - FI vs TRN Validation)
│
├─── Interface Layer
│    ├── CLI (main.py)
│    └── Web UI (revenue-report-web/ — แยก repo)
│
└─── Support Layer
     ├── Config Manager (Configuration Management)
     ├── ConfigAdapter (Config → ETL attribute mapping)
     ├── Logger Utils (Logging System)
     └── Error Handling (Graceful Pipeline Control)
```

### ไฟล์ในระบบ

```
revenue-report/
│
├── Configuration
│   └── config.json                    # ไฟล์ configuration หลัก
│
├── Main Applications
│   └── main.py                        # CLI Application
│
├── Core Modules
│   ├── config_manager.py              # Configuration Manager
│   ├── fi_revenue_expense_module.py   # FI Processing Module
│   ├── revenue_etl_report.py          # ETL Pipeline Module + GL Validation
│   ├── revenue_reconciliation.py      # Reconciliation Module (Step 0)
│   └── logger_utils.py                # Logging Utilities
│
├── Documentation
│   ├── README.md                      # คู่มือหลัก (ไฟล์นี้)
│   └── SETUP_GUIDE.md                 # คู่มือการติดตั้งและตั้งค่า
│
├── Dependencies
│   └── requirements.txt               # Python packages
│
└── Runtime (Generated)
    └── logs/                          # Log files
        ├── system_YYYYMMDD.log
        ├── fi_module_YYYYMMDD.log
        ├── etl_module_YYYYMMDD.log
        └── config_manager_YYYYMMDD.log
```

---

## Quick Start

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

## การใช้งาน

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

Web Application อยู่ใน repository แยก: `revenue-report-web/`

ดูรายละเอียดได้ที่ [revenue-report-web/README.md](../revenue-report-web/README.md)

---

## ขั้นตอนการประมวลผล

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
- `pl_revenue_nt_output_{YYYYMM}.csv` - ข้อมูล Revenue (UTF-8) — ใช้ใน Step 0 Reconciliation

### Phase 2: Revenue ETL Pipeline

```
┌─────────────────────────────────────────────────────┐
│  STEP 0: Reconciliation (FI vs TRN)                 │
│     ├── เทียบ ทุก GL ราย GL (Primary Check)         │
│     │   ├── FI Monthly vs TRN Monthly               │
│     │   └── FI YTD vs TRN YTD                       │
│     ├── ถ้าตรงทั้งหมด → PASSED ✅                    │
│     ├── ถ้าไม่ตรง → หัก ADJ_GL แล้วเทียบใหม่        │
│     │   └── (Secondary Check)                       │
│     ├── ถ้า secondary ตรง → WARNING ⚠️ → ไปต่อ      │
│     └── Generate reconciliation logs                │
├─────────────────────────────────────────────────────┤
│  STEP 1: Concatenate CSV Files                      │
│     ├── TRN_REVENUE_NT1_*.csv        (รายได้หลัก)    │
│     ├── TRN_REVENUE_ADJ_GL_NT1_*.csv (GL transfers) │
│     ├── TRN_REVENUE_ADJ_*.csv        (ผลตอบแทนฯ)   │
│     └── Output: trn_revenue_nt_{YYYY}.csv           │
├─────────────────────────────────────────────────────┤
│  STEP 2: Map Cost Center                            │
│     ├── Read MAPPING_CC.csv                         │
│     ├── Map COST_CENTER_OLD → COST_CENTER_NEW       │
│     └── Output: revenue_new_cc_{YYYY}.csv           │
├─────────────────────────────────────────────────────┤
│  STEP 3: Map Product Codes                          │
│     ├── Read MAP_PRODUCT_NT_NEW_2024.csv            │
│     ├── Apply Special Mappings (e.g. GSaaS)         │
│     └── Output: revenue_mapped_product_{YYYY}.csv   │
├─────────────────────────────────────────────────────┤
│  STEP 4: Merge with Master + GL Validation          │
│     ├── Merge with MASTER_PRODUCT                   │
│     ├── Merge with MASTER_REVENUE_GL_CODE           │
│     ├── Apply Business Rules                        │
│     ├── Generate error files                        │
│     └── 🔒 Multi-tier GL Validation (ดูด้านล่าง)    │
├─────────────────────────────────────────────────────┤
│  STEP 5: Anomaly Detection (4 Levels)               │
│     ├── Product Level                               │
│     ├── Service Group Level                         │
│     ├── Business Group Level                        │
│     └── Grand Total Level                           │
│     └── Generate Excel Report                       │
│         └── REVENUE_NT_REPORT_{YYYY}.xlsx           │
└─────────────────────────────────────────────────────┘
```

---

## Multi-tier GL Validation (Step 4)

หลังจาก merge ข้อมูลกับ Master files แล้ว Step 4 จะตรวจสอบความถูกต้องของ GL 4 ระดับ โดยเทียบเฉพาะ **Core GLs** (ยกเว้น GL กลุ่ม "ผลตอบแทนทางการเงินและรายได้อื่น") กับข้อมูล FI:

```
Step 4 GL Validation Flow
│
├── Check 1: GL by GL Comparison
│   ├── เทียบ Core GL ราย GL (FI vs TRN)
│   ├── ทั้ง Monthly และ YTD
│   └── ✅ ตรงทุก GL → PASSED → ไปต่อ Step 5
│
├── Check 2: หัก ADJ_GL แล้วเทียบใหม่
│   ├── หัก TRN_REVENUE_ADJ_GL (zero-sum GL transfers) ออก
│   ├── เทียบ GL by GL อีกครั้ง
│   └── ✅ ตรงทุก GL → WARNING → ไปต่อ Step 5
│
├── Check 3: Net Total Comparison
│   ├── รวมยอด Core GLs ทั้งหมด (ไม่ดูรายตัว)
│   ├── เทียบ FI sum vs TRN sum
│   └── ✅ ยอดรวมตรง → WARNING → ไปต่อ Step 5
│       💡 รายงานออกในมิติ Product ไม่ใช่ GL
│
└── Check 4: เทียบกับงบการเงิน (Financial Statement)
    ├── อ่านไฟล์ Excel งบการเงิน (sheet PLสะสม)
    ├── คำนวณ: รวมรายได้ - รายได้อื่น = รายได้จากการให้บริการ
    ├── เทียบกับ TRN Core GLs YTD
    ├── ✅ ตรง → WARNING → ไปต่อ Step 5
    │   💡 FI file อาจยังไม่ update แต่ TRN ตรงกับงบการเงิน
    └── ❌ ไม่ตรงทุกวิธี → หยุด Pipeline (graceful stop)
```

### ความแตกต่างระหว่าง Step 0 กับ Step 4 Validation

| รายการ | Step 0 Reconciliation | Step 4 GL Validation |
|--------|----------------------|---------------------|
| **ขอบเขต GL** | ทุก GL (รวม ผลตอบแทนฯ) | เฉพาะ Core GL (ยกเว้น ผลตอบแทนฯ) |
| **จุดประสงค์** | ตรวจข้อมูลดิบ FI vs TRN | ตรวจหลัง merge กับ Master |
| **เมื่อไม่ผ่าน** | WARNING → ไปต่อ | 4-tier check → ไม่ผ่านทุกวิธี = หยุด |
| **จำนวน check** | 2 (primary + secondary) | 4 (GL→ADJ_GL→Net Total→งบการเงิน) |
| **การหยุด** | ไม่หยุด (WARNING) | หยุด graceful (return None) |

### ประเภทไฟล์ข้อมูลที่เกี่ยวข้อง

| ไฟล์ | คำอธิบาย | ใช้ใน |
|------|----------|-------|
| `TRN_REVENUE_NT1_*.csv` | รายได้หลักจาก Transaction | Step 0, Step 1-4 |
| `TRN_REVENUE_ADJ_GL_NT1_*.csv` | GL transfers (ยอดรวม = 0) | Step 0 (secondary), Step 4 (Check 2) |
| `TRN_REVENUE_ADJ_*.csv` | ผลตอบแทนฯ adjustments | Step 1 (concat เข้ารายงาน) |
| `pl_revenue_nt_output_{YYYYMM}.csv` | FI revenue จาก SAP | Step 0, Step 4 |
| งบการเงิน*.xlsx | Financial Statement Excel | Step 4 (Check 4) |

### Graceful Pipeline Stop

เมื่อ Step 4 Validation ไม่ผ่านทุก check pipeline จะหยุดอย่างสวยงาม:
- ไม่มี error traceback — ใช้ `return None` แทน `raise`
- แสดง log ชัดเจนว่าหยุดเพราะอะไร
- Web Application รองรับการหยุดกลางคัน (แสดง error บน UI)

---

## Configuration

### Overview

ระบบใช้ไฟล์ `config.json` เป็น central configuration โดยแบ่งเป็น sections หลักๆ ดังนี้:

1. **Environment & Paths** - การตั้งค่าพื้นฐานและ paths ตาม OS
2. **Processing Settings** - ปีและเดือนที่ประมวลผล
3. **FI Module** - การตั้งค่าสำหรับ FI processing
4. **ETL Module** - การตั้งค่าสำหรับ ETL pipeline
5. **Validation** - การตั้งค่า GL Validation และงบการเงิน
6. **Logging** - การตั้งค่า logging system

### Validation Configuration (v2.2 ใหม่)

```json
"validation": {
  "grand_total_diff_threshold": 0.01,
  "required_columns": [
    "YEAR", "MONTH", "CUSTOMER_GROUP_KEY", "PRODUCT_KEY",
    "SUB_PRODUCT_KEY", "GL_CODE", "COST_CENTER", "REVENUE_VALUE"
  ],
  "fi_statement_file": "/path/to/งบการเงิน ณ วันที่ 31 ธันวาคม 2568 ... เอกสารแนบ 1.xlsx",
  "fi_statement_dir": "/path/to/fi"
}
```

| Key | คำอธิบาย | ตัวอย่าง |
|-----|----------|---------|
| `grand_total_diff_threshold` | ค่า tolerance สำหรับเทียบยอดรวม | `0.01` (บาท) |
| `required_columns` | คอลัมน์ที่ต้องมีในข้อมูลขั้นสุดท้าย | — |
| `fi_statement_file` | **path ไฟล์งบการเงิน (primary)** — ระบุตรง, เปลี่ยนได้ง่าย | ไฟล์ Excel ที่ต้องการ |
| `fi_statement_dir` | **directory สำรอง (fallback)** — ค้นหาด้วย glob pattern | โฟลเดอร์ที่เก็บงบการเงิน |

#### การค้นหาไฟล์งบการเงิน (Check 4)

ระบบค้นหาไฟล์งบการเงินตามลำดับความสำคัญ:

1. **Primary** — ใช้ `fi_statement_file` (explicit path จาก config)
   - ถ้าไฟล์มีอยู่จริง → ใช้เลย
   - ข้อดี: ระบุตรง, ไม่สับสนเมื่อมีหลายไฟล์ใน folder เดียวกัน
2. **Fallback** — ถ้า `fi_statement_file` ไม่พบ → ค้นหาจาก `fi_statement_dir`
   - ค้นหาด้วย glob: `งบการเงิน*เอกสารแนบ*.xlsx`
   - fallback: `งบกำไรขาดทุน*สะสม*เอกสารแนบ*.xlsx`
   - ใช้ไฟล์ล่าสุด (sorted, pick last)

**เมื่อต้องเปลี่ยนเดือน/ปี:** แก้ค่า `fi_statement_file` ใน config.json ให้ชี้ไปไฟล์ใหม่

#### โครงสร้างไฟล์งบการเงิน Excel

ไฟล์งบการเงินที่ใช้ใน Check 4:
- **Sheet:** ชื่อที่มีคำว่า "PLสะสม" (เช่น "หน้างบ-PLสะสม (New)")
- **Column B (index 1):** label (ชื่อรายการ)
- **Column C (index 2):** จำนวนเงิน (หลังปรับปรุง) — **ใช้ค่านี้**
- **Row สำคัญ:** "รวมรายได้" และ "รายได้อื่น"
- **สูตร:** `รายได้จากการให้บริการ = รวมรายได้ - รายได้อื่น`

> **สำหรับรายละเอียดครบถ้วนของ config.json โปรดดูที่ [SETUP_GUIDE.md](SETUP_GUIDE.md#-configuration-reference)**

---

## โครงสร้างรายงานสุดท้าย

รายงานหลัก (`REVENUE_NT_REPORT_{YYYY}.xlsx`) มีโครงสร้างรายได้:

```
รวมรายได้จากการให้บริการ          ← Core GLs (ตรวจ Step 4)
  ├── Mobile
  ├── Fixed Broadband
  ├── Enterprise / ICT
  └── ... (ตาม Business Group)

+ รวมผลตอบแทนทางการเงินและรายได้อื่น  ← จาก ADJ files
  ├── ผลตอบแทนทางการเงิน
  └── รายได้อื่น

= รวมรายได้ทั้งสิ้น
```

---

## Output Files Reference

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
| `trn_revenue_nt_{YYYY}.csv` | ข้อมูล transaction รวมทุกเดือน (Step 1) |
| `revenue_new_cc_{YYYY}.csv` | หลัง map cost center (Step 2) |
| `revenue_mapped_product_{YYYY}_.csv` | หลัง map product (Step 3) |

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
| `reconcile_summary_{YYYY}_{timestamp}.txt` | สรุปผลการ reconcile (Step 0) |
| `reconcile_monthly_errors_{YYYY}_{timestamp}.csv` | รายการที่แตกต่าง (Monthly) |
| `reconcile_ytd_errors_{YYYY}_{timestamp}.csv` | รายการที่แตกต่าง (YTD) |

---

## Troubleshooting

### Common Issues และวิธีแก้ไข

#### 1. Month Mismatch Error
```
🚨 เดือนไม่ตรงกัน! FI: 09, ETL: 10 → Reconciliation จะล้มเหลว
```
**สาเหตุ:** FI และ ETL ใช้เดือนไม่เท่ากัน
**วิธีแก้:**
- **CLI:** ใช้ `--month 10` เพื่อ sync ทั้งคู่
- **Web App:** ไปที่ Configuration Editor → กด Sync เดือนให้ตรงกัน

#### 2. Step 0 Reconciliation Warning
```
⚠️ Secondary check ผ่าน (หลังหัก ADJ_GL)
```
**สาเหตุ:** ยอด FI และ TRN ไม่ตรงเมื่อเทียบตรง แต่ตรงหลังหัก ADJ_GL
**หมายความว่า:** มี GL transfer (ADJ_GL) ที่ทำให้ยอดเปลี่ยน — ปกติ, pipeline ไปต่อได้

#### 3. Step 4 GL Validation Failed — Pipeline หยุด
```
❌ ไม่ผ่านการตรวจสอบทุกวิธี — หยุดการทำงาน
```
**สาเหตุ:** Core GLs ไม่ตรงกับ FI ทุก 4 วิธี (GL, ADJ_GL, Net Total, งบการเงิน)
**วิธีแก้:**
1. ตรวจสอบ log ว่าแต่ละ check ผิดอะไร
2. ตรวจสอบว่า FI file เป็นเดือนล่าสุดหรือไม่
3. ตรวจสอบ `fi_statement_file` ใน config.json ว่าชี้ไปงบการเงินที่ถูกต้อง
4. ตรวจสอบ ADJ_GL files ว่ามีครบไม่

#### 4. ไม่พบไฟล์งบการเงิน (Check 4)
```
⚠️ ไม่พบไฟล์งบการเงิน — ตรวจสอบ fi_statement_file และ fi_statement_dir ใน config
```
**วิธีแก้:**
1. ตรวจสอบ `fi_statement_file` ใน config.json ว่า path ถูกต้อง
2. ตรวจสอบว่าไฟล์ยังอยู่ที่ path นั้น
3. ถ้าไม่ได้ระบุ → ตรวจสอบ `fi_statement_dir` ว่ามีไฟล์งบการเงินอยู่
4. ตรวจสอบชื่อ sheet ว่ามีคำว่า "PLสะสม"

#### 5. Master File Not Found
```
❌ expense: MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv (Not found)
```
**สาเหตุ:** Path ไม่ถูกต้องหรือไฟล์ไม่มี
**วิธีแก้:**
1. ตรวจสอบว่าไฟล์อยู่ใน `master_path/source/`
2. ตรวจสอบชื่อไฟล์ให้ตรงกับใน `config.json`
3. ดู expected path ใน Web App Dashboard

#### 6. Encoding Error
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
**สาเหตุ:** Encoding ของไฟล์ไม่ตรงกับที่ระบุ
**วิธีแก้:**
- ไฟล์ FI input ควรเป็น `tis-620`
- Master files ควรเป็น `utf-8`
- ตรวจสอบ `fi_module.encoding` ใน config

#### 7. Permission Denied
```
PermissionError: [Errno 13] Permission denied
```
**วิธีแก้:**
- ตรวจสอบสิทธิ์การเข้าถึง folder
- ปิดไฟล์ Excel ที่เปิดอยู่

---

## Version History

### v2.2.0 (Current - March 2026)
- **Multi-tier GL Validation** — ตรวจสอบ GL 4 ระดับใน Step 4
  - Check 1: GL by GL comparison (Core GLs)
  - Check 2: หัก ADJ_GL แล้วเทียบใหม่
  - Check 3: Net total comparison
  - Check 4: เทียบกับงบการเงิน Excel (PLสะสม)
- **Step 0 ตรวจทุก GL** — Reconciliation เทียบทุก GL (ไม่กรอง) เป็น primary check
- **Graceful Pipeline Stop** — ใช้ `return None` แทน `raise` ไม่มี error traceback
- **Financial Statement Config** — เพิ่ม `fi_statement_file` (primary) + `fi_statement_dir` (fallback)
- **ConfigAdapter ปรับปรุง** — รองรับ `FI_STATEMENT_FILE` และ `FI_STATEMENT_DIR`

### v2.1.0 (November 2025)
- เพิ่ม Web Application พร้อม UI ที่สมบูรณ์
- ระบบตรวจสอบและ sync เดือนอัตโนมัติ
- แสดง Reconciliation Results จาก log files จริง
- แสดง Anomaly Detection Results แบบ interactive
- Configuration Editor ใน Web UI
- Real-time progress tracking

### v2.0.0
- ปรับโครงสร้างเป็น Modular Architecture
- เพิ่ม Configuration Management
- รองรับ Cross-platform
- เพิ่ม Command Line Interface

### v1.0.0
- Initial release
- FI Revenue Expense Processing
- Revenue ETL Pipeline
- Basic Reconciliation

---

## Support & Contact

### การรายงานปัญหา
หากพบปัญหาหรือต้องการความช่วยเหลือ:

1. ตรวจสอบ [Troubleshooting](#troubleshooting) ด้านบน
2. ดู log files ใน `logs/` directory
3. ดู reconciliation logs ใน `revenue/output/reconcile_logs/`
4. ติดต่อทีมพัฒนา

---

## License

Copyright &copy; 2025-2026 Revenue ETL System. All rights reserved.

**Proprietary Software** - ห้ามทำซ้ำ แจกจ่าย หรือดัดแปลงโดยไม่ได้รับอนุญาต

---

พัฒนาโดย Revenue ETL Team
**Version:** 2.2.0
**Last Updated:** March 2026
