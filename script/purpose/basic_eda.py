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
    df = load_pickle(os.path.join(output_dir, 'processed_timeseries.pkl'))
    # Descriptive statistics
    desc = df[['price_index', 'jeonse_index']].describe()
    print('Descriptive Statistics:')
    print(desc)
    # Yearly aggregation and percentage change
    df['year'] = df.index.year
    yearly = df.groupby('year')[['price_index', 'jeonse_index']].mean().reset_index()
    yearly['price_pct_change'] = yearly['price_index'].pct_change() * 100
    yearly['jeonse_pct_change'] = yearly['jeonse_index'].pct_change() * 100
    print('Yearly Averages and YoY Changes:')
    print(yearly)
    # Correlation matrix
    corr = df[['price_index', 'jeonse_index']].corr()
    print('Overall Correlation Matrix:')
    print(corr)
    # Save yearly summary
    save_pickle(yearly, os.path.join(output_dir, 'yearly_summary.pkl'))
    print('Basic EDA complete')

if __name__ == '__main__':
    main() 