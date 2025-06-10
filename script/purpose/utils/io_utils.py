#!/usr/bin/env python3
import os
import pandas as pd
import pickle

def list_csv_files(data_dir):
    """Recursively list all CSV files in the given directory."""
    csv_files = []
    for root, _, files in os.walk(data_dir):
        for f in files:
            if f.endswith('.csv'):
                csv_files.append(os.path.join(root, f))
    return csv_files


def read_csv_with_encoding(path, encodings=['utf-8', 'cp949'], **kwargs):
    """Read a CSV file, trying multiple encodings if necessary."""
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)


def save_pickle(obj, path):
    """Save a pandas DataFrame or other object to a pickle file."""
    obj.to_pickle(path)


def load_pickle(path):
    """Load a pandas DataFrame or other object from a pickle file."""
    return pd.read_pickle(path) 