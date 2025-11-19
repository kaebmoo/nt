# anomaly_web/utils/data_analyzer.py
"""
Data Analyzer - Auto-detect data types, columns, and patterns
วิเคราะห์ข้อมูลอัตโนมัติ เพื่อช่วยผู้ใช้ในการ config
"""

import pandas as pd
import numpy as np
from collections import Counter
import re

class DataAnalyzer:
    """วิเคราะห์และแนะนำ configuration อัตโนมัติ"""
    
    def analyze_dataframe(self, df, input_mode='long'):
        """
        วิเคราะห์ DataFrame และแนะนำ configuration
        
        Args:
            df: pandas DataFrame
            input_mode: 'long' หรือ 'crosstab'
        
        Returns:
            dict: ผลการวิเคราะห์
        """
        analysis = {
            'input_mode': input_mode,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': {},
            'recommendations': {}
        }
        
        # Analyze each column
        for col in df.columns:
            analysis['columns'][col] = self._analyze_column(df[col])
        
        # Generate recommendations based on input mode
        if input_mode == 'long':
            analysis['recommendations'] = self._recommend_long_format(df, analysis['columns'])
        elif input_mode == 'crosstab':
            analysis['recommendations'] = self._recommend_crosstab_format(df, analysis['columns'])
        
        return analysis
    
    def _analyze_column(self, series):
        """วิเคราะห์ column แต่ละตัว"""
        col_info = {
            'dtype': str(series.dtype),
            'null_count': int(series.isnull().sum()),
            'null_percentage': round(series.isnull().sum() / len(series) * 100, 2),
            'unique_count': int(series.nunique()),
            'sample_values': series.dropna().head(5).tolist()
        }
        
        # Detect column type
        col_info['detected_type'] = self._detect_column_type(series)
        
        # For numeric columns
        if col_info['detected_type'] == 'numeric':
            col_info['stats'] = {
                'min': float(series.min()) if not series.isnull().all() else None,
                'max': float(series.max()) if not series.isnull().all() else None,
                'mean': float(series.mean()) if not series.isnull().all() else None,
                'median': float(series.median()) if not series.isnull().all() else None
            }
        
        # For date columns
        elif col_info['detected_type'] == 'date':
            col_info['date_format'] = self._detect_date_format(series)
        
        # For categorical columns
        elif col_info['detected_type'] == 'categorical':
            col_info['categories'] = series.value_counts().head(10).to_dict()
        
        return col_info
    
    def _detect_column_type(self, series):
        """
        ตรวจจับประเภทของ column
        Returns: 'numeric', 'date', 'categorical', 'text', 'id'
        """
        # Skip if mostly null
        if series.isnull().sum() / len(series) > 0.9:
            return 'mostly_null'
        
        # Try numeric
        try:
            # Clean and convert
            cleaned = series.astype(str).str.replace(',', '').str.replace('(', '-').str.replace(')', '')
            pd.to_numeric(cleaned, errors='raise')
            return 'numeric'
        except:
            pass
        
        # Try date
        if self._is_date_column(series):
            return 'date'
        
        # Check if ID (mostly unique)
        if series.nunique() / len(series) > 0.95:
            return 'id'
        
        # Check if categorical (low cardinality)
        if series.nunique() < 50:
            return 'categorical'
        
        # Default to text
        return 'text'
    
    def _is_date_column(self, series):
        """ตรวจสอบว่าเป็น column วันที่หรือไม่"""
        try:
            pd.to_datetime(series.dropna().head(100), errors='raise')
            return True
        except:
            pass
        
        # Check for date-like patterns
        sample = series.dropna().head(100).astype(str)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-01
            r'\d{2}/\d{2}/\d{4}',  # 01/01/2024
            r'\d{4}/\d{2}',         # 2024/01
            r'\d{4}-\d{2}',         # 2024-01
        ]
        
        for pattern in date_patterns:
            if sample.str.match(pattern).sum() / len(sample) > 0.8:
                return True
        
        return False
    
    def _detect_date_format(self, series):
        """ตรวจหา date format"""
        sample = series.dropna().head(10).astype(str)
        
        formats = {
            r'\d{4}-\d{2}-\d{2}': '%Y-%m-%d',
            r'\d{2}/\d{2}/\d{4}': '%d/%m/%Y',
            r'\d{4}/\d{2}': '%Y/%m',
            r'\d{4}-\d{2}': '%Y-%m',
        }
        
        for pattern, fmt in formats.items():
            if sample.str.match(pattern).sum() > 0:
                return fmt
        
        return 'unknown'
    
    def _recommend_long_format(self, df, columns_info):
        """แนะนำ configuration สำหรับ Long Format"""
        recommendations = {
            'year_column': None,
            'month_column': None,
            'date_column': None,
            'value_columns': [],
            'dimension_columns': [],
            'id_columns': []
        }
        
        for col_name, info in columns_info.items():
            col_upper = col_name.upper()
            
            # Detect YEAR column
            if 'YEAR' in col_upper and info['detected_type'] in ['numeric', 'categorical']:
                recommendations['year_column'] = col_name
            
            # Detect MONTH column
            elif 'MONTH' in col_upper and info['detected_type'] in ['numeric', 'categorical']:
                recommendations['month_column'] = col_name
            
            # Detect DATE column
            elif info['detected_type'] == 'date':
                if not recommendations['date_column']:  # เอาตัวแรกที่เจอ
                    recommendations['date_column'] = col_name
            
            # Detect VALUE columns (numeric with "VALUE", "AMOUNT", "EXPENSE", "REVENUE")
            elif info['detected_type'] == 'numeric':
                value_keywords = ['VALUE', 'AMOUNT', 'EXPENSE', 'REVENUE', 'COST', 'SALES', 'PRICE']
                if any(kw in col_upper for kw in value_keywords):
                    recommendations['value_columns'].append({
                        'name': col_name,
                        'confidence': 'high',
                        'stats': info.get('stats', {})
                    })
                else:
                    recommendations['value_columns'].append({
                        'name': col_name,
                        'confidence': 'medium',
                        'stats': info.get('stats', {})
                    })
            
            # Detect DIMENSION columns (categorical with reasonable cardinality)
            elif info['detected_type'] == 'categorical' and 5 <= info['unique_count'] <= 1000:
                recommendations['dimension_columns'].append({
                    'name': col_name,
                    'unique_count': info['unique_count'],
                    'categories_sample': list(info.get('categories', {}).keys())[:5]
                })
            
            # Detect ID columns
            elif info['detected_type'] == 'id':
                recommendations['id_columns'].append(col_name)
        
        return recommendations
    
    def _recommend_crosstab_format(self, df, columns_info):
        """แนะนำ configuration สำหรับ Crosstab Format"""
        recommendations = {
            'id_vars': [],  # Dimension columns (non-numeric)
            'value_name_options': [],  # ชื่อที่เหมาะสมสำหรับค่า
            'date_columns': [],  # Columns ที่อาจเป็นวันที่
            'mode': 'auto'
        }
        
        date_like_cols = []
        dimension_cols = []
        
        for col_name, info in columns_info.items():
            # Dimension columns (categorical, text)
            if info['detected_type'] in ['categorical', 'text']:
                dimension_cols.append({
                    'name': col_name,
                    'unique_count': info['unique_count'],
                    'sample': info['sample_values'][:3]
                })
            
            # Date-like columns
            elif info['detected_type'] in ['date', 'numeric']:
                # Check if looks like date format
                if self._looks_like_date_header(col_name):
                    date_like_cols.append({
                        'name': col_name,
                        'format': self._guess_date_format(col_name)
                    })
        
        recommendations['id_vars'] = dimension_cols
        recommendations['date_columns'] = date_like_cols
        
        # Suggest value name
        if any('expense' in c['name'].lower() for c in dimension_cols):
            recommendations['value_name_options'].append('EXPENSE_VALUE')
        if any('revenue' in c['name'].lower() for c in dimension_cols):
            recommendations['value_name_options'].append('REVENUE_VALUE')
        
        # Default
        if not recommendations['value_name_options']:
            recommendations['value_name_options'] = ['VALUE', 'AMOUNT']
        
        # Detect mode
        if date_like_cols:
            recommendations['mode'] = 'date'
        else:
            recommendations['mode'] = 'sequential'
        
        return recommendations
    
    def _looks_like_date_header(self, col_name):
        """ตรวจสอบว่า column header ดูเหมือนวันที่หรือไม่"""
        patterns = [
            r'\d{4}-\d{2}',      # 2024-01
            r'\d{4}/\d{2}',      # 2024/01
            r'[A-Za-zก-ฮ]{3,}',  # Jan, ม.ค.
            r'\d{1,2}',          # 1, 2, 3 (month or period)
        ]
        
        for pattern in patterns:
            if re.match(pattern, str(col_name)):
                return True
        return False
    
    def _guess_date_format(self, col_name):
        """เดาว่า column เป็น format ใด"""
        col_str = str(col_name)
        
        if re.match(r'\d{4}-\d{2}', col_str):
            return 'YYYY-MM'
        elif re.match(r'\d{4}/\d{2}', col_str):
            return 'YYYY/MM'
        elif re.match(r'[A-Za-z]{3}', col_str):
            return 'Mon (Jan, Feb, ...)'
        elif re.match(r'[ก-ฮ]{3,}', col_str):
            return 'Mon (ม.ค., ก.พ., ...)'
        elif re.match(r'\d{1,2}', col_str):
            return 'Sequential (1, 2, 3, ...)'
        
        return 'unknown'
