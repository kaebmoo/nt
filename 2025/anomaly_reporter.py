import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

class ExcelReporter:
    def __init__(self, output_file):
        self.writer = pd.ExcelWriter(output_file, engine='openpyxl')
        print(f"[Reporter]: Initialized for file: {output_file}")
        
        # กำหนด Style สีต่างๆ
        self.styles = {
            "High_Spike": PatternFill(start_color="FFC7CE", fill_type="solid"),
            "Spike_vs_Constant": PatternFill(start_color="FFC7CE", fill_type="solid"),
            "Low_Spike": PatternFill(start_color="FFEB9C", fill_type="solid"),
            "New_Item": PatternFill(start_color="C6E0B4", fill_type="solid"),
            "Negative_Value": PatternFill(start_color="FF0000", fill_type="solid"),
            "Low_Drop": PatternFill(start_color="FFEB9C", fill_type="solid"),
        }
        self.font_negative = Font(color="FFFFFF", bold=True)
        self.font_bold = Font(bold=True)
        self.align_right = Alignment(horizontal='right')
        self.num_format = "#,##0.00"

    def _build_anomaly_lookup(self, df_log, dimensions, date_col_name):
        """สร้าง Dictionary สำหรับค้นหา Anomaly เพื่อทาสี"""
        print("[Reporter]: Building cell anomaly lookup...")
        lookup = {}
        if df_log.empty: return lookup
        
        valid_dims = [d for d in dimensions if d in df_log.columns]
        
        for _, row in df_log.iterrows():
            key_parts = [str(row[d]) for d in valid_dims]
            row_key = "|".join(key_parts)
            
            if isinstance(row[date_col_name], pd.Timestamp):
                date_key = row[date_col_name].strftime('%Y-%m')
            else:
                date_key = str(row[date_col_name])[:7]
            
            lookup[(row_key, date_key)] = row['ISSUE_DESC']
            
        return lookup

    def _add_legend(self, ws):
        """ฟังก์ชันใหม่: สร้างตารางคำอธิบายสี (Legend) ต่อท้ายข้อมูล"""
        start_row = ws.max_row + 4  # เว้นว่าง 3 บรรทัดจากข้อมูลสุดท้าย
        
        # หัวข้อ
        cell_header = ws.cell(row=start_row, column=2, value="คำอธิบายความหมายสี (Color Legend)")
        cell_header.font = self.font_bold
        
        legend_data = [
            ("High_Spike",      "ยอดพุ่งสูงผิดปกติ (High Spike)"),
            ("Low_Spike",       "ยอดตกลงต่ำผิดปกติ (Low Drop)"),
            ("New_Item",        "รายการใหม่ / เพิ่งมียอด (New Item)"),
            ("Negative_Value",  "ยอดติดลบ")
        ]

        for i, (key, desc) in enumerate(legend_data):
            r = start_row + 1 + i
            
            # ช่องสี (Column B)
            c_color = ws.cell(row=r, column=2, value="     ") # เว้นว่างไว้โชว์สี
            if key in self.styles:
                c_color.fill = self.styles[key]
                if key == "Negative_Value": c_color.font = self.font_negative
            
            # ช่องคำอธิบาย (Column C)
            c_desc = ws.cell(row=r, column=3, value=desc)
            c_desc.alignment = Alignment(horizontal='left')

        print(f"[Reporter]: ✓ Added Color Legend at row {start_row}")

    def add_crosstab_sheet(self, df_report, df_anomaly_log, dimensions, date_col_name, date_cols_sorted):
        """เพิ่ม Crosstab Sheet และทาสีทั้งเดือนปัจจุบันและอดีต"""
        if df_report.empty: return

        print("[Reporter]: Adding Crosstab Sheet with Cell Highlighting...")
        sheet_name = 'Crosstab_Report'
        df_report.to_excel(self.writer, sheet_name=sheet_name, index=False)
        
        anomaly_lookup = self._build_anomaly_lookup(df_anomaly_log, dimensions, date_col_name)
        ws = self.writer.sheets[sheet_name]
        
        header_cells = ws[1]
        col_map = {cell.value: (cell.column, cell.column_letter) for cell in header_cells}
        
        # Loop ทุกแถวข้อมูลเพื่อทาสี
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, max_row=ws.max_row), 2):
            dim_values = []
            for dim_name in dimensions:
                col_info = col_map.get(dim_name)
                if col_info:
                    cell_val = ws[f"{col_info[1]}{row_idx}"].value
                    dim_values.append(str(cell_val))
            row_key = "|".join(dim_values)
            
            for col_name, (col_idx, col_letter) in col_map.items():
                cell = ws[f"{col_letter}{row_idx}"]
                
                if col_name in date_cols_sorted:
                    cell.number_format = self.num_format
                    cell.alignment = self.align_right
                    lookup_key = (row_key, col_name)
                    issue = anomaly_lookup.get(lookup_key)
                    if issue and issue in self.styles:
                        cell.fill = self.styles[issue]
                        if issue == "Negative_Value": cell.font = self.font_negative
                
                elif col_name == 'ANOMALY_STATUS':
                    status = cell.value
                    if status in self.styles:
                        cell.fill = self.styles[status]
                        if status == "Negative_Value": cell.font = self.font_negative
                
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

        # --- ส่วนที่เพิ่มใหม่: เรียกใช้ฟังก์ชันสร้าง Legend ---
        self._add_legend(ws)
        # ------------------------------------------------

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
            print(f"[Reporter]: ✓ Report saved: {self.writer.path}")
        except:
            print(f"[Reporter]: ✓ Report saved.")