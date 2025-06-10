#!/usr/bin/env python3
import os
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from utils.io_utils import list_csv_files, read_csv_with_encoding
import pandas as pd

def main():
    root_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
    data_dir = os.path.join(root_dir, 'data')
    csv_files = list_csv_files(data_dir)
    summary = []
    for file in csv_files:
        try:
            df = read_csv_with_encoding(file, nrows=5)
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
        summary.append({
            'Filename': file,
            'Preview Shape': (df.shape[0], df.shape[1]),
            'Columns': list(df.columns)
        })
    summary_df = pd.DataFrame(summary)
    # Create output directory
    output_dir = os.path.join(root_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'data_structure_summary.csv')
    summary_df.to_csv(output_path, index=False)
    print(f"Saved data structure summary to {output_path}")
    print(summary_df)

if __name__ == '__main__':
    main() 