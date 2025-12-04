#!/usr/bin/env python3
import pandas as pd
import sys

csv_file = '001_ต้นทุน_Product_1025 - 10-11-68.csv'
df = pd.read_csv(csv_file, encoding='cp874', sep='\t')

print('=== CSV Shape ===')
print(f'Rows: {len(df)}, Columns: {len(df.columns)}')

print('\n=== Row 0-8 (Headers) ===')
for i in range(min(9, len(df))):
    first_col = str(df.iloc[i, 0])[:80] if pd.notna(df.iloc[i, 0]) else 'NaN'
    print(f'Row {i}: {first_col}')

print('\n=== Row 3 (BU Headers - first 8 cols) ===')
if len(df) > 3:
    for j in range(min(8, len(df.columns))):
        val = df.iloc[3, j]
        print(f'Col {j}: {val}')

print('\n=== Row 4 (Sub Headers - first 8 cols) ===')
if len(df) > 4:
    for j in range(min(8, len(df.columns))):
        val = df.iloc[4, j]
        print(f'Col {j}: {val}')

print('\n=== Row 5 (Product Group? - first 8 cols) ===')
if len(df) > 5:
    for j in range(min(8, len(df.columns))):
        val = df.iloc[5, j]
        print(f'Col {j}: {val}')

print('\n=== Row 6 (Product Code? - first 8 cols) ===')
if len(df) > 6:
    for j in range(min(8, len(df.columns))):
        val = df.iloc[6, j]
        print(f'Col {j}: {val}')
