#!/usr/bin/env python3
import pandas as pd

# ตรวจสอบประเภทข้อมูลในไฟล์ CSV
csv_file = '001_ต้นทุน_BU_1025 - 10-11-68.csv'
df = pd.read_csv(csv_file, encoding='cp874', sep='\t')

# ดูข้อมูลในแถวที่ 7-10 (data rows)
print('=== Data rows 7-10 ===')
for i in range(7, min(11, len(df))):
    print(f'\nRow {i}:')
    for j in range(min(6, len(df.columns))):
        val = df.iloc[i, j]
        print(f'  Col {j}: {val} (type: {type(val).__name__})')

        # ถ้าเป็น string ให้แสดงว่ามี comma หรือไม่
        if isinstance(val, str):
            print(f'    Has comma: {("," in val)}')
