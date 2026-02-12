# แผนการแก้ไข: Cross-Year Historical Data for Anomaly Detection

**วันที่:** 2026-02-10
**ปัญหา:** เมื่อเริ่มปีใหม่ (2026-01) anomaly detection ไม่ทำงานเพราะไม่มีข้อมูลย้อนหลังเพียงพอ

---

## 📋 สรุปปัญหา

เมื่อเริ่มปีใหม่ (เช่น 2026 เดือน 1) anomaly detection ไม่ทำงาน เพราะ:
- ระบบโหลดข้อมูลเฉพาะปีปัจจุบัน (2026) เท่านั้น
- ต้องการข้อมูลย้อนหลังอย่างน้อย 3 เดือน (min_history) และใช้ rolling window 6 เดือน
- เดือน 1 ของ 2026 ไม่มีข้อมูลย้อนหลังเพียงพอ → ข้าม anomaly detection

**ความต้องการ:**
- ✅ มีข้อมูลปี 2025 ครบทั้ง 12 เดือน พร้อมใช้งาน
- ✅ ต้องการกำหนดผ่าน config.json (ไม่ใช่ command line parameter)
- ✅ โหลดข้อมูลจาก final report (REVENUE_NT_REPORT_2025.csv)

---

## 🎯 วิธีแก้ไข

เพิ่มความสามารถในการโหลดข้อมูลข้ามปีสำหรับ anomaly detection โดย:

1. **เพิ่ม configuration option** สำหรับระบุปีที่ต้องการโหลดเพิ่มเติม
2. **แก้ไข data loading logic** ให้โหลดข้อมูลจาก final report ของปีก่อนหน้า
3. **ปรับ month comparison logic** เปลี่ยนจาก MONTH_INT (1-12) เป็น YEAR_MONTH (YYYYMM)
4. **Backward compatible** - สามารถปิดการทำงานได้ถ้าไม่ต้องการ

---

## 📝 ขั้นตอนการแก้ไข

### Phase 1: แก้ไข Configuration

**ไฟล์:** `/Users/seal/Documents/GitHub/nt/revenue-report/config.json`

เพิ่ม option ใหม่ในส่วน `anomaly_detection` (บรรทัด 131-151):

```json
"anomaly_detection": {
  "enabled": true,
  "iqr_multiplier": 1.5,
  "min_history": 3,
  "rolling_window": 6,
  "enable_historical_highlight": true,
  "cross_year_historical_data": {
    "enabled": true,
    "include_years": [2025]
  },
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

**หมายเหตุ:**
- `enabled`: เปิด/ปิดการโหลดข้ามปี
- `include_years`: ระบุปีที่ต้องการโหลดเพิ่มเติม (สามารถใส่หลายปีได้)

---

### Phase 2: แก้ไข Config Manager

**ไฟล์:** `/Users/seal/Documents/GitHub/nt/revenue-report/config_manager.py`

เพิ่มเมธอดใหม่หลังจาก `get_reconciliation_config()` (บรรทัดประมาณ 285):

```python
def get_anomaly_cross_year_config(self) -> Dict[str, Any]:
    """
    ดึง cross-year configuration สำหรับ anomaly detection

    Returns:
        dict: {
            'enabled': bool,
            'include_years': list[str],
            'base_path': str
        }
    """
    anomaly_config = self.config.get('etl_module', {}).get('anomaly_detection', {})
    cross_year = anomaly_config.get('cross_year_historical_data', {})

    # Get base path for loading historical data
    base_path = self.config['paths'][self.os_platform]['base_path']

    return {
        'enabled': cross_year.get('enabled', False),
        'include_years': [str(year) for year in cross_year.get('include_years', [])],
        'base_path': base_path
    }
