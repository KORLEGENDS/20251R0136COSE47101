#!/usr/bin/env python3
import os
import sys
import re
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.io_utils import read_csv_with_encoding, save_pickle
from utils.date_utils import convert_year_month
import pandas as pd

def main():
    root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    data_dir = os.path.join(root_dir, 'data', 'transactions')
    maemae_file = os.path.join(data_dir, '(월) 매매가격지수_아파트.csv')
    jeonse_file = os.path.join(data_dir, '(월) 전세가격지수_아파트.csv')
    maemae_df = read_csv_with_encoding(maemae_file)
    jeonse_df = read_csv_with_encoding(jeonse_file)

    region_cols = ['분류', '분류.1', '분류.2', '분류.3']
    time_cols_maemae = [col for col in maemae_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]
    time_cols_jeonse = [col for col in jeonse_df.columns if re.match(r"\d{4}년\s*\d{1,2}월", str(col))]

    maemae_long = maemae_df.melt(
        id_vars=region_cols,
        value_vars=time_cols_maemae,
        var_name='YearMonth',
        value_name='MaemaeIndex'
    )
    jeonse_long = jeonse_df.melt(
        id_vars=region_cols,
        value_vars=time_cols_jeonse,
        var_name='YearMonth',
        value_name='JeonseIndex'
    )

    maemae_long['YearMonth'] = maemae_long['YearMonth'].apply(convert_year_month)
    jeonse_long['YearMonth'] = jeonse_long['YearMonth'].apply(convert_year_month)

    maemae_clean = maemae_long[maemae_long['분류'] != '분류'].copy()
    jeonse_clean = jeonse_long[jeonse_long['분류'] != '분류'].copy()

    maemae_clean['MaemaeIndex'] = pd.to_numeric(maemae_clean['MaemaeIndex'], errors='coerce')
    jeonse_clean['JeonseIndex'] = pd.to_numeric(jeonse_clean['JeonseIndex'], errors='coerce')

    # Save outputs to output directory
    output_dir = os.path.join(root_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    save_pickle(maemae_clean, os.path.join(output_dir, 'maemae_clean.pkl'))
    save_pickle(jeonse_clean, os.path.join(output_dir, 'jeonse_clean.pkl'))
    print('Preprocessing indices complete')

if __name__ == '__main__':
    main() 