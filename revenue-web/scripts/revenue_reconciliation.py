import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

class ReconciliationError(Exception):
    """Custom Exception for Reconciliation Error"""
    def __init__(self, message, reconcile_results=None):
        super().__init__(message)
        self.reconcile_results = reconcile_results

class RevenueReconciliation:
    """
    Module for verifying revenue data integrity by comparing financial statements (FI)
    with transaction records (TRN).
    """
    
    def __init__(self, config, paths, logger):
        """
        Initializes the RevenueReconciliation instance.
        Args:
            config (dict): Configuration dictionary.
            paths (dict): Dictionary of all relevant paths.
            logger: Logger object for logging messages.
        """
        self.config = config
        self.paths = paths
        self.reconcile_results = {}
        self.logger = logger

    def reconcile_revenue(self, fi_file_path, trn_file_path, tolerance=0.00):
        self.logger.info("=" * 80)
        self.logger.info("RECONCILIATION - Starting data validation")
        self.logger.info("=" * 80)

        if not Path(trn_file_path).exists():
            self.logger.error(f"TRN file not found: {trn_file_path}")
            raise FileNotFoundError(f"TRN file not found: {trn_file_path}")
        
        if not Path(fi_file_path).exists():
            self.logger.error(f"FI file not found: {fi_file_path}")
            raise FileNotFoundError(f"FI file not found: {fi_file_path}")

        self.logger.info(f"Reading FI data from: {Path(fi_file_path).name}")
        try:
            df_fi = pd.read_csv(fi_file_path)
            self.logger.info(f"✓ Successfully read FI data: {len(df_fi):,} GL Codes")
        except Exception as e:
            self.logger.error(f"Failed to read FI file: {e}")
            raise

        required_fi_cols = ['GL_CODE', 'REVENUE_VALUE', 'REVENUE_VALUE_YTD']
        if not all(col in df_fi.columns for col in required_fi_cols):
            raise ValueError(f"FI file is missing required columns. Found: {df_fi.columns.tolist()}")

        self.logger.info(f"Reading TRN data from: {Path(trn_file_path).name}")
        try:
            df_trn = pd.read_csv(trn_file_path)
            self.logger.info(f"✓ Successfully read TRN data: {len(df_trn):,} records")
        except Exception as e:
            self.logger.error(f"Failed to read TRN file: {e}")
            raise

        required_trn_cols = ['GL_CODE', 'YEAR', 'MONTH', 'REVENUE_VALUE']
        if not all(col in df_trn.columns for col in required_trn_cols):
            raise ValueError(f"TRN file is missing required columns. Found: {df_trn.columns.tolist()}")

        df_fi['GL_CODE'] = df_fi['GL_CODE'].astype(str).str.strip()
        df_trn['GL_CODE'] = df_trn['GL_CODE'].astype(str).str.strip()
        df_trn['MONTH'] = pd.to_numeric(df_trn['MONTH'].astype(str).str.strip()).astype(int)
        
        latest_month = df_trn['MONTH'].max()
        latest_year = df_trn[df_trn['MONTH'] == latest_month]['YEAR'].max()
        self.logger.info(f"Latest month in TRN data: {latest_month:02d}/{latest_year}")

        total_fi_monthly = df_fi['REVENUE_VALUE'].sum()
        total_fi_ytd = df_fi['REVENUE_VALUE_YTD'].sum()
        self.logger.info(f"FI Monthly Total: {total_fi_monthly:,.2f}")
        self.logger.info(f"FI YTD Total: {total_fi_ytd:,.2f}")

        df_trn_latest = df_trn[(df_trn['YEAR'] == latest_year) & (df_trn['MONTH'] == latest_month)]
        df_trn_ytd = df_trn[df_trn['YEAR'] == latest_year]
        
        trn_monthly = df_trn_latest.groupby('GL_CODE')['REVENUE_VALUE'].sum().reset_index()
        trn_monthly.columns = ['GL_CODE', 'TRN_MONTHLY']
        
        trn_ytd = df_trn_ytd.groupby('GL_CODE')['REVENUE_VALUE'].sum().reset_index()
        trn_ytd.columns = ['GL_CODE', 'TRN_YTD']
        
        total_trn_monthly = trn_monthly['TRN_MONTHLY'].sum()
        total_trn_ytd = trn_ytd['TRN_YTD'].sum()
        self.logger.info(f"TRN Monthly Total: {total_trn_monthly:,.2f}")
        self.logger.info(f"TRN YTD Total: {total_trn_ytd:,.2f}")
        
        self.logger.info("=" * 80)
        self.logger.info("Comparing data...")
        self.logger.info("=" * 80)
        
        self.logger.info("\n[1] Reconciling Latest Month")
        monthly_result = self._reconcile_by_gl(
            df_fi=df_fi[['GL_CODE', 'REVENUE_VALUE']].rename(columns={'REVENUE_VALUE': 'FI_VALUE'}),
            df_trn=trn_monthly.rename(columns={'TRN_MONTHLY': 'TRN_VALUE'}),
            reconcile_type='MONTHLY',
            tolerance=tolerance
        )
        
        self.logger.info("\n[2] Reconciling Year-to-Date (YTD)")
        ytd_result = self._reconcile_by_gl(
            df_fi=df_fi[['GL_CODE', 'REVENUE_VALUE_YTD']].rename(columns={'REVENUE_VALUE_YTD': 'FI_VALUE'}),
            df_trn=trn_ytd.rename(columns={'TRN_YTD': 'TRN_VALUE'}),
            reconcile_type='YTD',
            tolerance=tolerance
        )
        
        self.reconcile_results = {
            'monthly': monthly_result,
            'ytd': ytd_result,
            'latest_month': latest_month,
            'latest_year': latest_year,
            'fi_file': fi_file_path,
            'trn_file': trn_file_path
        }
        
        self.logger.info("\n" + "=" * 80)
        self.logger.info("Reconciliation Summary")
        self.logger.info("=" * 80)
        
        all_passed = monthly_result['passed'] and ytd_result['passed']
        
        if all_passed:
            self.logger.info("✓ All checks passed!")
        else:
            self.logger.error("❌ Discrepancies found!")
        
        self._save_reconcile_log()
        
        if not all_passed:
            error_msg = self._format_error_message(monthly_result, ytd_result)
            raise ReconciliationError(error_msg, self.reconcile_results)
        
        return {'status': True, 'details': self.reconcile_results}

    def _reconcile_by_gl(self, df_fi, df_trn, reconcile_type, tolerance):
        df_compare = pd.merge(df_fi, df_trn, on='GL_CODE', how='outer', indicator=True)
        df_compare.fillna(0, inplace=True)
        df_compare['DIFF'] = (df_compare['FI_VALUE'] - df_compare['TRN_VALUE']).round(2)
        df_compare['ABS_DIFF'] = df_compare['DIFF'].abs()
        
        df_errors = df_compare[df_compare['ABS_DIFF'] > tolerance].copy()
        
        errors = [row.to_dict() for _, row in df_errors.iterrows()]
        
        passed = len(errors) == 0
        
        self.logger.info(f"  Total Records: {len(df_compare):,}")
        self.logger.info(f"  FI Total: {df_compare['FI_VALUE'].sum():,.2f}")
        self.logger.info(f"  TRN Total: {df_compare['TRN_VALUE'].sum():,.2f}")
        self.logger.info(f"  Diff: {(df_compare['FI_VALUE'].sum() - df_compare['TRN_VALUE'].sum()):,.2f}")
        
        if passed:
            self.logger.info("  ✓ PASSED!")
        else:
            self.logger.error(f"  ❌ FAILED: Found {len(errors)} discrepancies.")
            self._display_errors(errors, reconcile_type)
        
        return {
            'passed': passed, 'errors': errors, 'error_count': len(errors),
            'total_records': len(df_compare), 'total_fi': df_compare['FI_VALUE'].sum(),
            'total_trn': df_compare['TRN_VALUE'].sum(), 'total_diff': df_compare['FI_VALUE'].sum() - df_compare['TRN_VALUE'].sum(),
            'reconcile_type': reconcile_type
        }

    def _display_errors(self, errors, reconcile_type, max_display=10):
        self.logger.error(f"  Top {min(len(errors), max_display)} Discrepancies for {reconcile_type}:")
        for err in errors[:max_display]:
            self.logger.error(f"    GL: {err['gl_code']}, FI: {err['fi_value']:,.2f}, TRN: {err['trn_value']:,.2f}, Diff: {err['diff']:,.2f}")

    def _format_error_message(self, monthly_result, ytd_result):
        msg = "Reconciliation failed. "
        if not monthly_result['passed']:
            msg += f"Monthly check failed with {monthly_result['error_count']} errors. "
        if not ytd_result['passed']:
            msg += f"YTD check failed with {ytd_result['error_count']} errors."
        return msg

    def _save_reconcile_log(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path(self.paths.get('reconcile_logs', 'logs/reconciliation'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = log_dir / f"reconcile_summary_{self.config.get('year', 'NA')}_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("REVENUE RECONCILIATION REPORT\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            monthly = self.reconcile_results['monthly']
            f.write("[MONTHLY RECONCILIATION]\n")
            f.write(f"Status: {'PASSED' if monthly['passed'] else 'FAILED'}\n")
            f.write(f"Error Count: {monthly['error_count']}\n\n")
            if not monthly['passed']:
                pd.DataFrame(monthly['errors']).to_string(f)
                f.write("\n\n")

            ytd = self.reconcile_results['ytd']
            f.write("[YTD RECONCILIATION]\n")
            f.write(f"Status: {'PASSED' if ytd['passed'] else 'FAILED'}\n")
            f.write(f"Error Count: {ytd['error_count']}\n\n")
            if not ytd['passed']:
                pd.DataFrame(ytd['errors']).to_string(f)
        
        self.logger.info(f"✓ Reconciliation summary log saved to: {summary_file}")

def run_reconciliation(config, logger, fi_file_path, trn_file_path, tolerance=0.00):
    """
    Callable function to run the revenue reconciliation process.
    """
    paths = config.get('paths', {})
    reconciler = RevenueReconciliation(config, paths, logger)
    return reconciler.reconcile_revenue(fi_file_path, trn_file_path, tolerance)
