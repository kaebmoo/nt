import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

class FullAuditDetector:
    def __init__(self, df):
        self.df = df.copy()

    # ---------------------------------------------------------
    # แบบที่ 1: ตรวจสอบประวัติย้อนหลังทั้งหมด (Time Series)
    # "Product A มีเดือนไหนผิดปกติบ้าง ตั้งแต่อดีตจนถึงปัจจุบัน"
    # ---------------------------------------------------------
    def check_time_series_all_months(self, target_col, date_col, dimension_cols, window=3):
        print(f"🔍 กำลังตรวจสอบประวัติย้อนหลังของแต่ละรายการ (Rolling Window {window} เดือน)...")
        
        results = []
        
        # จัดกลุ่มตาม Product/Service (Dimension)
        # สร้าง ID ชั่วคราวเพื่อวนลูป
        self.df['TEMP_ID'] = self.df[dimension_cols].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        
        for item_id, group_data in self.df.groupby('TEMP_ID'):
            # เรียงตามเวลาให้ถูกต้อง
            group_data = group_data.sort_values(date_col)
            
            # วนลูปตรวจทีละเดือน (เริ่มตั้งแต่เดือนที่ window + 1)
            values = group_data[target_col].values
            dates = group_data[date_col].values
            
            for i in range(window, len(group_data)):
                current_val = values[i]
                current_date = dates[i]
                
                # ดึงประวัติย้อนหลังตาม window ที่กำหนด (เช่น 3 เดือนก่อนหน้า)
                history = values[i-window : i]
                
                # ตรวจสอบด้วย IQR (เหมือนเดิมแต่ทำเป็น Loop)
                status = self._detect_iqr(current_val, history)
                
                if status != 'Normal':
                    row_result = group_data.iloc[i].to_dict()
                    row_result['ANOMALY_TYPE'] = 'Time_Series' # ระบุว่าเป็นความผิดปกติเทียบกับเวลา
                    row_result['ISSUE'] = status
                    row_result['COMPARED_WITH'] = f"Avg Past {window} Months: {np.mean(history):.2f}"
                    results.append(row_result)
                    
        return pd.DataFrame(results)

    # ---------------------------------------------------------
    # แบบที่ 2: ตรวจสอบเทียบกลุ่มเพื่อน (Peer Group)
    # "ในเดือนนี้ มีหน่วยงานไหนจ่ายค่าซ่อมแพงกว่าชาวบ้าน"
    # ---------------------------------------------------------
    def check_peer_group(self, target_col, date_col, group_by_cols):
        print(f"👥 กำลังตรวจสอบเปรียบเทียบกลุ่ม (Peer Comparison)...")
        
        results = []
        
        # วนลูปทีละเดือน (เพราะเราเทียบเพื่อนในเดือนเดียวกัน)
        unique_months = self.df[date_col].unique()
        
        for month in unique_months:
            month_data = self.df[self.df[date_col] == month].copy()
            
            if len(month_data) < 3: continue # ถ้าข้อมูลน้อยไปเทียบไม่ได้
            
            # เตรียมข้อมูลสำหรับคำนวณ (Z-Score หรือ Isolation Forest)
            values = month_data[target_col].values.reshape(-1, 1)
            
            # ใช้ Isolation Forest (เหมาะกับหาตัวที่แปลกแยกจากกลุ่ม)
            clf = IsolationForest(contamination=0.05, random_state=42)
            preds = clf.fit_predict(values) # -1 คือผิดปกติ
            
            # หรือจะใช้ Z-Score ง่ายๆ
            mean_val = np.mean(month_data[target_col])
            std_val = np.std(month_data[target_col])
            
            # หาบรรทัดที่ผิดปกติ
            anomalies = month_data[preds == -1]
            
            for _, row in anomalies.iterrows():
                # Double check ด้วย Z-Score เพื่อความชัวร์ว่าสูงหรือต่ำ
                z_score = (row[target_col] - mean_val) / std_val if std_val > 0 else 0
                
                issue_type = "High_vs_Peers" if row[target_col] > mean_val else "Low_vs_Peers"
                
                row_result = row.to_dict()
                row_result['ANOMALY_TYPE'] = 'Peer_Group' # ระบุว่าเป็นความผิดปกติเทียบกับเพื่อน
                row_result['ISSUE'] = issue_type
                row_result['COMPARED_WITH'] = f"Group Avg: {mean_val:.2f} (Z={z_score:.2f})"
                results.append(row_result)
                
        return pd.DataFrame(results)

    def _detect_iqr(self, current, history):
        """ฟังก์ชันคำนวณ IQR เดิมของคุณ"""
        # กรองค่า 0 หรือติดลบออกก่อนคำนวณ Baseline (ตามความต้องการ)
        history_clean = history[history > 0]
        if len(history_clean) == 0: return "Normal"
        
        Q1 = np.percentile(history_clean, 25)
        Q3 = np.percentile(history_clean, 75)
        IQR = Q3 - Q1
        
        if IQR == 0: return "Normal"
        
        k = 1.5
        upper = Q3 + (k * IQR)
        lower = Q1 - (k * IQR)
        
        if current > upper: return "High_Spike"
        # ถ้าต่ำกว่า 0 ปกติ IQR จะมองว่าเป็น Low แต่บัญชีอาจจะมองเป็นเรื่องปกติ
        # คุณอาจจะปรับ Logic ตรงนี้ได้
        if current < lower and current > 0: return "Low_Drop" 
        
        return "Normal"

# =========================================
# วิธีเรียกใช้งาน
# =========================================
#สมมติ df มีคอลัมน์: MONTH, DEPT_NAME, EXPENSE_TYPE, AMOUNT

# detector = FullAuditDetector(df)

# 1. อยากรู้ว่า "แผนก IT" เคยมีค่าซ่อมคอมเดือนไหนพุ่งผิดปกติบ้าง (เทียบตัวเอง)
# ts_anomalies = detector.check_time_series_all_months(
#     target_col='AMOUNT', 
#     date_col='MONTH', 
#     dimension_cols=['DEPT_NAME', 'EXPENSE_TYPE'],
#     window=6 # เทียบกับ 6 เดือนก่อนหน้า
# )

# 2. อยากรู้ว่า "เดือน ก.ย." แผนกไหนเบิกค่าเดินทางเยอะกว่าแผนกอื่น (เทียบเพื่อน)
# peer_anomalies = detector.check_peer_group(
#     target_col='AMOUNT',
#     date_col='MONTH',
#     group_by_cols=['EXPENSE_TYPE'] # เทียบในหมวดค่าใช้จ่ายเดียวกัน
# )

# 3. เอามารวมกันดู
# all_issues = pd.concat([ts_anomalies, peer_anomalies])
# print(all_issues)