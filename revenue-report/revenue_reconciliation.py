import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


class RevenueReconciliation:
    """
    Module สำหรับตรวจสอบความถูกต้องของข้อมูล Revenue
    เทียบระหว่างข้อมูลจากงบการเงิน (FI) กับข้อมูลจาก Transaction (TRN)
    """
    
    def __init__(self, config: dict, paths: dict):
        """
        Args:
            config: Configuration dictionary (from ConfigManager)
            paths: dict ของ paths ทั้งหมด
        """
        self.config = config
        self.paths = paths
        self.reconcile_results = {}
        
    def log(self, message, level="INFO"):
        """แสดงข้อความ log พร้อม timestamp และ level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def reconcile_revenue(self, fi_file_path, trn_file_path, tolerance=0.00):
        """
        ตรวจสอบความถูกต้องของข้อมูล Revenue
        
        Args:
            fi_file_path: path ของไฟล์จากงบการเงิน (pl_revenue_nt_output_YYYYMM.csv)
            trn_file_path: path ของไฟล์ transaction (trn_revenue_nt_YYYY.csv)
            tolerance: ยอดความแตกต่างที่ยอมรับได้ (default = 0.00)
        
        Returns:
            dict: ผลการ reconcile {'status': bool, 'details': dict}
            
        Raises:
            ReconciliationError: เมื่อพบความแตกต่างที่ไม่ยอมรับได้
        """
        self.log("=" * 80)
        self.log("RECONCILIATION - ตรวจสอบความถูกต้องของข้อมูล")
        self.log("=" * 80)
        
        # ตรวจสอบว่าไฟล์ TRN มีอยู่หรือไม่
        if not Path(trn_file_path).exists():
            self.log(f"❌ ไม่พบไฟล์ TRN: {trn_file_path}", "ERROR")
            raise FileNotFoundError(f"ไม่พบไฟล์ TRN: {trn_file_path}")
        
        # ตรวจสอบว่าไฟล์ FI มีอยู่หรือไม่
        if not Path(fi_file_path).exists():
            self.log(f"❌ ไม่พบไฟล์ FI: {fi_file_path}", "ERROR")
            raise FileNotFoundError(f"ไม่พบไฟล์ FI: {fi_file_path}")
        
        # อ่านข้อมูลจากงบการเงิน (FI)
        self.log(f"อ่านข้อมูลจากงบการเงิน: {Path(fi_file_path).name}")
        try:
            df_fi = pd.read_csv(fi_file_path)
            self.log(f"✓ อ่านข้อมูล FI สำเร็จ: {len(df_fi):,} GL Codes")
        except Exception as e:
            self.log(f"❌ ไม่สามารถอ่านไฟล์ FI: {e}", "ERROR")
            raise
        
        # ตรวจสอบโครงสร้างไฟล์ FI
        required_fi_cols = ['GL_CODE', 'REVENUE_VALUE', 'REVENUE_VALUE_YTD']
        missing_cols = [col for col in required_fi_cols if col not in df_fi.columns]
        if missing_cols:
            self.log(f"❌ ไฟล์ FI ขาดคอลัมน์: {missing_cols}", "ERROR")
            raise ValueError(f"ไฟล์ FI ขาดคอลัมน์: {missing_cols}")
        
        # อ่านข้อมูลจาก Transaction (TRN)
        self.log(f"อ่านข้อมูลจาก Transaction: {Path(trn_file_path).name}")
        try:
            df_trn = pd.read_csv(trn_file_path)
            self.log(f"✓ อ่านข้อมูล TRN สำเร็จ: {len(df_trn):,} records")
        except Exception as e:
            self.log(f"❌ ไม่สามารถอ่านไฟล์ TRN: {e}", "ERROR")
            raise
        
        # ตรวจสอบโครงสร้างไฟล์ TRN
        required_trn_cols = ['GL_CODE', 'YEAR', 'MONTH', 'REVENUE_VALUE']
        missing_cols = [col for col in required_trn_cols if col not in df_trn.columns]
        if missing_cols:
            self.log(f"❌ ไฟล์ TRN ขาดคอลัมน์: {missing_cols}", "ERROR")
            raise ValueError(f"ไฟล์ TRN ขาดคอลัมน์: {missing_cols}")
        
        # แปลง GL_CODE เป็น string
        df_fi['GL_CODE'] = df_fi['GL_CODE'].astype(str).str.strip()
        df_trn['GL_CODE'] = df_trn['GL_CODE'].astype(str).str.strip()
        
        # แปลง MONTH เป็น int (รองรับทั้ง string และ int)
        if df_trn['MONTH'].dtype == 'object':
            df_trn['MONTH'] = df_trn['MONTH'].astype(str).str.strip().astype(int)
        else:
            df_trn['MONTH'] = df_trn['MONTH'].astype(int)
        
        # หาเดือนล่าสุดจาก TRN
        latest_month = df_trn['MONTH'].max()
        latest_year = df_trn[df_trn['MONTH'] == latest_month]['YEAR'].max()
        
        self.log(f"เดือนล่าสุดใน TRN: {latest_month:02d}/{latest_year}")
        
        # สรุปข้อมูล FI
        total_fi_monthly = df_fi['REVENUE_VALUE'].sum()
        total_fi_ytd = df_fi['REVENUE_VALUE_YTD'].sum()
        self.log(f"FI - ยอดรายเดือน: {total_fi_monthly:,.2f}")
        self.log(f"FI - ยอดสะสม (YTD): {total_fi_ytd:,.2f}")
        
        # สรุปข้อมูล TRN
        df_trn_latest = df_trn[(df_trn['YEAR'] == latest_year) & (df_trn['MONTH'] == latest_month)]
        df_trn_ytd = df_trn[df_trn['YEAR'] == latest_year]
        
        # Aggregate TRN ตาม GL_CODE
        trn_monthly = df_trn_latest.groupby('GL_CODE')['REVENUE_VALUE'].sum().reset_index()
        trn_monthly.columns = ['GL_CODE', 'TRN_MONTHLY']
        
        trn_ytd = df_trn_ytd.groupby('GL_CODE')['REVENUE_VALUE'].sum().reset_index()
        trn_ytd.columns = ['GL_CODE', 'TRN_YTD']
        
        total_trn_monthly = trn_monthly['TRN_MONTHLY'].sum()
        total_trn_ytd = trn_ytd['TRN_YTD'].sum()
        self.log(f"TRN - ยอดรายเดือน: {total_trn_monthly:,.2f}")
        self.log(f"TRN - ยอดสะสม (YTD): {total_trn_ytd:,.2f}")
        
        self.log("=" * 80)
        self.log("กำลังเปรียบเทียบข้อมูล...")
        self.log("=" * 80)
        
        # ========================
        # RECONCILE 1: ยอดรายเดือน
        # ========================
        self.log("\n[1] Reconcile ยอดรายเดือน (Latest Month)")
        monthly_result = self._reconcile_by_gl(
            df_fi=df_fi[['GL_CODE', 'REVENUE_VALUE']].rename(columns={'REVENUE_VALUE': 'FI_VALUE'}),
            df_trn=trn_monthly.rename(columns={'TRN_MONTHLY': 'TRN_VALUE'}),
            reconcile_type='MONTHLY',
            tolerance=tolerance
        )
        
        # ========================
        # RECONCILE 2: ยอดสะสม (YTD)
        # ========================
        self.log("\n[2] Reconcile ยอดสะสม (YTD)")
        ytd_result = self._reconcile_by_gl(
            df_fi=df_fi[['GL_CODE', 'REVENUE_VALUE_YTD']].rename(columns={'REVENUE_VALUE_YTD': 'FI_VALUE'}),
            df_trn=trn_ytd.rename(columns={'TRN_YTD': 'TRN_VALUE'}),
            reconcile_type='YTD',
            tolerance=tolerance
        )
        
        # เก็บผลลัพธ์
        self.reconcile_results = {
            'monthly': monthly_result,
            'ytd': ytd_result,
            'latest_month': latest_month,
            'latest_year': latest_year,
            'fi_file': fi_file_path,
            'trn_file': trn_file_path
        }
        
        # สรุปผลลัพธ์
        self.log("\n" + "=" * 80)
        self.log("สรุปผลการ Reconciliation")
        self.log("=" * 80)
        
        all_passed = monthly_result['passed'] and ytd_result['passed']
        
        if all_passed:
            self.log("✓ ผ่านการตรวจสอบทั้งหมด!", "SUCCESS")
            self.log(f"  - Reconcile รายเดือน: PASSED ({monthly_result['total_records']} GL Codes)")
            self.log(f"  - Reconcile YTD: PASSED ({ytd_result['total_records']} GL Codes)")
        else:
            self.log("❌ พบความแตกต่างที่ไม่ยอมรับได้!", "ERROR")
            
            if not monthly_result['passed']:
                self.log(f"  - Reconcile รายเดือน: FAILED ({monthly_result['error_count']} errors)", "ERROR")
            else:
                self.log(f"  - Reconcile รายเดือน: PASSED", "SUCCESS")
                
            if not ytd_result['passed']:
                self.log(f"  - Reconcile YTD: FAILED ({ytd_result['error_count']} errors)", "ERROR")
            else:
                self.log(f"  - Reconcile YTD: PASSED", "SUCCESS")
        
        # บันทึก log file
        self._save_reconcile_log()
        
        # ถ้าไม่ผ่าน ให้ raise error
        if not all_passed:
            error_msg = self._format_error_message(monthly_result, ytd_result)
            raise ReconciliationError(error_msg, self.reconcile_results)
        
        return {
            'status': True,
            'details': self.reconcile_results
        }
    
    def _reconcile_by_gl(self, df_fi, df_trn, reconcile_type, tolerance):
        """
        เปรียบเทียบข้อมูลระหว่าง FI และ TRN ตาม GL_CODE
        
        Returns:
            dict: {'passed': bool, 'errors': list, 'error_count': int, 'total_records': int}
        """
        # Merge ข้อมูล
        df_compare = pd.merge(
            df_fi,
            df_trn,
            on='GL_CODE',
            how='outer',
            indicator=True
        )
        
        # แทนที่ NaN ด้วย 0
        df_compare['FI_VALUE'] = df_compare['FI_VALUE'].fillna(0)
        df_compare['TRN_VALUE'] = df_compare['TRN_VALUE'].fillna(0)
        
        # คำนวณความแตกต่าง
        # [FIX] Round to 2 decimal places to avoid floating point precision issues
        df_compare['DIFF'] = (df_compare['FI_VALUE'] - df_compare['TRN_VALUE']).round(2)
        df_compare['ABS_DIFF'] = df_compare['DIFF'].abs()
        
        # หา errors (ความแตกต่างที่มากกว่า tolerance)
        df_errors = df_compare[df_compare['ABS_DIFF'] > tolerance].copy()
        
        errors = []
        for _, row in df_errors.iterrows():
            error_detail = {
                'gl_code': row['GL_CODE'],
                'fi_value': row['FI_VALUE'],
                'trn_value': row['TRN_VALUE'],
                'diff': row['DIFF'],
                'abs_diff': row['ABS_DIFF'],
                'source': row['_merge']  # 'left_only', 'right_only', 'both'
            }
            errors.append(error_detail)
        
        # สรุปผล
        total_records = len(df_compare)
        error_count = len(errors)
        passed = error_count == 0
        
        # สถิติ
        total_fi = df_compare['FI_VALUE'].sum()
        total_trn = df_compare['TRN_VALUE'].sum()
        total_diff = total_fi - total_trn
        
        self.log(f"  Total Records: {total_records:,}")
        self.log(f"  FI Total: {total_fi:,.2f}")
        self.log(f"  TRN Total: {total_trn:,.2f}")
        self.log(f"  Diff: {total_diff:,.2f}")
        
        if passed:
            self.log(f"  ✓ ผ่านการตรวจสอบ!", "SUCCESS")
        else:
            self.log(f"  ❌ พบ {error_count} รายการที่แตกต่าง", "ERROR")
            # แสดง top 10 errors
            self._display_errors(errors, reconcile_type)
        
        return {
            'passed': passed,
            'errors': errors,
            'error_count': error_count,
            'total_records': total_records,
            'total_fi': total_fi,
            'total_trn': total_trn,
            'total_diff': total_diff,
            'reconcile_type': reconcile_type
        }
    
    def _display_errors(self, errors, reconcile_type, max_display=10):
        """แสดงรายละเอียด errors"""
        self.log(f"\n  รายละเอียดความแตกต่าง ({reconcile_type}) - แสดง {min(len(errors), max_display)} รายการแรก:")
        self.log("  " + "-" * 76)
        self.log(f"  {'GL_CODE':<12} {'FI':>18} {'TRN':>18} {'DIFF':>18} {'SOURCE':<10}")
        self.log("  " + "-" * 76)
        
        for i, err in enumerate(errors[:max_display]):
            source_text = {
                'left_only': 'FI Only',
                'right_only': 'TRN Only',
                'both': 'Both'
            }.get(err['source'], err['source'])
            
            self.log(
                f"  {err['gl_code']:<12} "
                f"{err['fi_value']:>18,.2f} "
                f"{err['trn_value']:>18,.2f} "
                f"{err['diff']:>18,.2f} "
                f"{source_text:<10}"
            )
        
        if len(errors) > max_display:
            self.log(f"  ... และอีก {len(errors) - max_display} รายการ")
        self.log("  " + "-" * 76)
    
    def _format_error_message(self, monthly_result, ytd_result):
        """สร้างข้อความ error แบบละเอียด"""
        msg = "\n" + "=" * 80 + "\n"
        msg += "RECONCILIATION FAILED - พบความแตกต่างที่ไม่ยอมรับได้\n"
        msg += "=" * 80 + "\n\n"
        
        if not monthly_result['passed']:
            msg += f"[รายเดือน] พบ {monthly_result['error_count']} รายการที่แตกต่าง:\n"
            msg += f"  - FI Total: {monthly_result['total_fi']:,.2f}\n"
            msg += f"  - TRN Total: {monthly_result['total_trn']:,.2f}\n"
            msg += f"  - Diff: {monthly_result['total_diff']:,.2f}\n\n"
        
        if not ytd_result['passed']:
            msg += f"[YTD] พบ {ytd_result['error_count']} รายการที่แตกต่าง:\n"
            msg += f"  - FI Total: {ytd_result['total_fi']:,.2f}\n"
            msg += f"  - TRN Total: {ytd_result['total_trn']:,.2f}\n"
            msg += f"  - Diff: {ytd_result['total_diff']:,.2f}\n\n"
        
        msg += "กรุณาตรวจสอบ log file สำหรับรายละเอียดเพิ่มเติม\n"
        msg += "=" * 80
        
        return msg
    
    def _save_reconcile_log(self):
        """บันทึก log file ของการ reconcile"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(self.paths['output']) / 'reconcile_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # บันทึก Summary Log (Text)
        summary_file = log_dir / f"reconcile_summary_{self.config['year']}_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REVENUE RECONCILIATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Year: {self.reconcile_results['latest_year']}\n")
            f.write(f"Latest Month: {self.reconcile_results['latest_month']:02d}\n")
            f.write(f"FI File: {self.reconcile_results['fi_file']}\n")
            f.write(f"TRN File: {self.reconcile_results['trn_file']}\n\n")
            
            # Monthly Result
            monthly = self.reconcile_results['monthly']
            f.write("=" * 80 + "\n")
            f.write("[1] RECONCILE รายเดือน (MONTHLY)\n")
            f.write("=" * 80 + "\n")
            f.write(f"Status: {'PASSED' if monthly['passed'] else 'FAILED'}\n")
            f.write(f"Total Records: {monthly['total_records']:,}\n")
            f.write(f"FI Total: {monthly['total_fi']:,.2f}\n")
            f.write(f"TRN Total: {monthly['total_trn']:,.2f}\n")
            f.write(f"Diff: {monthly['total_diff']:,.2f}\n")
            f.write(f"Error Count: {monthly['error_count']}\n\n")
            
            if monthly['error_count'] > 0:
                f.write("Errors:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'GL_CODE':<12} {'FI':>18} {'TRN':>18} {'DIFF':>18} {'SOURCE':<10}\n")
                f.write("-" * 80 + "\n")
                for err in monthly['errors']:
                    f.write(
                        f"{err['gl_code']:<12} "
                        f"{err['fi_value']:>18,.2f} "
                        f"{err['trn_value']:>18,.2f} "
                        f"{err['diff']:>18,.2f} "
                        f"{err['source']:<10}\n"
                    )
                f.write("\n")
            
            # YTD Result
            ytd = self.reconcile_results['ytd']
            f.write("=" * 80 + "\n")
            f.write("[2] RECONCILE ยอดสะสม (YTD)\n")
            f.write("=" * 80 + "\n")
            f.write(f"Status: {'PASSED' if ytd['passed'] else 'FAILED'}\n")
            f.write(f"Total Records: {ytd['total_records']:,}\n")
            f.write(f"FI Total: {ytd['total_fi']:,.2f}\n")
            f.write(f"TRN Total: {ytd['total_trn']:,.2f}\n")
            f.write(f"Diff: {ytd['total_diff']:,.2f}\n")
            f.write(f"Error Count: {ytd['error_count']}\n\n")
            
            if ytd['error_count'] > 0:
                f.write("Errors:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'GL_CODE':<12} {'FI':>18} {'TRN':>18} {'DIFF':>18} {'SOURCE':<10}\n")
                f.write("-" * 80 + "\n")
                for err in ytd['errors']:
                    f.write(
                        f"{err['gl_code']:<12} "
                        f"{err['fi_value']:>18,.2f} "
                        f"{err['trn_value']:>18,.2f} "
                        f"{err['diff']:>18,.2f} "
                        f"{err['source']:<10}\n"
                    )
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            overall_status = "PASSED" if (monthly['passed'] and ytd['passed']) else "FAILED"
            f.write(f"OVERALL STATUS: {overall_status}\n")
            f.write("=" * 80 + "\n")
        
        self.log(f"\n✓ บันทึก Summary Log: {summary_file}")
        
        # บันทึก Detail Log (CSV) - เฉพาะ errors
        if monthly['error_count'] > 0:
            monthly_csv = log_dir / f"reconcile_monthly_errors_{self.config['year']}_{timestamp}.csv"
            df_monthly_errors = pd.DataFrame(monthly['errors'])
            df_monthly_errors.to_csv(monthly_csv, index=False, encoding='utf-8-sig')
            self.log(f"✓ บันทึก Monthly Errors CSV: {monthly_csv}")
        
        if ytd['error_count'] > 0:
            ytd_csv = log_dir / f"reconcile_ytd_errors_{self.config['year']}_{timestamp}.csv"
            df_ytd_errors = pd.DataFrame(ytd['errors'])
            df_ytd_errors.to_csv(ytd_csv, index=False, encoding='utf-8-sig')
            self.log(f"✓ บันทึก YTD Errors CSV: {ytd_csv}")


class ReconciliationError(Exception):
    """Custom Exception สำหรับ Reconciliation Error"""
    def __init__(self, message, reconcile_results=None):
        super().__init__(message)
        self.reconcile_results = reconcile_results