# anomaly_web/utils/data_analyzer.py
"""
Data Analyzer - Auto-detect data types, columns, and patterns
วิเคราะห์ข้อมูลอัตโนมัติ เพื่อช่วยผู้ใช้ในการ config
"""

import pandas as pd
import numpy as np
from collections import Counter
import re

try:
    from .data_cleaning import blank_mask, clean_numeric_series, numeric_bad_mask, parse_date_series
except ImportError:
    from data_cleaning import blank_mask, clean_numeric_series, numeric_bad_mask, parse_date_series

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
            
        # Merge dimension recommendations back into the main columns analysis
        if 'dimension_columns' in analysis['recommendations']:
            for dim_col in analysis['recommendations']['dimension_columns']:
                if dim_col['name'] in analysis['columns']:
                    analysis['columns'][dim_col['name']]['is_recommended_dimension'] = dim_col['recommended']
        
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

        numeric = clean_numeric_series(series)
        non_blank_count = int((~blank_mask(series)).sum())
        valid_numeric_count = int(numeric.notna().sum())
        col_info['numeric_parse'] = {
            'valid_count': valid_numeric_count,
            'invalid_count': int(numeric_bad_mask(series, numeric).sum()),
            'valid_percentage': round(valid_numeric_count / non_blank_count * 100, 2) if non_blank_count else 0
        }
        
        # Detect column type
        col_info['detected_type'] = self._detect_column_type(series)
        
        # For numeric columns
        if col_info['detected_type'] == 'numeric':
            try:
                col_info['stats'] = {
                    'min': float(numeric.min()) if not numeric.isnull().all() else None,
                    'max': float(numeric.max()) if not numeric.isnull().all() else None,
                    'mean': float(numeric.mean()) if not numeric.isnull().all() else None,
                    'median': float(numeric.median()) if not numeric.isnull().all() else None
                }
            except Exception as e:
                col_info['stats'] = {'error': str(e)}
        
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
        col_name = series.name
        col_upper = str(col_name).upper()

        # Skip if mostly null
        if series.isnull().sum() / len(series) > 0.9:
            return 'mostly_null'

        is_likely_dimension = self._is_dimension_name(col_upper)
        is_measure = self._is_measure_name(col_upper)
        is_date_keyword = self._is_date_name(col_upper)

        # Try date first only when the name supports it. This avoids treating YEAR=2026 as a date.
        if (is_date_keyword or not is_likely_dimension) and self._is_date_column(series):
            return 'date'

        numeric = clean_numeric_series(series)
        non_blank = ~blank_mask(series)
        non_blank_count = int(non_blank.sum())
        numeric_ratio = numeric[non_blank].notna().sum() / non_blank_count if non_blank_count else 0
        is_numeric = numeric_ratio >= 0.75

        if is_numeric:
            if is_likely_dimension and not self._is_strong_measure_name(col_upper):
                return 'categorical'
            if is_measure:
                return 'numeric'
            if series.nunique() <= 50:
                return 'categorical'
            return 'numeric'

        # Check if ID (mostly unique) - for text-based IDs
        if series.nunique() / len(series) > 0.95:
            return 'id'

        # Check if categorical (low cardinality)
        if series.nunique() < 50:
            return 'categorical'

        # Medium cardinality but has dimension pattern
        if is_likely_dimension and series.nunique() < 10000:
            return 'categorical'

        # Default to text
        return 'text'
    
    def _is_date_column(self, series):
        """ตรวจสอบว่าเป็น column วันที่หรือไม่"""
        sample = series.dropna().head(100).astype(str)
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-01
            r'\d{2}/\d{2}/\d{4}',  # 01/01/2024
            r'\d{2}\.\d{2}\.\d{4}', # 01.02.2024
            r'\d{4}/\d{2}',         # 2024/01
            r'\d{4}-\d{2}',         # 2024-01
            r'\d{8}',               # 20240101
            r'\d{1,2}[A-Za-z]{3}\d{4}', # 01JAN2024
        ]
        
        for pattern in date_patterns:
            if len(sample) and sample.str.fullmatch(pattern, flags=re.IGNORECASE).sum() / len(sample) >= 0.6:
                return True

        numeric = pd.to_numeric(series, errors='coerce').dropna().head(100)
        if not numeric.empty and numeric.between(20000, 80000).mean() >= 0.8:
            return True
        
        return False
    
    def _detect_date_format(self, series):
        """ตรวจหา date format"""
        sample = series.dropna().head(10).astype(str)
        
        formats = {
            r'\d{4}-\d{2}-\d{2}': '%Y-%m-%d',
            r'\d{2}/\d{2}/\d{4}': '%d/%m/%Y',
            r'\d{2}\.\d{2}\.\d{4}': '%d.%m.%Y',
            r'\d{4}/\d{2}': '%Y/%m',
            r'\d{4}-\d{2}': '%Y-%m',
            r'\d{8}': '%Y%m%d',
            r'\d{1,2}[A-Za-z]{3}\d{4}': '%d%b%Y',
        }
        
        for pattern, fmt in formats.items():
            if sample.str.fullmatch(pattern, flags=re.IGNORECASE).sum() > 0:
                return fmt
        
        return 'unknown'

    def _is_dimension_name(self, col_upper):
        patterns = [
            '_KEY', '_ID', '_CODE', '_NUMBER', '_NO', 'KEY_', 'ID_', 'CODE_',
            'ACCOUNT', 'DOCUMENT', 'DOC', 'INVOICE', 'SEQ', 'PK',
            'CENTER', 'DEPARTMENT', 'DIVISION', 'GROUP', 'TYPE', 'CATEGORY',
            'PRODUCT', 'CUSTOMER', 'SEGMENT', 'GL', 'BUSA', 'BP', 'PERIOD',
            'บัญชี', 'เลข', 'รหัส', 'เอกสาร', 'ใบแจ้งหนี้', 'ลำดับ',
            'เซกเมนต์', 'ผลิตภัณฑ์', 'ผ.ภัณฑ์', 'บริการ', 'ประเภท', 'ประเภทราย',
            'กลุ่ม', 'ศูนย์', 'ลูกค้า', 'งวด'
        ]
        return any(pattern in col_upper for pattern in patterns)

    def _is_measure_name(self, col_upper):
        patterns = [
            'VALUE', 'AMOUNT', 'EXPENSE', 'REVENUE', 'COST', 'SALES', 'PRICE',
            'BALANCE', 'TOTAL', 'NET', 'GROSS',
            'จำนวนเงิน', 'จำนวนสกุลเงิน', 'ยอด', 'มูลค่า', 'รายได้', 'ค่าใช้จ่าย', 'เงิน'
        ]
        return any(pattern in col_upper for pattern in patterns)

    def _is_strong_measure_name(self, col_upper):
        patterns = [
            'VALUE', 'AMOUNT', 'REVENUE', 'EXPENSE', 'SALES', 'PRICE',
            'BALANCE', 'TOTAL', 'NET', 'GROSS',
            'จำนวนเงิน', 'จำนวนสกุลเงิน', 'ยอด', 'มูลค่า', 'รายได้', 'ค่าใช้จ่าย', 'เงิน'
        ]
        return any(pattern in col_upper for pattern in patterns)

    def _is_date_name(self, col_upper):
        patterns = ['YEAR', 'MONTH', 'DAY', 'DATE', 'TIME', 'PERIOD', 'POSTING', 'PSTNG', 'วันที่', 'ว/ท']
        return any(pattern in col_upper for pattern in patterns)
    
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

        # First pass: Check for YYYY-MM format columns that should be treated as dates
        year_month_candidates = []
        for col_name, info in columns_info.items():
            # Check if column contains YYYY-MM format
            if info['detected_type'] == 'date':
                date_format = info.get('date_format', '')
                if date_format in ['%Y-%m', '%Y/%m']:
                    year_month_candidates.append(col_name)

        date_candidates = [
            col_name for col_name, info in columns_info.items()
            if info['detected_type'] == 'date' and col_name not in year_month_candidates
        ]
        preferred_date_column = None
        if date_candidates:
            preferred_date_column = max(date_candidates, key=self._date_column_score)

        for col_name, info in columns_info.items():
            col_upper = col_name.upper()

            # Skip if this is a YYYY-MM column (should be treated as date, not year)
            if col_name in year_month_candidates:
                if not recommendations['date_column']:
                    recommendations['date_column'] = col_name
                continue

            # Detect YEAR column (exact match or starts with YEAR_)
            # But NOT if it's a YYYY-MM format
            if col_upper == 'YEAR' or col_upper.startswith('YEAR_'):
                if info['detected_type'] in ['numeric', 'categorical']:
                    # Make sure it's actually a year (4-digit number between 1900-2100)
                    sample_values = df[col_name].dropna().head(10)
                    try:
                        numeric_values = pd.to_numeric(sample_values, errors='coerce')
                        if numeric_values.notna().any():
                            min_val = numeric_values.min()
                            max_val = numeric_values.max()
                            if 1900 <= min_val <= 2100 and 1900 <= max_val <= 2100:
                                recommendations['year_column'] = col_name
                                continue
                    except:
                        pass

            # Detect MONTH column (exact match or starts with MONTH_)
            # But NOT if it's a YYYY-MM format
            if col_upper == 'MONTH' or col_upper.startswith('MONTH_'):
                if info['detected_type'] in ['numeric', 'categorical']:
                    # Make sure it's actually a month (1-12)
                    sample_values = df[col_name].dropna().head(10)
                    try:
                        numeric_values = pd.to_numeric(sample_values, errors='coerce')
                        if numeric_values.notna().any():
                            min_val = numeric_values.min()
                            max_val = numeric_values.max()
                            if 1 <= min_val <= 12 and 1 <= max_val <= 12:
                                recommendations['month_column'] = col_name
                                continue
                    except:
                        pass

            # Detect DATE column (including YYYY-MM-DD, YYYY-MM formats)
            if info['detected_type'] == 'date':
                if not recommendations['date_column']:  # เอาตัวแรกที่เจอ
                    recommendations['date_column'] = preferred_date_column or col_name
                continue

            # Detect VALUE columns (only pure numeric, not KEY/ID/CODE)
            # Exclude columns with dimension patterns
            is_dimension_pattern = self._is_dimension_name(col_upper)

            if info['detected_type'] == 'numeric' and (not is_dimension_pattern or self._is_strong_measure_name(col_upper)):
                if self._is_strong_measure_name(col_upper):
                    recommendations['value_columns'].append({
                        'name': col_name,
                        'confidence': 'high',
                        'stats': info.get('stats', {}),
                        'numeric_parse': info.get('numeric_parse', {})
                    })
                else:
                    # Even without keywords, if it's numeric and not a dimension pattern, it's likely a value
                    recommendations['value_columns'].append({
                        'name': col_name,
                        'confidence': 'medium',
                        'stats': info.get('stats', {}),
                        'numeric_parse': info.get('numeric_parse', {})
                    })
                continue

            # Detect DIMENSION columns (categorical with reasonable cardinality)
            # Now includes numeric columns with dimension patterns
            if info['detected_type'] in ['categorical', 'text']:
                # Reasonable cardinality for dimensions
                if 2 <= info['unique_count'] <= 10000:
                    # Recommend based on common dimension keywords
                    dim_keywords = ['GROUP', 'CODE', 'NAME', 'KEY', 'CENTER', 'SEGMENT', 'TYPE', 'CATEGORY',
                                    'PRODUCT', 'CUSTOMER', 'GL', 'ACCOUNT', 'COST', 'DEPARTMENT', 'DIVISION']
                    is_recommended = any(kw in col_upper for kw in dim_keywords)

                    recommendations['dimension_columns'].append({
                        'name': col_name,
                        'unique_count': info['unique_count'],
                        'categories_sample': list(info.get('categories', {}).keys())[:5] if info.get('categories') else [],
                        'recommended': is_recommended
                    })
                    continue

            # Detect ID columns (very high cardinality)
            if info['detected_type'] == 'id':
                recommendations['id_columns'].append(col_name)

        return recommendations

    def _date_column_score(self, col_name):
        col_upper = str(col_name).upper()
        score = 0
        if any(key in col_upper for key in ['PSTNG', 'POSTING', 'POST DATE', 'POSTED']):
            score += 100
        if 'TIME_KEY_DATE' in col_upper:
            score += 80
        if any(key in col_upper for key in ['DATE', 'วันที่', 'ว/ท']):
            score += 10
        if any(key in col_upper for key in ['DOCUMENT', 'DOC', 'เอกสาร']):
            score -= 30
        return score
    
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
