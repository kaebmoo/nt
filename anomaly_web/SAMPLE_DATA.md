เข้าใจครับ ผมจะสร้างตัวอย่างข้อมูล long format ที่มีข้อมูล 12 เดือนให้ เพื่อใช้ประกอบกับ code anomaly detection ของคุณ

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# สร้างข้อมูลตัวอย่าง 12 เดือน
np.random.seed(42)

# สร้างวันที่ 12 เดือน
start_date = datetime(2024, 1, 1)
months = pd.date_range(start=start_date, periods=12, freq='MS')

# สร้างข้อมูลสำหรับหลายสาขา/ผลิตภัณฑ์
branches = ['สาขากรุงเทพ', 'สาขาเชียงใหม่', 'สาขาขอนแก่น', 'สาขาภูเก็ต']
products = ['บริการ A', 'บริการ B', 'บริการ C']

data = []

for branch in branches:
    for product in products:
        # สร้างข้อมูลรายได้แต่ละเดือน
        base_revenue = np.random.uniform(500000, 2000000)
        
        for i, month in enumerate(months):
            # สร้างรายได้ปกติ
            revenue = base_revenue * (1 + np.random.uniform(-0.1, 0.1))
            
            # แทรก anomaly บางจุด
            if (branch == 'สาขากรุงเทพ' and product == 'บริการ A' and i == 5):
                revenue = revenue * 2.5  # Spike ผิดปกติ
            elif (branch == 'สาขาเชียงใหม่' and product == 'บริการ B' and i == 8):
                revenue = revenue * 0.3  # Drop ผิดปกติ
            elif (branch == 'สาขาขอนแก่น' and product == 'บริการ C' and i == 10):
                revenue = revenue * 3.0  # Spike ผิดปกติ
            
            data.append({
                'เดือน': month.strftime('%Y-%m'),
                'วันที่': month,
                'สาขา': branch,
                'ผลิตภัณฑ์': product,
                'รายได้': round(revenue, 2),
                'จำนวนลูกค้า': int(revenue / np.random.uniform(5000, 8000)),
                'หน่วย': 'บาท'
            })

# สร้าง DataFrame
df = pd.DataFrame(data)

# เรียงลำดับข้อมูล
df = df.sort_values(['สาขา', 'ผลิตภัณฑ์', 'วันที่']).reset_index(drop=True)

# แสดงตัวอย่างข้อมูล
print("ตัวอย่างข้อมูล 20 แถวแรก:")
print(df.head(20))

print("\n" + "="*80)
print(f"รูปแบบข้อมูล: {df.shape}")
print(f"จำนวนสาขา: {df['สาขา'].nunique()}")
print(f"จำนวนผลิตภัณฑ์: {df['ผลิตภัณฑ์'].nunique()}")
print(f"ช่วงเวลา: {df['เดือน'].min()} ถึง {df['เดือน'].max()}")

# แสดง summary statistics
print("\n" + "="*80)
print("สถิติรายได้แยกตามสาขา:")
print(df.groupby('สาขา')['รายได้'].describe())

# บันทึกเป็น CSV (ถ้าต้องการ)
df.to_csv('sample_revenue_data.csv', index=False, encoding='utf-8-sig')
print("\n✓ บันทึกข้อมูลเป็น 'sample_revenue_data.csv' เรียบร้อย")

# แสดงตัวอย่างข้อมูลที่มี anomaly
print("\n" + "="*80)
print("จุดที่มี Anomaly ที่ถูกแทรกไว้:")
print("1. สาขากรุงเทพ - บริการ A - มิถุนายน (เดือนที่ 6): Spike 2.5x")
print("2. สาขาเชียงใหม่ - บริการ B - กันยายน (เดือนที่ 9): Drop 0.3x")
print("3. สาขาขอนแก่น - บริการ C - พฤศจิกายน (เดือนที่ 11): Spike 3.0x")
```

ข้อมูลตัวอย่างนี้มีลักษณะดังนี้:

**โครงสร้างข้อมูล (Long Format):**
- เดือน: รูปแบบ YYYY-MM
- วันที่: datetime object
- สาขา: 4 สาขา
- ผลิตภัณฑ์: 3 ผลิตภัณฑ์
- รายได้: ค่าตัวเลขรายได้
- จำนวนลูกค้า: จำนวนลูกค้าที่คำนวณจากรายได้
- หน่วย: บาท

**จุดเด่น:**
- มีข้อมูล 144 แถว (4 สาขา × 3 ผลิตภัณฑ์ × 12 เดือน)
- แทรก anomaly ไว้ 3 จุดเพื่อทดสอบระบบตรวจจับ
- ข้อมูลเป็นภาษาไทยสามารถนำไปใช้ในเอกสารหรือ presentation ได้เลย

คุณสามารถปรับแต่ง:
- จำนวนสาขา/ผลิตภัณฑ์
- ช่วงรายได้
- จำนวนและตำแหน่ง anomaly
- คอลัมน์เพิ่มเติมตามต้องการ

ต้องการให้ปรับแต่งอะไรเพิ่มเติมไหมครับ?