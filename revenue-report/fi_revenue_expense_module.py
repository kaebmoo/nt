"""
FI Revenue Expense Module
=========================
Module สำหรับประมวลผลข้อมูลงบการเงิน (Financial Income Statement)
จัดการข้อมูล Revenue และ Expense จากระบบ GL

Author: Revenue ETL System
Version: 2.0.0 (Modularized)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import os
import traceback


class FIRevenueExpenseProcessor:
    """
    Processor สำหรับประมวลผลข้อมูล Revenue และ Expense จากงบการเงิน
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize FI Processor
        
        Args:
            config: configuration dictionary จาก ConfigManager
        """
        self.config = config
        self.paths = config['paths']
        self.year = config['year']
        
        # ตั้งค่า pandas display
        pd.options.display.float_format = '{:,.2f}'.format
        
        # Master DataFrames
        self.master_expense_gl = None
        self.master_revenue_gl = None
        
        # Results
        self.results = {}
        
        # สร้าง directories
        self._setup_directories()
        
    def _setup_directories(self) -> None:
        """สร้าง directories ที่จำเป็น"""
        Path(self.paths['output']).mkdir(parents=True, exist_ok=True)
        print(f"✓ ตรวจสอบ/สร้าง Output Directory: {self.paths['output']}")
    
    def log(self, message: str, level: str = "INFO") -> None:
        """
        แสดงข้อความ log
        
        Args:
            message: ข้อความที่ต้องการแสดง
            level: ระดับของ log (INFO, WARNING, ERROR, SUCCESS)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def load_master_files(self) -> bool:
        """
        โหลดไฟล์ Master ทั้งหมด
        
        Returns:
            bool: True ถ้าโหลดสำเร็จ, False ถ้าล้มเหลว
        """
        try:
            self.log("=" * 80)
            self.log("กำลังโหลด Master Files...")
            self.log("=" * 80)
            
            # โหลด Master Expense
            master_expense_file = os.path.join(
                self.paths['master_source'],
                self.config['master_files']['expense']
            )
            
            self.log(f"โหลด Master Expense: {self.config['master_files']['expense']}")
            self.master_expense_gl = pd.read_csv(master_expense_file, encoding="utf8")
            self.master_expense_gl = self.master_expense_gl[["CODE_GROUP", "GROUP_NAME", "GL_CODE_NT1", "GL_NAME_NT1"]]
            self.master_expense_gl = self.master_expense_gl.rename(columns={
                "GL_CODE_NT1": "GL_CODE",
                "GL_NAME_NT1": "GL_NAME"
            })
            self.master_expense_gl["GL_CODE"] = self.master_expense_gl["GL_CODE"].astype(str)
            self.log(f"✓ โหลด Master Expense สำเร็จ: {len(self.master_expense_gl)} GL Codes", "SUCCESS")
            
            # โหลด Master Revenue
            master_revenue_file = os.path.join(
                self.paths['master_source'],
                self.config['master_files']['revenue']
            )
            
            self.log(f"โหลด Master Revenue: {self.config['master_files']['revenue']}")
            self.master_revenue_gl = pd.read_csv(master_revenue_file, encoding="utf8")
            self.master_revenue_gl = self.master_revenue_gl[["REPORT_CODE", "GL_GROUP", "GL_CODE_NT1", "GL_NAME_NT1"]]
            self.master_revenue_gl = self.master_revenue_gl.rename(columns={
                "GL_CODE_NT1": "GL_CODE",
                "GL_NAME_NT1": "GL_NAME"
            })
            self.master_revenue_gl["GL_CODE"] = self.master_revenue_gl["GL_CODE"].astype(str)
            self.log(f"✓ โหลด Master Revenue สำเร็จ: {len(self.master_revenue_gl)} GL Codes", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ เกิดข้อผิดพลาดในการโหลด Master Files: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def process_financial_and_other(
        self,
        of_revenue: pd.DataFrame,
        gl_group_expense: pd.DataFrame
    ) -> Optional[pd.DataFrame]:
        """
        ประมวลผลส่วนของผลตอบแทนทางการเงิน, รายได้อื่น, และค่าใช้จ่ายอื่น
        (Logic 3.0 - เหมือนโค้ดเดิม)
        
        Args:
            of_revenue: DataFrame ของ Revenue
            gl_group_expense: DataFrame ของ Expense ที่ merge กับ master แล้ว
            
        Returns:
            DataFrame: สรุปผลลัพธ์ หรือ None ถ้าเกิดข้อผิดพลาด
        """
        print("\n" + "="*80)
        print("Starting 'process_financial_and_other' (New Logic)")
        print("="*80)
        
        try:
            # --- Step 1: สร้างข้อมูล R (รายได้ที่อยู่ใน MASTER_OTHER_REVENUE_NET) ---
            print("\n--- Step 1: สร้างข้อมูล R ---")
            
            master_other_rev_file = os.path.join(
                self.paths['master'],
                self.config['master_files']['other_revenue']
            )
            master_other_rev = pd.read_csv(master_other_rev_file)
            master_other_rev.columns = master_other_rev.columns.str.strip()
            
            # ทำความสะอาด GL_GROUP
            if 'GL_GROUP' in master_other_rev.columns:
                master_other_rev['GL_GROUP'] = master_other_rev['GL_GROUP'].astype(str).str.replace(r'["\r\n]', '', regex=True).str.strip()
            else:
                raise KeyError(f"Column 'GL_GROUP' not found in {self.config['master_files']['other_revenue']}")
                
            master_other_rev['GL_CODE'] = master_other_rev['GL_CODE'].astype(str)
            
            # Merge เพื่อคัดเฉพาะ GL_CODE ที่อยู่ใน Master
            data_R = pd.merge(of_revenue, master_other_rev, on='GL_CODE', how='inner')
            print(f"✓ สร้าง Data R เรียบร้อย: {len(data_R)} รายการ")
            
            # --- Step 2: สร้างข้อมูล F (ผลตอบแทนทางการเงิน) ---
            print("\n--- Step 2: สร้างข้อมูล F (ผลตอบแทนทางการเงิน) ---")
            data_F = data_R[data_R['GL_GROUP'] == 'ผลตอบแทนทางการเงิน'].copy()
            
            # Log รายการก่อน sum
            print(f"รายการผลตอบแทนทางการเงิน ({len(data_F)} รายการ):")
            for idx, row in data_F.iterrows():
                print(f"  - GL_CODE: {row['GL_CODE']}, GL_NAME: {row['GL_NAME']}")
                print(f"    เดือน: {row['REVENUE_VALUE']:>15,.2f}, สะสม: {row['REVENUE_VALUE_YTD']:>15,.2f}")
            
            # เปลี่ยนชื่อ column GL_GROUP เป็น GROUP
            data_F = data_F.rename(columns={
                'GL_GROUP': 'GROUP',
                'REVENUE_VALUE': 'VALUE',
                'REVENUE_VALUE_YTD': 'VALUE_YTD'
            })
            
            # Sum รวม
            f_month = data_F['VALUE'].sum()
            f_ytd = data_F['VALUE_YTD'].sum()
            print(f"\n✓ ผลรวม F: เดือน = {f_month:,.2f}, สะสม = {f_ytd:,.2f}")
            
            # --- Step 3: สร้างข้อมูล E (ค่าใช้จ่ายอื่น จาก gl_group_expense) ---
            print("\n--- Step 3: สร้างข้อมูล E (ค่าใช้จ่ายอื่น) ---")
            data_E = gl_group_expense[gl_group_expense['GROUP_NAME'] == 'ค่าใช้จ่ายอื่น'].copy()
            
            # Log รายการก่อนคูณ -1
            print(f"รายการค่าใช้จ่ายอื่น ({len(data_E)} รายการ) ก่อนคูณ -1:")
            for idx, row in data_E.iterrows():
                print(f"  - GL_CODE: {row['GL_CODE']}, GL_NAME: {row['GL_NAME']}")
                print(f"    เดือน: {row['EXPENSE_VALUE']:>15,.2f}, สะสม: {row['EXPENSE_VALUE_YTD']:>15,.2f}")
            
            # คูณ -1
            data_E['VALUE'] = data_E['EXPENSE_VALUE'] * -1
            data_E['VALUE_YTD'] = data_E['EXPENSE_VALUE_YTD'] * -1
            
            print(f"\nหลังคูณ -1:")
            for idx, row in data_E.iterrows():
                print(f"  - GL_CODE: {row['GL_CODE']}, เดือน: {row['VALUE']:>15,.2f}, สะสม: {row['VALUE_YTD']:>15,.2f}")
            
            # เลือกเฉพาะ columns ที่ต้องการ
            data_E_final = data_E[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()
            
            # --- Step 4: สร้างข้อมูล RE (รวม R กับ E) ---
            print("\n--- Step 4: สร้างข้อมูล RE (รวม R + E) ---")
            # เปลี่ยนชื่อ columns ของ R ให้ตรงกัน
            data_R_renamed = data_R.rename(columns={
                'REVENUE_VALUE': 'VALUE',
                'REVENUE_VALUE_YTD': 'VALUE_YTD'
            })
            
            # เลือกเฉพาะ columns ที่ต้องการจาก R
            data_R_for_concat = data_R_renamed[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()
            
            # รวม R กับ E
            data_RE = pd.concat([data_R_for_concat, data_E_final], ignore_index=True)
            print(f"✓ สร้าง Data RE: {len(data_RE)} รายการ (R: {len(data_R_for_concat)}, E: {len(data_E_final)})")
            
            # --- Step 5: สร้างข้อมูล RE_OTHER (Merge กับ master_revenue_expense_net) ---
            print("\n--- Step 5: สร้างข้อมูล RE_OTHER ---")
            
            master_rev_exp_net_file = os.path.join(
                self.paths['master'],
                self.config['master_files']['revenue_expense_net']
            )
            master_rev_exp_net = pd.read_csv(master_rev_exp_net_file)
            master_rev_exp_net.columns = master_rev_exp_net.columns.str.strip()
            
            # ทำความสะอาด GROUP
            if 'GROUP' in master_rev_exp_net.columns:
                master_rev_exp_net['GROUP'] = master_rev_exp_net['GROUP'].astype(str).str.replace(r'["\r\n]', '', regex=True).str.strip()
            else:
                raise KeyError(f"Column 'GROUP' not found in {self.config['master_files']['revenue_expense_net']}")
                
            master_rev_exp_net['GL_CODE'] = master_rev_exp_net['GL_CODE'].astype(str)
            
            # Merge (inner join - เอาเฉพาะที่ GL_CODE ตรงกัน)
            data_RE_OTHER = pd.merge(data_RE, master_rev_exp_net[["GL_CODE", "SUB_GROUP", "GROUP"]], on='GL_CODE', how='inner')
            print(f"✓ สร้าง Data RE_OTHER: {len(data_RE_OTHER)} รายการ")
            print(data_RE_OTHER.sum(numeric_only=True))
            
            # --- Step 6: แยกข้อมูล R_OTHER (รายได้อื่น) ---
            print("\n--- Step 6: แยกข้อมูล R_OTHER (GROUP = รายได้อื่น) ---")
            data_R_OTHER = data_RE_OTHER[data_RE_OTHER['GROUP'] == 'รายได้อื่น'].copy()
            print(f"✓ พบข้อมูล R_OTHER: {len(data_R_OTHER)} รายการ")
            print(data_R_OTHER.groupby('GROUP').sum(numeric_only=True))
            
            data_R_OTHER = data_R_OTHER.groupby(['GROUP', 'SUB_GROUP'], dropna=False).agg({
                'GL_CODE': 'first',
                'GL_NAME': 'first',
                'VALUE': 'sum',
                'VALUE_YTD': 'sum'
            }).reset_index()
            
            # --- Step 7: แยก R_OTHER_NET และ R_OTHER_E (แยกระดับคอลัมน์) ---
            print("\n--- Step 7: แยก R_OTHER_NET และ R_OTHER_E (แยกระดับคอลัมน์) ---")
            
            print(f"ยอดรวมใน data_R_OTHER (ก่อนแยก):")
            print(f"  VALUE ทั้งหมด: {data_R_OTHER['VALUE'].sum():,.2f}")
            print(f"  VALUE_YTD ทั้งหมด: {data_R_OTHER['VALUE_YTD'].sum():,.2f}")
            
            # คำนวณผลรวมโดยตรง - แยกในระดับคอลัมน์
            # รายได้อื่น (บวก)
            r_other_net_month = data_R_OTHER.loc[data_R_OTHER['VALUE'] > 0, 'VALUE'].sum()
            r_other_net_ytd = data_R_OTHER.loc[data_R_OTHER['VALUE_YTD'] > 0, 'VALUE_YTD'].sum()
            
            # ค่าใช้จ่ายอื่น (ลบ)
            r_other_e_month = data_R_OTHER.loc[data_R_OTHER['VALUE'] < 0, 'VALUE'].sum()
            r_other_e_ytd = data_R_OTHER.loc[data_R_OTHER['VALUE_YTD'] < 0, 'VALUE_YTD'].sum()
            
            print(f"\n✓ R_OTHER_NET (รายได้อื่น - บวก):")
            print(f"  เดือน: {r_other_net_month:,.2f}")
            print(f"  สะสม: {r_other_net_ytd:,.2f}")
            
            print(f"\n✓ R_OTHER_E (ค่าใช้จ่ายอื่น - ลบ):")
            print(f"  เดือน: {r_other_e_month:,.2f}")
            print(f"  สะสม: {r_other_e_ytd:,.2f}")
            
            # --- Step 8: สร้างผลลัพธ์สุดท้าย ---
            print("\n--- Step 8: สรุปผลลัพธ์สุดท้าย ---")
            
            # ผลตอบแทนทางการเงิน (จาก F)
            financial_month = f_month
            financial_ytd = f_ytd
            
            # รายได้อื่น (จาก R_OTHER_NET)
            other_income_month = r_other_net_month
            other_income_ytd = r_other_net_ytd
            
            # ค่าใช้จ่ายอื่น (จาก R_OTHER_E)
            other_expense_month = r_other_e_month
            other_expense_ytd = r_other_e_ytd
            
            # สร้าง Summary DataFrame
            summary_data = {
                'รายการ': ['ผลตอบแทนทางการเงิน', 'รายได้อื่น', 'ค่าใช้จ่ายอื่น'],
                'เดือน': [financial_month, other_income_month, other_expense_month],
                'สะสม': [financial_ytd, other_income_ytd, other_expense_ytd]
            }
            summary_df = pd.DataFrame(summary_data)
            
            # แสดงผลลัพธ์
            print("\n" + "="*80)
            print("ผลลัพธ์สุดท้าย: รายได้/ค่าใช้จ่ายอื่น")
            print("="*80)
            print(f"{'รายการ':<35} {'เดือน':>20} {'สะสม':>20}")
            print("-"*80)
            print(f"{'ผลตอบแทนทางการเงิน':<35} {financial_month:>20,.2f} {financial_ytd:>20,.2f}")
            print(f"{'รายได้อื่น':<35} {other_income_month:>20,.2f} {other_income_ytd:>20,.2f}")
            print(f"{'ค่าใช้จ่ายอื่น':<35} {other_expense_month:>20,.2f} {other_expense_ytd:>20,.2f}")
            print("="*80)
            
            print("\n✓ End 'process_financial_and_other' (New Logic)")
            
            return summary_df
            
        except FileNotFoundError as e:
            print(f"\n*** ERROR: ไม่พบไฟล์! ***")
            print(f"File not found: {e.filename}")
            print("\nกรุณาตรวจสอบว่าไฟล์เหล่านี้อยู่ใน master_path:")
            print(f"1. {self.config['master_files']['other_revenue']}")
            print(f"2. {self.config['master_files']['revenue_expense_net']}")
            return None
        except KeyError as e:
            print(f"\n*** ERROR: ไม่พบคอลัมน์ที่ต้องการ! ***")
            print(f"KeyError: {e}")
            print("\nกรุณาตรวจสอบชื่อคอลัมน์ในไฟล์ Master (เช่น 'GL_CODE', 'GL_GROUP', 'GROUP')")
            return None
        except Exception as e:
            print(f"\n*** ERROR (Unexpected): {e} ***")
            traceback.print_exc()
            return None
    
    def process_file(self, input_file: str) -> Dict[str, Any]:
        """
        ประมวลผลไฟล์ input หนึ่งไฟล์
        
        Args:
            input_file: ชื่อไฟล์ที่ต้องการประมวลผล
            
        Returns:
            dict: ผลลัพธ์การประมวลผล
        """
        self.log(f"Processing file: {input_file}")
        
        input_path = os.path.join(self.paths['input'], input_file)
        
        # อ่านไฟล์ Input
        df = pd.read_csv(
            input_path,
            encoding=self.config['encoding']['input'],
            delimiter=self.config['processing_rules']['delimiter'],
            header=None,
            on_bad_lines="skip"
        )
        
        # สร้าง DataFrame พื้นฐาน
        of_base = pd.DataFrame()
        of_base["GL_CODE"] = df[4]
        of_base["VALUE"] = df[11]
        of_base["VALUE_YTD"] = df[13]
        
        # ทำความสะอาดข้อมูลตัวเลข
        for col in ["VALUE", "VALUE_YTD"]:
            of_base[col] = of_base[col].replace(",", "", regex=True)
            of_base[col] = of_base[col].replace(r"\(", "-", regex=True)
            of_base[col] = of_base[col].replace(r"\)", "", regex=True)
        
        of_base["VALUE"] = pd.to_numeric(of_base["VALUE"])
        of_base["VALUE_YTD"] = pd.to_numeric(of_base["VALUE_YTD"])
        of_base["GL_CODE"] = of_base["GL_CODE"].astype(str)
        
        # --- ประมวลผลส่วนของ Expense ---
        self.log("Processing Expenses...")
        expense_pattern = self.config['processing_rules']['expense_gl_pattern']
        of_expense = of_base[of_base["GL_CODE"].fillna("").str.match(expense_pattern)].copy()
        of_expense = of_expense.rename(columns={"VALUE": "EXPENSE_VALUE", "VALUE_YTD": "EXPENSE_VALUE_YTD"})
        
        # Merge กับ Master Expense
        gl_group_expense = pd.merge(of_expense, self.master_expense_gl, on="GL_CODE", how="left")
        gl_group_expense = gl_group_expense[["CODE_GROUP", "GROUP_NAME", "GL_CODE", "GL_NAME", "EXPENSE_VALUE", "EXPENSE_VALUE_YTD"]]
        
        # Group by
        gl_group_by_expense = gl_group_expense[["CODE_GROUP", "GROUP_NAME", "EXPENSE_VALUE", "EXPENSE_VALUE_YTD"]]
        gl_group_by_expense = gl_group_by_expense.groupby(by=["CODE_GROUP", "GROUP_NAME"], dropna=False).sum().reset_index()
        gl_group_by_expense.loc['Total'] = gl_group_by_expense.sum(axis=0, numeric_only=True)
        
        # --- ประมวลผลส่วนของ Revenue ---
        self.log("Processing Revenues...")
        revenue_pattern = self.config['processing_rules']['revenue_gl_pattern']
        of_revenue = of_base[of_base["GL_CODE"].str.startswith("4")].copy()
        of_revenue = of_revenue.rename(columns={"VALUE": "REVENUE_VALUE", "VALUE_YTD": "REVENUE_VALUE_YTD"})
        
        # Merge กับ Master Revenue
        gl_group_revenue = pd.merge(of_revenue, self.master_revenue_gl, on="GL_CODE", how="left")
        gl_group_revenue = gl_group_revenue[["REPORT_CODE", "GL_GROUP", "GL_NAME", "GL_CODE", "REVENUE_VALUE", "REVENUE_VALUE_YTD"]]
        
        # Group by
        gl_group_by_revenue = gl_group_revenue[["REPORT_CODE", "GL_GROUP", "REVENUE_VALUE", "REVENUE_VALUE_YTD"]]
        gl_group_by_revenue = gl_group_by_revenue.groupby(by=["REPORT_CODE", "GL_GROUP"], dropna=False).sum().reset_index()
        gl_group_by_revenue.loc['Total'] = gl_group_by_revenue.sum(axis=0, numeric_only=True)
        
        # --- เรียกใช้ฟังก์ชันวิเคราะห์รายได้/ค่าใช้จ่ายอื่น ---
        summary_other_fin_df = self.process_financial_and_other(
            of_revenue=of_revenue,
            gl_group_expense=gl_group_expense
        )
        
        return {
            'of_expense': of_expense,
            'gl_group_expense': gl_group_expense,
            'gl_group_by_expense': gl_group_by_expense,
            'of_revenue': of_revenue,
            'gl_group_revenue': gl_group_revenue,
            'gl_group_by_revenue': gl_group_by_revenue,
            'summary_other_fin_df': summary_other_fin_df
        }
    
    def save_results(self, results: Dict[str, Any]) -> bool:
        """
        บันทึกผลลัพธ์เป็นไฟล์ Excel และ CSV
        
        Args:
            results: ผลลัพธ์จากการประมวลผล
            
        Returns:
            bool: True ถ้าบันทึกสำเร็จ, False ถ้าล้มเหลว
        """
        try:
            # บันทึก CSV files
            csv_expense_path = os.path.join(self.paths['output'], self.config['output_files']['csv_expense'])
            csv_revenue_path = os.path.join(self.paths['output'], self.config['output_files']['csv_revenue'])
            
            results['of_expense'].to_csv(csv_expense_path, index=False)
            results['of_revenue'].to_csv(csv_revenue_path, index=False)
            
            self.log(f"✓ บันทึก CSV: {self.config['output_files']['csv_expense']}", "SUCCESS")
            self.log(f"✓ บันทึก CSV: {self.config['output_files']['csv_revenue']}", "SUCCESS")
            
            # บันทึก Excel file
            excel_path = os.path.join(self.paths['output'], self.config['output_files']['excel'])
            writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
            
            # เขียนชีต Expense
            results['of_expense'].to_excel(writer, sheet_name="expense_data", index=False)
            results['gl_group_expense'].to_excel(writer, sheet_name="expense_gl_group_data", index=False)
            results['gl_group_by_expense'].to_excel(writer, sheet_name="expense_gl_group", index=False)
            
            # เขียนชีต Revenue
            results['of_revenue'].to_excel(writer, sheet_name="revenue_data", index=False)
            results['gl_group_revenue'].to_excel(writer, sheet_name="revenue_gl_group_data", index=False)
            results['gl_group_by_revenue'].to_excel(writer, sheet_name="revenue_gl_group", index=False)
            
            # เขียนชีตสรุปรายได้/ค่าใช้จ่ายอื่น
            if results['summary_other_fin_df'] is not None:
                results['summary_other_fin_df'].to_excel(writer, sheet_name="summary_other", index=False)
            else:
                self.log("⚠️ ไม่สามารถสร้างชีต summary_other ได้ เนื่องจากข้อมูลเป็น None", "WARNING")
            
            # จัดรูปแบบ Excel
            workbook = writer.book
            number_format = workbook.add_format({'num_format': '#,##0.00'})
            
            # จัดรูปแบบชีต Expense
            worksheet_data_exp = writer.sheets["expense_data"]
            worksheet_gl_group_data_exp = writer.sheets["expense_gl_group_data"]
            worksheet_gl_group_by_exp = writer.sheets["expense_gl_group"]
            
            worksheet_data_exp.set_column(1, 2, 18, number_format)
            worksheet_gl_group_data_exp.set_column(0, 0, 12)
            worksheet_gl_group_data_exp.set_column(1, 1, 36)
            worksheet_gl_group_data_exp.set_column(2, 2, 9)
            worksheet_gl_group_data_exp.set_column(3, 3, 36)
            worksheet_gl_group_data_exp.set_column(4, 5, 18, number_format)
            
            worksheet_gl_group_by_exp.set_column(0, 0, 12)
            worksheet_gl_group_by_exp.set_column(1, 1, 36)
            worksheet_gl_group_by_exp.set_column(2, 3, 18, number_format)
            
            # จัดรูปแบบชีต Revenue
            worksheet_data_rev = writer.sheets["revenue_data"]
            worksheet_gl_group_data_rev = writer.sheets["revenue_gl_group_data"]
            worksheet_gl_group_by_rev = writer.sheets["revenue_gl_group"]
            
            worksheet_data_rev.set_column(1, 2, 18, number_format)
            worksheet_gl_group_data_rev.set_column(0, 0, 12)
            worksheet_gl_group_data_rev.set_column(1, 1, 36)
            worksheet_gl_group_data_rev.set_column(2, 3, 36)
            worksheet_gl_group_data_rev.set_column(4, 5, 18, number_format)
            
            worksheet_gl_group_by_rev.set_column(0, 0, 12)
            worksheet_gl_group_by_rev.set_column(1, 1, 36)
            worksheet_gl_group_by_rev.set_column(2, 3, 18, number_format)
            
            # จัดรูปแบบชีตสรุป summary_other
            if results['summary_other_fin_df'] is not None:
                worksheet_summary = writer.sheets["summary_other"]
                worksheet_summary.set_column(0, 0, 35)
                worksheet_summary.set_column(1, 2, 20, number_format)
            
            writer.close()
            
            self.log(f"✓ บันทึก Excel: {self.config['output_files']['excel']}", "SUCCESS")
            self.log(f"✓ Successfully combined output to {excel_path}", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ เกิดข้อผิดพลาดในการบันทึกไฟล์: {e}", "ERROR")
            traceback.print_exc()
            return False
    
    def run(self) -> bool:
        """
        รันกระบวนการประมวลผลทั้งหมด
        
        Returns:
            bool: True ถ้าสำเร็จ, False ถ้าล้มเหลว
        """
        self.log("=" * 80)
        self.log("เริ่มประมวลผล FI Revenue Expense")
        self.log("=" * 80)
        
        # โหลด Master Files
        if not self.load_master_files():
            self.log("❌ ไม่สามารถโหลด Master Files ได้", "ERROR")
            return False
        
        # ประมวลผลไฟล์ input ทุกไฟล์
        for input_file in self.config['input_files']:
            try:
                self.log(f"\nประมวลผลไฟล์: {input_file}")
                results = self.process_file(input_file)
                
                # บันทึกผลลัพธ์
                if not self.save_results(results):
                    self.log(f"❌ ไม่สามารถบันทึกผลลัพธ์ของไฟล์ {input_file}", "ERROR")
                    return False
                    
                self.results[input_file] = results
                
            except Exception as e:
                self.log(f"❌ เกิดข้อผิดพลาดในการประมวลผลไฟล์ {input_file}: {e}", "ERROR")
                traceback.print_exc()
                return False
        
        self.log("\n" + "=" * 80)
        self.log("✓ ประมวลผล FI Revenue Expense เสร็จสมบูรณ์", "SUCCESS")
        self.log("=" * 80)
        
        return True
    
    def get_output_files(self) -> Dict[str, str]:
        """
        ดึงรายชื่อไฟล์ output ที่สร้างขึ้น
        
        Returns:
            dict: รายชื่อไฟล์ output พร้อม path
        """
        return {
            'excel': os.path.join(self.paths['output'], self.config['output_files']['excel']),
            'csv_expense': os.path.join(self.paths['output'], self.config['output_files']['csv_expense']),
            'csv_revenue': os.path.join(self.paths['output'], self.config['output_files']['csv_revenue'])
        }


if __name__ == "__main__":
    # ทดสอบ module โดยอิสระ
    print("FI Revenue Expense Module - Test Mode")
    print("This module should be run through main.py")
    print("To test independently, ensure config.json is available")