import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

try:
    from .anomaly_settings import DEFAULT_ANOMALY_SETTINGS, normalize_anomaly_settings
    from .data_cleaning import apply_date_grain, format_date_label
except ImportError:
    from anomaly_settings import DEFAULT_ANOMALY_SETTINGS, normalize_anomaly_settings
    from data_cleaning import apply_date_grain, format_date_label

K = DEFAULT_ANOMALY_SETTINGS["iqr_k"]  # Backward-compatible default


def detect_iqr_anomaly(value, history, min_history=3, anomaly_settings=None):
    settings = normalize_anomaly_settings(anomaly_settings)
    latest_val = pd.to_numeric(pd.Series([value]), errors='coerce').fillna(0).iloc[0]
    if latest_val < 0:
        return "Negative_Value", latest_val, 0

    history_clean = pd.to_numeric(pd.Series(history), errors='coerce').dropna()
    history_clean = history_clean[history_clean > 0]
    if len(history_clean) < min_history:
        return ("New_Item" if latest_val > 0 else "Not_Enough_Data"), latest_val, 0

    avg_historical = history_clean.mean()
    pct_change = 0 if avg_historical == 0 else abs((latest_val - avg_historical) / avg_historical)

    if pct_change < settings["min_change_ratio"]:
        return "Normal", latest_val, avg_historical

    Q1, Q3 = history_clean.quantile(0.25), history_clean.quantile(0.75)
    IQR = Q3 - Q1

    if IQR == 0:
        if pct_change < settings["constant_change_ratio"]:
            return "Normal", latest_val, avg_historical
        if Q1 == 0 and latest_val > 0:
            return "High_Spike", latest_val, avg_historical
        if latest_val != Q1:
            return "Spike_vs_Constant", latest_val, avg_historical
        return "Normal", latest_val, avg_historical

    k = settings["iqr_k"]
    lower_fence = max(0, Q1 - (k * IQR))
    upper_fence = Q3 + (k * IQR)

    if latest_val > upper_fence:
        return "High_Spike", latest_val, avg_historical
    if latest_val < lower_fence:
        return "Low_Spike", latest_val, avg_historical

    return "Normal", latest_val, avg_historical


class CrosstabGenerator:
    """Class นี้สร้าง 'Crosstab Report' (สถานะเดือนล่าสุด)"""
    def __init__(self, df, min_history=3, anomaly_settings=None):
        self.df = df.copy()
        # FIX: Check if dataframe is empty or missing the column before sorting
        if not self.df.empty and '__date_col__' in self.df.columns:
            self.df.sort_values(by='__date_col__', inplace=True)
            
        self.min_history = min_history
        self.anomaly_settings = normalize_anomaly_settings(anomaly_settings)
        self.date_grain = self.anomaly_settings["date_grain"]
        self.date_cols_sorted = []
        print("[Engine]: CrosstabGenerator Initialized.")

    def create_report(self, target_col, date_col, dimensions):
        print(f"[Engine]: Creating Crosstab Report for '{target_col}'...")
        if self.df.empty: return pd.DataFrame() # Safety check

        df_calc = self.df.copy()
        df_calc[date_col] = apply_date_grain(df_calc[date_col], self.date_grain)
        agg_df = df_calc.groupby(dimensions + [date_col])[target_col].sum().reset_index()
        crosstab = agg_df.pivot_table(
            index=dimensions, columns=date_col, values=target_col, fill_value=0
        )
        crosstab.columns = [format_date_label(col, self.date_grain) for col in crosstab.columns]
        self.date_cols_sorted = sorted(crosstab.columns)
        if not self.date_cols_sorted: return pd.DataFrame()

        report_data = crosstab.apply(
            lambda row: self._get_status_helper(row[self.date_cols_sorted], self.min_history),
            axis=1, result_type='expand'
        )
        report_data.columns = ['ANOMALY_STATUS', 'LATEST_VALUE', 'AVG_HISTORICAL']
        final_report = pd.concat([crosstab, report_data], axis=1)
        if len(self.date_cols_sorted) >= 2:
            final_report['PREVIOUS_VALUE'] = crosstab[self.date_cols_sorted[-2]]
        else:
            final_report['PREVIOUS_VALUE'] = 0
        final_report['DIFF_PREVIOUS'] = final_report['LATEST_VALUE'] - final_report['PREVIOUS_VALUE']
        final_report['PCT_DIFF_PREVIOUS'] = (
            final_report['DIFF_PREVIOUS'] / final_report['PREVIOUS_VALUE'].replace(0, np.nan) * 100
        ).fillna(0)
        final_report['PCT_CHANGE'] = ((final_report['LATEST_VALUE'] - final_report['AVG_HISTORICAL']) / 
                                      final_report['AVG_HISTORICAL'].replace(0, np.nan) * 100).fillna(0)
        return final_report.reset_index()

    def _get_status_helper(self, row_series, min_history):
        """Helper: ตรวจสอบสถานะ 7 แบบ (ปรับปรุงใหม่: ใส่ Threshold กัน Sensitive เกินไป)"""
        return detect_iqr_anomaly(row_series.iloc[-1], row_series.iloc[:-1], min_history, self.anomaly_settings)

