## ภาพรวม

ระบบเป็น Flask web app ที่รับไฟล์ CSV/Excel แล้วส่งเข้า "Hybrid Anomaly Detection Engine" ใน [anomaly_engine.py](../../../nt/anomaly_web/utils/anomaly_engine.py) ซึ่งตรวจ 3 มุมมอง แล้วออกรายงาน Excel ทาสีตามสถานะ

| ชั้นการตรวจ | เทียบกับอะไร | วิธี | ผลออกที่ |
|---|---|---|---|
| Crosstab Report | อดีตทั้งหมดของรายการเดียวกัน | IQR fence | Sheet 1 (สถานะงวดล่าสุด + ทาสีทุกช่อง) |
| Time Series Rolling | N งวดก่อนหน้าของรายการเดียวกัน | IQR fence แบบ rolling window | Sheet audit log |
| Peer Group | รายการอื่นในกลุ่มเดียวกัน งวดเดียวกัน | Isolation Forest + Z-score | Sheet peer log + peer crosstab |

ทุกชั้นทำงานบนยอดที่ถูก **รวมยอดตาม dimension + งวด** ก่อน (group by แล้ว sum) เพื่อให้เห็นยอด Net รายเดือนจริง ไม่ใช่ transaction ย่อย งวดปรับได้เป็น day / month / year ผ่าน `date_grain`

## 1. กติกาหลัก: IQR fence (`detect_iqr_anomaly`)

เป็นหัวใจที่ทุกชั้นใช้ร่วมกัน รับค่างวดปัจจุบัน 1 ค่า กับ history เป็น list แล้วตัดสินตามลำดับนี้

1. **ค่าติดลบ** ตอบ `Negative_Value` ทันที
2. **ทำความสะอาด history** ตัดค่าที่ไม่ใช่ตัวเลข และตัดค่า ≤ 0 ทิ้ง เหลือแต่ค่าบวก
3. **ประวัติไม่พอ** (น้อยกว่า `min_history` ค่าเริ่มต้น 3 งวด) ถ้าค่าปัจจุบัน > 0 ตอบ `New_Item` ไม่งั้น `Not_Enough_Data`
4. **กันความอ่อนไหวเกิน** คำนวณ % เปลี่ยนแปลงเทียบกับค่าเฉลี่ยอดีต ถ้าเปลี่ยนน้อยกว่า `min_change_ratio` (10%) ตอบ `Normal` โดยไม่ต้องดู IQR เลย
5. **กรณีอดีตนิ่งสนิท** (IQR = 0 คือ Q1 = Q3)
   - เปลี่ยนน้อยกว่า `constant_change_ratio` (15%) ตอบ `Normal`
   - อดีตเป็น 0 ตลอดแล้วจู่ ๆ มียอด ตอบ `High_Spike`
   - อดีตคงที่แล้วค่าเปลี่ยน ตอบ `Spike_vs_Constant`
6. **กรณีปกติ** คำนวณ Q1, Q3, IQR แล้วตั้งรั้ว
   - รั้วบน = Q3 + k × IQR
   - รั้วล่าง = max(0, Q1 − k × IQR)
   - ทะลุบน `High_Spike` หลุดล่าง `Low_Spike` อยู่ในรั้ว `Normal`

ค่า k (`iqr_k`) เริ่มต้น 2.0 ยิ่งต่ำยิ่งเข้มงวด (1.5 = strict, 3.0 = relaxed) สรุปคือค่าจะถูกนับเป็น anomaly ต้องผ่าน **สองด่าน** ทั้งเปลี่ยนจากค่าเฉลี่ยเกิน 10% และทะลุรั้ว IQR ด้วย

### ภาพลำดับการตัดสิน