```

---

### Phase 3: เพิ่มฟังก์ชันโหลดข้อมูลข้ามปี

**ไฟล์:** `/Users/seal/Documents/GitHub/nt/revenue-report/revenue_etl_report.py`

เพิ่มฟังก์ชันใหม่หลังจาก `step1_concat_revenue_files()` (บรรทัดประมาณ 543):

```python
def load_historical_data_for_anomaly(self) -> pd.DataFrame:
    """
    โหลดข้อมูล aggregated เพิ่มเติมจากปีก่อนหน้าสำหรับ anomaly detection

    IMPORTANT: โหลดจากไฟล์ final report (REVENUE_NT_REPORT_{year}.csv)
    เพื่อไม่ต้อง re-process ข้อมูลทั้งหมดใหม่

    Returns:
        pd.DataFrame: ข้อมูล historical aggregated หรือ empty DataFrame
    """
    # ตรวจสอบว่า cross-year enabled หรือไม่
    if not hasattr(self, 'config_manager'):
        self.log("⚠️  ไม่มี config_manager - ข้ามการโหลด historical data")
        return pd.DataFrame()

    cross_year_config = self.config_manager.get_anomaly_cross_year_config()

    if not cross_year_config.get('enabled', False):
        self.log("ℹ️  Cross-year historical data: ปิดการใช้งาน")
        return pd.DataFrame()

    include_years = cross_year_config.get('include_years', [])
    base_path = cross_year_config.get('base_path', '')

    if not include_years:
        self.log("⚠️  ไม่มีปีที่ระบุใน include_years")
        return pd.DataFrame()

    self.log("=" * 80)
    self.log(f"📊 CROSS-YEAR HISTORICAL DATA: โหลดข้อมูลจากปี {include_years}")
    self.log("=" * 80)

    all_historical_dfs = []

    for year in include_years:
        year_str = str(year)

        # สร้าง path ของ final report file
        final_output_path = os.path.join(
            base_path,
            "all",
            "revenue",
            year_str
        )

        # ชื่อไฟล์ final report (ตรงกับ OUTPUT_FINAL_REPORT_FILE)
        report_file = os.path.join(
            final_output_path,
            f"REVENUE_NT_REPORT_{year_str}.csv"
        )

        if not os.path.exists(report_file):
            self.log(f"⚠️  ไม่พบไฟล์: {report_file}")
            self.log(f"    กรุณารันโปรแกรมสำหรับปี {year_str} ก่อน")
            continue

        self.log(f"✓ กำลังโหลด: {os.path.basename(report_file)}")

        try:
            # อ่านไฟล์ final report
            df_year = pd.read_csv(
                report_file,
                converters={
                    "YEAR": str,
                    "MONTH": str,  # Already 2-digit string
                    "PRODUCT_KEY": str,
                    "SUB_PRODUCT_KEY": str
                }
            )

            # Validate required columns
            required = ["YEAR", "MONTH", "BUSINESS_GROUP", "SERVICE_GROUP",
                       "PRODUCT_KEY", "PRODUCT_NAME", "REVENUE_VALUE"]
            missing = set(required) - set(df_year.columns)
            if missing:
                self.log(f"⚠️  ขาดคอลัมน์: {missing} - ข้ามปี {year_str}")
                continue

            # Filter เฉพาะ columns ที่ต้องใช้
            df_year = df_year[required]

            all_historical_dfs.append(df_year)

            self.log(f"  ✓ โหลดสำเร็จ: {len(df_year):,} รายการ")
            self.log(f"    ยอดรวม: {df_year['REVENUE_VALUE'].sum():,.2f} บาท")

        except Exception as e:
            self.log(f"⚠️  เกิดข้อผิดพลาด: {e}")
            import traceback
            traceback.print_exc()

    if not all_historical_dfs:
        self.log("⚠️  ไม่สามารถโหลดข้อมูล historical ได้")
        self.log("=" * 80)
        return pd.DataFrame()

    # รวมข้อมูลทั้งหมด
    historical_df = pd.concat(all_historical_dfs, ignore_index=True)

    self.log(f"\n✓ สรุป: โหลดข้อมูล {len(include_years)} ปี รวม {len(historical_df):,} รายการ")
    self.log(f"  ยอดรวมทั้งหมด: {historical_df['REVENUE_VALUE'].sum():,.2f} บาท")
    self.log("=" * 80)

    return historical_df
