"""
Crosstab to Long Format Converter
แปลงไฟล์ Crosstab (Pivot Table) เป็น Long Format สำหรับ main_audit.py

Author: Claude
Date: 2025-01-18
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import sys

class CrosstabConverter:
    """
    แปลงข้อมูลจาก Crosstab Format เป็น Long Format
    """

    def __init__(self, input_file, output_file=None):
        """
        Parameters:
        -----------
        input_file : str
            ไฟล์ Crosstab (Excel หรือ CSV)
        output_file : str, optional
            ไฟล์ผลลัพธ์ (ถ้าไม่ระบุ จะใช้ชื่อเดียวกันต่อท้าย _long.csv)
        """
        self.input_file = input_file

        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            self.output_file = f"{base_name}_long.csv"
        else:
            self.output_file = output_file

        self.df = None
        self.df_long = None

    def read_file(self, sheet_name=0, skiprows=0):
        """
        อ่านไฟล์ Crosstab

        Parameters:
        -----------
        sheet_name : str or int
            ชื่อหรือ index ของ sheet (สำหรับ Excel)
        skiprows : int
            จำนวนแถวที่ข้ามด้านบน
        """
        print(f"📂 Loading file: {self.input_file}")

        ext = os.path.splitext(self.input_file)[1].lower()

        if ext in ['.xlsx', '.xls']:
            self.df = pd.read_excel(self.input_file, sheet_name=sheet_name, skiprows=skiprows)
        elif ext == '.csv':
            self.df = pd.read_csv(self.input_file, skiprows=skiprows)
        else:
            raise ValueError(f"ไม่รองรับไฟล์นามสกุล {ext}")

        print(f"   ✓ Loaded {len(self.df):,} rows × {len(self.df.columns)} columns")
        return self.df

    def identify_date_columns(self):
        """
        ระบุคอลัมน์วันที่ (รูปแบบ 01/01/2025, 2025-01, etc.)
        """
        date_cols = []

        for col in self.df.columns:
            col_str = str(col)

            # ตรวจสอบรูปแบบวันที่ต่างๆ
            if '/' in col_str or '-' in col_str:
                try:
                    # ลอง parse เป็นวันที่
                    pd.to_datetime(col_str)
                    date_cols.append(col)
                except:
                    continue

        return date_cols

    def convert_to_long(self,
                       id_vars=None,
                       value_name='VALUE',
                       auto_detect_dates=True,
                       mode='auto'):
        """
        แปลง Crosstab → Long Format

        Parameters:
        -----------
        id_vars : list, optional
            คอลัมน์ที่เป็น dimension (ถ้าไม่ระบุ จะใช้ทุกคอลัมน์ที่ไม่ใช่วันที่)
        value_name : str
            ชื่อคอลัมน์ค่า (เช่น EXPENSE_VALUE, REVENUE_VALUE)
        auto_detect_dates : bool
            ให้ตรวจหาคอลัมน์วันที่อัตโนมัติ
        mode : str
            'auto' = ตรวจสอบอัตโนมัติ (default)
            'date' = คอลัมน์เป็นวันที่ (2025-01, 01/01/2025)
            'sequential' = คอลัมน์ไม่ใช่วันที่ (1,2,3 หรือ A,B,C หรือ ม.ค., Jan)
        """
        print("\n🔄 Converting Crosstab → Long Format...")

        if self.df is None:
            raise ValueError("กรุณาอ่านไฟล์ก่อน (ใช้ read_file())")

        # เก็บ mode ไว้ใช้ใน parse_dates()
        self.mode = mode

        # ตรวจหาคอลัมน์วันที่
        if auto_detect_dates and mode in ['auto', 'date']:
            date_cols = self.identify_date_columns()

            # ถ้าเป็น auto mode และหาวันที่ไม่เจอ ให้สลับเป็น sequential
            if mode == 'auto' and len(date_cols) == 0:
                print(f"   ⚠ No date columns detected → switching to 'sequential' mode")
                self.mode = 'sequential'
            elif mode == 'auto' and len(date_cols) > 0:
                print(f"   ✓ Found {len(date_cols)} date columns → using 'date' mode")
                self.mode = 'date'
            else:
                # mode เป็น 'date' อยู่แล้ว
                print(f"   ✓ Found {len(date_cols)} date columns")
                self.mode = 'date'

            # คอลัมน์ที่ไม่ใช่วันที่ = Dimensions
            if id_vars is None:
                id_vars = [col for col in self.df.columns
                          if col not in date_cols and col != 'ANOMALY_STATUS']

        # ถ้าเป็น sequential mode หรือ auto ที่ไม่เจอวันที่
        if mode == 'sequential' or (mode == 'auto' and not auto_detect_dates):
            if id_vars is None:
                # ให้ผู้ใช้ระบุ id_vars เอง หรือใช้คอลัมน์แรกๆ ที่ไม่ใช่ตัวเลข
                id_vars = [col for col in self.df.columns
                          if col != 'ANOMALY_STATUS'][:3]  # เอา 3 คอลัมน์แรก (ปรับได้)

            print(f"   ℹ Mode: sequential (non-date columns)")
            self.mode = 'sequential'

        # ลบคอลัมน์ ANOMALY_STATUS ออก (ถ้ามี)
        df_clean = self.df.drop(columns=['ANOMALY_STATUS'], errors='ignore')

        # ลบคอลัมน์ผลรวม (ถ้ามี)
        df_clean = df_clean.drop(columns=['ผลรวม', 'Total', 'SUM'], errors='ignore')

        # Melt (แปลง Wide → Long)
        var_col_name = 'DATE_COL' if self.mode == 'date' else 'PERIOD'

        self.df_long = pd.melt(
            df_clean,
            id_vars=id_vars,
            var_name=var_col_name,
            value_name=value_name
        )

        print(f"   ✓ Converted to {len(self.df_long):,} rows")
        return self.df_long

    def parse_dates(self, date_col='DATE_COL'):
        """
        แยก DATE → YEAR, MONTH, DATE (สำหรับ date mode)
        หรือเก็บเป็น PERIOD (สำหรับ sequential mode)
        """
        # ตรวจสอบ mode
        mode = getattr(self, 'mode', 'date')

        if mode == 'sequential':
            print("\n📊 Processing sequential periods...")
            # ไม่ต้อง parse วันที่ เก็บเป็น PERIOD เท่านั้น
            # ถ้ามีคอลัมน์ชื่อ PERIOD อยู่แล้ว ก็ใช้เลย
            if 'PERIOD' in self.df_long.columns:
                print(f"   ✓ Sequential periods preserved (PERIOD column)")
            else:
                print(f"   ⚠ Warning: PERIOD column not found")
            return self.df_long

        # Date mode (เหมือนเดิม)
        print("\n📅 Parsing dates...")

        # แปลง string → datetime
        self.df_long['DATE'] = pd.to_datetime(self.df_long[date_col], errors='coerce')

        # แยกเป็น YEAR, MONTH
        self.df_long['YEAR'] = self.df_long['DATE'].dt.year
        self.df_long['MONTH'] = self.df_long['DATE'].dt.month

        # ลบคอลัมน์เดิม
        self.df_long = self.df_long.drop(columns=[date_col])

        # เรียงคอลัมน์ใหม่
        cols = list(self.df_long.columns)
        if 'YEAR' in cols and 'MONTH' in cols and 'DATE' in cols:
            # ย้าย YEAR, MONTH, DATE มาข้างหน้า
            other_cols = [c for c in cols if c not in ['YEAR', 'MONTH', 'DATE']]
            self.df_long = self.df_long[['YEAR', 'MONTH', 'DATE'] + other_cols]

        print(f"   ✓ Parsed dates successfully")
        return self.df_long

    def clean_numeric_value(self, series):
        """
        ทำความสะอาดค่าตัวเลข รองรับรูปแบบบัญชี
        - ลบ comma: 3,000.00 → 3000.00
        - แปลงวงเล็บเป็นลบ: (3000) → -3000
        - รองรับทั้งสองรวมกัน: (30,000.00) → -30000.00
        - ลบช่องว่าง, สกุลเงิน: $ 3,000 → 3000
        """
        # แปลงเป็น string
        s = series.astype(str)

        # ตรวจสอบวงเล็บ (ค่าลบในระบบบัญชี)
        is_negative = s.str.contains(r'\(.*\)', regex=True, na=False)

        # ลบอักขระพิเศษ (เว้น . และ -)
        # เก็บเครื่องหมาย - ไว้ (ถ้ามี)
        s = s.str.replace(r'[,\(\)\s$฿%]', '', regex=True)

        # แปลงเป็นตัวเลข
        s = pd.to_numeric(s, errors='coerce')

        # ใส่เครื่องหมายลบสำหรับค่าที่อยู่ในวงเล็บ
        s.loc[is_negative] = -s.loc[is_negative].abs()

        return s

    def clean_data(self, value_col='VALUE'):
        """
        ทำความสะอาดข้อมูล
        - ลบแถวที่ค่าเป็น null/0
        - แปลงค่าเป็นตัวเลข (รองรับ comma, วงเล็บ)
        """
        print("\n🧹 Cleaning data...")

        before = len(self.df_long)

        # แปลงค่าเป็นตัวเลข (รองรับรูปแบบบัญชี)
        self.df_long[value_col] = self.clean_numeric_value(self.df_long[value_col])

        # ลบแถวที่ไม่มีค่า
        self.df_long = self.df_long.dropna(subset=[value_col])

        # ลบแถวที่ค่า = 0 (optional)
        # self.df_long = self.df_long[self.df_long[value_col] != 0]

        after = len(self.df_long)
        print(f"   ✓ Removed {before - after:,} null/invalid rows")
        print(f"   ✓ Final dataset: {after:,} rows")

        return self.df_long

    def save(self, encoding='utf-8-sig'):
        """
        บันทึกไฟล์
        """
        print(f"\n💾 Saving to: {self.output_file}")

        self.df_long.to_csv(self.output_file, index=False, encoding=encoding)

        print(f"   ✓ Saved successfully!")
        print(f"   📊 File size: {os.path.getsize(self.output_file) / 1024:.1f} KB")

    def convert(self,
                sheet_name=0,
                skiprows=0,
                id_vars=None,
                value_name='EXPENSE_VALUE',
                auto_detect_dates=True,
                clean=True,
                mode='auto'):
        """
        แปลงทั้งหมดในขั้นตอนเดียว

        Parameters:
        -----------
        mode : str
            'auto' = ตรวจสอบอัตโนมัติ (default)
            'date' = คอลัมน์เป็นวันที่ (2025-01, 01/01/2025) → สร้าง YEAR, MONTH, DATE
            'sequential' = คอลัมน์ไม่ใช่วันที่ (1,2,3 หรือ A,B,C หรือ ม.ค.) → สร้าง PERIOD
        """
        print("="*60)
        print("📊 CROSSTAB TO LONG FORMAT CONVERTER")
        print("="*60)

        # 1. อ่านไฟล์
        self.read_file(sheet_name=sheet_name, skiprows=skiprows)

        # 2. แปลง Crosstab → Long
        self.convert_to_long(
            id_vars=id_vars,
            value_name=value_name,
            auto_detect_dates=auto_detect_dates,
            mode=mode
        )

        # 3. แยกวันที่ (หรือ sequential period)
        self.parse_dates()

        # 4. ทำความสะอาด
        if clean:
            self.clean_data(value_col=value_name)

        # 5. บันทึก
        self.save()

        print("\n" + "="*60)
        print("✅ CONVERSION COMPLETED!")
        print(f"   Mode: {getattr(self, 'mode', 'date')}")
        print("="*60)

        return self.df_long


# =============================================================================
# ตัวอย่างการใช้งาน
# =============================================================================

if __name__ == "__main__":

    # ตัวอย่างที่ 1: Date Mode - Revenue Report (คอลัมน์เป็นวันที่)
    # converter = CrosstabConverter(
    #     input_file="revenue_crosstab.xlsx",
    #     output_file="revenue_long.csv"
    # )
    # converter.convert(
    #     sheet_name="Sheet1",
    #     value_name="REVENUE_VALUE",
    #     mode='date'  # หรือ 'auto' (ตรวจอัตโนมัติ)
    # )
    # ผลลัพธ์จะมีคอลัมน์: YEAR, MONTH, DATE, REVENUE_VALUE

    # ตัวอย่างที่ 2: Sequential Mode - คอลัมน์ไม่ใช่วันที่ (1,2,3 หรือ ม.ค., Jan)
    # converter = CrosstabConverter("data_sequential.xlsx")
    # converter.convert(
    #     value_name="AMOUNT",
    #     id_vars=["PRODUCT", "REGION"],
    #     mode='sequential'  # คอลัมน์เป็น 1,2,3 หรือ A,B,C
    # )
    # ผลลัพธ์จะมีคอลัมน์: PRODUCT, REGION, PERIOD, AMOUNT

    # ตัวอย่างที่ 3: Auto Mode - ให้โปรแกรมตรวจสอบเอง
    # converter = CrosstabConverter("expense_crosstab.csv")
    # converter.convert(
    #     value_name="EXPENSE_VALUE",
    #     id_vars=["GROUP_NAME", "GL_CODE", "GL_NAME_NT1"],
    #     mode='auto'  # ตรวจสอบอัตโนมัติ
    # )

    # ตัวอย่างที่ 4: แบบละเอียด (Step by Step)
    # converter = CrosstabConverter("data.xlsx")
    # converter.read_file(sheet_name=0, skiprows=1)
    # converter.convert_to_long(value_name="AMOUNT", mode='sequential')
    # converter.parse_dates()  # จะข้าม parse ถ้า mode='sequential'
    # converter.clean_data(value_col="AMOUNT")
    # converter.save()

    print(__doc__)
    print("\n💡 วิธีใช้งาน:")
    print("   1. แก้ไข input_file ในส่วน __main__")
    print("   2. เลือก mode:")
    print("      - 'date' = คอลัมน์เป็นวันที่ (2025-01, 01/01/2025)")
    print("      - 'sequential' = คอลัมน์ไม่ใช่วันที่ (1,2,3, A,B,C, ม.ค., Jan)")
    print("      - 'auto' = ให้โปรแกรมตรวจสอบเอง (แนะนำ)")
    print("   3. รัน: python crosstab_converter.py")
    print("   4. ไฟล์ผลลัพธ์จะอยู่ในโฟลเดอร์เดียวกัน")
