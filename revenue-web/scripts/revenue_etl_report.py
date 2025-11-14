import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path
from datetime import datetime
import logging
from .revenue_reconciliation import RevenueReconciliation, ReconciliationError

class RevenueETL:
    """
    ETL Pipeline for processing revenue data.
    """
    
    def __init__(self, config, year, month, logger):
        self.config = config
        self.year = str(year)
        self.month = str(month).zfill(2)
        self.logger = logger
        self.paths = self.config.get('paths', {})
        self.master_files = self.config.get('master_files', {})
        self.etl_params = self.config.get('etl_params', {})
        self.df_adj_ytd = pd.DataFrame()
        self.setup_directories()

    def setup_directories(self):
        self.logger.info("Setting up directories...")
        for path_name, path in self.paths.items():
            # Create only directories meant for output to avoid errors on source paths
            if 'output' in path_name or 'final' in path_name or 'logs' in path_name:
                 Path(path).mkdir(parents=True, exist_ok=True)
        self.logger.info("Directories are set up.")

    def step0_reconcile_revenue(self):
        self.logger.info("STEP 0: RECONCILIATION - Starting data validation")
        if not self.etl_params.get('enable_reconciliation', False):
            self.logger.warning("Reconciliation is disabled in config. Skipping.")
            return

        # Pass the logger to the reconciliation class
        reconciler = RevenueReconciliation(self.config, self.paths, self.logger)
        
        fi_month = self.etl_params.get('reconcile_fi_month', self.month)
        fi_file_name = f'pl_revenue_nt_output_{self.year}{fi_month}.csv'
        fi_file_path = os.path.join(self.paths.get('fi_output'), fi_file_name)
        
        trn_file_name = self.master_files.get('output_concat_file', f'trn_revenue_nt_{self.year}.csv')
        trn_file_path = os.path.join(self.paths.get('revenue_output'), trn_file_name)
        
        self.logger.info(f"FI file for reconciliation: {fi_file_path}")
        self.logger.info(f"TRN file for reconciliation: {trn_file_path}")

        try:
            reconciler.reconcile_revenue(
                fi_file_path=fi_file_path,
                trn_file_path=trn_file_path,
                tolerance=self.etl_params.get('reconcile_tolerance', 0.0)
            )
            self.logger.info("✓ Reconciliation successful!")
        except (ReconciliationError, FileNotFoundError) as e:
            self.logger.error(f"❌ Reconciliation failed, stopping ETL pipeline: {e}", exc_info=True)
            raise

    def step1_concat_revenue_files(self):
        self.logger.info("STEP 1: Concatenating source CSV files (NT1)")
        input_dir = self.paths.get('revenue_input')
        patterns = self.etl_params.get('input_file_patterns', [])
        all_files = [f for p in patterns for f in glob.glob(os.path.join(input_dir, p))]
        
        if not all_files:
            raise FileNotFoundError(f"No source files found in {input_dir} for configured patterns: {patterns}")

        df_list = []
        required_cols = self.etl_params.get('required_columns', [])
        
        for file in sorted(list(set(all_files))):
            self.logger.info(f"Reading file: {os.path.basename(file)}")
            try:
                df = pd.read_csv(file, converters={"YEAR": str, "MONTH": int, "COST_CENTER": str, "PRODUCT_KEY": str, "SUB_PRODUCT_KEY": int, "GL_CODE_NT1": str, "GL_CODE": str})
                df.columns = df.columns.str.strip()
                df["REVENUE_VALUE"] = pd.to_numeric(df["REVENUE_VALUE"].astype(str).str.replace(",", "", regex=False).str.replace(r"\(", "-", regex=True).str.replace(r"\)", "", regex=True).str.strip(), errors='coerce')
                df["GL_CODE"] = df["GL_CODE_NT1"].fillna(df["GL_CODE"]).astype(str)
                
                df = df[required_cols]
                df.dropna(subset=["PRODUCT_KEY", "REVENUE_VALUE"], inplace=True)
                df_list.append(df)
            except Exception as e:
                self.logger.warning(f"Could not process file {file}: {e}")
        
        if not df_list:
            raise ValueError("No data could be loaded from any source file.")

        df_combined = pd.concat(df_list, ignore_index=True)
        df_combined["MONTH"] = df_combined["MONTH"].astype(int).astype(str).str.zfill(2)
        df_combined["SUB_PRODUCT_KEY"] = df_combined["SUB_PRODUCT_KEY"].astype(int).astype(str)
        
        output_filename = self.master_files.get('output_concat_file', f'trn_revenue_nt_{self.year}.csv')
        output_file = os.path.join(self.paths.get('revenue_output'), output_filename)
        df_combined.to_csv(output_file, index=False, float_format="%.2f")
        self.logger.info(f"Step 1 finished. Total rows: {len(df_combined):,}. Grand Total: {df_combined['REVENUE_VALUE'].sum():,.2f}")
        return df_combined

    def run(self):
        """Runs the entire ETL pipeline."""
        try:
            self.logger.info(f"--- Starting ETL Pipeline for {self.month}/{self.year} ---")
            
            df = self.step1_concat_revenue_files()
            
            # Reconciliation runs after concatenation
            self.step0_reconcile_revenue()
            
            # In a full implementation, steps 2, 3, 4, 5 would be called here.
            self.logger.info("Steps 2, 3, 4, and 5 (mapping, final report, anomaly detection) are currently placeholders.")
            df_final = df # This would be the result of all processing
            
            # The final report generation would happen here.
            final_output_filename = self.master_files.get('output_final_report_file', f"REVENUE_NT_REPORT_{self.year}.csv")
            final_output_path = os.path.join(self.paths.get('final_output'), final_output_filename)
            df_final.to_csv(final_output_path, index=False)
            self.logger.info(f"✓ ETL Pipeline completed successfully! Final raw data at {final_output_path}")
            
            return {"status": "success", "output_file": final_output_path}

        except Exception as e:
            self.logger.error(f"❌ ETL Pipeline failed: {e}", exc_info=True)
            # Re-raise the exception so the RQ worker can mark the job as failed
            raise

def run_etl_report(config, year, month, logger):
    """
    Main function to run the Revenue ETL report pipeline.
    """
    try:
        etl_pipeline = RevenueETL(config, year, month, logger)
        result = etl_pipeline.run()
        return result
    except Exception as e:
        # The exception is already logged by the run method, so just return status
        return {"status": "error", "message": str(e)}