```

**ข้อดี:**
1. โหลดจาก final report แทน raw files → เร็วกว่า ประหยัด memory
2. ใช้ converters เพื่อให้แน่ใจว่า data types ตรงกัน
3. Validate columns ก่อนใช้งาน
4. Filter เฉพาะ columns ที่จำเป็น

---

### Phase 4: แก้ไข detect_anomalies()

**ไฟล์:** `/Users/seal/Documents/GitHub/nt/revenue-report/revenue_etl_report.py`
**ฟังก์ชัน:** `detect_anomalies()` (บรรทัด 1164-1304)

#### Step 1: โหลดและรวมข้อมูล historical

**แทนที่บรรทัด ~1174:**
```python
# หาเดือนล่าสุด - ใช้ end_month จาก config แทนการใช้ max จาก data
df_final['MONTH_INT'] = df_final['MONTH'].astype(int)
```

**ด้วย:**
```python
# โหลดข้อมูล historical เพิ่มเติม (ถ้ามี)
df_historical = self.load_historical_data_for_anomaly()

# รวมข้อมูลปัจจุบันกับ historical
if not df_historical.empty:
    df_combined = pd.concat([df_historical, df_final], ignore_index=True)
    self.log(f"รวมข้อมูล: {len(df_final):,} รายการปัจจุบัน + {len(df_historical):,} historical")
else:
    df_combined = df_final.copy()

# เตรียมข้อมูลสำหรับการตรวจสอบ
df_combined['MONTH_INT'] = df_combined['MONTH'].astype(int)
df_combined['YEAR'] = df_combined['YEAR'].astype(str)

# สร้าง YEAR_MONTH สำหรับเปรียบเทียบข้ามปี (YYYYMM format)
df_combined['YEAR_MONTH'] = (
    df_combined['YEAR'].astype(str) +
    df_combined['MONTH_INT'].astype(str).str.zfill(2)
).astype(int)
```

#### Step 2: ใช้ df_combined แทน df_final

**เปลี่ยนทุกที่ที่ใช้ `df_final` เป็น `df_combined`**

#### Step 3: Pivot ด้วย YEAR_MONTH

**เปลี่ยนจาก:**
```python
df_pivot = df_grouped.pivot_table(
    index=group_by,
    columns='MONTH_INT',  # เดิม
    values='REVENUE_VALUE',
    fill_value=0
).reset_index()

month_cols = [col for col in df_pivot.columns if isinstance(col, int)]
```

**เป็น:**
```python
df_pivot = df_grouped.pivot_table(
    index=group_by,
    columns='YEAR_MONTH',  # ใหม่
    values='REVENUE_VALUE',
    fill_value=0
).reset_index()

year_month_cols = [col for col in df_pivot.columns if isinstance(col, (int, np.integer))]
year_month_cols.sort()
```

#### Step 4: แก้ไข comparison logic

**เปลี่ยนจาก:**
```python
if latest_month not in month_cols:
    self.log(f"⚠️  ไม่พบเดือน {latest_month} ในข้อมูล - ข้าม")
    continue

latest_col = latest_month
historical_cols = [m for m in month_cols if m < latest_month]
```

**เป็น:**
```python
# คำนวณ YEAR_MONTH ล่าสุดจาก config
current_year = int(self.config.YEAR)
current_month = latest_month  # ได้มาจาก config.end_month
latest_year_month = current_year * 100 + current_month  # เช่น 202601

if latest_year_month not in year_month_cols:
    self.log(f"⚠️  ไม่พบเดือน {latest_year_month} ในข้อมูล - ข้าม")
    continue

