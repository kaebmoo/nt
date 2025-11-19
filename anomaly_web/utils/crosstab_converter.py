# anomaly_web/utils/crosstab_converter.py
"""
Converts Crosstab/Pivot-Table data into a long format.
"""

import pandas as pd

class CrosstabConverter:
    """
    A class to convert wide-format (crosstab) dataframes to long-format.
    """

    def __init__(self, input_file, output_file=None):
        """
        Initializes the converter.
        
        Args:
            input_file (str): Path to the input Excel or CSV file.
            output_file (str, optional): Path to save the long-format output. Defaults to None.
        """
        self.input_file = input_file
        self.output_file = output_file

    def convert(self, sheet_name=0, skiprows=0, id_vars=None, value_name='VALUE', mode='auto'):
        """
        Performs the conversion from crosstab to long format.

        Args:
            sheet_name (int or str, optional): Sheet to read from Excel. Defaults to 0.
            skiprows (int, optional): Rows to skip at the beginning of the file. Defaults to 0.
            id_vars (list, optional): List of columns to use as identifier variables. Defaults to None.
            value_name (str, optional): Name for the new column holding the values. Defaults to 'VALUE'.
            mode (str, optional): 'auto', 'date', or 'sequential'. Determines how to handle period columns.

        Returns:
            pd.DataFrame: The converted long-format DataFrame.
        """
        # 1. Read Data
        try:
            if self.input_file.endswith('.csv'):
                df = pd.read_csv(self.input_file, skiprows=skiprows)
            else:
                df = pd.read_excel(self.input_file, sheet_name=sheet_name, skiprows=skiprows)
        except FileNotFoundError:
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        except Exception as e:
            raise ValueError(f"Error reading input file: {e}")

        if id_vars is None:
            raise ValueError("id_vars must be provided.")

        # 2. Melt DataFrame
        df_long = pd.melt(df, id_vars=id_vars, var_name='PERIOD', value_name=value_name)

        # 3. Process Period Column based on mode
        if mode == 'date' or (mode == 'auto' and self._is_date_like(df_long['PERIOD'])):
            try:
                # Attempt to convert to YYYY-MM-01 format
                df_long['DATE'] = pd.to_datetime(df_long['PERIOD'], errors='coerce').dt.strftime('%Y-%m-01')
                # Drop rows where conversion failed
                df_long = df_long.dropna(subset=['DATE'])
                df_long['DATE'] = pd.to_datetime(df_long['DATE'])
            except Exception:
                # Fallback for non-standard date formats
                df_long.rename(columns={'PERIOD': 'DATE'}, inplace=True)
        else: # sequential mode
            df_long.rename(columns={'PERIOD': 'DATE'}, inplace=True)


        # 4. Save if output file is specified
        if self.output_file:
            df_long.to_csv(self.output_file, index=False, encoding='utf-8')

        return df_long

    def _is_date_like(self, series):
        """
        Heuristically checks if a series contains date-like strings.
        """
        sample = series.dropna().unique()[:5]
        if len(sample) == 0:
            return False
        
        # Check if a good portion can be parsed as dates
        try:
            parsed_count = pd.to_datetime(sample, errors='coerce').notna().sum()
            if parsed_count / len(sample) > 0.5:
                return True
        except Exception:
            return False
            
        return False