```
        ค่างวดปัจจุบัน v  +  history
                    │
                    ▼
            v < 0 ? ──────────yes──────▶ Negative_Value
                    │no
                    ▼
      ล้าง history: เก็บเฉพาะค่า > 0
                    │
                    ▼
   เหลือ < min_history (3) ? ──yes──▶ v > 0 ? ──yes──▶ New_Item
                    │no                     └───no──▶ Not_Enough_Data
                    ▼
 ด่าน 1  |v − mean| / mean < 10% ? ──yes──▶ Normal
                    │no
                    ▼
            IQR == 0 ? ──yes──▶ เปลี่ยน < 15% ?        ──yes──▶ Normal
                    │           Q1 == 0 และ v > 0 ?    ──yes──▶ High_Spike
                    │no         v != Q1 ?              ──yes──▶ Spike_vs_Constant
                    ▼
 ด่าน 2  v > Q3 + k·IQR ?          ──yes──▶ High_Spike
         v < max(0, Q1 − k·IQR) ?  ──yes──▶ Low_Spike
                    │no
                    ▼
                  Normal
```

### ภาพรั้ว IQR (ตัวอย่างตัวเลขจริง)

history = `[100, 110, 95, 105, 120]` เรียงแล้ว `95 100 105 110 120`
Q1 = 100, Q3 = 110, IQR = 10, mean = 106, k = 2

```
      Low_Spike        │              Normal              │       High_Spike
  ◀────────────────────┤                                  ├────────────────────▶
                      80        100     106     110      130
                       ▲         Q1     mean    Q3        ▲
                  Q1 − 2×IQR             ├─ IQR ─┤    Q3 + 2×IQR
```

| v ที่เข้ามา | ด่าน 1: เปลี่ยนจาก mean | ด่าน 2: เทียบรั้ว | ผล |
|---|---|---|---|
| 112 | 5.7% < 10% | ไม่ต้องดู | `Normal` |
| 125 | 18% ผ่าน | 125 ≤ 130 อยู่ในรั้ว | `Normal` |
| 140 | 32% ผ่าน | 140 > 130 | `High_Spike` |
| 75 | 29% ผ่าน | 75 < 80 | `Low_Spike` |
| −5 | ไม่ต้องดู | ไม่ต้องดู | `Negative_Value` |

## 2. Crosstab Report (`CrosstabGenerator`)

- Pivot ข้อมูลเป็นตาราง แถว = dimensions ที่เลือก คอลัมน์ = งวด
- แต่ละแถวเอา **งวดสุดท้าย** เป็นค่าปัจจุบัน งวดก่อนหน้าทั้งหมดเป็น history ส่งเข้ากติกาข้อ 1
- คำนวณคอลัมน์เสริม `PREVIOUS_VALUE`, `DIFF_PREVIOUS`, `PCT_DIFF_PREVIOUS`, `PCT_CHANGE` (เทียบค่าเฉลี่ยอดีต)
- ตอน export [anomaly_reporter.py](../../../nt/anomaly_web/utils/anomaly_reporter.py) จะ **ไล่ทาสีทุกช่อง** ไม่ใช่แค่งวดล่าสุด โดยเอาแต่ละงวดเป็นค่าปัจจุบัน และทุกงวดก่อนหน้ามันเป็น history (expanding window) ใช้กติกาเดิม
- มีชั้นทาสีเพิ่มอีกแบบคือ **เทียบงวดก่อนหน้าตรง ๆ** ถ้า `PCT_DIFF_PREVIOUS` เกิน +10% ทาสีแดง ต่ำกว่า −10% ทาสีเหลือง ปิดได้ด้วย `highlight_previous_change`

### ภาพการเลือก history แบบ expanding window

```
งวด:        01    02    03    04    05    06
ค่า:       100   110    95   105   120   180
                                          ▲
   ANOMALY_STATUS ของแถว = ตรวจงวดล่าสุด (06)
   history = ทุกงวดก่อนหน้า ◀──────────────┘
             [100 110 95 105 120]  →  รั้ว 80–130  →  180 = High_Spike

ตอน reporter ไล่ทาสีทุกช่อง (หน้าต่างขยายไปเรื่อย ๆ):
   ช่อง 01–03   history < 3 ค่า          → ไม่ทาสี
   ช่อง 04      [01 02 03]         ──▶ 04
   ช่อง 05      [01 02 03 04]      ──▶ 05
   ช่อง 06      [01 02 03 04 05]   ──▶ 06
                ├── ยิ่งงวดหลัง history ยิ่งยาว ──┤

ทาสีชั้นที่สอง (เทียบงวดก่อนตรง ๆ):
   05 → 06 :  (180 − 120) / 120 = +50%  > +10%  → ทาสีแดง
```