latest_col = latest_year_month
historical_cols = [ym for ym in year_month_cols if ym < latest_year_month]
```

#### Step 5: ปรับ metadata

**เปลี่ยนจาก:**
```python
df_pivot['LATEST_MONTH'] = latest_month
```

**เป็น:**
```python
latest_month_display = latest_year_month % 100
df_pivot['LATEST_MONTH'] = latest_month_display
df_pivot['LATEST_YEAR_MONTH'] = latest_year_month  # เพิ่มสำหรับ debug
```

---

### Phase 5: แก้ไข detect_historical_anomalies()

**ไฟล์:** `/Users/seal/Documents/GitHub/nt/revenue-report/revenue_etl_report.py`
**ฟังก์ชัน:** `detect_historical_anomalies()` (บรรทัด 1076-1162)

#### Step 1: โหลดและรวมข้อมูล

**เพิ่มหลังบรรทัด 1085:**
```python
# [NEW] โหลดข้อมูล historical เพิ่มเติม
df_historical = self.load_historical_data_for_anomaly()

# [NEW] รวมข้อมูล
if not df_historical.empty:
    df_combined = pd.concat([df_historical, df_final], ignore_index=True)
    self.log(f"รวมข้อมูล historical: {len(df_combined):,} รายการ")
else:
    df_combined = df_final.copy()
```

#### Step 2: สร้าง YEAR_MONTH

**เปลี่ยนจาก:**
```python
df_final = df_final.copy()
df_final['MONTH_INT'] = df_final['MONTH'].astype(int)
```

**เป็น:**
```python
df_combined = df_combined.copy()
df_combined['MONTH_INT'] = df_combined['MONTH'].astype(int)
df_combined['YEAR'] = df_combined['YEAR'].astype(str)

df_combined['YEAR_MONTH'] = (
    df_combined['YEAR'].astype(str) +
    df_combined['MONTH_INT'].astype(str).str.zfill(2)
).astype(int)
```

#### Step 3: ใช้ df_combined

**เปลี่ยนทุกที่ที่ใช้ `df_final` เป็น `df_combined`**

#### Step 4: Pivot ด้วย YEAR_MONTH

**เปลี่ยนจาก:**
```python
df_pivot = df_grouped.pivot_table(
    index=group_by,
    columns='MONTH_INT',  # เดิม
    values='REVENUE_VALUE',
    fill_value=0
)
```

**เป็น:**
```python
df_pivot = df_grouped.pivot_table(
    index=group_by,
    columns='YEAR_MONTH',  # ใหม่
    values='REVENUE_VALUE',
    fill_value=0
)
```

#### Step 5: แก้ไข date_str generation

**เปลี่ยนจาก:**
```python
for idx, _ in anomalies.items():
    month_int = idx[-1]
    # ...
    date_str = f"01/{month_int:02d}/{self.config.YEAR}"
```

**เป็น:**
```python
for idx, _ in anomalies.items():
    year_month = idx[-1]  # เป็น YEAR_MONTH (เช่น 202512)

    # แยก year และ month จาก YEAR_MONTH
    year = year_month // 100
    month = year_month % 100

    # ...
    date_str = f"01/{month:02d}/{year}"
