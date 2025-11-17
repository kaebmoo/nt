# 📦 Revenue ETL System v2.1 - Setup Guide

## คู่มือการติดตั้งและการตั้งค่าอย่างละเอียด

---

## 📑 สารบัญ

1. [การติดตั้งระบบ](#-การติดตั้งระบบ)
2. [โครงสร้าง Folder](#-โครงสร้าง-folder)
3. [Configuration Reference](#-configuration-reference)
4. [การใช้งาน Web Application](#-การใช้งาน-web-application)
5. [Troubleshooting](#-troubleshooting)
6. [Best Practices](#-best-practices)

---

## 🚀 การติดตั้งระบบ

### ข้อกำหนดเบื้องต้น

#### Software Requirements
- **Python:** 3.8 หรือสูงกว่า (แนะนำ 3.9+)
- **pip:** Version ล่าสุด
- **Git:** (ถ้าจะ clone จาก repository)

#### Hardware Requirements
- **CPU:** Intel Core i5 หรือเทียบเท่า (2 cores ขึ้นไป)
- **RAM:** อย่างน้อย 4 GB (แนะนำ 8 GB)
- **Disk Space:** อย่างน้อย 5 GB
  - 2 GB สำหรับข้อมูล
  - 1 GB สำหรับ logs
  - 2 GB สำหรับ output files

#### Operating System
- Windows 10/11 (64-bit)
- macOS 10.14 (Mojave) หรือสูงกว่า
- Linux (Ubuntu 18.04+, CentOS 7+, หรือเทียบเท่า)

---

### ขั้นตอนการติดตั้ง

#### Step 1: ดาวน์โหลดและแตกไฟล์

```bash
# Option A: ใช้ Git Clone
git clone https://github.com/your-org/revenue-report.git
cd revenue-report

# Option B: แตกไฟล์ ZIP
unzip revenue_etl_system_v2.1.zip
cd revenue-report
```

#### Step 2: ติดตั้ง Python Dependencies

**สำหรับ Windows:**
```powershell
# ตรวจสอบ Python version
python --version

# อัพเกรด pip
python -m pip install --upgrade pip

# ติดตั้ง dependencies
pip install -r requirements.txt
```

**สำหรับ macOS/Linux:**
```bash
# ตรวจสอบ Python version
python3 --version

# อัพเกรด pip
python3 -m pip install --upgrade pip

# ติดตั้ง dependencies
pip3 install -r requirements.txt
```

#### Step 3: ตรวจสอบการติดตั้ง

```bash
# ทดสอบ import modules
python -c "import pandas; import openpyxl; import streamlit; print('✓ All packages installed')"
```

---

## 📁 โครงสร้าง Folder

### โครงสร้างข้อมูล (Data Directory Structure)

```
{base_path}/
│
├── {year}/                          # ปีที่ประมวลผล เช่น 2025/
│   │
│   ├── fi/                          # FI Module Data
│   │   ├── pld_nt_20251031.txt     # Input file (TIS-620 encoding)
│   │   └── output/                  # Output directory (auto-created)
│   │       ├── pl_combined_output_202510.xlsx
│   │       ├── pl_expense_nt_output_202510.csv
│   │       └── pl_revenue_nt_output_202510.csv
│   │
│   └── revenue/                     # ETL Module Data
│       ├── TRN_REVENUE_NT1_01.csv  # Transaction files
│       ├── TRN_REVENUE_NT1_02.csv
│       ├── ...
│       └── output/                  # Output directory (auto-created)
│           ├── trn_revenue_nt_2025.csv
│           ├── revenue_new_cc_2025.csv
│           ├── revenue_mapped_product_2025.csv
│           └── reconcile_logs/      # Reconciliation logs
│               ├── reconcile_summary_*.txt
│               ├── reconcile_monthly_errors_*.csv
│               └── reconcile_ytd_errors_*.csv
│
└── all/                             # Final outputs
    └── revenue/
        └── 2025/
            ├── REVENUE_NT_REPORT_2025.xlsx
            ├── REVENUE_NT_REPORT_2025.csv
            ├── error_gl_REVENUE_NT_REPORT_2025.csv
            └── error_product_REVENUE_NT_REPORT_2025.csv
```

### โครงสร้าง Master Files

```
{master_path}/
│
├── source/                          # Master files สำหรับ FI Module
│   ├── MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv
│   ├── MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv
│   ├── MASTER_OTHER_REVENUE_NET.csv
│   └── master_revenue_expense_net.csv
│
├── MASTER_PRODUCT_NT_2025.csv       # Master product
├── MAPPING_CC.csv                   # Cost center mapping
│
└── clean/                           # Cleaned master files
    └── MAP_PRODUCT_NT_NEW_2024.csv  # Product mapping
```

---

## ⚙️ Configuration Reference

### Overview

ไฟล์ `config.json` เป็น **ศูนย์กลาง** ในการตั้งค่าทั้งระบบ แบ่งเป็น 5 sections หลัก:

```json
{
  "environment": { ... },           // 1. Environment settings
  "paths": { ... },                 // 2. OS-specific paths
  "processing_year": "2025",        // 3. Processing year
  "processing_months": { ... },     // 4. Processing months
  "fi_module": { ... },            // 5. FI Module config
  "etl_module": { ... },           // 6. ETL Module config
  "logging": { ... }               // 7. Logging config
}
```

---

### 1. Environment Section

```json
"environment": {
  "name": "production",
  "description": "Revenue ETL Configuration"
}
```

**คำอธิบาย:**
- `name` - ชื่อ environment (เช่น `production`, `development`, `testing`)
- `description` - คำอธิบาย configuration นี้

**การใช้งาน:**
- ใช้แยก config ระหว่าง production และ development
- สามารถมีหลายไฟล์ config สำหรับแต่ละ environment

---

### 2. Paths Section

```json
"paths": {
  "darwin": {
    "base_path": "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/Datasource",
    "master_path": "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/master"
  },
  "linux": {
    "base_path": "/home/seal/nt/data",
    "master_path": "/home/seal/nt/master"
  },
  "windows": {
    "base_path": "C:\\Users\\00320845\\OneDrive\\share\\Datasource",
    "master_path": "C:\\Users\\00320845\\OneDrive\\share\\master"
  }
}
```

**คำอธิบาย:**

**`darwin` (macOS):**
- `base_path` - path หลักสำหรับข้อมูล (input และ output)
- `master_path` - path สำหรับ master files

**`linux`:**
- ตั้งค่าสำหรับ Linux OS
- Format เดียวกับ darwin

**`windows`:**
- ตั้งค่าสำหรับ Windows OS
- ใช้ `\\` (double backslash) หรือ `/` (forward slash)

**Path Logic:**
```
base_path/{year}/fi/          → FI input files
base_path/{year}/fi/output/   → FI output files
base_path/{year}/revenue/     → ETL input files
base_path/{year}/revenue/output/ → ETL intermediate files
base_path/all/revenue/{year}/ → ETL final outputs
master_path/source/           → FI master files
master_path/                  → ETL master files
```

**การเลือก OS อัตโนมัติ:**
- ระบบจะเลือก paths ตาม OS ที่รันโดยอัตโนมัติ
- macOS → `darwin`
- Linux → `linux`
- Windows → `windows`

---

### 3. Processing Year

```json
"processing_year": "2025"
```

**คำอธิบาย:**
- ปีที่ต้องการประมวลผล (รูปแบบ: "YYYY")
- ใช้ในการสร้าง paths และชื่อไฟล์

**ตัวอย่างการใช้งาน:**
- Year = "2025" → paths: `/data/2025/fi/`
- Year = "2024" → paths: `/data/2024/fi/`

**การเปลี่ยนปี:**
1. แก้ไข `"processing_year": "2026"`
2. อัพเดทชื่อไฟล์ master ให้ตรงกับปีใหม่
3. สร้าง folder structure สำหรับปีใหม่

---

### 4. Processing Months

```json
"processing_months": {
  "fi_current_month": 10,
  "etl_end_month": 10
}
```

**คำอธิบาย:**

**`fi_current_month`** (1-12):
- เดือนล่าสุดที่มีข้อมูล FI
- ใช้ในการเลือก input file และสร้าง output filename
- ใช้ใน reconciliation เพื่อเทียบกับ TRN

**`etl_end_month`** (1-12):
- เดือนสิ้นสุดสำหรับ ETL processing
- ควรเท่ากับ `fi_current_month` เสมอ (เพื่อให้ reconciliation ถูกต้อง)

**⚠️ สำคัญมาก:**
```
fi_current_month = etl_end_month (ต้องเท่ากัน!)
```

**เหตุผล:**
- Reconciliation เปรียบเทียบ FI กับ TRN ของเดือนเดียวกัน
- ถ้าไม่เท่ากัน → reconciliation จะ FAILED

**Web App จะเตือนอัตโนมัติ:**
- แสดง error banner เมื่อเดือนไม่ตรงกัน
- มีปุ่ม "Sync" เพื่อแก้ไขทันที

---

### 5. FI Module Configuration

#### 5.1 Basic Settings

```json
"fi_module": {
  "description": "FI Revenue Expense Processing Configuration",
  "input_subpath": "fi",
  "output_subpath": "fi/output",
  "master_subpath": "source"
}
```

**คำอธิบาย:**
- `input_subpath` - subfolder สำหรับ input files ภายใต้ `{base_path}/{year}/`
- `output_subpath` - subfolder สำหรับ output files
- `master_subpath` - subfolder ใน master_path ที่เก็บ master files

**ผลลัพธ์:**
```
Input:  {base_path}/2025/fi/pld_nt_20251031.txt
Output: {base_path}/2025/fi/output/pl_combined_output_202510.xlsx
Master: {master_path}/source/MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv
```

#### 5.2 Input Files

```json
"input_files": [
  "pld_nt_{YYYYMMDD}.txt"
]
```

**Template Variables:**
- `{YYYY}` - ปี 4 หลัก (เช่น 2025)
- `{MM}` - เดือน 2 หลัก (เช่น 01, 10)
- `{YYYYMM}` - ปีเดือน (เช่น 202510)
- `{YYYYMMDD}` - ปีเดือนวัน (วันสุดท้ายของเดือน, เช่น 20251031)

**ตัวอย่าง:**
```
Template: pld_nt_{YYYYMMDD}.txt
Year: 2025, Month: 10
→ Result: pld_nt_20251031.txt
```

#### 5.3 Master Files

```json
"master_files": {
  "expense": "MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv",
  "revenue": "MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv",
  "other_revenue": "source/MASTER_OTHER_REVENUE_NET.csv",
  "revenue_expense_net": "source/master_revenue_expense_net.csv"
}
```

**Path Logic:**

**ไฟล์ที่ไม่มี "/" → อยู่ใน `master_path/source/`:**
```
"expense": "MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv"
→ Full path: {master_path}/source/MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv
```

**ไฟล์ที่มี "/" → relative จาก `master_path/`:**
```
"other_revenue": "source/MASTER_OTHER_REVENUE_NET.csv"
→ Full path: {master_path}/source/MASTER_OTHER_REVENUE_NET.csv
```

**รายละเอียดแต่ละไฟล์:**

| Key | Description | Format |
|-----|-------------|--------|
| `expense` | Master expense GL codes | CSV (UTF-8) |
| `revenue` | Master revenue GL codes | CSV (UTF-8) |
| `other_revenue` | Master other revenue mapping | CSV (UTF-8) |
| `revenue_expense_net` | Master revenue/expense net mapping | CSV (UTF-8) |

#### 5.4 Output Files

```json
"output_files": {
  "excel": "pl_combined_output_{YYYYMM}.xlsx",
  "csv_expense": "pl_expense_nt_output_{YYYYMM}.csv",
  "csv_revenue": "pl_revenue_nt_output_{YYYYMM}.csv"
}
```

**รายละเอียด:**
- `excel` - รายงาน Excel รวม (3 sheets: expense_nt, revenue_nt, summary_other)
- `csv_expense` - ข้อมูล Expense (UTF-8)
- `csv_revenue` - ข้อมูล Revenue (UTF-8) **สำคัญสำหรับ reconciliation**

**ตัวอย่าง:**
```
Year: 2025, Month: 10
→ pl_combined_output_202510.xlsx
→ pl_expense_nt_output_202510.csv
→ pl_revenue_nt_output_202510.csv
```

#### 5.5 Encoding

```json
"encoding": {
  "input": "tis-620",
  "output": "utf-8",
  "master": "utf-8"
}
```

**คำอธิบาย:**
- `input` - encoding ของไฟล์ input (FI data มักเป็น `tis-620`)
- `output` - encoding ของไฟล์ output (แนะนำ `utf-8`)
- `master` - encoding ของ master files (แนะนำ `utf-8`)

**Common Encodings:**
- `tis-620` - Thai Industrial Standard (ระบบเก่า)
- `utf-8` - Universal (รองรับทุกภาษา, แนะนำ)
- `cp874` - Windows Thai

#### 5.6 Processing Rules

```json
"processing_rules": {
  "delimiter": "\t",
  "expense_gl_pattern": "^(51|53|54|59|52)",
  "revenue_gl_pattern": "^4"
}
```

**คำอธิบาย:**
- `delimiter` - ตัวแบ่งคอลัมน์ในไฟล์ input (`\t` = Tab)
- `expense_gl_pattern` - Regex pattern สำหรับ GL codes ของ Expense
- `revenue_gl_pattern` - Regex pattern สำหรับ GL codes ของ Revenue

**Pattern Explanation:**
```
"^(51|53|54|59|52)"
  ^  - เริ่มต้นด้วย
  51|53|54|59|52 - GL codes ที่ขึ้นต้นด้วยเลขเหล่านี้

"^4"
  ^  - เริ่มต้นด้วย
  4  - GL codes ที่ขึ้นต้นด้วย 4
```

---

### 6. ETL Module Configuration

#### 6.1 Basic Settings

```json
"etl_module": {
  "description": "Revenue ETL Pipeline Configuration",
  "input_subpath": "revenue",
  "output_subpath": "revenue/output",
  "final_output_subpath": "all/revenue"
}
```

**Path Results:**
```
Input:  {base_path}/2025/revenue/TRN_*.csv
Output: {base_path}/2025/revenue/output/
Final:  {base_path}/all/revenue/2025/
```

#### 6.2 Reconciliation Settings

```json
"reconciliation": {
  "enabled": true,
  "fi_month": "{FI_MONTH}",
  "tolerance": 0.00
}
```

**คำอธิบาย:**

**`enabled`** (true/false):
- `true` - เปิดใช้งาน reconciliation (แนะนำ)
- `false` - ปิด reconciliation (ใช้เมื่อต้องการ skip การตรวจสอบ)

**`fi_month`** (template):
- จะถูกแทนที่ด้วย `processing_months.fi_current_month`
- ใช้ในการหาไฟล์ FI ที่จะเทียบ

**`tolerance`** (float):
- ความคลาดเคลื่อนที่ยอมรับได้ (หน่วย: THB)
- `0.00` = ต้องตรงพอดี
- `0.01` = ยอมรับความแตกต่าง ±0.01 บาท

**ตัวอย่างการใช้งาน:**
```json
// สำหรับข้อมูลที่ต้องการความแม่นยำสูง
"tolerance": 0.00

// สำหรับข้อมูลที่ยอมรับความคลาดเคลื่อนเล็กน้อย
"tolerance": 0.01
```

**Reconciliation Process:**
1. เปรียบเทียบ FI (Monthly) vs TRN (Monthly)
2. เปรียบเทียบ FI (YTD) vs TRN (YTD)
3. ตรวจสอบแต่ละ GL_CODE
4. บันทึก errors ใน `reconcile_logs/`

**Output:**
- `reconcile_summary_{timestamp}.txt` - สรุปผล
- `reconcile_monthly_errors_{timestamp}.csv` - รายการที่แตกต่าง (Monthly)
- `reconcile_ytd_errors_{timestamp}.csv` - รายการที่แตกต่าง (YTD)

#### 6.3 Master Files

```json
"master_files": {
  "product": "MASTER_PRODUCT_NT_2025.csv",
  "gl_code": "source/MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv",
  "mapping_cc": "MAPPING_CC.csv",
  "mapping_product": "clean/MAP_PRODUCT_NT_NEW_2024.csv"
}
```

**รายละเอียด:**

| File | Path | Description |
|------|------|-------------|
| `product` | `{master_path}/MASTER_PRODUCT_NT_2025.csv` | Product master |
| `gl_code` | `{master_path}/source/MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv` | GL code master |
| `mapping_cc` | `{master_path}/MAPPING_CC.csv` | Cost center mapping |
| `mapping_product` | `{master_path}/clean/MAP_PRODUCT_NT_NEW_2024.csv` | Product mapping |

#### 6.4 Input Patterns

```json
"input_patterns": {
  "main_files": [
    "TRN_REVENUE_NT1_*.csv",
    "TRN_REVENUE_ADJ_GL_NT1_*.csv"
  ],
  "adj_monthly": "TRN_REVENUE_ADJ_*.csv",
  "adj_ytd": "TRN_REVENUE_ADJ_YTD_*.csv"
}
```

**คำอธิบาย:**
- ใช้ wildcard `*` เพื่อค้นหาไฟล์ที่ตรงกับ pattern
- ระบบจะรวมไฟล์ทั้งหมดที่เจอ

**ตัวอย่าง:**
```
Pattern: TRN_REVENUE_NT1_*.csv
จะหา: TRN_REVENUE_NT1_01.csv
      TRN_REVENUE_NT1_02.csv
      ...
      TRN_REVENUE_NT1_12.csv
```

#### 6.5 Output Files

```json
"output_files": {
  "concat": "trn_revenue_nt_2025.csv",
  "mapped_cc": "revenue_new_cc_2025.csv",
  "mapped_product": "revenue_mapped_product_2025_.csv",
  "final_report": "REVENUE_NT_REPORT_2025.csv",
  "error_gl": "error_gl_REVENUE_NT_REPORT_2025.csv",
  "error_product": "error_product_REVENUE_NT_REPORT_2025.csv"
}
```

**Pipeline Flow:**
```
Input Files
  ↓ STEP 1: Concatenate
concat (trn_revenue_nt_2025.csv)
  ↓ STEP 2: Map Cost Center
mapped_cc (revenue_new_cc_2025.csv)
  ↓ STEP 3: Map Product
mapped_product (revenue_mapped_product_2025.csv)
  ↓ STEP 4: Merge & Business Rules
final_report (REVENUE_NT_REPORT_2025.csv)
  ↓ STEP 5: Anomaly Detection
REVENUE_NT_REPORT_2025.xlsx (with highlighting)
```

**Error Files:**
- `error_gl` - GL codes ที่ไม่พบใน master
- `error_product` - Product codes ที่ไม่พบใน master

#### 6.6 Business Rules

```json
"business_rules": {
  "exclude_business_group": "รายได้อื่น",
  "non_telecom_service_group": "กลุ่มบริการอื่นไม่ใช่โทรคมนาคม",
  "new_adj_business_group": "ผลตอบแทนทางการเงินและรายได้อื่น",
  "financial_income_name": "ผลตอบแทนทางการเงิน",
  "other_revenue_adj_name": "รายได้อื่น"
}
```

**คำอธิบาย:**
กฎทางธุรกิจสำหรับการจัดกลุ่มรายได้

**`exclude_business_group`:**
- Business group ที่จะถูกแยกออกจากการประมวลผลหลัก

**`non_telecom_service_group`:**
- Service group สำหรับบริการที่ไม่ใช่โทรคมนาคม

**`new_adj_business_group`:**
- Business group ใหม่สำหรับรายได้ปรับปรุง

**`financial_income_name`:**
- ชื่อสำหรับผลตอบแทนทางการเงิน

**`other_revenue_adj_name`:**
- ชื่อสำหรับรายได้อื่นๆ ที่ปรับปรุง

#### 6.7 Special Mappings

```json
"special_mappings": [
  {
    "name": "GSaaS to Other Revenue",
    "condition": {
      "PRODUCT_KEY": "102010407",
      "GL_CODE": "46400101"
    },
    "mapping": {
      "PRODUCT_KEY": "292020407",
      "SUB_PRODUCT_KEY": "1"
    }
  }
]
```

**คำอธิบาย:**
กฎพิเศษสำหรับ mapping ข้อมูลที่มีเงื่อนไขเฉพาะ

**โครงสร้าง:**
- `name` - ชื่อของ mapping rule
- `condition` - เงื่อนไขที่ต้องตรงทั้งหมด
- `mapping` - ค่าใหม่ที่จะแทนที่

**ตัวอย่าง:**
```
ถ้า PRODUCT_KEY = "102010407" และ GL_CODE = "46400101"
→ เปลี่ยนเป็น PRODUCT_KEY = "292020407" และ SUB_PRODUCT_KEY = "1"
```

#### 6.8 Validation

```json
"validation": {
  "grand_total_diff_threshold": 0.01,
  "required_columns": [
    "YEAR", "MONTH", "CUSTOMER_GROUP_KEY", "PRODUCT_KEY",
    "SUB_PRODUCT_KEY", "GL_CODE", "COST_CENTER", "REVENUE_VALUE"
  ]
}
```

**คำอธิบาย:**

**`grand_total_diff_threshold`:**
- ความคลาดเคลื่อนสูงสุดที่ยอมรับได้สำหรับยอดรวมทั้งหมด

**`required_columns`:**
- คอลัมน์ที่ต้องมีในข้อมูลขั้นสุดท้าย
- ถ้าขาดคอลัมน์ใดๆ → จะแสดง error

#### 6.9 Anomaly Detection

```json
"anomaly_detection": {
  "enabled": true,
  "iqr_multiplier": 1.5,
  "min_history": 3,
  "rolling_window": 6,
  "enable_historical_highlight": true,
  "levels": {
    "product": {
      "group_by": ["BUSINESS_GROUP", "SERVICE_GROUP", "PRODUCT_KEY", "PRODUCT_NAME"]
    },
    "service": {
      "group_by": ["BUSINESS_GROUP", "SERVICE_GROUP"]
    },
    "business": {
      "group_by": ["BUSINESS_GROUP"]
    },
    "grand_total": {
      "group_by": []
    }
  }
}
```

**คำอธิบาย:**

**`enabled`** (true/false):
- เปิด/ปิด anomaly detection

**`iqr_multiplier`** (float):
- ตัวคูณสำหรับ IQR (Interquartile Range)
- `1.5` = standard (Tukey's method)
- เพิ่มค่า = ตรวจจับน้อยลง (strict น้อยลง)
- ลดค่า = ตรวจจับมากขึ้น (strict มากขึ้น)

**`min_history`** (int):
- จำนวนเดือนขั้นต่ำที่ต้องมีข้อมูลประวัติ
- `3` = ต้องมีข้อมูลอย่างน้อย 3 เดือน

**`rolling_window`** (int):
- ขนาดของ rolling window สำหรับคำนวณ trend
- `6` = ใช้ข้อมูล 6 เดือนล่าสุด

**`enable_historical_highlight`** (true/false):
- เปิด/ปิด การ highlight ข้อมูลที่ผิดปกติในอดีต

**`levels`** - 4 ระดับของ anomaly detection:

1. **Product Level** - ตรวจจับที่ระดับ Product
   ```
   Group by: BUSINESS_GROUP, SERVICE_GROUP, PRODUCT_KEY, PRODUCT_NAME
   ```

2. **Service Level** - ตรวจจับที่ระดับ Service Group
   ```
   Group by: BUSINESS_GROUP, SERVICE_GROUP
   ```

3. **Business Level** - ตรวจจับที่ระดับ Business Group
   ```
   Group by: BUSINESS_GROUP
   ```

4. **Grand Total Level** - ตรวจจับที่ระดับ Grand Total
   ```
   Group by: (none) - ยอดรวมทั้งหมด
   ```

**Anomaly Types:**
- `High Spike` - ค่าสูงผิดปกติ
- `Low Dip` - ค่าต่ำผิดปกติ
- `New Item` - รายการใหม่
- `Zero/Null` - ค่า 0 หรือ null ผิดปกติ

---

### 7. Logging Configuration

```json
"logging": {
  "level": "INFO",
  "format": "[%(asctime)s] [%(levelname)s] %(message)s",
  "date_format": "%Y-%m-%d %H:%M:%S",
  "enable_file_logging": true,
  "log_directory": "logs"
}
```

**คำอธิบาย:**

**`level`** - ระดับ log ที่จะบันทึก:
- `DEBUG` - ทุกอย่าง (รายละเอียดมากที่สุด)
- `INFO` - ข้อมูลทั่วไป (แนะนำ)
- `WARNING` - เฉพาะ warnings และ errors
- `ERROR` - เฉพาะ errors

**`format`** - รูปแบบของ log message:
```
[2025-11-17 19:30:51] [INFO] ✓ FI Module completed
```

**`date_format`** - รูปแบบวันที่:
- `%Y-%m-%d %H:%M:%S` = 2025-11-17 19:30:51

**`enable_file_logging`** (true/false):
- `true` - บันทึก log ลงไฟล์ (แนะนำ)
- `false` - แสดงเฉพาะบนหน้าจอ

**`log_directory`** - โฟลเดอร์สำหรับเก็บ log files
- Default: `logs/`
- จะสร้างไฟล์ต่อวัน: `system_20251117.log`

**Log Files ที่จะถูกสร้าง:**
```
logs/
├── system_20251117.log           # System logs
├── fi_module_20251117.log        # FI Module logs
├── etl_module_20251117.log       # ETL Module logs
└── config_manager_20251117.log   # Config Manager logs
```

---

## 🌐 การใช้งาน Web Application

### เริ่มต้น Web Server

```bash
# ใน directory ที่มี web_app.py
streamlit run web_app.py

# กำหนด port (default: 8501)
streamlit run web_app.py --server.port 8080

# เปิดให้เข้าถึงจากภายนอก
streamlit run web_app.py --server.address 0.0.0.0
```

### การใช้งานแต่ละ Tab

#### 1. Dashboard Tab
**จุดประสงค์:** ดูภาพรวมระบบ

**คุณสมบัติ:**
- แสดงสถานะ FI และ ETL modules
- ตรวจสอบ master files (✅/❌)
- แสดง FI และ ETL output files
- เตือนเมื่อเดือนไม่ตรงกัน

**การใช้งาน:**
1. Load Configuration (กดปุ่มใน Sidebar)
2. ตรวจสอบ master files status
3. ตรวจสอบว่าเดือน FI และ ETL ตรงกันหรือไม่
4. ดู configuration overview

#### 2. FI Module Tab
**จุดประสงค์:** รัน FI processing

**การใช้งาน:**
1. ตรวจสอบ configuration (input files, master files, output files)
2. กดปุ่ม "▶️ Run FI Processing"
3. รอจนประมวลผลเสร็จ
4. ดูผลลัพธ์ในตาราง Summary
5. ดูกราฟ "สรุปผลตอบแทนทางการเงินและรายได้อื่น"

#### 3. ETL Module Tab
**จุดประสงค์:** รัน ETL pipeline

**การใช้งาน:**
1. ตรวจสอบ pipeline steps
2. ดู business rules และ special mappings
3. ตรวจสอบ reconciliation และ anomaly detection settings
4. กดปุ่ม "▶️ Run ETL Pipeline"
5. รอจนประมวลผลเสร็จ

#### 4. Reconciliation Tab
**จุดประสงค์:** ดูผลการตรวจสอบความถูกต้อง

**การใช้งาน:**
1. ต้องรัน ETL Module ก่อน
2. ดูสถานะ Monthly Reconciliation (PASSED/FAILED)
3. ดูสถานะ YTD Reconciliation (PASSED/FAILED)
4. ดู FI Total, TRN Total, Difference
5. ดู Validation Results (Total Records, Unique Products, etc.)

#### 5. Analytics Tab
**จุดประสงค์:** วิเคราะห์ข้อมูลและดู anomalies

**การใช้งาน:**
1. ต้องรัน ETL Module ก่อน
2. ดู Anomaly Detection Summary (Total Anomalies, High Spikes, etc.)
3. คลิกเปิด expander แต่ละ level เพื่อดูรายละเอียด
4. ดูกราฟ Monthly Revenue Trend
5. ดูกราฟ Revenue by Business Group
6. ดู Data Summary

#### 6. Logs Tab
**จุดประสงค์:** ดู logs และ error files

**การใช้งาน:**
1. เลือก log file ที่ต้องการดู
2. ตั้งค่า Max Lines, Filter Level, Search
3. ดู Log Statistics (Errors, Warnings, Info, etc.)
4. Download log file ถ้าต้องการ
5. ดู Error Files (error_gl, error_product) และ download

#### 7. Configuration Editor (Sidebar)
**จุดประสงค์:** แก้ไข configuration

**การใช้งาน:**
1. กด "📝 Edit Configuration" ใน expander
2. แก้ไข Processing Year
3. แก้ไข Processing Month (FI & ETL)
4. ปรับ Reconciliation settings
5. ปรับ Anomaly Detection parameters
6. กดปุ่ม "💾 Save All Changes"
7. (Optional) กดปุ่ม "🔄 Reset" เพื่อรีเซ็ตสถานะ

**⚠️ Note:** การเปลี่ยนแปลงจะเป็น temporary และหายเมื่อปิดโปรแกรม ถ้าต้องการเปลี่ยนแบบถาวร ให้แก้ไขใน `config.json` โดยตรง

---

## 🚨 Troubleshooting

### Installation Issues

#### 1. ❌ Python version ไม่ตรง
```bash
Error: Python 3.7 is not supported
```
**วิธีแก้:**
```bash
# ตรวจสอบ version
python --version

# ติดตั้ง Python 3.8+
# macOS: brew install python@3.9
# Ubuntu: sudo apt install python3.9
# Windows: ดาวน์โหลดจาก python.org
```

#### 2. ❌ ติดตั้ง dependencies ไม่สำเร็จ
```bash
Error: Could not install packages
```
**วิธีแก้:**
```bash
# อัพเกรด pip
python -m pip install --upgrade pip

# ติดตั้งทีละ package
pip install pandas
pip install openpyxl
pip install streamlit

# หรือ force reinstall
pip install -r requirements.txt --force-reinstall
```

### Configuration Issues

#### 3. ❌ Path ไม่ถูกต้อง
```
Error: FileNotFoundError: [Errno 2] No such file or directory
```
**วิธีแก้:**
1. ตรวจสอบ `paths` ใน config.json ให้ตรงกับระบบ
2. ใช้ absolute path แทน relative path
3. Windows: ใช้ `\\` หรือ `/` (ห้ามใช้ `\` เดี่ยว)
4. สร้าง folder structure ตามที่ระบุใน config

#### 4. ❌ Master file not found
```
Error: ไม่พบไฟล์ Master: MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv
```
**วิธีแก้:**
1. ตรวจสอบว่าไฟล์อยู่ที่ `{master_path}/source/`
2. ตรวจสอบชื่อไฟล์ให้ตรงกับใน config
3. ตรวจสอบ case sensitivity (Linux/Mac)
4. ดู "Expected path" ใน Web App Dashboard

### Runtime Issues

#### 5. ❌ Month mismatch
```
🚨 เดือนไม่ตรงกัน! FI: 09, ETL: 10
```
**วิธีแก้:**
```bash
# CLI
python main.py --month 10

# Web App
# Sidebar → Edit Configuration → กด "🔄 Sync เดือนให้ตรงกัน"
```

#### 6. ❌ Reconciliation failed
```
❌ Reconciliation ล้มเหลว
```
**วิธีแก้:**
1. ตรวจสอบว่าเดือนตรงกันหรือไม่
2. ดู log files: `revenue/output/reconcile_logs/reconcile_summary_*.txt`
3. พิจารณาเพิ่ม tolerance: `"tolerance": 0.01`
4. หรือปิด reconciliation ชั่วคราว: `"enabled": false`

#### 7. ❌ Encoding error
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
**วิธีแก้:**
1. ตรวจสอบ encoding ของไฟล์จริง
2. แก้ไข `fi_module.encoding.input` ใน config:
   ```json
   "encoding": {
     "input": "tis-620",  // หรือ "cp874"
     "output": "utf-8",
     "master": "utf-8"
   }
   ```

#### 8. ❌ Memory error
```
MemoryError: Unable to allocate array
```
**วิธีแก้:**
1. เพิ่ม RAM
2. ประมวลผลทีละเดือน
3. ลดขนาดไฟล์ input
4. ใช้ chunking (ต้องแก้ไข code)

### Web App Issues

#### 9. ❌ Streamlit ไม่เริ่มต้น
```
Error: No module named 'streamlit'
```
**วิธีแก้:**
```bash
pip install streamlit
```

#### 10. ❌ Port already in use
```
Error: Port 8501 is already in use
```
**วิธีแก้:**
```bash
# ใช้ port อื่น
streamlit run web_app.py --server.port 8502

# หรือปิด process ที่ใช้ port 8501
# macOS/Linux:
lsof -ti:8501 | xargs kill -9

# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

---

## 📋 File Format Examples

เพื่อให้เข้าใจรูปแบบข้อมูลในแต่ละไฟล์ได้ดียิ่งขึ้น ด้านล่างนี้คือตัวอย่างข้อมูลในไฟล์ต่างๆ

### 1. Master Files

#### 1.1 MASTER_EXPENSE_GL_CODE

ไฟล์ Master สำหรับ mapping GL codes ของค่าใช้จ่าย

**Format:** CSV (UTF-8)

```csv
CODE_GROUP,GROUP_NAME,GL_CODE_NT1,GL_NAME_NT1
51,ต้นทุนขาย,51100101,ต้นทุนบริการ Mobile
51,ต้นทุนขาย,51100102,ต้นทุนบริการ Fixed Line
52,ค่าใช้จ่ายในการขาย,52200101,เงินเดือนพนักงานขาย
53,ค่าใช้จ่ายบริหาร,53300101,เงินเดือนผู้บริหาร
54,ค่าเสื่อมราคาและค่าตัดจำหน่าย,54400101,ค่าเสื่อมราคาอุปกรณ์
59,ค่าใช้จ่ายอื่น,59900101,ค่าใช้จ่ายอื่นๆ
```

**คำอธิบาย:**
- `CODE_GROUP`: รหัสกลุ่ม (51, 52, 53, 54, 59)
- `GROUP_NAME`: ชื่อกลุ่มค่าใช้จ่าย
- `GL_CODE_NT1`: รหัส GL Code (8 หลัก)
- `GL_NAME_NT1`: ชื่อ GL Code

---

#### 1.2 MASTER_REVENUE_GL_CODE

ไฟล์ Master สำหรับ mapping GL codes ของรายได้

**Format:** CSV (UTF-8)

```csv
REPORT_CODE,GL_GROUP,GL_CODE,GL_NAME
401,รายได้จากการให้บริการ,40100101,รายได้บริการ Mobile
401,รายได้จากการให้บริการ,40100102,รายได้บริการ Fixed Broadband
402,รายได้จากการขายสินค้า,40200101,รายได้ขายอุปกรณ์
464,ผลตอบแทนทางการเงิน,46400101,ดอกเบี้ยรับ
469,รายได้อื่น,46900101,รายได้อื่นๆ
```

**คำอธิบาย:**
- `REPORT_CODE`: รหัสรายงาน (401, 402, 464, 469, etc.)
- `GL_GROUP`: กลุ่มรายได้
- `GL_CODE`: รหัส GL Code (8 หลัก)
- `GL_NAME`: ชื่อ GL Code

---

#### 1.3 MASTER_PRODUCT_NT

ไฟล์ Master สำหรับข้อมูล Product Hierarchy

**Format:** CSV (UTF-8)

```csv
ITEM,BUSINESS_GROUP,SUB_ITEM,SERVICE_GROUP,PRODUCT_KEY,PRODUCT_NAME
รายได้จากการให้บริการ,Mobile,Mobile Data,Mobile Postpaid,102010101,3G/4G/5G Data Package
รายได้จากการให้บริการ,Mobile,Mobile Voice,Mobile Prepaid,102010201,Voice Package Prepaid
รายได้จากการให้บริการ,Fixed Broadband,Internet Service,Fixed Internet,102020101,Fiber Broadband
รายได้จากการให้บริการ,Enterprise,ICT Solution,Cloud Services,102030101,Cloud Storage Service
รายได้อื่น,Other Revenue,Financial Income,Interest Income,292010101,ดอกเบี้ยรับ
```

**คำอธิบาย:**
- `ITEM`: หมวดหลัก (รายได้จากการให้บริการ, รายได้อื่น)
- `BUSINESS_GROUP`: กลุ่มธุรกิจ (Mobile, Fixed Broadband, Enterprise)
- `SUB_ITEM`: หมวดย่อย
- `SERVICE_GROUP`: กลุ่มบริการ
- `PRODUCT_KEY`: รหัสผลิตภัณฑ์ (9 หลัก)
- `PRODUCT_NAME`: ชื่อผลิตภัณฑ์

---

### 2. Input Files

#### 2.1 FI Input File (pld_nt_{YYYYMMDD}.txt)

ไฟล์ข้อมูลจากระบบ GL (P&L Data)

**Format:** Tab-delimited text (TIS-620 encoding)

```
# มี 14 columns (tab-separated), ไม่มี header
# เฉพาะ columns ที่ใช้งาน:
# Column 5 (index 4): GL_CODE
# Column 12 (index 11): MONTHLY_VALUE
# Column 14 (index 13): YTD_VALUE

CompanyCode	CostCenter	Account	...	51100101	...	1,234,567.89	...	12,345,678.90
CompanyCode	CostCenter	Account	...	40100101	...	9,876,543.21	...	98,765,432.10
CompanyCode	CostCenter	Account	...	46400101	...	(123,456.78)	...	(1,234,567.80)
```

**คำอธิบาย:**
- ข้อมูลถูกคั่นด้วย Tab (`\t`)
- ไม่มี header row
- ตัวเลขมี comma separator และวงเล็บสำหรับค่าลบ
- Encoding: TIS-620 หรือ CP874 (Thai encoding)
- Column 5 (index 4) = GL_CODE
- Column 12 (index 11) = Monthly Value
- Column 14 (index 13) = YTD Value

---

#### 2.2 TRN Revenue Input (TRN_REVENUE_NT1_*.csv)

ไฟล์ Transaction Revenue หลัก

**Format:** CSV (TIS-620 encoding)

```csv
YEAR,MONTH,CUSTOMER_GROUP_KEY,PRODUCT_KEY,SUB_PRODUCT_KEY,GL_CODE,COST_CENTER,REVENUE_VALUE
2025,1,1001,102010101,1,40100101,CC001,1234567.89
2025,1,1001,102010201,2,40100102,CC001,987654.32
2025,2,1002,102020101,1,40100201,CC002,555666.77
2025,3,1001,102010101,1,40100101,CC001,1334567.89
```

**คำอธิบาย:**
- ข้อมูล Transaction Revenue แต่ละเดือน
- `YEAR`: ปี (YYYY)
- `MONTH`: เดือน (1-12)
- `CUSTOMER_GROUP_KEY`: รหัสกลุ่มลูกค้า
- `PRODUCT_KEY`: รหัสผลิตภัณฑ์ (9 หลัก)
- `SUB_PRODUCT_KEY`: รหัสผลิตภัณฑ์ย่อย
- `GL_CODE`: รหัส GL Code (8 หลัก)
- `COST_CENTER`: Cost Center
- `REVENUE_VALUE`: มูลค่ารายได้ (ทศนิยม 2 ตำแหน่ง)

---

#### 2.3 Adjustment Files (TRN_REVENUE_ADJ_*.csv)

ไฟล์ปรับปรุงรายเดือน

**Format:** CSV (TIS-620 encoding)

```csv
YEAR,MONTH,CUSTOMER_GROUP_KEY,PRODUCT_KEY,SUB_PRODUCT_KEY,GL_CODE,COST_CENTER,REVENUE_VALUE
2025,10,9999,292010101,1,46400101,ADJ001,123456.78
2025,10,9999,292010201,1,46900101,ADJ001,-50000.00
```

**คำอธิบาย:**
- ข้อมูลปรับปรุง (Adjustment) สำหรับแต่ละเดือน
- รูปแบบเหมือนกับ TRN_REVENUE_NT1 แต่เป็นข้อมูล adjustment
- มักใช้ `CUSTOMER_GROUP_KEY = 9999` สำหรับ adjustment entries
- `REVENUE_VALUE` อาจเป็นค่าบวกหรือลบ

---

### 3. Output Files

#### 3.1 FI Output (pl_revenue_nt_output_{YYYYMM}.csv)

ผลลัพธ์จาก FI Module - Revenue

**Format:** CSV (UTF-8)

```csv
GL_CODE,REVENUE_VALUE,REVENUE_VALUE_YTD
40100101,1234567.89,12345678.90
40100102,987654.32,9876543.21
40200101,555666.77,5556667.70
46400101,123456.78,1234567.80
46900101,99999.99,999999.90
```

**คำอธิบาย:**
- ข้อมูล Revenue ที่ประมวลผลแล้ว
- `GL_CODE`: รหัส GL Code
- `REVENUE_VALUE`: รายได้เดือนปัจจุบัน
- `REVENUE_VALUE_YTD`: รายได้สะสม (Year-to-Date)

---

#### 3.2 ETL Final Report (REVENUE_NT_REPORT_{YYYY}.csv)

รายงานสุดท้ายจาก ETL Pipeline

**Format:** CSV (UTF-8)

```csv
YEAR,MONTH,ITEM,BUSINESS_GROUP,SUB_ITEM,SERVICE_GROUP,PRODUCT_KEY,PRODUCT_NAME,AMOUNT
2025,1,รายได้จากการให้บริการ,Mobile,Mobile Data,Mobile Postpaid,102010101,3G/4G/5G Data Package,1234567.89
2025,1,รายได้จากการให้บริการ,Mobile,Mobile Voice,Mobile Prepaid,102010201,Voice Package Prepaid,987654.32
2025,2,รายได้จากการให้บริการ,Fixed Broadband,Internet Service,Fixed Internet,102020101,Fiber Broadband,555666.77
2025,1,รายได้อื่น,Other Revenue,Financial Income,Interest Income,292010101,ดอกเบี้ยรับ,123456.78
```

**คำอธิบาย:**
- ข้อมูลรายได้ที่ผ่านการ map และ transform แล้ว
- มี Product Hierarchy ครบถ้วน (ITEM → BUSINESS_GROUP → SERVICE_GROUP → PRODUCT)
- `AMOUNT`: มูลค่ารายได้หลังจาก mapping

---

#### 3.3 Error Files (error_gl_*.csv)

ไฟล์ข้อมูลที่ GL Code mapping ไม่สำเร็จ

**Format:** CSV (UTF-8)

```csv
YEAR,MONTH,PRODUCT_KEY,GL_CODE,COST_CENTER,REVENUE_VALUE,ERROR_REASON
2025,5,102010999,40199999,CC999,12345.67,GL_CODE not found in master
2025,6,999999999,40100101,CC001,98765.43,PRODUCT_KEY not found in master
```

**คำอธิบาย:**
- บันทึกรายการที่ไม่สามารถ map ได้
- `ERROR_REASON`: สาเหตุที่ mapping ล้มเหลว
- ใช้สำหรับตรวจสอบและแก้ไข master files

---

### 4. Log Files

#### 4.1 System Log (system_{YYYYMMDD}.log)

Log หลักของระบบ

**Format:** Plain text

```
[2025-11-17 19:30:45] [INFO] ================================================================================
[2025-11-17 19:30:45] [INFO] Revenue ETL System v2.1.0
[2025-11-17 19:30:45] [INFO] ================================================================================
[2025-11-17 19:30:45] [INFO] 📅 Processing Year: 2025, Month: 10
[2025-11-17 19:30:45] [INFO] 🖥️  Platform: macOS (darwin)
[2025-11-17 19:30:45] [INFO] ================================================================================
[2025-11-17 19:30:46] [SUCCESS] ✓ FI Module completed successfully
[2025-11-17 19:35:12] [INFO] Starting ETL Pipeline...
[2025-11-17 19:35:12] [INFO] STEP 1: Concatenate CSV Files
[2025-11-17 19:35:15] [SUCCESS] ✓ Loaded 1,234 records from TRN files
[2025-11-17 19:35:20] [WARNING] ⚠️  Found 5 records with missing GL codes
[2025-11-17 19:40:30] [SUCCESS] ✓ ETL Pipeline completed
[2025-11-17 19:40:35] [ERROR] ❌ Reconciliation failed: Difference detected
```

**Log Levels:**
- `[DEBUG]`: รายละเอียดทุกอย่าง
- `[INFO]`: ข้อมูลทั่วไป
- `[SUCCESS]`: ดำเนินการสำเร็จ (✓)
- `[WARNING]`: คำเตือน (⚠️)
- `[ERROR]`: ข้อผิดพลาด (❌)

---

#### 4.2 Reconciliation Summary (reconcile_summary_{timestamp}.txt)

สรุปผล Reconciliation

**Format:** Plain text

```
================================================================================
REVENUE RECONCILIATION REPORT
================================================================================

Timestamp: 2025-11-17 19:50:32
Year: 2025
Latest Month: 10
FI File: /path/to/pl_revenue_nt_output_202510.csv
TRN File: /path/to/trn_revenue_nt_2025.csv

================================================================================
[1] RECONCILE รายเดือน (MONTHLY)
================================================================================
Status: PASSED
Total Records: 86
FI Total: 3,324,811,103.24
TRN Total: 3,324,811,103.24
Diff: 0.00
Error Count: 0

================================================================================
[2] RECONCILE ยอดสะสม (YTD)
================================================================================
Status: PASSED
Total Records: 88
FI Total: 53,228,017,547.38
TRN Total: 53,228,017,547.38
Diff: 0.00
Error Count: 0

================================================================================
OVERALL STATUS: PASSED
================================================================================
```

**คำอธิบาย:**
- ตรวจสอบความสอดคล้องระหว่าง FI และ TRN data
- แสดงผลทั้ง Monthly และ YTD
- `Status`: PASSED หรือ FAILED
- `Diff`: ผลต่างระหว่าง FI และ TRN (ต้องเป็น 0.00)

---

## 💡 Best Practices

### 1. การจัดการ Config

**แนะนำ:**
- สร้างหลาย config files สำหรับแต่ละ environment:
  ```
  config_production.json
  config_development.json
  config_testing.json
  ```
- Version control config files ด้วย git
- Backup config files เป็นประจำ

### 2. การตั้งชื่อไฟล์

**แนะนำ:**
- ใช้ template variables: `{YYYY}`, `{MM}`, `{YYYYMM}`, `{YYYYMMDD}`
- ตั้งชื่อให้สื่อความหมาย
- รวมปีและเดือนในชื่อไฟล์เสมอ

### 3. การจัดการ Master Files

**แนะนำ:**
- ตั้งชื่อ master files ให้มีวันที่อัพเดท
- เก็บ history ของ master files
- ตรวจสอบ master files ก่อนรันระบบ

### 4. การ Monitor ระบบ

**แนะนำ:**
- ตรวจสอบ log files เป็นประจำ
- ดู reconciliation results ทุกครั้งที่รัน
- ตรวจสอบ error files
- ติดตาม anomalies

### 5. การ Backup

**แนะนำ:**
- Backup input files ก่อนประมวลผล
- Backup output files หลังเสร็จ
- Backup config files และ master files
- เก็บ log files สำคัญๆ

---

## 📞 Support

หากมีปัญหาหรือคำถาม:

1. ตรวจสอบ [Troubleshooting](#-troubleshooting) ด้านบน
2. ตรวจสอบ log files ใน `logs/`
3. ดู reconciliation logs ใน `revenue/output/reconcile_logs/`
4. ติดต่อทีมพัฒนา

---

**Version:** 2.1.0
**Last Updated:** November 2025
**Developed by:** Revenue ETL Team