## 3. Time Series Rolling Window (`audit_time_series_all_months`)

กติกาเดียวกับข้อ 1 แต่ทำแบบ vectorized ด้วย pandas เพื่อสแกน **ทุกงวด** ของทุกรายการ

- history ไม่ใช่อดีตทั้งหมด แต่เป็น **`window` งวดล่าสุดก่อนหน้า** (ค่าเริ่มต้น 3) ใช้ `rolling(window).shift(1)` เพื่อไม่ให้งวดปัจจุบันปนเข้าไปในสถิติของตัวเอง
- คำนวณ mean, count, Q1, Q3 แบบ rolling แล้วใช้ `np.select` ตัดสิน 8 เงื่อนไขเรียงตามลำดับเดียวกับกติกาหลัก
- ยอมรับ history ขั้นต่ำ `window − 1` งวด
- คืนเฉพาะแถวที่ไม่ใช่ `Normal` / `Not_Enough_Data` ติดป้าย `ANOMALY_TYPE = Time_Series_Roll` พร้อมข้อความ `COMPARED_WITH` บอกค่าเฉลี่ยที่ใช้เทียบ

### ภาพการเลือก history แบบ rolling window (window = 3)

```
งวด:        01    02    03    04    05    06
ค่า:       100   110    95   105   120   180

   ช่อง 04   [01 02 03] ──▶ 04
   ช่อง 05         [02 03 04] ──▶ 05
   ช่อง 06               [03 04 05] ──▶ 06
                         ├── ขนาดคงที่ 3 ──┤   เลื่อนไปทีละงวด

   rolling(3).shift(1) = สถิติของแถวนี้มาจาก 3 แถวก่อนหน้า ไม่รวมตัวเอง
   ยอมรับ history ขั้นต่ำ window − 1 = 2 งวด  →  ช่อง 03 ตรวจได้ด้วย [01 02]
```

เปรียบเทียบ history ที่ใช้ตรวจ **ช่อง 06** ในสองชั้น

```
Crosstab (expanding)   [100 110  95 105 120]   5 ค่า   Q1=100   Q3=110    รั้ว 80–130
Rolling  (window=3)    [         95 105 120]   3 ค่า   Q1=100   Q3=112.5  รั้ว 75–137.5
```

รั้วไม่เท่ากันเพราะ history ต่างกัน ค่าที่อยู่ระหว่างรั้วทั้งสองจึงถูกจับในชั้นหนึ่งแต่ไม่ถูกจับในอีกชั้น

## 4. Peer Group: Isolation Forest (`audit_peer_group_all_months`)

ตรวจว่ารายการนี้ **แปลกกว่าเพื่อนร่วมกลุ่มในงวดเดียวกัน** หรือไม่ เช่น GL เดียวกันแต่ต่างศูนย์ต้นทุน

1. แยกข้อมูลทีละงวด แล้วแยกทีละกลุ่มตาม `audit_peer_group_by`
2. กลุ่มที่มีสมาชิกน้อยกว่า `peer_min_group_size` (5) ข้าม
3. รัน `IsolationForest` จาก scikit-learn บนค่ายอดมิติเดียว ตั้ง `contamination` = `peer_contamination` (5%) คือคาดว่าประมาณ 5% ของกลุ่มเป็น outlier `random_state=42` ให้ผลซ้ำได้
4. ตัวที่โมเดลทายว่าเป็น outlier (−1) ยังต้องผ่าน **ด่านที่สอง** คือ Z-score เทียบ mean/std ของกลุ่มต้องเกิน `peer_zscore_threshold` (2.0) ถึงจะรายงาน เพื่อกัน false positive จาก contamination ที่บังคับให้มี outlier เสมอ
5. ติดป้าย `Peer_Group_ISO` และ `High Outlier (vs Peers)` หรือ `Low Outlier (vs Peers)` ตามเครื่องหมายของ Z

