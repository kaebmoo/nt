# https://stackoverflow.com/questions/18039057/python-pandas-error-tokenizing-data

import pandas as pd
from pathlib import Path
pd.options.display.float_format = '{:,.2f}'.format

# --- 1. การตั้งค่า (Configuration) ---
input_path = "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/Datasource/2025/fi/"
output_path = "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/Datasource/2025/fi/output/"
master_path = "/Users/seal/Library/CloudStorage/OneDrive-Personal/share/master/source/"

input_files = ["pld_nt_20251031.txt"]

# ชื่อไฟล์ Master
master_expense_file = "MASTER_EXPENSE_GL_CODE_NT1_NT_20251028.csv"
master_revenue_file = "MASTER_REVENUE_GL_CODE_NT1_NT_20250723.csv"
# (ใหม่) Master files สำหรับการวิเคราะห์นี้
master_other_rev_file = "MASTER_OTHER_REVENUE_NET.csv"
master_rev_exp_net_file = "master_revenue_expense_net.csv"


# ชื่อไฟล์ Output
output_excel_file = "pl_combined_output_202510.xlsx"
output_csv_expense = "pl_expense_nt_output_202510.csv"
output_csv_revenue = "pl_revenue_nt_output_202510.csv"

# สร้างโฟลเดอร์ output หากยังไม่มี
Path(output_path).mkdir(parents=True, exist_ok=True)

# --- 2. โหลดไฟล์ Master (Load Master Files) ---

# โหลด Master Expense
master_expense_gl = pd.read_csv(master_path + master_expense_file, encoding="utf8")
master_expense_gl = master_expense_gl[["CODE_GROUP", "GROUP_NAME", "GL_CODE_NT1", "GL_NAME_NT1"]]
master_expense_gl = master_expense_gl.rename(columns={"GL_CODE_NT1": "GL_CODE", "GL_NAME_NT1": "GL_NAME"})
master_expense_gl["GL_CODE"] = master_expense_gl["GL_CODE"].astype(str)

# โหลด Master Revenue
master_revenue_gl = pd.read_csv(master_path + master_revenue_file, encoding="utf8")
master_revenue_gl = master_revenue_gl[["REPORT_CODE", "GL_GROUP", "GL_CODE_NT1", "GL_NAME_NT1"]]
master_revenue_gl = master_revenue_gl.rename(columns={"GL_CODE_NT1": "GL_CODE", "GL_NAME_NT1": "GL_NAME"})
master_revenue_gl["GL_CODE"] = master_revenue_gl["GL_CODE"].astype(str)