```

---

## 🧪 วิธีการทดสอบ

### Test Case 1: เดือนแรกของปี (2026-01)

**ตั้งค่า:**
1. แก้ไข `config.json`:
   ```json
   "processing_year": "2026",
   "processing_months": {
     "etl_end_month": 1
   },
   "anomaly_detection": {
     "cross_year_historical_data": {
       "enabled": true,
       "include_years": [2025]
     }
   }
   ```

2. รันคำสั่ง:
   ```bash
   cd /Users/seal/Documents/GitHub/nt/revenue-report
   python3 main.py --module etl --year 2026 --month 1
   ```

**ผลที่คาดหวัง:**
- ✅ Log แสดงว่าโหลดข้อมูล 2025
- ✅ รวมข้อมูลได้ 13 เดือน (202501-202512, 202601)
- ✅ Anomaly detection ทำงานได้ (ไม่มีข้อความ "ข้อมูลในอดีตไม่เพียงพอ")
- ✅ Excel มี highlighting anomalies ปกติ

### Test Case 2: ปิดการโหลดข้ามปี

**ตั้งค่า:**
```json
"cross_year_historical_data": {
  "enabled": false
}
```

**ผลที่คาดหวัง:**
- ✅ ไม่โหลดข้อมูล 2025
- ✅ ทำงานเหมือนเดิม (ข้าม anomaly detection ถ้าข้อมูลไม่พอ)

### Test Case 3: กลางปี (2026-06)

**ตั้งค่า:**
```json
"etl_end_month": 6,
"cross_year_historical_data": {
  "enabled": true,
  "include_years": [2025]
}
```

**ผลที่คาดหวัง:**
- ✅ โหลดข้อมูล 2025 และ 2026
- ✅ Anomaly detection ทำงานปกติ (มีข้อมูล 202501-202606)

---

## 📁 ไฟล์ที่ต้องแก้ไข

| ไฟล์ | สิ่งที่ต้องทำ | บรรทัด |
|------|--------------|--------|
| `config.json` | เพิ่ม `cross_year_historical_data` config | 131-151 |
| `config_manager.py` | เพิ่มเมธอด `get_anomaly_cross_year_config()` | ~285 |
| `revenue_etl_report.py` | เพิ่มฟังก์ชัน `load_historical_data_for_anomaly()` | ~543 |
| `revenue_etl_report.py` | แก้ไข `detect_anomalies()` | 1164-1304 |
| `revenue_etl_report.py` | แก้ไข `detect_historical_anomalies()` | 1076-1162 |

---

## ✅ ข้อดี

- ✅ **แก้ปัญหา year boundary** - เดือนแรกของปีสามารถตรวจสอบ anomaly ได้
- ✅ **Flexible** - กำหนดปีที่ต้องการโหลดผ่าน config
- ✅ **Backward compatible** - สามารถปิดได้ถ้าไม่ต้องการ
- ✅ **ไม่ต้องสร้างไฟล์ใหม่** - ใช้ไฟล์ที่มีอยู่แล้ว
- ✅ **Logic ชัดเจน** - ใช้ YEAR_MONTH เป็นตัวเปรียบเทียบ

---

## ⚠️ ข้อควรระวัง

1. **ต้องรันโปรแกรมปี 2025 ให้เสร็จก่อน** - เพื่อให้มีไฟล์ `REVENUE_NT_REPORT_2025.csv`
2. **Schema ต้องตรงกัน** - ถ้าเปลี่ยนโครงสร้าง columns ข้ามปี อาจมีปัญหา
3. **Memory usage** - ถ้าโหลดหลายปี จะใช้ memory มากขึ้น (แต่ยังน้อยกว่าโหลด raw files)

---

## 🔄 Alternative Approaches (ที่ไม่ได้เลือก)

### 1. Consolidated Historical File
- สร้างไฟล์ historical data รวมทุกปี
- ❌ **ปัญหา:** ต้องบำรุงรักษาไฟล์เพิ่ม, อาจ out-of-sync

### 2. Always Load All Years
- Auto-scan และโหลดทุกปีที่มี
- ❌ **ปัญหา:** ใช้ memory มาก, ช้า, ไม่ flexible

### 3. Command Line Parameter
- ส่ง `--include-years 2025` ทุกครั้ง
- ❌ **ปัญหา:** ไม่สะดวกสำหรับ automation

---

## 📌 สรุป

แก้ไขปัญหาการตรวจสอบ anomaly ในเดือนแรกของปีใหม่ โดย:

1. เพิ่ม config option `cross_year_historical_data` ใน anomaly_detection
2. สร้างฟังก์ชันโหลดข้อมูลจาก final report ของปีที่ระบุ
3. เปลี่ยนจาก MONTH_INT (1-12) เป็น YEAR_MONTH (YYYYMM)
4. แก้ไข comparison logic ใน `detect_anomalies()` และ `detect_historical_anomalies()`
5. Backward compatible - ปิดได้ถ้าไม่ต้องการใช้งาน

---

**สถานะ:** พร้อม implement
**ผู้เขียนแผน:** Claude Sonnet 4.5
**อนุมัติโดย:** รอการตรวจสอบ