class FullAuditEngine:
    """Class นี้ Audit ข้อมูล 'ทั้งหมด' (Rolling & IsolationForest)"""
    def __init__(self, df, anomaly_settings=None):
        self.df = df.copy()
        if '__date_col__' in self.df.columns:
            self.df.sort_values(by='__date_col__', inplace=True)
        self.anomaly_settings = normalize_anomaly_settings(anomaly_settings)
        print("[Engine]: FullAuditEngine Initialized.")
        # ยืม Logic การตรวจจับจาก Crosstab มาใช้
        self.status_helper = CrosstabGenerator(pd.DataFrame(), anomaly_settings=self.anomaly_settings)._get_status_helper

    def audit_time_series_all_months(self, target_col, date_col, dimensions, window=3):
        """
        Rolling Window Scan (Optimized Vectorized Version v2)
        * Update: เพิ่มการ Group By เพื่อตรวจสอบยอดรวมรายเดือน (แก้ปัญหา Transaction ย่อย)
        """
        print(f"[Engine]: Running Full Time Series (Vectorized Rolling Window={window})...")
        
        # 1. เตรียมข้อมูล 
        # ❌ ลบอันเก่า: df_calc = self.df.copy()
        
        # ✅ ใช้อันใหม่: ยุบรวมยอดขายรายเดือนก่อนเริ่มคำนวณ
        # เพื่อให้ Engine มองเห็นยอด Net ของเดือนนั้นจริงๆ
        df_base = self.df.copy()
        date_grain = self.anomaly_settings["date_grain"]
        df_base[date_col] = apply_date_grain(df_base[date_col], date_grain)
        df_calc = df_base.groupby(dimensions + [date_col])[target_col].sum().reset_index()
        
        # Validation: ตรวจสอบว่ามี columns ที่จำเป็น
        required_cols = dimensions + [date_col, target_col]
        missing = [c for c in required_cols if c not in df_calc.columns]
        if missing:
            print(f"   ❌ Missing columns: {missing}")
            return pd.DataFrame()
        
        # สร้าง ID ชั่วคราวสำหรับ Group
        try:
            df_calc['__GRP_ID__'] = df_calc[dimensions].apply(
                lambda x: '|'.join(x.astype(str)), axis=1
            )
        except Exception as e:
            print(f"   ❌ Error creating Temp ID: {e}")
            return pd.DataFrame()
        
        # ต้องเรียงข้อมูลตาม กลุ่ม และ วันที่ ให้เป๊ะก่อนคำนวณ Rolling
        df_calc.sort_values(by=['__GRP_ID__', date_col], inplace=True)
        df_calc.reset_index(drop=True, inplace=True)  # ← สำคัญ! reset index ก่อน
        
        # 2. คำนวณ Rolling Stats
        # ใช้ min_periods=window เพื่อให้แน่ใจว่ามีข้อมูลครบก่อนคำนวณ
        # แต่ให้ยืดหยุ่นเล็กน้อย โดยใช้ max(1, window-1)
        min_periods_safe = max(1, window - 1)

        # ✅ ใช้ transform() แทน reset_index() เพื่อรับประกันว่า index ตรงกับ df_calc
        # transform() จะ maintain index ของ original dataframe โดยอัตโนมัติ
        # และไม่มีความเสี่ยงเรื่อง index misalignment

        # คำนวณค่าทางสถิติของ "window เดือนก่อนหน้า" (ไม่รวมเดือนปัจจุบัน)
        # shift(1) จะทำให้ค่า stats ของแถวนี้ มาจาก window เดือนที่แล้ว
        df_calc['HIST_MEAN'] = df_calc.groupby('__GRP_ID__', group_keys=False)[target_col].transform(
            lambda x: x.rolling(window=window, min_periods=min_periods_safe).mean().shift(1)
        ).fillna(0)

        df_calc['HIST_COUNT'] = df_calc.groupby('__GRP_ID__', group_keys=False)[target_col].transform(
            lambda x: x.rolling(window=window, min_periods=min_periods_safe).count().shift(1)
        ).fillna(0)

        df_calc['HIST_Q1'] = df_calc.groupby('__GRP_ID__', group_keys=False)[target_col].transform(
            lambda x: x.rolling(window=window, min_periods=min_periods_safe).quantile(0.25).shift(1)
        ).fillna(0)

        df_calc['HIST_Q3'] = df_calc.groupby('__GRP_ID__', group_keys=False)[target_col].transform(
            lambda x: x.rolling(window=window, min_periods=min_periods_safe).quantile(0.75).shift(1)
        ).fillna(0)

        df_calc['HIST_IQR'] = df_calc['HIST_Q3'] - df_calc['HIST_Q1']
        
        # 3. คำนวณ PCT_CHANGE (ป้องกัน division by zero)
        df_calc['PCT_CHANGE'] = 0.0
        mask_mean_nonzero = df_calc['HIST_MEAN'] > 0  # ← เปลี่ยนจาก != เป็น >
        df_calc.loc[mask_mean_nonzero, 'PCT_CHANGE'] = abs(
            (df_calc.loc[mask_mean_nonzero, target_col] - df_calc.loc[mask_mean_nonzero, 'HIST_MEAN']) 
            / df_calc.loc[mask_mean_nonzero, 'HIST_MEAN']
        )
        
        # 4. คำนวณ Fences (IQR Method)
        k = self.anomaly_settings["iqr_k"]  # Sensitivity (1.5 = strict, 2.0 = moderate, 3.0 = relaxed)
        df_calc['UPPER_FENCE'] = df_calc['HIST_Q3'] + (k * df_calc['HIST_IQR'])
        df_calc['LOWER_FENCE'] = (df_calc['HIST_Q1'] - (k * df_calc['HIST_IQR'])).clip(lower=0)
        
        # 5. ตัดสินสถานะ (ใช้ np.select เพื่อความเร็ว)
        conditions = [
            # Case 0: ค่าติดลบ
            (df_calc[target_col] < 0),
            
            # Case 1: ข้อมูลประวัติไม่พอ (น้อยกว่า window-1 เดือน)
            # หมายเหตุ: ใช้ window-1 เพื่อให้ยืดหยุ่นเล็กน้อย
            (df_calc['HIST_COUNT'] < (window - 1)),
            
            # Case 2: เปลี่ยนแปลงน้อยกว่า threshold -> Normal
            (df_calc['PCT_CHANGE'] < self.anomaly_settings["min_change_ratio"]),
            
            # Case 3: IQR = 0 (ประวัตินิ่งสนิท) แต่เปลี่ยนไม่ถึง threshold -> Normal
            ((df_calc['HIST_IQR'] == 0) & (df_calc['PCT_CHANGE'] < self.anomaly_settings["constant_change_ratio"])),
            
            # Case 4: IQR = 0 แต่ Q1=0 แล้วมียอดเด้งขึ้นมา -> High Spike
            ((df_calc['HIST_IQR'] == 0) & (df_calc['HIST_Q1'] == 0) & (df_calc[target_col] > 0)),
            
            # Case 5: IQR = 0 แต่ค่าไม่เท่าเดิม -> Spike vs Constant
            ((df_calc['HIST_IQR'] == 0) & (df_calc[target_col] != df_calc['HIST_Q1'])),
            
            # Case 6: ทะลุเพดานบน -> High Spike
            (df_calc[target_col] > df_calc['UPPER_FENCE']),
            
            # Case 7: ทะลุพื้นล่าง -> Low Spike
            (df_calc[target_col] < df_calc['LOWER_FENCE'])
        ]
        
        choices = [
            'Negative_Value',       # 0
            'Not_Enough_Data',      # 1
            'Normal',               # 2
            'Normal',               # 3
            'High_Spike',           # 4
            'Spike_vs_Constant',    # 5
            'High_Spike',           # 6
            'Low_Spike'             # 7
        ]
        
        df_calc['ISSUE_DESC'] = np.select(conditions, choices, default='Normal')
        
        # จัดการ New Item เพิ่มเติม (ถ้าข้อมูลไม่พอ แต่มียอด > 0)
        mask_new_item = (df_calc['ISSUE_DESC'] == 'Not_Enough_Data') & (df_calc[target_col] > 0)
        df_calc.loc[mask_new_item, 'ISSUE_DESC'] = 'New_Item'
        
        # 6. กรองเฉพาะตัวที่มีปัญหา
        anomalies = df_calc[
            ~df_calc['ISSUE_DESC'].isin(['Normal', 'Not_Enough_Data'])
        ].copy()
        
        if anomalies.empty:
            print("[Engine]:    ✓ No anomalies found in Time Series scan.")
            return pd.DataFrame()
        
        # 7. จัดเตรียม Output
        anomalies['ANOMALY_TYPE'] = 'Time_Series_Roll'
        anomalies['COMPARED_WITH'] = anomalies.apply(
            lambda row: f"Avg Past {window}: {row['HIST_MEAN']:,.2f} (Count: {int(row['HIST_COUNT'])})",
            axis=1
        )
        
        # ลบ Column ชั่วคราวออก
        cols_to_drop = ['__GRP_ID__', 'HIST_MEAN', 'HIST_COUNT', 'HIST_Q1', 'HIST_Q3', 
                        'HIST_IQR', 'PCT_CHANGE', 'UPPER_FENCE', 'LOWER_FENCE']
        anomalies.drop(columns=[c for c in cols_to_drop if c in anomalies.columns], 
                    inplace=True, errors='ignore')
        
        print(f"[Engine]:    ✓ Found {len(anomalies)} anomalies in Time Series scan.")
        return anomalies

    def audit_peer_group_all_months(self, target_col, date_col, group_dims, item_id_col):
        """Isolation Forest Scan"""
        print("[Engine]: Running Full Peer Group (IsolationForest)...")
        results = []
        peer_min_group_size = self.anomaly_settings["peer_min_group_size"]
        peer_contamination = self.anomaly_settings["peer_contamination"]
        peer_zscore_threshold = self.anomaly_settings["peer_zscore_threshold"]
        df_base = self.df.copy()
        df_base[date_col] = apply_date_grain(df_base[date_col], self.anomaly_settings["date_grain"])
        for d in df_base[date_col].unique():
            period_data = df_base[df_base[date_col] == d].copy()
            if group_dims:
                try: period_data['__GRP_ID__'] = period_data[group_dims].apply(lambda x: '|'.join(x.astype(str)), axis=1)
                except: continue
            else: period_data['__GRP_ID__'] = 'ALL'

            for grp_id, batch in period_data.groupby('__GRP_ID__'):
                if len(batch) < peer_min_group_size: continue
                X = batch[target_col].values.reshape(-1, 1)
                clf = IsolationForest(contamination=peer_contamination, random_state=42)
                preds = clf.fit_predict(X)
                mean_val, std_val = np.mean(batch[target_col]), np.std(batch[target_col])
                
                for _, row in batch[preds == -1].iterrows():
                    z = (row[target_col] - mean_val) / std_val if std_val > 0 else 0
                    if abs(z) > peer_zscore_threshold:
                        row_res = row.to_dict()
                        row_res['ANOMALY_TYPE'] = 'Peer_Group_ISO'
                        row_res['ISSUE_DESC'] = "High Outlier (vs Peers)" if z > 0 else "Low Outlier (vs Peers)"
                        row_res['COMPARED_WITH'] = f"Group Avg: {mean_val:,.2f} (Z={z:.2f})"
                        results.append(row_res)
        return pd.DataFrame(results)
