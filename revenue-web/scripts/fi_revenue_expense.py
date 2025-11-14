import pandas as pd
from pathlib import Path
import os
import logging

def process_financial_and_other(of_revenue, gl_group_expense, master_path, master_files, logger):
    """
    Processes financial income, other income, and other expenses.
    """
    logger.info("Starting 'process_financial_and_other'")
    master_other_rev_file = master_files.get("other_revenue_net_mapping")
    master_rev_exp_net_file = master_files.get("revenue_expense_net_mapping")
    
    try:
        logger.info("Step 1: Creating R data")
        master_other_rev = pd.read_csv(os.path.join(master_path, master_other_rev_file))
        master_other_rev.columns = master_other_rev.columns.str.strip()
        master_other_rev['GL_CODE'] = master_other_rev['GL_CODE'].astype(str)
        data_R = pd.merge(of_revenue, master_other_rev, on='GL_CODE', how='inner')
        
        logger.info("Step 2: Creating F data (financial income)")
        data_F = data_R[data_R['GL_GROUP'] == 'ผลตอบแทนทางการเงิน'].copy()
        data_F = data_F.rename(columns={'GL_GROUP': 'GROUP', 'REVENUE_VALUE': 'VALUE', 'REVENUE_VALUE_YTD': 'VALUE_YTD'})
        
        logger.info("Step 3: Creating E data (other expenses)")
        data_E = gl_group_expense[gl_group_expense['GROUP_NAME'] == 'ค่าใช้จ่ายอื่น'].copy()
        data_E['VALUE'] = data_E['EXPENSE_VALUE'] * -1
        data_E['VALUE_YTD'] = data_E['EXPENSE_VALUE_YTD'] * -1
        data_E_final = data_E[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()

        logger.info("Step 4: Creating RE data (R + E)")
        data_R_renamed = data_R.rename(columns={'REVENUE_VALUE': 'VALUE', 'REVENUE_VALUE_YTD': 'VALUE_YTD'})
        data_R_for_concat = data_R_renamed[['GL_CODE', 'GL_NAME', 'VALUE', 'VALUE_YTD']].copy()
        data_RE = pd.concat([data_R_for_concat, data_E_final], ignore_index=True)

        logger.info("Step 5: Creating RE_OTHER data")
        master_rev_exp_net = pd.read_csv(os.path.join(master_path, master_rev_exp_net_file))
        master_rev_exp_net.columns = master_rev_exp_net.columns.str.strip()
        master_rev_exp_net['GL_CODE'] = master_rev_exp_net['GL_CODE'].astype(str)
        data_RE_OTHER = pd.merge(data_RE, master_rev_exp_net[["GL_CODE", "SUB_GROUP", "GROUP"]], on='GL_CODE', how='inner')

        logger.info("Step 6 & 7: Separating other revenue components")
        data_R_OTHER = data_RE_OTHER[data_RE_OTHER['GROUP'] == 'รายได้อื่น'].copy()
        r_other_net_value = data_R_OTHER[data_R_OTHER['VALUE'] > 0]['VALUE'].sum()
        r_other_net_value_ytd = data_R_OTHER[data_R_OTHER['VALUE_YTD'] > 0]['VALUE_YTD'].sum()
        r_other_e_value = data_R_OTHER[data_R_OTHER['VALUE'] < 0]['VALUE'].sum()
        r_other_e_value_ytd = data_R_OTHER[data_R_OTHER['VALUE_YTD'] < 0]['VALUE_YTD'].sum()
        data_R_OTHER_NET = pd.DataFrame({'GROUP': ['รายได้อื่น'], 'VALUE': [r_other_net_value], 'VALUE_YTD': [r_other_net_value_ytd]})
        data_R_OTHER_E = pd.DataFrame({'GROUP': ['ค่าใช้จ่ายอื่น'], 'VALUE': [r_other_e_value], 'VALUE_YTD': [r_other_e_value_ytd]})

        logger.info("Step 8: Creating other expense components")
        data_E_OTHER = data_RE_OTHER[data_RE_OTHER['GROUP'] == 'ค่าใช้จ่ายอื่น'].copy()
        data_E_OTHER_NET = pd.concat([data_E_OTHER, data_R_OTHER_E], ignore_index=True)
        data_E_OTHER_NET['VALUE'] *= -1
        data_E_OTHER_NET['VALUE_YTD'] *= -1

        logger.info("Step 9: Combining all financial components")
        final_columns = ['GROUP', 'VALUE', 'VALUE_YTD']
        final_result = pd.concat([
            data_F[final_columns].copy(),
            data_R_OTHER_NET[final_columns].copy(),
            data_E_OTHER_NET[final_columns].copy()
        ], ignore_index=True)

        logger.info("Step 10 & 11: Creating final summary")
        summary_data = {
            'รายการ': ['ผลตอบแทนทางการเงิน', 'รายได้อื่น', 'ค่าใช้จ่ายอื่น'],
            'เดือน': [final_result.loc[final_result['GROUP'] == 'ผลตอบแทนทางการเงิน', 'VALUE'].sum(), final_result.loc[final_result['GROUP'] == 'รายได้อื่น', 'VALUE'].sum(), final_result.loc[final_result['GROUP'] == 'ค่าใช้จ่ายอื่น', 'VALUE'].sum()],
            'สะสม': [final_result.loc[final_result['GROUP'] == 'ผลตอบแทนทางการเงิน', 'VALUE_YTD'].sum(), final_result.loc[final_result['GROUP'] == 'รายได้อื่น', 'VALUE_YTD'].sum(), final_result.loc[final_result['GROUP'] == 'ค่าใช้จ่ายอื่น', 'VALUE_YTD'].sum()]
        }
        summary_df = pd.DataFrame(summary_data)
        logger.info("Finished 'process_financial_and_other'")
        return summary_df

    except Exception as e:
        logger.error(f"Error in process_financial_and_other: {e}", exc_info=True)
        return None

def run_fi_script(config, year, month, logger):
    """
    Refactored main function for the FI Revenue/Expense script.
    """
    try:
        logger.info("--- Starting FI Revenue/Expense Script ---")
        pd.options.display.float_format = '{:,.2f}'.format

        paths = config.get('paths', {})
        master_files = config.get('master_files', {})
        
        input_path = paths.get('fi_input')
        output_path = paths.get('fi_output')
        master_path = paths.get('master_source')

        input_file_pattern = f"pld_nt_{year}{month}*.txt"
        input_files = list(Path(input_path).glob(input_file_pattern))
        if not input_files:
            raise FileNotFoundError(f"No input file found in {input_path} for pattern {input_file_pattern}")
        
        input_filename = input_files[0]
        logger.info(f"Using input file: {input_filename.name}")

        master_expense_file = master_files.get("expense_mapping")
        master_revenue_file = master_files.get("revenue_mapping_fi")

        output_excel_file = f"pl_combined_output_{year}{month}.xlsx"
        output_csv_expense = f"pl_expense_nt_output_{year}{month}.csv"
        output_csv_revenue = f"pl_revenue_nt_output_{year}{month}.csv"

        Path(output_path).mkdir(parents=True, exist_ok=True)

        logger.info("Loading master files...")
        master_expense_gl = pd.read_csv(os.path.join(master_path, master_expense_file), encoding="utf8", dtype={'GL_CODE_NT1': str}).rename(columns={"GL_CODE_NT1": "GL_CODE", "GL_NAME_NT1": "GL_NAME"})
        master_revenue_gl = pd.read_csv(os.path.join(master_path, master_revenue_file), encoding="utf8", dtype={'GL_CODE_NT1': str}).rename(columns={"GL_CODE_NT1": "GL_CODE", "GL_NAME_NT1": "GL_NAME"})

        writer = pd.ExcelWriter(os.path.join(output_path, output_excel_file), engine='xlsxwriter')
        
        logger.info(f"Processing file: {input_filename.name}")
        df = pd.read_csv(input_filename, encoding="tis-620", delimiter="\t", header=None, on_bad_lines="skip")

        of_base = pd.DataFrame({"GL_CODE": df[4].astype(str), "VALUE": df[11], "VALUE_YTD": df[13]})
        for col in ["VALUE", "VALUE_YTD"]:
            of_base[col] = pd.to_numeric(of_base[col].replace({",": "", r"\(": "-", r"\)": ""}, regex=True))

        logger.info("Processing Expenses...")
        of_expense = of_base[of_base["GL_CODE"].str.match(r"^(51|53|54|59|52)", na=False)].copy().rename(columns={"VALUE": "EXPENSE_VALUE", "VALUE_YTD": "EXPENSE_VALUE_YTD"})
        of_expense.to_csv(os.path.join(output_path, output_csv_expense), index=False)
        gl_group_expense = pd.merge(of_expense, master_expense_gl, on="GL_CODE", how="left")
        gl_group_by_expense = gl_group_expense.groupby(by=["CODE_GROUP", "GROUP_NAME"], dropna=False)[["EXPENSE_VALUE", "EXPENSE_VALUE_YTD"]].sum().reset_index()

        logger.info("Processing Revenues...")
        of_revenue = of_base[of_base["GL_CODE"].str.startswith("4", na=False)].copy().rename(columns={"VALUE": "REVENUE_VALUE", "VALUE_YTD": "REVENUE_VALUE_YTD"})
        of_revenue.to_csv(os.path.join(output_path, output_csv_revenue), index=False)
        gl_group_revenue = pd.merge(of_revenue, master_revenue_gl, on="GL_CODE", how="left")
        gl_group_by_revenue = gl_group_revenue.groupby(by=["REPORT_CODE", "GL_GROUP"], dropna=False)[["REVENUE_VALUE", "REVENUE_VALUE_YTD"]].sum().reset_index()

        summary_other_fin_df = process_financial_and_other(of_revenue, gl_group_expense, master_path, master_files, logger)

        logger.info("Writing to Excel file...")
        sheets = {"expense_data": of_expense, "expense_gl_group_data": gl_group_expense, "expense_gl_group": gl_group_by_expense, "revenue_data": of_revenue, "revenue_gl_group_data": gl_group_revenue, "revenue_gl_group": gl_group_by_revenue, "summary_other": summary_other_fin_df}
        for sheet_name, data in sheets.items():
            if data is not None:
                data.to_excel(writer, sheet_name=sheet_name, index=False)
        writer.close()
        
        logger.info(f"Successfully created FI report: {output_excel_file}")
        return {"status": "success", "output_file": os.path.join(output_path, output_excel_file)}

    except Exception as e:
        logger.error(f"FI Script failed: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}