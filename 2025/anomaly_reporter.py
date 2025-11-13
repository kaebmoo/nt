import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

class ExcelReporter:
    def __init__(self, output_file):
        self.writer = pd.ExcelWriter(output_file, engine='openpyxl')
        print(f"[Reporter]: Initialized for file: {output_file}")
        
        self.styles = {
            "High_Spike": PatternFill(start_color="FFC7CE", fill_type="solid"),
            "Spike_vs_Constant": PatternFill(start_color="FFC7CE", fill_type="solid"),
            "Low_Spike": PatternFill(start_color="FFEB9C", fill_type="solid"),
            "New_Item": PatternFill(start_color="C6E0B4", fill_type="solid"),
            "Negative_Value": PatternFill(start_color="FF0000", fill_type="solid"),
            "Low_Drop": PatternFill(start_color="FFEB9C", fill_type="solid"), # ชื่อ Alias สำหรับ Low_Spike
        }
        self.font_negative = Font(color="FFFFFF", bold=True)
        self.align_right = Alignment(horizontal='right')
        self.num_format = "#,##0.00"

    def _build_anomaly_lookup(self, df_log, dimensions, date_col_name):
        """สร้าง Dictionary สำหรับค้นหา Anomaly เพื่อทาสี"""
        print("[Reporter]: Building cell anomaly lookup...")
        lookup = {}
        if df_log.empty: return lookup
        
        # กรอง Log เฉพาะที่มี Dimension ครบ
        valid_dims = [d for d in dimensions if d in df_log.columns]
        
        for _, row in df_log.iterrows():
            # Key 1: สร้าง Key ของแถว (Dimension รวมกัน)
            key_parts = [str(row[d]) for d in valid_dims]
            row_key = "|".join(key_parts)
            
            # Key 2: สร้าง Key ของคอลัมน์วันที่ (YYYY-MM)
            if isinstance(row[date_col_name], pd.Timestamp):
                date_key = row[date_col_name].strftime('%Y-%m')
            else:
                date_key = str(row[date_col_name])[:7] # Fallback
            
            # Map: (RowKey, DateKey) -> Issue
            lookup[(row_key, date_key)] = row['ISSUE_DESC']
            
        print(f"[Reporter]: ✓ Lookup ready ({len(lookup)} entries).")
        return lookup

    def add_crosstab_sheet(self, df_report, df_anomaly_log, dimensions, date_col_name, date_cols_sorted):
        """เพิ่ม Crosstab Sheet และทาสีทั้งเดือนปัจจุบันและอดีต"""
        if df_report.empty: return

        print("[Reporter]: Adding Crosstab Sheet with Cell Highlighting...")
        sheet_name = 'Crosstab_Report'
        df_report.to_excel(self.writer, sheet_name=sheet_name, index=False)
        
        # สร้าง Lookup จาก Log ไฟล์
        anomaly_lookup = self._build_anomaly_lookup(df_anomaly_log, dimensions, date_col_name)

        ws = self.writer.sheets[sheet_name]
        
        # Map หัวตาราง -> ตัวอักษรคอลัมน์ (A, B, C...)
        header_cells = ws[1]
        col_map = {cell.value: (cell.column, cell.column_letter) for cell in header_cells}
        
        status_col_letter = col_map.get('ANOMALY_STATUS', (None, None))[1]

        # Loop ทุกแถวข้อมูล (เริ่มแถว 2)
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), 2):
            
            # 1. สร้าง Row Key สำหรับแถวนี้
            dim_values = []
            for dim_name in dimensions:
                col_info = col_map.get(dim_name)
                if col_info:
                    cell_val = ws[f"{col_info[1]}{row_idx}"].value
                    dim_values.append(str(cell_val))
            row_key = "|".join(dim_values)
            
            # 2. Loop ทุกคอลัมน์ในแถวนี้
            for col_name, (col_idx, col_letter) in col_map.items():
                cell = ws[f"{col_letter}{row_idx}"]
                
                # A. ถ้าเป็นคอลัมน์วันที่ (Data Cells) -> เช็ค Lookup เพื่อทาสี
                if col_name in date_cols_sorted:
                    cell.number_format = self.num_format
                    cell.alignment = self.align_right
                    
                    # ตรวจสอบว่า Cell นี้มี Anomaly ใน Log ไหม
                    lookup_key = (row_key, col_name)
                    issue = anomaly_lookup.get(lookup_key)
                    
                    if issue and issue in self.styles:
                        cell.fill = self.styles[issue]
                        if issue == "Negative_Value": cell.font = self.font_negative
                
                # B. ถ้าเป็นคอลัมน์สถานะล่าสุด (Last Month Status)
                elif col_name == 'ANOMALY_STATUS':
                    status = cell.value
                    if status in self.styles:
                        cell.fill = self.styles[status]
                        if status == "Negative_Value": cell.font = self.font_negative
                
                # C. จัด Format คอลัมน์อื่นๆ
                elif col_name == 'PCT_CHANGE':
                    cell.number_format = '0.00"%"'
                    cell.alignment = self.align_right
                elif col_name in ['LATEST_VALUE', 'AVG_HISTORICAL']:
                    cell.number_format = self.num_format
                    cell.alignment = self.align_right

        # จัดความกว้างคอลัมน์
        for col_name, (idx, letter) in col_map.items():
            if col_name in dimensions: ws.column_dimensions[letter].width = 30
            elif col_name in date_cols_sorted: ws.column_dimensions[letter].width = 15
            elif col_name == 'ANOMALY_STATUS': ws.column_dimensions[letter].width = 20
            else: ws.column_dimensions[letter].width = 18

        ws.freeze_panes = f'{get_column_letter(len(dimensions) + 1)}2'

    def add_audit_log_sheet(self, df_log, sheet_name, cols_to_show):
        print(f"[Reporter]: Adding Log Sheet: {sheet_name}...")
        if df_log.empty: df_log = pd.DataFrame({'Message': ['No Anomalies Found']}); cols_to_show = ['Message']
        
        valid_cols = [c for c in cols_to_show if c in df_log.columns]
        df_log[valid_cols].to_excel(self.writer, sheet_name=sheet_name, index=False)
        
        ws = self.writer.sheets[sheet_name]
        for i, col in enumerate(valid_cols, 1):
            ws.column_dimensions[get_column_letter(i)].width = 25

    def save(self):
        try:
            self.writer.close()
            print(f"[Reporter]: ✓ Report saved: {self.writer.path}") # Updated access for path
        except:
            print(f"[Reporter]: ✓ Report saved.")