### ภาพการแบ่งกลุ่มก่อนตรวจ

```
ข้อมูลทั้งหมด
   │ แยกตามงวด (date_grain)
   ├── 2024-05 ──┐
   ├── 2024-06 ──┤ แยกตามกลุ่ม (audit_peer_group_by เช่น GL_CODE)
   │             ├── GL 510100 ── 8 รายการ   ✓ ≥ 5  ตรวจ
   │             ├── GL 520200 ── 3 รายการ   ✗ < 5  ข้าม
   │             └── ...
   └── 2024-07 ──┘
   ทุกงวด × ทุกกลุ่ม fit โมเดลใหม่ 1 ตัว  →  จึงช้าที่สุดใน 3 ชั้น
```

### ภาพสองด่านในกลุ่มเดียว (ตัวเลขจริงจาก scikit-learn)

งวด 2024-06 กลุ่ม GL 510100 แต่ละ item คือศูนย์ต้นทุน

```
   item:    A     B     C     D     E     F     G     H
   ค่า:    100   105    98   110   102    95   400    30
   mean = 130    std = 104.8

ด่าน 1  Isolation Forest (contamination = 5%, random_state = 42)
   A B C D E F H  →  +1  ปกติ
   G              →  −1  outlier

ด่าน 2  Z-score = (v − mean) / std  ต้อง |z| > 2.0
   G:  (400 − 130) / 104.8 = +2.58   ✓  →  High Outlier (vs Peers)
       COMPARED_WITH = "Group Avg: 130.00 (Z=2.58)"

ถ้าปรับ contamination เป็น 25% โมเดลจะจับ H เพิ่ม
   H:  (30 − 130) / 104.8 = −0.95    ✗  ไม่ถึง 2  →  ด่าน 2 กรองทิ้ง ไม่รายงาน
```

### ภาพแนวคิด Isolation Forest

โมเดลสุ่มตัดเส้นแบ่งค่าไปเรื่อย ๆ ค่าที่โดดเดี่ยวจะถูกแยกออกมาได้ในไม่กี่ครั้ง

```
   ตัดครั้งที่ 1 ที่ 250  →  [A B C D E F H] | [G]      G โดดเดี่ยวทันที (1 ครั้ง)
   ตัดครั้งที่ 2 ที่  60  →  [H] | [A B C D E F]        H โดดเดี่ยว (2 ครั้ง)
   ตัดครั้งที่ 3 ที่ 103  →  [C A E] | [B D F]          A–F ยังปนกัน
   ตัดครั้งที่ 4, 5, ...                                 ต้องตัดอีกหลายครั้ง

   ยิ่งใช้จำนวนครั้งน้อย  →  คะแนน anomaly ยิ่งสูง
   contamination บอกโมเดลว่าให้ตัดสินกี่ % ของกลุ่มเป็น outlier
   (จึงมี outlier เสมอแม้กลุ่มจะปกติหมด นี่คือเหตุผลที่ต้องมีด่าน 2)
```

### ภาพรั้ว Z-score ของกลุ่มนี้

```
     Low Outlier      │                   ปกติ                    │   High Outlier
  ◀───────────────────┤                                           ├─────────────────▶
                   −79.6       30     95…110      130           339.6        400
                 mean − 2σ      H       A–F       mean        mean + 2σ        G
```

รั้วล่างติดลบเพราะ G ดึง std ให้กว้าง กลุ่มนี้จึงไม่มีทางเกิด Low Outlier ในงวดเดียวกันได้ นี่คือข้อจำกัดของ Z-score เมื่อกลุ่มมีค่าสุดโต่งฝั่งเดียว

## ลำดับการรันจริง

ข้อ 1 ไม่ใช่ขั้นตอน แต่เป็น **กติกา** (`detect_iqr_anomaly`) ที่ชั้นอื่นหยิบไปใช้ ข้อ 3 ไม่ได้เรียกฟังก์ชันนี้ตรง ๆ แต่เขียนเงื่อนไขชุดเดียวกันใหม่แบบ vectorized ด้วย `np.select` ต่างกันแค่ history มาจาก rolling window

