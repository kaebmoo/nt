"""
ทดสอบฟังก์ชันทำความสะอาดข้อมูลตัวเลข
รองรับรูปแบบบัญชี: comma, วงเล็บ (negative), สกุลเงิน
"""

import pandas as pd
import numpy as np

def clean_numeric_column(series):
    """
    ทำความสะอาดคอลัมน์ตัวเลข รองรับรูปแบบบัญชี
    """
    # แปลงเป็น string
    s = series.astype(str)

    # ตรวจสอบวงเล็บ (ค่าลบในระบบบัญชี)
    is_negative = s.str.contains(r'\(.*\)', regex=True, na=False)

    # ลบอักขระพิเศษ (เว้น . และ -)
    s = s.str.replace(r'[,\(\)\s$฿%]', '', regex=True)

    # แปลงเป็นตัวเลข
    s = pd.to_numeric(s, errors='coerce').fillna(0)

    # ใส่เครื่องหมายลบสำหรับค่าที่อยู่ในวงเล็บ
    s.loc[is_negative] = -s.loc[is_negative].abs()

    return s

# =============================================================================
# Test Cases
# =============================================================================

print("="*70)
print("🧪 ทดสอบฟังก์ชันทำความสะอาดข้อมูลตัวเลข (Accounting Format)")
print("="*70)

# ข้อมูลทดสอบ
test_data = {
    'Description': [
        'Normal number',
        'With comma',
        'With thousand separator',
        'With decimal',
        'Negative with parentheses',
        'Negative with comma and parentheses',
        'Large number with parentheses',
        'With spaces',
        'With dollar sign',
        'With Thai Baht sign',
        'With percentage sign',
        'Mixed: currency + comma',
        'Empty string',
        'Zero',
        'Decimal only',
        'Multiple commas'
    ],
    'Original': [
        '1000',
        '3,000',
        '1,234,567',
        '3000.50',
        '(3000)',
        '(30,000)',
        '(1,234,567.89)',
        ' 5000 ',
        '$1,000',
        '฿2,500',
        '50%',
        '$ 10,000.00',
        '',
        '0',
        '.50',
        '1,234,567.89'
    ]
}

df = pd.DataFrame(test_data)

# ทดสอบ
df['Cleaned'] = clean_numeric_column(df['Original'])

# Expected values (manual)
expected = [
    1000.00,      # Normal number
    3000.00,      # With comma
    1234567.00,   # With thousand separator
    3000.50,      # With decimal
    -3000.00,     # Negative with parentheses
    -30000.00,    # Negative with comma and parentheses
    -1234567.89,  # Large number with parentheses
    5000.00,      # With spaces
    1000.00,      # With dollar sign
    2500.00,      # With Thai Baht sign
    50.00,        # With percentage sign
    10000.00,     # Mixed: currency + comma
    0.00,         # Empty string
    0.00,         # Zero
    0.50,         # Decimal only
    1234567.89    # Multiple commas
]

df['Expected'] = expected
df['Match'] = np.isclose(df['Cleaned'], df['Expected'], rtol=1e-5)

# แสดงผล
print("\n📊 ผลการทดสอบ:\n")
print(df.to_string(index=False))

# สรุปผล
print("\n" + "="*70)
passed = df['Match'].sum()
total = len(df)
print(f"✅ ผ่าน: {passed}/{total} test cases ({passed/total*100:.1f}%)")

if passed == total:
    print("🎉 ทุก test cases ผ่านหมด!")
else:
    failed = df[~df['Match']]
    print(f"\n❌ ไม่ผ่าน {total - passed} test cases:")
    print(failed[['Description', 'Original', 'Cleaned', 'Expected']].to_string(index=False))

print("="*70)

# =============================================================================
# ตัวอย่างการใช้งานกับข้อมูลจริง
# =============================================================================

print("\n\n📋 ตัวอย่างการใช้งานกับข้อมูลจริง:")
print("="*70)

# สร้าง DataFrame ตัวอย่าง
expense_data = {
    'GL_CODE': ['51642102', '51642103', '51642104', '51642105', '51642106'],
    'GL_NAME': ['ค่าซ่อมแซม-อาคาร', 'ค่าซ่อมแซม-ชุมสาย', 'ค่าซ่อมแซม-เสา', 'ค่าซ่อมแซม-อุปกรณ์', 'ค่าซ่อมแซม-เครื่องใช้'],
    'EXPENSE_VALUE': ['24,972.44', '(1,503,671.96)', '41,208,496.98', '21,023,087.60', '4,600.00']
}

df_expense = pd.DataFrame(expense_data)

print("\n📥 ข้อมูลเดิม (Before):")
print(df_expense.to_string(index=False))

# ทำความสะอาด
df_expense['EXPENSE_VALUE_CLEANED'] = clean_numeric_column(df_expense['EXPENSE_VALUE'])

print("\n✨ ข้อมูลหลังทำความสะอาด (After):")
print(df_expense[['GL_CODE', 'GL_NAME', 'EXPENSE_VALUE', 'EXPENSE_VALUE_CLEANED']].to_string(index=False))

print("\n" + "="*70)
print("✅ การทำความสะอาดเสร็จสมบูรณ์!")
print("="*70)
