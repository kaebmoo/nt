import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

class CrosstabGenerator:
    """Class นี้สร้าง 'Crosstab Report' (สถานะเดือนล่าสุด)"""
    def __init__(self, df, min_history=3):
        self.df = df.copy()
        # FIX: Check if dataframe is empty or missing the column before sorting
        if not self.df.empty and '__date_col__' in self.df.columns:
            self.df.sort_values(by='__date_col__', inplace=True)
            
        self.min_history = min_history
        self.date_cols_sorted = []
        print("[Engine]: CrosstabGenerator Initialized.")

    def create_report(self, target_col, date_col, dimensions):
        print(f"[Engine]: Creating Crosstab Report for '{target_col}'...")
        if self.df.empty: return pd.DataFrame() # Safety check

        agg_df = self.df.groupby(dimensions + [date_col])[target_col].sum().reset_index()
        crosstab = agg_df.pivot_table(
            index=dimensions, columns=date_col, values=target_col, fill_value=0
        )
        crosstab.columns = [col.strftime('%Y-%m') for col in crosstab.columns]
        self.date_cols_sorted = sorted(crosstab.columns)
        if not self.date_cols_sorted: return pd.DataFrame()

        report_data = crosstab.apply(
            lambda row: self._get_status_helper(row[self.date_cols_sorted], self.min_history),
            axis=1, result_type='expand'
        )
        report_data.columns = ['ANOMALY_STATUS', 'LATEST_VALUE', 'AVG_HISTORICAL']
        final_report = pd.concat([crosstab, report_data], axis=1)
        final_report['PCT_CHANGE'] = ((final_report['LATEST_VALUE'] - final_report['AVG_HISTORICAL']) / 
                                      final_report['AVG_HISTORICAL'].replace(0, np.nan) * 100).fillna(0)
        return final_report.reset_index()

    def _get_status_helper(self, row_series, min_history):
        """Helper: ตรวจสอบสถานะ 7 แบบ (ปรับปรุงใหม่: ใส่ Threshold กัน Sensitive เกินไป)"""
        latest_val = row_series.iloc[-1]
        history = row_series.iloc[:-1]
        
        if latest_val < 0: return "Negative_Value", latest_val, 0
        
        history_clean = history[history > 0]
        if len(history_clean) < min_history:
            return ("New_Item" if latest_val > 0 else "Not_Enough_Data"), latest_val, 0
        
        avg_historical = history_clean.mean()
        
        # --- ส่วนที่เพิ่ม Logic เพื่อแก้ปัญหา ---
        # คำนวณ % การเปลี่ยนแปลงเทียบกับค่าเฉลี่ย
        if avg_historical == 0: pct_change = 0
        else: pct_change = abs((latest_val - avg_historical) / avg_historical)
        
        # 1. ถ้าเปลี่ยนน้อยกว่า 10% (0.10) ให้ปล่อยผ่านเป็น Normal เลย (แก้ปัญหาแดงทั้งกระดาน)
        if pct_change < 0.10: 
             return "Normal", latest_val, avg_historical
        # ------------------------------------

        Q1, Q3 = history_clean.quantile(0.25), history_clean.quantile(0.75)
        IQR = Q3 - Q1
        
        # Logic เดิม...
        if IQR == 0:
            if Q1 == 0 and latest_val > 0: return "High_Spike", latest_val, avg_historical
            if latest_val != Q1: return "Spike_vs_Constant", latest_val, avg_historical
            return "Normal", latest_val, avg_historical
        
        k = 1.5
        lower_fence = max(0, Q1 - (k * IQR))
        upper_fence = Q3 + (k * IQR)
        
        if latest_val > upper_fence: return "High_Spike", latest_val, avg_historical
        if latest_val < lower_fence: return "Low_Spike", latest_val, avg_historical
        
        return "Normal", latest_val, avg_historical

class FullAuditEngine:
    """Class นี้ Audit ข้อมูล 'ทั้งหมด' (Rolling & IsolationForest)"""
    def __init__(self, df):
        self.df = df.copy()
        if '__date_col__' in self.df.columns:
            self.df.sort_values(by='__date_col__', inplace=True)
        print("[Engine]: FullAuditEngine Initialized.")
        # ยืม Logic การตรวจจับจาก Crosstab มาใช้
        self.status_helper = CrosstabGenerator(pd.DataFrame())._get_status_helper

    def audit_time_series_all_months(self, target_col, date_col, dimensions, window=3):
        """Rolling Window Scan"""
        print("[Engine]: Running Full Time Series (Rolling Window)...")
        results = []
        try:
            self.df['__TEMP_ID__'] = self.df[dimensions].apply(lambda x: '|'.join(x.astype(str)), axis=1)
        except Exception as e:
            print(f"   ❌ Error creating Temp ID: {e}"); return pd.DataFrame()

        for item_id, group in self.df.groupby('__TEMP_ID__'):
            ts = group.set_index(date_col)[target_col]
            for i in range(window, len(ts)):
                current_window_series = ts.iloc[i-window : i+1]
                # ตรวจสอบสถานะ
                status, _, avg_hist = self.status_helper(current_window_series, 1) 

                if status not in ['Normal', 'Not_Enough_Data']:
                    row_res = group.iloc[i].to_dict()
                    row_res['ANOMALY_TYPE'] = 'Time_Series_Roll'
                    row_res['ISSUE_DESC'] = status
                    row_res['COMPARED_WITH'] = f"Avg Past {window} periods: {avg_hist:,.2f}"
                    results.append(row_res)     
        return pd.DataFrame(results)

    def audit_peer_group_all_months(self, target_col, date_col, group_dims, item_id_col):
        """Isolation Forest Scan"""
        print("[Engine]: Running Full Peer Group (IsolationForest)...")
        results = []
        for d in self.df[date_col].unique():
            period_data = self.df[self.df[date_col] == d].copy()
            if group_dims:
                try: period_data['__GRP_ID__'] = period_data[group_dims].apply(lambda x: '|'.join(x.astype(str)), axis=1)
                except: continue
            else: period_data['__GRP_ID__'] = 'ALL'

            for grp_id, batch in period_data.groupby('__GRP_ID__'):
                if len(batch) < 5: continue
                X = batch[target_col].values.reshape(-1, 1)
                clf = IsolationForest(contamination=0.05, random_state=42)
                preds = clf.fit_predict(X)
                mean_val, std_val = np.mean(batch[target_col]), np.std(batch[target_col])
                
                for _, row in batch[preds == -1].iterrows():
                    z = (row[target_col] - mean_val) / std_val if std_val > 0 else 0
                    if abs(z) > 2.0:
                        row_res = row.to_dict()
                        row_res['ANOMALY_TYPE'] = 'Peer_Group_ISO'
                        row_res['ISSUE_DESC'] = "High Outlier (vs Peers)" if z > 0 else "Low Outlier (vs Peers)"
                        row_res['COMPARED_WITH'] = f"Group Avg: {mean_val:,.2f} (Z={z:.2f})"
                        results.append(row_res)
        return pd.DataFrame(results)