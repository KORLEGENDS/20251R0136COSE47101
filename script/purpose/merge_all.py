#!/usr/bin/env python3
import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.io_utils import load_pickle, save_pickle
import pandas as pd

def main():
    # Prepare output directory and input paths
    root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    output_dir = os.path.join(root_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    df_idx = load_pickle(os.path.join(output_dir, 'processed_timeseries.pkl'))

    df_zone = load_pickle(os.path.join(output_dir, 'transactions_by_zone.pkl'))
    df_merged = (
        df_idx.reset_index()
        .merge(
            df_zone.rename(columns={'zone': 'region_name'}),
            on=['region_name', 'year_month'],
            how='left'
        )
        .set_index('year_month')
    )
    save_pickle(df_merged, os.path.join(output_dir, 'final_df_region.pkl'))
    print('Merged all data complete')

if __name__ == '__main__':
    main() 