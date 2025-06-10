#!/usr/bin/env python3
import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.io_utils import load_pickle, save_pickle
import pandas as pd

def main():
    # Prepare output directory and input path
    root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    output_dir = os.path.join(root_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    merged = load_pickle(os.path.join(output_dir, 'merged_indices.pkl'))
    merged['region_name'] = merged['분류']
    merged['year_month'] = pd.to_datetime(merged['YearMonth'], format='%Y-%m')
    df = merged[['region_name', 'year_month', 'MaemaeIndex', 'JeonseIndex']].copy()
    df = df.rename(columns={
        'MaemaeIndex': 'price_index',
        'JeonseIndex': 'jeonse_index'
    })
    df = df.set_index('year_month').sort_index()
    save_pickle(df, os.path.join(output_dir, 'processed_timeseries.pkl'))
    print('Prepared time series complete')

if __name__ == '__main__':
    main() 