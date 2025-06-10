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
    trans_file = os.path.join(root_dir, 'data', 'transactions', '(월) 행정구역별 아파트매매거래현황_전체.csv')
    df_trans = read_csv_with_encoding(trans_file)
    # Filter for transaction count rows
    df_tc = df_trans[df_trans['항목'] == '호수[호수]'].copy()
    # Extract time columns
    time_cols = [col for col in df_tc.columns if re.match(r"\d{4}\.\d{2}\s월", str(col))]
    # Melt to long format
    df_long = df_tc.melt(
        id_vars=['행정구역별'],
        value_vars=time_cols,
        var_name='YearMonth',
        value_name='transaction_count'
    )
    # Convert YearMonth and filter
    df_long['YearMonth'] = df_long['YearMonth'].apply(convert_year_month)
    df_long = df_long.dropna(subset=['YearMonth'])
    df_long['year_month'] = pd.to_datetime(df_long['YearMonth'], format='%Y-%m')
    df_long['transaction_count'] = pd.to_numeric(df_long['transaction_count'], errors='coerce')
    # Filter to administrative level (sido)
    sido_names = [
        '서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시',
        '울산광역시','세종특별자치시','경기도','강원도','충청북도','충청남도',
        '전라북도','전라남도','경상북도','경상남도','제주특별자치도'
    ]
    df_sido = df_long[df_long['행정구역별'].isin(sido_names)].copy()
    # Assign zone
    df_sido['zone'] = df_sido['행정구역별'].apply(lambda x: '수도권' if x in ['서울특별시','경기도','인천광역시'] else '지방권')
    # Aggregate by zone and month
    df_zone_trans = df_sido.groupby(['zone', 'year_month'])['transaction_count'].sum().reset_index()
    # Nationwide aggregate
    df_nation = df_zone_trans.groupby('year_month')['transaction_count'].sum().reset_index()
    df_nation['zone'] = '전국'
    df_zone_all = pd.concat([df_zone_trans, df_nation], ignore_index=True)
    # Save to output directory
    output_dir = os.path.join(root_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    save_pickle(df_zone_all, os.path.join(output_dir, 'transactions_by_zone.pkl'))
    print('Processed transactions complete')

if __name__ == '__main__':
    main() 