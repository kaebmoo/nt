# anomaly_web/utils/audit_runner.py
"""
Audit Runner - Wrapper for running anomaly detection
รัน anomaly detection และติดตาม progress
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import traceback

# Import anomaly detection engines
from .anomaly_engine import CrosstabGenerator, FullAuditEngine
from .csv_io import read_any
from .anomaly_reporter import ExcelReporter
from .crosstab_converter import CrosstabConverter
from .data_cleaning import (
    apply_date_grain,
    apply_value_transform,
    clean_numeric_series,
    numeric_bad_mask,
    parse_date_series,
)

class AuditRunner:
    """รัน anomaly detection พร้อมติดตาม progress"""
    
    def __init__(self, progress_folder):
        self.progress_folder = progress_folder
        os.makedirs(self.progress_folder, exist_ok=True)
    
    def run_audit(self, input_file, output_file, config, callback=None):
        """
        รัน anomaly detection
        
        Args:
            input_file: path to input file
            output_file: path to output file
            config: configuration dict
            callback: function(progress_data) for progress updates
        
        Returns:
            dict: ผลลัพธ์การรัน
        """
        file_id = config.get('file_id', 'unknown')
        
        try:
            # Initialize progress
            self._update_progress(file_id, {
                'status': 'starting',
                'progress': 0,
                'message': 'Initializing...',
                'started_at': datetime.now().isoformat()
            }, callback)
            
            # Step 1: Load data (10%)
            self._update_progress(file_id, {
                'status': 'loading',
                'progress': 10,
                'message': 'Loading data...'
            }, callback)
            
            df = self._load_data(input_file, config)
            if df is None:
                raise ValueError("Failed to load or convert data.")

            
            # Step 2: Preprocess (20%)
            self._update_progress(file_id, {
                'status': 'preprocessing',
                'progress': 20,
                'message': 'Preprocessing data...'
            }, callback)
            
            df_clean = self._prepare_data(df, config)
            
            # Initialize reporter
            reporter = ExcelReporter(output_file, anomaly_settings=config)
            
            # ตัวแปรเก็บ Log
            df_ts_log = pd.DataFrame()
            df_peer_log = pd.DataFrame()
            
            # Step 3: Run Time Series Analysis (30-50%)
            if config.get('run_time_series_analysis', False):
                self._update_progress(file_id, {
                    'status': 'time_series',
                    'progress': 30,
                    'message': 'Running Time Series Analysis...'
                }, callback)
                
                df_ts_log = self._run_time_series(df_clean, config)
                
                self._update_progress(file_id, {
                    'progress': 50,
                    'message': f'Time Series: Found {len(df_ts_log)} anomalies'
                }, callback)
            
            # Step 4: Run Peer Group Analysis (50-70%)
            if config.get('run_peer_group_analysis', False):
                self._update_progress(file_id, {
                    'status': 'peer_group',
                    'progress': 50,
                    'message': 'Running Peer Group Analysis (this may take a while)...'
                }, callback)
                
                df_peer_log = self._run_peer_group(df_clean, config)
                
                self._update_progress(file_id, {
                    'progress': 70,
                    'message': f'Peer Group: Found {len(df_peer_log)} anomalies'
                }, callback)
            
            # Step 5: Generate Crosstab Report (70-80%)
            if config.get('run_crosstab_report', True):
                self._update_progress(file_id, {
                    'status': 'crosstab_report',
                    'progress': 70,
                    'message': 'Generating Crosstab Report...'
                }, callback)
                
                self._generate_crosstab_report(df_clean, df_ts_log, config, reporter)
                
                self._update_progress(file_id, {
                    'progress': 80
                }, callback)
            
            # Step 6: Add Peer Crosstab (if applicable)
            if config.get('run_peer_group_analysis', False) and not df_peer_log.empty:
                self._update_progress(file_id, {
                    'status': 'peer_crosstab',
                    'progress': 80,
                    'message': 'Adding Peer Group Crosstab...'
                }, callback)
                
                reporter.add_peer_crosstab_sheet(
                    df_clean=df_clean,
                    df_peer_log=df_peer_log,
                    group_dims=config.get('audit_peer_group_by', []),
                    item_id_col=config.get('audit_peer_item_id', 'ITEM_ID'),
                    target_col=config.get('target_col', 'VALUE'),
                    date_col=config.get('date_col_name', '__date_col__')
                )
                
                self._update_progress(file_id, {
                    'progress': 85
                }, callback)
            
            # Step 7: Add Audit Logs (85-95%)
            if config.get('run_full_audit_log', True):
                self._update_progress(file_id, {
                    'status': 'audit_logs',
                    'progress': 85,
                    'message': 'Adding Audit Logs...'
                }, callback)
                
                # Time Series Log
                if config.get('run_time_series_analysis', False) and not df_ts_log.empty:
                    date_col_name = config.get('date_col_name', '__date_col__')
                    target_col = config.get('target_col', 'VALUE')
                    audit_ts_dimensions = config.get('audit_ts_dimensions', [])
                    
                    reporter.add_audit_log_sheet(
                        df_ts_log, 
                        "Full_Audit_Log (Time)",
                        cols_to_show=[date_col_name, 'ISSUE_DESC', target_col, 'COMPARED_WITH'] + audit_ts_dimensions
                    )
                
                # Peer Group Log
                if config.get('run_peer_group_analysis', False) and not df_peer_log.empty:
                    date_col_name = config.get('date_col_name', '__date_col__')
                    target_col = config.get('target_col', 'VALUE')
                    audit_peer_group_by = config.get('audit_peer_group_by', [])
                    audit_peer_item_id = config.get('audit_peer_item_id', 'ITEM_ID')
                    
                    reporter.add_audit_log_sheet(
                        df_peer_log, 
                        "Full_Audit_Log (Peer)",
                        cols_to_show=[date_col_name, 'ISSUE_DESC', target_col, 'COMPARED_WITH'] + audit_peer_group_by + [audit_peer_item_id]
                    )
                
                self._update_progress(file_id, {
                    'progress': 95
                }, callback)
            
            # Step 8: Save Report (95-100%)
            self._update_progress(file_id, {
                'status': 'saving',
                'progress': 95,
                'message': 'Saving Excel report...'
            }, callback)
            
            reporter.save()
            
            # Complete
            result = {
                'status': 'completed',
                'total_rows': len(df_clean),
                'ts_anomalies': len(df_ts_log) if not df_ts_log.empty else 0,
                'peer_anomalies': len(df_peer_log) if not df_peer_log.empty else 0,
                'output_file': output_file
            }
            
            self._update_progress(file_id, {
                'status': 'completed',
                'progress': 100,
                'message': 'Completed successfully',
                'result': result,
                'completed_at': datetime.now().isoformat()
            }, callback)
            
            return result
            
        except Exception as e:
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            
            self._update_progress(file_id, {
                'status': 'error',
                'progress': 0,
                'message': str(e),
                'error': error_msg
            }, callback)
            
            raise
    
    def _load_data(self, input_file, config):
        """โหลดข้อมูล และแปลง crosstab ถ้าจำเป็น"""
        input_mode = config.get('input_mode', 'long')
        
        if input_mode == 'crosstab':
            print("   Converting Crosstab to Long format...")
            converter = CrosstabConverter(input_file=input_file)
            df = converter.convert(
                sheet_name=config.get('crosstab_sheet_name', 0),
                skiprows=config.get('crosstab_skiprows', 0),
                id_vars=config.get('crosstab_id_vars', []),
                value_name=config.get('crosstab_value_name', 'VALUE'),
                mode=config.get('crosstab_mode', 'auto'),
                date_parse_mode=config.get('date_parse_mode', 'auto')
            )
        else:
            # Direct long format
            print("   Loading Long format data...")
            df = read_any(input_file)
        
        return df
    
    def _prepare_data(self, df, config):
        """เตรียมข้อมูล (ใช้ logic จาก main_audit.py)"""
        print("   running: Data Preprocessing...")

        df = df.copy()

        # 1. สร้าง Column วันที่
        col_year = config.get('col_year')
        col_month = config.get('col_month')
        date_column = config.get('date_column')  # Date column in YYYY-MM or YYYY-MM-DD format
        date_col_name = config.get('date_col_name', '__date_col__')
        date_parse_mode = config.get('date_parse_mode', 'auto')

        # Priority 1: Use date_column if specified (YYYY-MM or YYYY-MM-DD format)
        if date_column and date_column in df.columns:
            df[date_col_name] = parse_date_series(df[date_column], date_parse_mode)
            # Extract year and month from date if not already present
            if not col_year or col_year not in df.columns:
                df['YEAR'] = df[date_col_name].dt.year
                col_year = 'YEAR'
            if not col_month or col_month not in df.columns:
                df['MONTH'] = df[date_col_name].dt.month
                col_month = 'MONTH'

        # Priority 2: Combine year + month columns
        elif col_year and col_year in df.columns and col_month and col_month in df.columns:
            # Check if year/month are already in YYYY-MM format (combined)
            sample_year = df[col_year].dropna().head(1).astype(str).iloc[0] if len(df[col_year].dropna()) > 0 else ''
            sample_month = df[col_month].dropna().head(1).astype(str).iloc[0] if len(df[col_month].dropna()) > 0 else ''

            # If year column looks like YYYY-MM format, use it directly
            if '-' in sample_year or '/' in sample_year:
                df[date_col_name] = parse_date_series(df[col_year], date_parse_mode)
                # Extract year and month
                df['YEAR'] = df[date_col_name].dt.year
                df['MONTH'] = df[date_col_name].dt.month
                col_year = 'YEAR'
                col_month = 'MONTH'
            else:
                # Normal case: separate year and month columns
                try:
                    df[date_col_name] = pd.to_datetime(
                        df[col_year].astype(str) + '-' +
                        df[col_month].astype(int).astype(str).str.zfill(2) + '-01',
                        errors='coerce'
                    )
                except (ValueError, TypeError):
                    # Fallback: try without int conversion
                    df[date_col_name] = pd.to_datetime(
                        df[col_year].astype(str) + '-' +
                        df[col_month].astype(str).str.zfill(2) + '-01',
                        errors='coerce'
                    )

        # Priority 3: If data comes from crosstab converter, it might already have a 'DATE' column
        elif 'DATE' in df.columns:
             df[date_col_name] = parse_date_series(df['DATE'], date_parse_mode)
             if not col_year or col_year not in df.columns:
                df['YEAR'] = df[date_col_name].dt.year
                col_year = 'YEAR'
             if not col_month or col_month not in df.columns:
                df['MONTH'] = df[date_col_name].dt.month
                col_month = 'MONTH'
        else:
            # If date columns don't exist, create dummy dates
            df[date_col_name] = pd.to_datetime('2024-01-01')
            print(f"   ⚠️ Warning: Date columns not found. Using dummy dates.")

        df = self._handle_bad_dates(df, date_col_name, config)
        df[date_col_name] = apply_date_grain(df[date_col_name], config.get('date_grain', 'month'))
        
        # 2. Clean numeric column
        target_col = config.get('target_col', 'VALUE')
        if target_col in df.columns:
            df = self._prepare_target_value(df, source_col=target_col, target_col=target_col, config=config)
        else:
            # This can happen if crosstab_value_name doesn't match the melt result
            value_name_from_config = config.get('crosstab_value_name', 'VALUE')
            if value_name_from_config in df.columns:
                 df = self._prepare_target_value(
                     df,
                     source_col=value_name_from_config,
                     target_col=target_col,
                     config=config,
                     drop_source=(target_col != value_name_from_config)
                 )
            else:
                print(f"   ⚠️ Warning: Target column '{target_col}' not found.")
                df[target_col] = 0
        
        # 3. Fill dimensions with 'N/A' for missing values
        all_dims = set(
            config.get('crosstab_dimensions', []) + 
            config.get('audit_ts_dimensions', []) +
            config.get('audit_peer_group_by', [])
        )
        if config.get('audit_peer_item_id'):
            all_dims.add(config.get('audit_peer_item_id'))

        
        for col in all_dims:
            if col in df.columns:
                df[col] = df[col].fillna('N/A')
            else:
                print(f"   ⚠️ Warning: Dimension '{col}' not found in data.")
                df[col] = 'N/A'
        
        print(f"   ✓ Data prepared: {len(df):,} rows")
        return df

    def _handle_bad_dates(self, df, date_col_name, config):
        bad_mask = df[date_col_name].isna()
        bad_count = int(bad_mask.sum())
        if bad_count == 0:
            return df

        policy = config.get('bad_date_policy', 'drop')
        if policy == 'error':
            raise ValueError(
                f"Date column แปลงวันที่ไม่ได้ {bad_count:,} แถว "
                f"(ลองเปลี่ยน Date Parse Mode ใน config)"
            )
        if policy == 'drop':
            print(f"   ⚠️ Dropping {bad_count:,} rows with invalid dates.")
            return df.loc[~bad_mask].copy()

        print(f"   ⚠️ Keeping {bad_count:,} rows with invalid dates.")
        return df

    def _prepare_target_value(self, df, source_col, target_col, config, drop_source=False):
        numeric = clean_numeric_series(df[source_col])
        bad_mask = numeric_bad_mask(df[source_col], numeric)
        bad_count = int(bad_mask.sum())
        policy = config.get('bad_value_policy', 'zero')

        if bad_count:
            examples = df.loc[bad_mask, source_col].astype(str).head(5).tolist()
            if policy == 'error':
                raise ValueError(
                    f"Value column '{source_col}' มี {bad_count:,} ค่า ที่แปลงเป็นตัวเลขไม่ได้ "
                    f"เช่น {examples}"
                )
            if policy == 'drop':
                print(f"   ⚠️ Dropping {bad_count:,} rows with invalid value in '{source_col}'.")
                df = df.loc[~bad_mask].copy()
                numeric = numeric.loc[~bad_mask]
            else:
                print(f"   ⚠️ Converting {bad_count:,} invalid values in '{source_col}' to 0.")

        numeric = numeric.fillna(0)
        multiplier = float(config.get('value_multiplier', 1.0) or 1.0)
        add = float(config.get('value_add', 0.0) or 0.0)
        df[target_col] = apply_value_transform(numeric, multiplier=multiplier, add=add)

        if multiplier != 1.0 or add != 0.0:
            print(f"   ✓ Applied value transform: ({source_col} * {multiplier}) + {add}")

        if drop_source and source_col in df.columns and source_col != target_col:
            df.drop(columns=[source_col], inplace=True)

        return df
    
    def _clean_numeric_column(self, series):
        """
        ทำความสะอาดคอลัมน์ตัวเลข รองรับรูปแบบบัญชี
        
        รองรับ:
        - Comma: 3,000.00 → 3000.00
        - Parentheses (negative): (3000) → -3000
        - Combined: (30,000.00) → -30000.00
        - Whitespace: " 3000 " → 3000
        - Currency: $3,000 หรือ ฿3,000 → 3000
        """
        return clean_numeric_series(series).fillna(0)
    
    def _run_time_series(self, df, config):
        """รัน Time Series Analysis"""
        print("   🔄 Running Time Series Analysis...")
        
        full_audit_gen = FullAuditEngine(df.copy(), anomaly_settings=config)
        
        df_ts_log = full_audit_gen.audit_time_series_all_months(
            target_col=config.get('target_col', 'VALUE'),
            date_col=config.get('date_col_name', '__date_col__'),
            dimensions=config.get('audit_ts_dimensions', []),
            window=config.get('audit_ts_window', 3)
        )
        
        # กรองเฉพาะปัญหาสำคัญ
        if not df_ts_log.empty:
            df_ts_log = df_ts_log[
                df_ts_log['ISSUE_DESC'].isin([
                    'High_Spike', 'Low_Spike', 'Negative_Value'
                ])
            ].copy()
            print(f"   ✓ Time Series: Found {len(df_ts_log)} critical anomalies")
        else:
            print(f"   ✓ Time Series: No anomalies detected")
        
        return df_ts_log
    
    def _run_peer_group(self, df, config):
        """รัน Peer Group Analysis"""
        print("   🔄 Running Peer Group Analysis...")
        print("   ⚠️  This may take a while for large datasets...")
        
        full_audit_gen = FullAuditEngine(df.copy(), anomaly_settings=config)
        
        df_peer_log = full_audit_gen.audit_peer_group_all_months(
            target_col=config.get('target_col', 'VALUE'),
            date_col=config.get('date_col_name', '__date_col__'),
            group_dims=config.get('audit_peer_group_by', []),
            item_id_col=config.get('audit_peer_item_id', 'ITEM_ID')
        )
        
        if not df_peer_log.empty:
            print(f"   ✓ Peer Group: Found {len(df_peer_log)} anomalies")
        else:
            print(f"   ✓ Peer Group: No anomalies detected")
        
        return df_peer_log
    
    def _generate_crosstab_report(self, df_clean, df_ts_log, config, reporter):
        """สร้าง Crosstab Report"""
        print("   📊 Generating Crosstab Report...")
        
        crosstab_gen = CrosstabGenerator(
            df_clean.copy(),
            min_history=config.get('crosstab_min_history', 3),
            anomaly_settings=config
        )
        
        df_crosstab = crosstab_gen.create_report(
            target_col=config.get('target_col', 'VALUE'),
            date_col=config.get('date_col_name', '__date_col__'),
            dimensions=config.get('crosstab_dimensions', [])
        )
        
        # ส่ง df_ts_log เข้าไปเพื่อช่วยทาสี Cell
        reporter.add_crosstab_sheet(
            df_report=df_crosstab,
            df_anomaly_log=df_ts_log,
            dimensions=config.get('crosstab_dimensions', []),
            date_col_name=config.get('date_col_name', '__date_col__'),
            date_cols_sorted=crosstab_gen.date_cols_sorted,
            min_history=config.get('crosstab_min_history', 3)
        )
        
        print(f"   ✓ Crosstab report generated")
    
    def _update_progress(self, file_id, progress_data, callback=None):
        """อัปเดต progress"""
        progress_file_path = os.path.join(self.progress_folder, f"{file_id}.json")
        
        current_progress = {}
        if os.path.exists(progress_file_path):
            try:
                with open(progress_file_path, 'r', encoding='utf-8') as f:
                    current_progress = json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted file or empty file
                current_progress = {}
        
        # Merge with existing progress
        current_progress.update(progress_data)
        
        # Update timestamp
        current_progress['updated_at'] = datetime.now().isoformat()
        
        # Save to file
        with open(progress_file_path, 'w', encoding='utf-8') as f:
            json.dump(current_progress, f, ensure_ascii=False, indent=2)
        
        # Call callback if provided
        if callback:
            callback(current_progress)
    
    def get_progress(self, file_id):
        """ดึง progress ปัจจุบัน"""
        progress_file_path = os.path.join(self.progress_folder, f"{file_id}.json")
        
        if os.path.exists(progress_file_path):
            try:
                with open(progress_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted file or empty file
                pass
        
        return {
            'status': 'not_started',
            'progress': 0,
            'message': 'No progress data available'
        }
    
    def update_progress(self, file_id, progress_data):
        """อัปเดต progress จากภายนอก"""
        self._update_progress(file_id, progress_data)
