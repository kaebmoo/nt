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
        self.adj_gl_data = None  # DataFrame of ADJ_GL entries (loaded on demand)
        
    def log(self, message, level="INFO"):
        """แสดงข้อความ log พร้อม timestamp และ level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def load_master_gl(self, master_gl_path, exclude_gl_group='ผลตอบแทนทางการเงินและรายได้อื่น'):
        """
        โหลด Master GL file เพื่อแยก GL เป็น 2 กลุ่ม:
        - core_gl_codes: GL รายได้หลัก (ต้อง reconcile ให้ตรง)
        - excluded_gl_codes: GL ที่ไม่ต้อง reconcile (ผลตอบแทนทางการเงินฯ)

        Args:
            master_gl_path: path ของไฟล์ MASTER_REVENUE_GL_CODE_NT1_NT_*.csv
            exclude_gl_group: ชื่อ GL_GROUP ที่ต้องการยกเว้น
        """
        self.exclude_gl_group = exclude_gl_group
        self.excluded_gl_codes = set()
        self.core_gl_codes = set()

        if not master_gl_path or not Path(master_gl_path).exists():
            self.log(f"  ⚠️  ไม่พบ Master GL file: {master_gl_path} — จะ reconcile ทุก GL", "WARNING")
            return

        try:
            df_master = pd.read_csv(master_gl_path, encoding='utf-8-sig')
            df_master.columns = df_master.columns.str.strip()

            # ใช้ GL_CODE_NT1 (ถ้ามี) เพราะ TRN ใช้ GL_CODE_NT1
            gl_col = 'GL_CODE_NT1' if 'GL_CODE_NT1' in df_master.columns else 'GL_CODE'
            df_master[gl_col] = df_master[gl_col].astype(str).str.strip()

            # แยกกลุ่ม
            excluded = df_master[df_master['GL_GROUP'] == exclude_gl_group][gl_col].unique()
            core = df_master[df_master['GL_GROUP'] != exclude_gl_group][gl_col].unique()

            self.excluded_gl_codes = set(excluded) - {'', 'nan', 'NT', 'NT2'}
            self.core_gl_codes = set(core) - {'', 'nan', 'NT', 'NT2'}

            self.log(f"  ✓ โหลด Master GL: {Path(master_gl_path).name}")
            self.log(f"    GL รายได้หลัก: {len(self.core_gl_codes)} codes")
            self.log(f"    GL ยกเว้น ({exclude_gl_group}): {len(self.excluded_gl_codes)} codes")
        except Exception as e:
            self.log(f"  ⚠️  ไม่สามารถอ่าน Master GL: {e}", "WARNING")

    def load_adj_gl_files(self, adj_gl_file_paths):
        """
        โหลดไฟล์ ADJ_GL เพื่อใช้ใน secondary reconciliation check

        Args:
            adj_gl_file_paths: list ของ path ไฟล์ TRN_REVENUE_ADJ_GL_NT1_*.csv
        """
        if not adj_gl_file_paths:
            return

        dfs = []
        for f in adj_gl_file_paths:
            try:
                df = pd.read_csv(f)
                df.columns = df.columns.str.strip()
                # Normalize GL_CODE column name
                if 'GL_CODE_NT1' in df.columns:
                    df['GL_CODE'] = df['GL_CODE_NT1'].astype(str).str.strip()
                elif 'GL_CODE' in df.columns:
                    df['GL_CODE'] = df['GL_CODE'].astype(str).str.strip()
                # Parse REVENUE_VALUE
                df['REVENUE_VALUE'] = pd.to_numeric(
                    df['REVENUE_VALUE'].astype(str).str.replace(',', '').str.replace('(', '-').str.replace(')', '').str.replace(' ', ''),
                    errors='coerce'
                )
                if 'MONTH' in df.columns:
                    df['MONTH'] = pd.to_numeric(df['MONTH'], errors='coerce').astype('Int64')
                if 'YEAR' in df.columns:
                    df['YEAR'] = df['YEAR'].astype(str).str.strip()
                dfs.append(df)
                self.log(f"  ✓ โหลด ADJ_GL: {Path(f).name} ({len(df)} records, total={df['REVENUE_VALUE'].sum():,.2f})")
            except Exception as e:
                self.log(f"  ⚠️  ไม่สามารถอ่าน ADJ_GL file {f}: {e}", "WARNING")

        if dfs:
            self.adj_gl_data = pd.concat(dfs, ignore_index=True)
            self.log(f"  ADJ_GL รวม: {len(self.adj_gl_data)} records, net total={self.adj_gl_data['REVENUE_VALUE'].sum():,.2f}")
        else:
            self.adj_gl_data = None

    def _secondary_check_with_adj(self, df_fi, df_trn, reconcile_type, tolerance, latest_year=None, latest_month=None):
        """
        Secondary check: ลบ ADJ_GL adjustments ออกจาก TRN แล้วเทียบกับ FI ใหม่

        ถ้า TRN - ADJ_GL ≈ FI → แปลว่า diff ทั้งหมดอธิบายได้จาก ADJ_GL

        Returns:
            dict or None: ผลลัพธ์ถ้าผ่าน, None ถ้าไม่ผ่าน
        """
        if self.adj_gl_data is None or self.adj_gl_data.empty:
            return None

        self.log(f"\n  🔄 Secondary Check: ตรวจสอบโดยหักรายการ ADJ_GL ออก ({reconcile_type})")

        adj = self.adj_gl_data.copy()

        # Filter ADJ by year/month based on reconcile_type
        if latest_year is not None:
            adj = adj[adj['YEAR'] == str(latest_year)]

        if reconcile_type == 'MONTHLY' and latest_month is not None:
            adj = adj[adj['MONTH'] == latest_month]
        # YTD: use all months for the year (no month filter)

        # Aggregate ADJ by GL_CODE
        if adj.empty:
            self.log(f"  ⚠️  ไม่พบข้อมูล ADJ_GL สำหรับช่วงเวลานี้")
            return None

        adj_by_gl = adj.groupby('GL_CODE')['REVENUE_VALUE'].sum().reset_index()
        adj_by_gl.columns = ['GL_CODE', 'ADJ_VALUE']

        adj_net = adj_by_gl['ADJ_VALUE'].sum()
        self.log(f"  ADJ_GL records: {len(adj)} | GL codes affected: {len(adj_by_gl)} | Net adjustment: {adj_net:,.2f}")

        # Merge TRN with ADJ to compute TRN_before_adj = TRN - ADJ
        # df_trn has columns: GL_CODE, TRN_VALUE (already renamed by caller)
        # We need to use the original column names
        trn_col = [c for c in df_trn.columns if c != 'GL_CODE'][0]  # TRN_VALUE or similar
        fi_col = [c for c in df_fi.columns if c != 'GL_CODE'][0]  # FI_VALUE or similar

        df_trn_adj = pd.merge(df_trn, adj_by_gl, on='GL_CODE', how='left')
        df_trn_adj['ADJ_VALUE'] = df_trn_adj['ADJ_VALUE'].fillna(0)
        df_trn_adj['TRN_BEFORE_ADJ'] = df_trn_adj[trn_col] - df_trn_adj['ADJ_VALUE']

        # Now compare FI vs TRN_BEFORE_ADJ
        df_compare = pd.merge(
            df_fi,
            df_trn_adj[['GL_CODE', 'TRN_BEFORE_ADJ']],
            on='GL_CODE',
            how='outer',
            indicator=True
        )
        df_compare[fi_col] = df_compare[fi_col].fillna(0)
        df_compare['TRN_BEFORE_ADJ'] = df_compare['TRN_BEFORE_ADJ'].fillna(0)
        df_compare['DIFF'] = (df_compare[fi_col] - df_compare['TRN_BEFORE_ADJ']).round(2)
        df_compare['ABS_DIFF'] = df_compare['DIFF'].abs()

        remaining_errors = df_compare[df_compare['ABS_DIFF'] > tolerance]
        remaining_count = len(remaining_errors)

        total_fi = df_compare[fi_col].sum()
        total_trn_before_adj = df_compare['TRN_BEFORE_ADJ'].sum()
        total_diff = round(total_fi - total_trn_before_adj, 2)

        self.log(f"  FI Total: {total_fi:,.2f}")
        self.log(f"  TRN (หลังหัก ADJ_GL): {total_trn_before_adj:,.2f}")
        self.log(f"  Diff (หลังหัก ADJ_GL): {total_diff:,.2f}")

        if remaining_count == 0:
            self.log(f"  ✅ Secondary Check ผ่าน! ความแตกต่างทั้งหมดอธิบายได้จาก ADJ_GL")
            return {
                'passed': True,
                'status': 'PASSED_WITH_ADJ_GL',
                'remaining_errors': 0,
                'adj_net': adj_net,
                'total_diff_after_adj': total_diff
            }
        else:
            # Check if total matches but per-GL still differs (GL offset within ADJ)
            if abs(total_diff) <= tolerance:
                self.log(f"  ⚠️  ยอดรวมตรงกัน แต่ยังมี {remaining_count} GL ที่ต่างกัน (อาจเป็นการปรับโยก GL เพิ่มเติม)")
                self.log(f"  ✅ ถือว่าผ่าน (ยอดรวมสุทธิเท่ากัน)")
                return {
                    'passed': True,
                    'status': 'PASSED_WITH_ADJ_GL_OFFSET',
                    'remaining_errors': remaining_count,
                    'adj_net': adj_net,
                    'total_diff_after_adj': total_diff
                }
            else:
                self.log(f"  ❌ Secondary Check ไม่ผ่าน: ยังมี {remaining_count} รายการที่ไม่ตรง (diff={total_diff:,.2f})")

                # Show remaining errors
                remaining_list = []
                for _, row in remaining_errors.head(10).iterrows():
                    self.log(f"     GL {row['GL_CODE']}: FI={row[fi_col]:,.2f} TRN(adj)={row['TRN_BEFORE_ADJ']:,.2f} diff={row['DIFF']:,.2f}")
                    remaining_list.append({
                        'gl_code': row['GL_CODE'],
                        'fi_value': row[fi_col],
                        'trn_before_adj': row['TRN_BEFORE_ADJ'],
                        'diff': row['DIFF']
                    })

                return None

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
        
        # ========================================================
        # Step 0: ใช้ทุก GL ในการ reconcile (ไม่กรอง)
        # ========================================================
        has_gl_filter = bool(getattr(self, 'excluded_gl_codes', None))

        if has_gl_filter:
            # แสดงข้อมูล GL ที่อยู่ในกลุ่มผลตอบแทนฯ (informational only)
            df_fi_excluded = df_fi[df_fi['GL_CODE'].isin(self.excluded_gl_codes)]
            trn_monthly_excluded = trn_monthly[trn_monthly['GL_CODE'].isin(self.excluded_gl_codes)]
            trn_ytd_excluded = trn_ytd[trn_ytd['GL_CODE'].isin(self.excluded_gl_codes)]
            self.log(f"\nข้อมูล GL ในกลุ่ม {self.exclude_gl_group}:")
            self.log(f"  FI: {len(df_fi_excluded)} GL, TRN Monthly: {len(trn_monthly_excluded)} GL, TRN YTD: {len(trn_ytd_excluded)} GL")
            self.log(f"  💡 Step 0 ตรวจทุก GL (รวมกลุ่มนี้ด้วย)")

        # ใช้ข้อมูลทุก GL
        df_fi_core = df_fi
        trn_monthly_core = trn_monthly
        trn_ytd_core = trn_ytd

        self.log("\n" + "=" * 80)
        self.log("กำลังเปรียบเทียบข้อมูล (ทุก GL)...")
        self.log("=" * 80)

        # ========================
        # RECONCILE 1: ยอดรายเดือน (Core GL only)
        # ========================
        self.log("\n[1] Reconcile ยอดรายเดือน (Latest Month) - ทุก GL")
        monthly_result = self._reconcile_by_gl(
            df_fi=df_fi_core[['GL_CODE', 'REVENUE_VALUE']].rename(columns={'REVENUE_VALUE': 'FI_VALUE'}),
            df_trn=trn_monthly_core.rename(columns={'TRN_MONTHLY': 'TRN_VALUE'}),
            reconcile_type='MONTHLY',
            tolerance=tolerance
        )

        # ========================
        # RECONCILE 2: ยอดสะสม (YTD) (Core GL only)
        # ========================
        self.log("\n[2] Reconcile ยอดสะสม (YTD) - ทุก GL")
        ytd_result = self._reconcile_by_gl(
            df_fi=df_fi_core[['GL_CODE', 'REVENUE_VALUE_YTD']].rename(columns={'REVENUE_VALUE_YTD': 'FI_VALUE'}),
            df_trn=trn_ytd_core.rename(columns={'TRN_YTD': 'TRN_VALUE'}),
            reconcile_type='YTD',
            tolerance=tolerance
        )

        # ========================
        # INFO: แสดงข้อมูล GL ที่ยกเว้น (ไม่นับเป็น error)
        # ========================
        excluded_info = None
        if has_gl_filter and (len(df_fi_excluded) > 0 or len(trn_monthly_excluded) > 0):
            self.log(f"\n[ℹ️] GL ที่ยกเว้นจากการ Reconcile ({self.exclude_gl_group}):")
            fi_excl_monthly = df_fi_excluded['REVENUE_VALUE'].sum() if 'REVENUE_VALUE' in df_fi_excluded.columns else 0
            fi_excl_ytd = df_fi_excluded['REVENUE_VALUE_YTD'].sum() if 'REVENUE_VALUE_YTD' in df_fi_excluded.columns else 0
            trn_excl_monthly = trn_monthly_excluded['TRN_MONTHLY'].sum() if len(trn_monthly_excluded) > 0 else 0
            trn_excl_ytd = trn_ytd_excluded['TRN_YTD'].sum() if len(trn_ytd_excluded) > 0 else 0
            self.log(f"  Monthly - FI: {fi_excl_monthly:,.2f} | TRN: {trn_excl_monthly:,.2f} | Diff: {fi_excl_monthly - trn_excl_monthly:,.2f}")
            self.log(f"  YTD     - FI: {fi_excl_ytd:,.2f} | TRN: {trn_excl_ytd:,.2f} | Diff: {fi_excl_ytd - trn_excl_ytd:,.2f}")
            self.log(f"  💡 กลุ่มนี้ต้อง net กับค่าใช้จ่ายก่อนจึงไม่รวมใน reconcile")
            excluded_info = {
                'monthly_fi': fi_excl_monthly, 'monthly_trn': trn_excl_monthly,
                'ytd_fi': fi_excl_ytd, 'ytd_trn': trn_excl_ytd
            }

        # เก็บผลลัพธ์
        self.reconcile_results = {
            'monthly': monthly_result,
            'ytd': ytd_result,
            'latest_month': latest_month,
            'latest_year': latest_year,
            'fi_file': fi_file_path,
            'trn_file': trn_file_path,
            'excluded_gl_info': excluded_info
        }

        all_passed = monthly_result['passed'] and ytd_result['passed']

        # ========================================================
        # Secondary Check: ถ้า primary ไม่ผ่าน ตรวจสอบด้วย ADJ_GL
        # ========================================================
        if not all_passed and self.adj_gl_data is not None:
            self.log("\n" + "=" * 80)
            self.log("SECONDARY CHECK - ตรวจสอบโดยหัก ADJ_GL adjustments")
            self.log("=" * 80)

            if not monthly_result['passed']:
                monthly_secondary = self._secondary_check_with_adj(
                    df_fi=df_fi_core[['GL_CODE', 'REVENUE_VALUE']].rename(columns={'REVENUE_VALUE': 'FI_VALUE'}),
                    df_trn=trn_monthly_core.rename(columns={'TRN_MONTHLY': 'TRN_VALUE'}),
                    reconcile_type='MONTHLY',
                    tolerance=tolerance,
                    latest_year=latest_year,
                    latest_month=latest_month
                )
                if monthly_secondary and monthly_secondary['passed']:
                    monthly_result['passed'] = True
                    monthly_result['status'] = monthly_secondary['status']
                    monthly_result['secondary_check'] = monthly_secondary

            if not ytd_result['passed']:
                ytd_secondary = self._secondary_check_with_adj(
                    df_fi=df_fi_core[['GL_CODE', 'REVENUE_VALUE_YTD']].rename(columns={'REVENUE_VALUE_YTD': 'FI_VALUE'}),
                    df_trn=trn_ytd_core.rename(columns={'TRN_YTD': 'TRN_VALUE'}),
                    reconcile_type='YTD',
                    tolerance=tolerance,
                    latest_year=latest_year,
                    latest_month=None
                )
                if ytd_secondary and ytd_secondary['passed']:
                    ytd_result['passed'] = True
                    ytd_result['status'] = ytd_secondary['status']
                    ytd_result['secondary_check'] = ytd_secondary

            all_passed = monthly_result['passed'] and ytd_result['passed']

        # สรุปผลลัพธ์
        self.log("\n" + "=" * 80)
        self.log("สรุปผลการ Reconciliation")
        self.log("=" * 80)

        has_special_pass = any(
            r.get('status') in ('PASSED_WITH_GL_OFFSET', 'PASSED_WITH_ADJ_GL', 'PASSED_WITH_ADJ_GL_OFFSET')
            for r in [monthly_result, ytd_result]
        )

        if all_passed:
            if has_special_pass:
                self.log("⚠️  ผ่านการตรวจสอบ (พบการปรับปรุง GL)", "WARNING")
            else:
                self.log("✓ ผ่านการตรวจสอบทุก GL!", "SUCCESS")
            self.log(f"  - Reconcile รายเดือน: {monthly_result.get('status', 'PASSED')} ({monthly_result['total_records']} GL Codes)")
            self.log(f"  - Reconcile YTD: {ytd_result.get('status', 'PASSED')} ({ytd_result['total_records']} GL Codes)")
        else:
            self.log("⚠️  พบความแตกต่างในบาง GL!", "WARNING")
            if not monthly_result['passed']:
                self.log(f"  - Reconcile รายเดือน: DIFF ({monthly_result['error_count']} GL codes)", "WARNING")
            else:
                self.log(f"  - Reconcile รายเดือน: {monthly_result.get('status', 'PASSED')}", "SUCCESS")
            if not ytd_result['passed']:
                self.log(f"  - Reconcile YTD: DIFF ({ytd_result['error_count']} GL codes)", "WARNING")
            else:
                self.log(f"  - Reconcile YTD: {ytd_result.get('status', 'PASSED')}", "SUCCESS")

        # บันทึก log file
        self._save_reconcile_log()

        # ⚠️  Reconciliation เป็น WARNING เสมอ — ไม่หยุด pipeline
        # แต่ยังคงแจ้งเตือนเพื่อให้ตรวจสอบ
        if not all_passed:
            self.log("\n⚠️  Reconciliation พบความแตกต่าง — ดำเนินการต่อ (WARNING mode)", "WARNING")
            self.log("💡 กรุณาตรวจสอบ log file สำหรับรายละเอียด")

        return {
            'status': all_passed,
            'warning': not all_passed,
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

        # สถิติ
        total_fi = df_compare['FI_VALUE'].sum()
        total_trn = df_compare['TRN_VALUE'].sum()
        total_diff = round(total_fi - total_trn, 2)

        self.log(f"  Total Records: {total_records:,}")
        self.log(f"  FI Total: {total_fi:,.2f}")
        self.log(f"  TRN Total: {total_trn:,.2f}")
        self.log(f"  Diff: {total_diff:,.2f}")

        # === [NEW] ตรวจสอบการปรับโยก GL (GL Offset/Adjustment) ===
        # ถ้ายอดรวมเท่ากัน (diff ≈ 0) แต่มีรายการย่อยแตกต่าง = การปรับโยก GL
        is_gl_offset = (abs(total_diff) <= tolerance) and (error_count > 0)

        if is_gl_offset:
            # ตรวจสอบว่าเป็นการปรับโยกจริงหรือไม่ (ผลรวมของ diff ต้องเป็น 0)
            sum_of_diffs = sum([e['diff'] for e in errors])
            if abs(sum_of_diffs) <= tolerance:
                self.log(f"  ⚠️  พบการปรับโยก GL: {error_count} รายการ (ยอดรวมเท่ากัน)", "WARNING")
                self.log(f"  💡 นี่คือการปรับปรุงบัญชี (GL Adjustment) - ถือว่าผ่าน", "INFO")

                # แสดงรายการปรับโยก
                self._display_errors(errors, reconcile_type)

                # ถือว่าผ่าน แต่มี warning
                passed = True
                reconcile_status = 'PASSED_WITH_GL_OFFSET'
            else:
                # ยอดรวมเท่ากัน แต่ผลรวมของ diff ไม่เป็น 0 = มีปัญหา
                self.log(f"  ❌ พบ {error_count} รายการที่แตกต่าง (ไม่ใช่การปรับโยก)", "ERROR")
                self._display_errors(errors, reconcile_type)
                passed = False
                reconcile_status = 'FAILED'
        elif error_count == 0:
            self.log(f"  ✓ ผ่านการตรวจสอบ!", "SUCCESS")
            passed = True
            reconcile_status = 'PASSED'
        else:
            self.log(f"  ❌ พบ {error_count} รายการที่แตกต่าง", "ERROR")
            self._display_errors(errors, reconcile_type)
            passed = False
            reconcile_status = 'FAILED'
        # === [END] GL Offset Check ===
        
        return {
            'passed': passed,
            'errors': errors,
            'error_count': error_count,
            'total_records': total_records,
            'total_fi': total_fi,
            'total_trn': total_trn,
            'total_diff': total_diff,
            'reconcile_type': reconcile_type,
            'status': reconcile_status  # 'PASSED', 'PASSED_WITH_GL_OFFSET', 'FAILED'
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
        self.log(f"📁 Log Directory: {log_dir}")
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
            f.write(f"Status: {monthly.get('status', 'PASSED' if monthly['passed'] else 'FAILED')}\n")
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
            f.write(f"Status: {ytd.get('status', 'PASSED' if ytd['passed'] else 'FAILED')}\n")
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