ลำดับที่ [audit_runner.py](../../../nt/anomaly_web/utils/audit_runner.py) รันคือ

```
df_clean (ข้อมูลที่ทำความสะอาดแล้ว ตัวเดียวกัน ส่งเข้าทุก step)
   │
   ├─ Step 3  Time Series Rolling   (ข้อ 3)  ──▶ df_ts_log      → sheet audit log
   │
   ├─ Step 4  Peer Group ISO        (ข้อ 4)  ──▶ df_peer_log    → sheet peer log
   │
   ├─ Step 5  Crosstab Report       (ข้อ 2)
   │            ├─ CrosstabGenerator  → เรียกกติกาข้อ 1 กับงวดล่าสุด  → ANOMALY_STATUS
   │            └─ reporter ทาสีทุกช่อง → เรียกกติกาข้อ 1 ซ้ำทีละช่อง (expanding window)
   │
   └─ Step 6  Peer Crosstab sheet   (จาก df_peer_log)
```

- ทุก step **เป็นอิสระต่อกัน** ผลของ step ก่อนไม่ได้ป้อนเข้า step ถัดไป ปิดข้อ 3 ทิ้ง ข้อ 2 ก็ให้ผลเหมือนเดิม
- `df_ts_log` ถูกส่งเข้า `add_crosstab_sheet` พร้อมคอมเมนต์ว่า "เพื่อช่วยทาสี" แต่ในฟังก์ชันไม่ได้ใช้พารามิเตอร์นั้นเลย สีในตาราง crosstab มาจากการคำนวณกติกาข้อ 1 ใหม่ทั้งหมด จึงอาจไม่ตรงกับ log ของข้อ 3

## พารามิเตอร์ที่ปรับได้ ([anomaly_settings.py](../../../nt/anomaly_web/utils/anomaly_settings.py))

| ค่า | เริ่มต้น | ใช้ใน |
|---|---|---|
| `iqr_k` | 2.0 | ความกว้างรั้ว IQR |
| `min_change_ratio` | 0.10 | ด่านแรก เปลี่ยนน้อยกว่านี้ = Normal |
| `constant_change_ratio` | 0.15 | เกณฑ์เมื่ออดีตคงที่ |
| `audit_ts_window` | 3 | จำนวนงวดย้อนหลังของ rolling |
| `crosstab_min_history` | 3 | history ขั้นต่ำของ crosstab |
| `peer_contamination` | 0.05 | สัดส่วน outlier ที่ Isolation Forest คาด |
| `peer_zscore_threshold` | 2.0 | ด่านกรอง Z-score หลัง ISO |
| `peer_min_group_size` | 5 | กลุ่มเล็กกว่านี้ไม่ตรวจ |
| `date_grain` | month | day / month / year |
| `previous_change_highlight_high/low_ratio` | ±0.10 | ทาสีเทียบงวดก่อน |

ค่าที่กรอกเป็น % (เช่น 10) จะถูกแปลงเป็นสัดส่วน (0.10) อัตโนมัติ

## จุดที่ควรรู้ตอนอ่านผล

- **Crosstab กับ Rolling อาจให้ผลต่างกัน** บนช่องเดียวกัน เพราะ crosstab ใช้อดีตทั้งหมดเป็น history ส่วน rolling ใช้แค่ N งวดล่าสุด
- **การจัดการค่า 0 ต่างกัน** กติกาหลักตัดค่า ≤ 0 ออกจาก history ก่อนคำนวณ แต่ rolling version เอาค่า 0 เข้ามาคำนวณ Q1/Q3 ด้วย รายการที่มีเดือนว่างบ่อยจึงอาจถูกจับต่างกันในสองชั้นนี้
- **New_Item ไม่ถูกทาสีในตาราง** แต่ยังปรากฏใน audit log
- Peer group ใช้เวลานานที่สุดเพราะ fit โมเดลใหม่ทุกกลุ่มทุกงวด README จึงทำเป็น optional