# --- (ใหม่) 3. ฟังก์ชันสำหรับประมวลผลรายได้/ค่าใช้จ่ายอื่น (Logic 3.0) ---
def process_financial_and_other(of_revenue, gl_group_expense, master_path):
    """
    ประมวลผลส่วนของผลตอบแทนทางการเงิน, รายได้อื่น, และค่าใช้จ่ายอื่น
    (ปรับปรุงตามลอจิกใหม่)
    """
    print("\n" + "="*80)
    print("Starting 'process_financial_and_other' (New Logic)")
    print("="*80)
    
    try:
        # --- Step 1: สร้างข้อมูล R (รายได้ที่อยู่ใน MASTER_OTHER_REVENUE_NET) ---
        print("\n--- Step 1: สร้างข้อมูล R ---")
        master_other_rev = pd.read_csv(master_path + master_other_rev_file)
        master_other_rev.columns = master_other_rev.columns.str.strip()
        
        # ทำความสะอาด GL_GROUP
        if 'GL_GROUP' in master_other_rev.columns:
            master_other_rev['GL_GROUP'] = master_other_rev['GL_GROUP'].astype(str).str.replace(r'["\r\n]', '', regex=True).str.strip()
        else:
            raise KeyError("Column 'GL_GROUP' not found in " + master_other_rev_file)
            
        master_other_rev['GL_CODE'] = master_other_rev['GL_CODE'].astype(str)
        
        # Merge เพื่อคัดเฉพาะ GL_CODE ที่อยู่ใน Master
        data_R = pd.merge(of_revenue, master_other_rev, on='GL_CODE', how='inner')
        print(f"✓ สร้าง Data R เรียบร้อย: {len(data_R)} รายการ")
        
        # --- Step 2: สร้างข้อมูล F (ผลตอบแทนทางการเงิน) ---
        print("\n--- Step 2: สร้างข้อมูล F (ผลตอบแทนทางการเงิน) ---")
        data_F = data_R[data_R['GL_GROUP'] == 'ผลตอบแทนทางการเงิน'].copy()
        
        # Log รายการก่อน sum
        print(f"รายการผลตอบแทนทางการเงิน ({len(data_F)} รายการ):")
        for idx, row in data_F.iterrows():
            print(f"  - GL_CODE: {row['GL_CODE']}, GL_NAME: {row['GL_NAME']}")
            print(f"    เดือน: {row['REVENUE_VALUE']:>15,.2f}, สะสม: {row['REVENUE_VALUE_YTD']:>15,.2f}")
        
        # เปลี่ยนชื่อ column GL_GROUP เป็น GROUP
        data_F = data_F.rename(columns={
            'GL_GROUP': 'GROUP',
            'REVENUE_VALUE': 'VALUE',
            'REVENUE_VALUE_YTD': 'VALUE_YTD'
        })
        
        # Sum รวม
        f_month = data_F['VALUE'].sum()
        f_ytd = data_F['VALUE_YTD'].sum()
        print(f"\n✓ ผลรวม F: เดือน = {f_month:,.2f}, สะสม = {f_ytd:,.2f}")
        
        # --- Step 3: สร้างข้อมูล E (ค่าใช้จ่ายอื่น จาก gl_group_expense) ---
        print("\n--- Step 3: สร้างข้อมูล E (ค่าใช้จ่ายอื่น) ---")
        data_E = gl_group_expense[gl_group_expense['GROUP_NAME'] == 'ค่าใช้จ่ายอื่น'].copy()
        
        # Log รายการก่อนคูณ -1
        print(f"รายการค่าใช้จ่ายอื่น ({len(data_E)} รายการ) ก่อนคูณ -1:")
        for idx, row in data_E.iterrows():
            print(f"  - GL_CODE: {row['GL_CODE']}, GL_NAME: {row['GL_NAME']}")
            print(f"    เดือน: {row['EXPENSE_VALUE']:>15,.2f}, สะสม: {row['EXPENSE_VALUE_YTD']:>15,.2f}")
        
        # คูณ -1
        data_E['VALUE'] = data_E['EXPENSE_VALUE'] * -1
        data_E['VALUE_YTD'] = data_E['EXPENSE_VALUE_YTD'] * -1
        
        print(f"\nหลังคูณ -1:")
        for idx, row in data_E.iterrows():
            print(f"  - GL_CODE: {row['GL_CODE']}, เดือน: {row['VALUE']:>15,.2f}, สะสม: {row['VALUE_YTD']:>15,.2f}")
        
        # เลือกเฉพาะ columns ที่ต้องการ
        data_E_final = data_E[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()
        
        # --- Step 4: สร้างข้อมูล RE (รวม R กับ E) ---
        print("\n--- Step 4: สร้างข้อมูล RE (รวม R + E) ---")
        # เปลี่ยนชื่อ columns ของ R ให้ตรงกัน
        data_R_renamed = data_R.rename(columns={
            'REVENUE_VALUE': 'VALUE',
            'REVENUE_VALUE_YTD': 'VALUE_YTD'
        })
        
        # เลือกเฉพาะ columns ที่ต้องการจาก R
        data_R_for_concat = data_R_renamed[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()
        
        # รวม R กับ E
        data_RE = pd.concat([data_R_for_concat, data_E_final], ignore_index=True)
        print(f"✓ สร้าง Data RE: {len(data_RE)} รายการ (R: {len(data_R_for_concat)}, E: {len(data_E_final)})")
        
        # --- Step 5: สร้างข้อมูล RE_OTHER (Merge กับ master_revenue_expense_net) ---
        print("\n--- Step 5: สร้างข้อมูล RE_OTHER ---")
        master_rev_exp_net = pd.read_csv(master_path + master_rev_exp_net_file)
        master_rev_exp_net.columns = master_rev_exp_net.columns.str.strip()
        
        # ทำความสะอาด GROUP
        if 'GROUP' in master_rev_exp_net.columns:
            master_rev_exp_net['GROUP'] = master_rev_exp_net['GROUP'].astype(str).str.replace(r'["\r\n]', '', regex=True).str.strip()
        else:
            raise KeyError("Column 'GROUP' not found in " + master_rev_exp_net_file)
            
        master_rev_exp_net['GL_CODE'] = master_rev_exp_net['GL_CODE'].astype(str)
        
        
        # Merge (inner join - เอาเฉพาะที่ GL_CODE ตรงกัน)
        data_RE_OTHER = pd.merge(data_RE, master_rev_exp_net[["GL_CODE", "SUB_GROUP", "GROUP"]], on='GL_CODE', how='inner')
        print(f"✓ สร้าง Data RE_OTHER: {len(data_RE_OTHER)} รายการ")
        print(data_RE_OTHER.sum(numeric_only=True))
        
        # --- Step 6: แยกข้อมูล R_OTHER (รายได้อื่น) ---
        print("\n--- Step 6: แยกข้อมูล R_OTHER (GROUP = รายได้อื่น) ---")
        data_R_OTHER = data_RE_OTHER[data_RE_OTHER['GROUP'] == 'รายได้อื่น'].copy()
        print(f"✓ พบข้อมูล R_OTHER: {len(data_R_OTHER)} รายการ")
        # print(data_R_OTHER)
        print(data_R_OTHER.groupby('GROUP').sum(numeric_only=True))
        
        data_R_OTHER = data_R_OTHER.groupby(['GROUP', 'SUB_GROUP'], dropna=False).agg({
            'GL_CODE': 'first',  # เอา GL_CODE แรก (หรือจะใช้วิธีอื่นก็ได้)
            'GL_NAME': 'first',  # เอา GL_NAME แรก
            'VALUE': 'sum',
            'VALUE_YTD': 'sum'
        }).reset_index()


        # --- Step 7: สร้าง R_OTHER_NET และ R_OTHER_E (แยกระดับคอลัมน์) ---
        print("\n--- Step 7: แยก R_OTHER_NET และ R_OTHER_E (แยกระดับคอลัมน์) ---")

        print(f"ยอดรวมใน data_R_OTHER (ก่อนแยก):")
        print(f"  VALUE ทั้งหมด: {data_R_OTHER['VALUE'].sum():,.2f}")
        print(f"  VALUE_YTD ทั้งหมด: {data_R_OTHER['VALUE_YTD'].sum():,.2f}")

        # คำนวณผลรวมโดยตรง - แยกในระดับคอลัมน์
        # รายได้อื่น (บวก)
        r_other_net_value = data_R_OTHER[data_R_OTHER['VALUE'] > 0]['VALUE'].sum()
        r_other_net_value_ytd = data_R_OTHER[data_R_OTHER['VALUE_YTD'] > 0]['VALUE_YTD'].sum()

        print(f"\n✓ รายได้อื่น (ค่าบวก):")
        print(f"  จำนวนแถวที่ VALUE > 0: {len(data_R_OTHER[data_R_OTHER['VALUE'] > 0])}")
        print(f"  ผลรวม VALUE (> 0): {r_other_net_value:,.2f}")
        print(f"  จำนวนแถวที่ VALUE_YTD > 0: {len(data_R_OTHER[data_R_OTHER['VALUE_YTD'] > 0])}")
        print(f"  ผลรวม VALUE_YTD (> 0): {r_other_net_value_ytd:,.2f}")

        # ค่าใช้จ่ายอื่น (ลบ) - มาจากรายได้
        r_other_e_value = data_R_OTHER[data_R_OTHER['VALUE'] < 0]['VALUE'].sum()
        r_other_e_value_ytd = data_R_OTHER[data_R_OTHER['VALUE_YTD'] < 0]['VALUE_YTD'].sum()

        print(f"\n✓ รายได้อื่นที่เป็นลบ (จะเปลี่ยนเป็นค่าใช้จ่าย):")
        print(f"  จำนวนแถวที่ VALUE < 0: {len(data_R_OTHER[data_R_OTHER['VALUE'] < 0])}")
        print(f"  ผลรวม VALUE (< 0): {r_other_e_value:,.2f}")
        print(f"  จำนวนแถวที่ VALUE_YTD < 0: {len(data_R_OTHER[data_R_OTHER['VALUE_YTD'] < 0])}")
        print(f"  ผลรวม VALUE_YTD (< 0): {r_other_e_value_ytd:,.2f}")

        data_R_OTHER_NET = pd.DataFrame({
            'GROUP': ['รายได้อื่น'],
            'VALUE': [r_other_net_value],
            'VALUE_YTD': [r_other_net_value_ytd]
        })
        # เปลี่ยน GROUP ของ R_OTHER_E เป็น 'ค่าใช้จ่ายอื่น'
        print("\n  → เปลี่ยน GROUP เป็น 'ค่าใช้จ่ายอื่น' แล้ว")

        data_R_OTHER_E = pd.DataFrame({
            'GROUP': ['ค่าใช้จ่ายอื่น'],
            'VALUE': [r_other_e_value],
            'VALUE_YTD': [r_other_e_value_ytd]
        })
        print(f"\n✓ สร้าง R_OTHER_NET และ R_OTHER_E เรียบร้อย:")

        # --- Step 8: สร้าง E_OTHER และ E_OTHER_NET ---
        print("\n--- Step 8: สร้าง E_OTHER และ E_OTHER_NET ---")
        data_E_OTHER = data_RE_OTHER[data_RE_OTHER['GROUP'] == 'ค่าใช้จ่ายอื่น'].copy()
        print(f"✓ E_OTHER (GROUP = ค่าใช้จ่ายอื่น): {len(data_E_OTHER)} รายการ")
        print(data_E_OTHER.sum(numeric_only=True))
        
        # รวม E_OTHER กับ R_OTHER_E
        data_E_OTHER_NET = pd.concat([data_E_OTHER, data_R_OTHER_E], ignore_index=True)
        print(f"✓ สร้าง E_OTHER_NET: {len(data_E_OTHER_NET)} รายการ (E_OTHER: {len(data_E_OTHER)}, R_OTHER_E: {len(data_R_OTHER_E)})")
        print(data_E_OTHER_NET.sum(numeric_only=True))

        # คูณ -1 เข้าไปที่เดือนและสะสม
        print("\n  กำลังคูณ -1 เข้าไปที่ VALUE และ VALUE_YTD...")
        data_E_OTHER_NET['VALUE'] = data_E_OTHER_NET['VALUE'] * -1
        data_E_OTHER_NET['VALUE_YTD'] = data_E_OTHER_NET['VALUE_YTD'] * -1
        print("  ✓ คูณ -1 เรียบร้อย")
        
        # --- Step 9: รวมทั้งหมด (F + R_OTHER_NET + E_OTHER_NET) ---
        print("\n--- Step 9: รวมข้อมูลทั้งหมด ---")
        
        # เลือกเฉพาะ columns ที่ต้องการ
        final_columns = ['GROUP', 'VALUE', 'VALUE_YTD']
        
        data_F_final = data_F[final_columns].copy()
        data_R_OTHER_NET_final = data_R_OTHER_NET[final_columns].copy()
        data_E_OTHER_NET_final = data_E_OTHER_NET[final_columns].copy()
        
        # Concat ทั้งหมด
        final_result = pd.concat([
            data_F_final,
            data_R_OTHER_NET_final,
            data_E_OTHER_NET_final
        ], ignore_index=True)
        
        print(f"✓ สร้างข้อมูลสุดท้าย: {len(final_result)} รายการ")
        print(f"  - ผลตอบแทนทางการเงิน: {len(data_F_final)} รายการ")
        print(f"  - รายได้อื่น: {len(data_R_OTHER_NET_final)} รายการ")
        print(f"  - ค่าใช้จ่ายอื่น: {len(data_E_OTHER_NET_final)} รายการ")
        
        # --- Step 10: คำนวณผลรวมแต่ละประเภท ---
        print("\n--- Step 10: คำนวณผลรวม ---")
        
        # ผลตอบแทนทางการเงิน
        financial_df = final_result[final_result['GROUP'] == 'ผลตอบแทนทางการเงิน']
        financial_month = financial_df['VALUE'].sum()
        financial_ytd = financial_df['VALUE_YTD'].sum()
        
        # รายได้อื่น
        other_income_df = final_result[final_result['GROUP'] == 'รายได้อื่น']
        other_income_month = other_income_df['VALUE'].sum()
        other_income_ytd = other_income_df['VALUE_YTD'].sum()
        
        # ค่าใช้จ่ายอื่น
        other_expense_df = final_result[final_result['GROUP'] == 'ค่าใช้จ่ายอื่น']
        other_expense_month = other_expense_df['VALUE'].sum()
        other_expense_ytd = other_expense_df['VALUE_YTD'].sum()
        
        
        # --- Step 11: สร้าง DataFrame สรุป และ แสดงผลลัพธ์ ---
        # (ใหม่) สร้าง DataFrame สรุป
        summary_data = {
            'รายการ': ['ผลตอบแทนทางการเงิน', 'รายได้อื่น', 'ค่าใช้จ่ายอื่น'],
            'เดือน': [financial_month, other_income_month, other_expense_month],
            'สะสม': [financial_ytd, other_income_ytd, other_expense_ytd]
        }
        summary_df = pd.DataFrame(summary_data)

        # แสดงผลลัพธ์ (เหมือนเดิม)
        print("\n" + "="*80)
        print("ผลลัพธ์สุดท้าย: รายได้/ค่าใช้จ่ายอื่น")
        print("="*80)
        print(f"{'รายการ':<35} {'เดือน':>20} {'สะสม':>20}")
        print("-"*80)
        print(f"{'ผลตอบแทนทางการเงิน':<35} {financial_month:>20,.2f} {financial_ytd:>20,.2f}")
        print(f"{'รายได้อื่น':<35} {other_income_month:>20,.2f} {other_income_ytd:>20,.2f}")
        print(f"{'ค่าใช้จ่ายอื่น':<35} {other_expense_month:>20,.2f} {other_expense_ytd:>20,.2f}")
        print("="*80)
        
        print("\n✓ End 'process_financial_and_other' (New Logic)")
        
        # (ใหม่) เปลี่ยนค่าที่ return จาก final_result เป็น summary_df
        return summary_df
        
    except FileNotFoundError as e:
        print(f"\n*** ERROR: ไม่พบไฟล์! ***")
        print(f"File not found: {e.filename}")
        print("\nกรุณาตรวจสอบว่าไฟล์เหล่านี้อยู่ใน master_path:")
        print(f"1. {master_other_rev_file}")
        print(f"2. {master_rev_exp_net_file}")
        return None
    except KeyError as e:
        print(f"\n*** ERROR: ไม่พบคอลัมน์ที่ต้องการ! ***")
        print(f"KeyError: {e}")
        print("\nกรุณาตรวจสอบชื่อคอลัมน์ในไฟล์ Master (เช่น 'GL_CODE', 'GL_GROUP', 'GROUP')")
        return None
    except Exception as e:
        print(f"\n*** ERROR (Unexpected): {e} ***")
        import traceback
        traceback.print_exc()
        return None


# --- 4. สร้าง Excel Writer (Create Excel Writer) ---
writer = pd.ExcelWriter(output_path + output_excel_file, engine='xlsxwriter')

# --- 5. การประมวลผลหลัก (Main Processing Loop) ---
for file in input_files:
    print(f"Processing file: {file}")
    
    # อ่านไฟล์ Input หลักเพียงครั้งเดียว
    df = pd.read_csv(input_path + file, 
                     encoding="tis-620", 
                     delimiter="\t", 
                     header=None, 
                     on_bad_lines="skip")

    # สร้าง DataFrame พื้นฐาน
    of_base = pd.DataFrame()
    of_base["GL_CODE"] = df[4]
    of_base["VALUE"] = df[11]
    of_base["VALUE_YTD"] = df[13]

    # ทำความสะอาดข้อมูลตัวเลข (Clean numeric data)
    for col in ["VALUE", "VALUE_YTD"]:
        of_base[col] = of_base[col].replace(",", "", regex=True)
        # *** FIX (แก้ไข): เพิ่ม r เพื่อแก้ SyntaxWarning ***
        of_base[col] = of_base[col].replace(r"\(", "-", regex=True)
        of_base[col] = of_base[col].replace(r"\)", "", regex=True)
        
    of_base["VALUE"] = pd.to_numeric(of_base["VALUE"])
    of_base["VALUE_YTD"] = pd.to_numeric(of_base["VALUE_YTD"])
    of_base["GL_CODE"] = of_base["GL_CODE"].astype(str)

    # --- 6. ประมวลผลส่วนของ Expense ---
    print("Processing Expenses...")
    of_expense = of_base[of_base["GL_CODE"].fillna("").str.match(r"^(51|53|54|59|52)")].copy()
    of_expense = of_expense.rename(columns={"VALUE": "EXPENSE_VALUE", "VALUE_YTD": "EXPENSE_VALUE_YTD"})

    # บันทึก CSV (ตามสคริปต์เดิม)
    of_expense.to_csv(output_path + output_csv_expense, index=False)

    # Merge กับ Master Expense
    gl_group_expense = pd.merge(of_expense, master_expense_gl, on="GL_CODE", how="left")
    gl_group_expense = gl_group_expense[["CODE_GROUP", "GROUP_NAME", "GL_CODE", "GL_NAME", "EXPENSE_VALUE", "EXPENSE_VALUE_YTD"]]
    
    # Group by
    gl_group_by_expense = gl_group_expense[["CODE_GROUP", "GROUP_NAME", "EXPENSE_VALUE", "EXPENSE_VALUE_YTD"]]
    gl_group_by_expense = gl_group_by_expense.groupby(by=["CODE_GROUP", "GROUP_NAME"], dropna=False).sum().reset_index()
    gl_group_by_expense.loc['Total'] = gl_group_by_expense.sum(axis=0, numeric_only=True)

    # --- 7. ประมวลผลส่วนของ Revenue ---
    print("Processing Revenues...")
    of_revenue = of_base[of_base["GL_CODE"].str.startswith("4")].copy()
    of_revenue = of_revenue.rename(columns={"VALUE": "REVENUE_VALUE", "VALUE_YTD": "REVENUE_VALUE_YTD"})

    # บันทึก CSV (ตามสคริปต์เดิม)
    of_revenue.to_csv(output_path + output_csv_revenue, index=False)
    
    # Merge กับ Master Revenue
    gl_group_revenue = pd.merge(of_revenue, master_revenue_gl, on="GL_CODE", how="left")
    gl_group_revenue = gl_group_revenue[["REPORT_CODE", "GL_GROUP", "GL_NAME", "GL_CODE", "REVENUE_VALUE", "REVENUE_VALUE_YTD"]]

    # Group by
    gl_group_by_revenue = gl_group_revenue[["REPORT_CODE", "GL_GROUP", "REVENUE_VALUE", "REVENUE_VALUE_YTD"]]
    gl_group_by_revenue = gl_group_by_revenue.groupby(by=["REPORT_CODE", "GL_GROUP"], dropna=False).sum().reset_index()
    gl_group_by_revenue.loc['Total'] = gl_group_by_revenue.sum(axis=0, numeric_only=True)

    # --- 8. เรียกใช้ฟังก์ชันวิเคราะห์รายได้/ค่าใช้จ่ายอื่น ---
    summary_other_fin_df = process_financial_and_other(
        of_revenue=of_revenue, 
        gl_group_expense=gl_group_expense, 
        master_path=master_path
    )

    # --- 9. บันทึกลง Excel (Write to Excel) ---
    print("Writing to Excel file...")
    # เขียนชีต Expense
    of_expense.to_excel(writer, sheet_name="expense_data", index=False)
    gl_group_expense.to_excel(writer, sheet_name="expense_gl_group_data", index=False)
    gl_group_by_expense.to_excel(writer, sheet_name="expense_gl_group", index=False)
    
    # เขียนชีต Revenue
    of_revenue.to_excel(writer, sheet_name="revenue_data", index=False)
    gl_group_revenue.to_excel(writer, sheet_name="revenue_gl_group_data", index=False)
    gl_group_by_revenue.to_excel(writer, sheet_name="revenue_gl_group", index=False)

    # เขียนชีตสรุปรายได้/ค่าใช้จ่ายอื่น
    if summary_other_fin_df is not None:
        summary_other_fin_df.to_excel(writer, sheet_name="summary_other", index=False)
    else:
        print("!!! Warning: ไม่สามารถสร้างชีต summary_other ได้ เนื่องจากข้อมูลเป็น None")

    # --- 10. จัดรูปแบบ Excel (Format Excel) ---
    workbook = writer.book
    number_format = workbook.add_format({'num_format': '#,##0.00'})

    # จัดรูปแบบชีต Expense
    worksheet_data_exp = writer.sheets["expense_data"]
    worksheet_gl_group_data_exp = writer.sheets["expense_gl_group_data"]
    worksheet_gl_group_by_exp = writer.sheets["expense_gl_group"]

    worksheet_data_exp.set_column(1, 2, 18, number_format)
    worksheet_gl_group_data_exp.set_column(0, 0, 12)
    worksheet_gl_group_data_exp.set_column(1, 1, 36)
    worksheet_gl_group_data_exp.set_column(2, 2, 9)
    worksheet_gl_group_data_exp.set_column(3, 3, 36) # GL_NAME
    worksheet_gl_group_data_exp.set_column(4, 5, 18, number_format) # Values
    
    worksheet_gl_group_by_exp.set_column(0, 0, 12)
    worksheet_gl_group_by_exp.set_column(1, 1, 36)
    worksheet_gl_group_by_exp.set_column(2, 3, 18, number_format)

    # จัดรูปแบบชีต Revenue
    worksheet_data_rev = writer.sheets["revenue_data"]
    worksheet_gl_group_data_rev = writer.sheets["revenue_gl_group_data"]
    worksheet_gl_group_by_rev = writer.sheets["revenue_gl_group"]

    worksheet_data_rev.set_column(1, 2, 18, number_format)
    worksheet_gl_group_data_rev.set_column(0, 0, 12)
    worksheet_gl_group_data_rev.set_column(1, 1, 36)
    worksheet_gl_group_data_rev.set_column(2, 3, 36) # GL_NAME, GL_CODE
    worksheet_gl_group_data_rev.set_column(4, 5, 18, number_format) # Values
    
    worksheet_gl_group_by_rev.set_column(0, 0, 12)
    worksheet_gl_group_by_rev.set_column(1, 1, 36)
    worksheet_gl_group_by_rev.set_column(2, 3, 18, number_format)

    # จัดรูปแบบชีตสรุป summary_other
    if summary_other_fin_df is not None:
        worksheet_summary = writer.sheets["summary_other"]
        worksheet_summary.set_column(0, 0, 35) # คอลัมน์ 'รายการ'
        worksheet_summary.set_column(1, 2, 20, number_format) # คอลัมน์ 'เดือน' และ 'สะสม'

# --- 11. ปิดและบันทึกไฟล์ Excel (Close and Save Excel) ---
writer.close()
print(f"Successfully combined output to {output_path}{output_excel_file}")