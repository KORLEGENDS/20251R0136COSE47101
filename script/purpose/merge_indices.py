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
    maemae_path = os.path.join(output_dir, 'maemae_clean.pkl')
    jeonse_path = os.path.join(output_dir, 'jeonse_clean.pkl')
    maemae = load_pickle(maemae_path)
    jeonse = load_pickle(jeonse_path)
    merged = pd.merge(
        maemae,
        jeonse,
        on=['분류', '분류.1', '분류.2', '분류.3', 'YearMonth'],
        how='inner'
    )
    save_pickle(merged, os.path.join(output_dir, 'merged_indices.pkl'))
    print('Merging indices complete')

if __name__ == '__main__':
    main() 