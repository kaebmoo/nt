# anomaly_web/utils/audit_runner.py
"""
Audit Runner - Wrapper for running anomaly detection
รัน anomaly detection และติดตาม progress
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
import traceback

class AuditRunner:
    """รัน anomaly detection พร้อมติดตาม progress"""
    
    def __init__(self):
        self.progress_data = {}
    
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
        file_id = config.get('_metadata', {}).get('file_id', 'unknown')
        
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
            
            # Step 2: Preprocess (20%)
            self._update_progress(file_id, {
                'status': 'preprocessing',
                'progress': 20,
                'message': 'Preprocessing data...'
            }, callback)
            
            df_clean = self._prepare_data(df, config)
            
            # Step 3: Run Time Series Analysis (30-60%)
            ts_log = pd.DataFrame()
            if config.get('run_time_series_analysis', False):
                self._update_progress(file_id, {
                    'status': 'time_series',
                    'progress': 30,
                    'message': 'Running Time Series Analysis...'
                }, callback)
                
                ts_log = self._run_time_series(df_clean, config, callback=lambda p: self._update_progress(
                    file_id, {'progress': 30 + p/2}, callback
                ))
            
            # Step 4: Run Peer Group Analysis (60-80%)
            peer_log = pd.DataFrame()
            if config.get('run_peer_group_analysis', False):
                self._update_progress(file_id, {
                    'status': 'peer_group',
                    'progress': 60,
                    'message': 'Running Peer Group Analysis...'
                }, callback)
                
                peer_log = self._run_peer_group(df_clean, config, callback=lambda p: self._update_progress(
                    file_id, {'progress': 60 + p/5}, callback
                ))
            
            # Step 5: Generate Report (80-95%)
            self._update_progress(file_id, {
                'status': 'generating_report',
                'progress': 80,
                'message': 'Generating Excel report...'
            }, callback)
            
            self._generate_report(df_clean, ts_log, peer_log, output_file, config)
            
            # Complete
            result = {
                'status': 'completed',
                'total_rows': len(df_clean),
                'ts_anomalies': len(ts_log) if not ts_log.empty else 0,
                'peer_anomalies': len(peer_log) if not peer_log.empty else 0,
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
        """โหลดข้อมูล"""
        input_mode = config.get('input_mode', 'long')
        
        if input_mode == 'crosstab':
            # Convert crosstab to long format
            from crosstab_converter import CrosstabConverter
            
            temp_output = input_file + '_temp_long.csv'
            converter = CrosstabConverter(input_file, temp_output)
            
            converter.convert(
                sheet_name=config.get('crosstab_sheet_name', 0),
                skiprows=config.get('crosstab_skiprows', 0),
                id_vars=config.get('crosstab_id_vars', []),
                value_name=config.get('crosstab_value_name', 'VALUE'),
                mode=config.get('crosstab_mode', 'auto')
            )
            
            df = pd.read_csv(temp_output)
            # Clean up temp file
            if os.path.exists(temp_output):
                os.remove(temp_output)
        else:
            # Direct long format
            df = pd.read_csv(input_file)
        
        return df
    
    def _prepare_data(self, df, config):
        """เตรียมข้อมูล (ใช้ logic จาก main_audit.py)"""
        # Import prepare_data function from main_audit
        # หรือ copy logic มาใส่ตรงนี้
        
        # Simplified version - ควร import จาก main_audit.py จริงๆ
        df = df.copy()
        
        # Create date column
        col_year = config.get('col_year', 'YEAR')
        col_month = config.get('col_month', 'MONTH')
        
        if col_year in df.columns and col_month in df.columns:
            df['__date_col__'] = pd.to_datetime(
                df[col_year].astype(str) + '-' +
                df[col_month].astype(int).astype(str).str.zfill(2) + '-01'
            )
        
        # Clean numeric column
        target_col = config.get('target_col', 'VALUE')
        if target_col in df.columns:
            df[target_col] = self._clean_numeric(df[target_col])
        
        # Fill dimensions
        all_dims = set(config.get('crosstab_dimensions', []) + 
                      config.get('audit_ts_dimensions', []) +
                      config.get('audit_peer_group_by', []))
        
        for col in all_dims:
            if col in df.columns:
                df[col] = df[col].fillna('N/A')
        
        return df
    
    def _clean_numeric(self, series):
        """ทำความสะอาดตัวเลข (accounting format)"""
        s = series.astype(str)
        is_negative = s.str.contains(r'\(.*\)', regex=True, na=False)
        s = s.str.replace(r'[,\(\)\s$฿%]', '', regex=True)
        s = pd.to_numeric(s, errors='coerce').fillna(0)
        s.loc[is_negative] = -s.loc[is_negative].abs()
        return s
    
    def _run_time_series(self, df, config, callback=None):
        """รัน Time Series Analysis"""
        # Import และใช้ FullAuditEngine จาก anomaly_engine.py
        # สำหรับ demo - return empty DataFrame
        return pd.DataFrame()
    
    def _run_peer_group(self, df, config, callback=None):
        """รัน Peer Group Analysis"""
        # Import และใช้ FullAuditEngine จาก anomaly_engine.py
        # สำหรับ demo - return empty DataFrame
        return pd.DataFrame()
    
    def _generate_report(self, df, ts_log, peer_log, output_file, config):
        """สร้าง Excel report"""
        # Import และใช้ ExcelReporter จาก anomaly_reporter.py
        # สำหรับ demo - สร้าง Excel แบบง่าย
        
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            # Sheet 1: Summary
            summary = pd.DataFrame({
                'Metric': ['Total Rows', 'Time Series Anomalies', 'Peer Group Anomalies'],
                'Value': [len(df), len(ts_log), len(peer_log)]
            })
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 2: Time Series Log
            if not ts_log.empty:
                ts_log.to_excel(writer, sheet_name='Time_Series_Log', index=False)
            
            # Sheet 3: Peer Group Log
            if not peer_log.empty:
                peer_log.to_excel(writer, sheet_name='Peer_Group_Log', index=False)
    
    def _update_progress(self, file_id, progress_data, callback=None):
        """อัปเดต progress"""
        # Merge with existing progress
        if file_id in self.progress_data:
            self.progress_data[file_id].update(progress_data)
        else:
            self.progress_data[file_id] = progress_data
        
        # Update timestamp
        self.progress_data[file_id]['updated_at'] = datetime.now().isoformat()
        
        # Call callback if provided
        if callback:
            callback(self.progress_data[file_id])
    
    def get_progress(self, file_id):
        """ดึง progress ปัจจุบัน"""
        return self.progress_data.get(file_id, {
            'status': 'not_started',
            'progress': 0,
            'message': 'No progress data available'
        })
    
    def update_progress(self, file_id, progress_data):
        """อัปเดต progress จากภายนอก"""
        self._update_progress(file_id, progress_data)
