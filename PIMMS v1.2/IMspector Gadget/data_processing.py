import pandas as pd
from config import DATA_FILE, STANDARDS_FILE


def load_adjusted_data():
    """Loads the main dataset."""
    try:
        print(f"[INFO] Loading data from: {DATA_FILE}")
        return pd.read_csv(DATA_FILE)
    except Exception as e:
        print(f"[ERROR] Could not load dataset: {e}")
        return pd.DataFrame()


def load_standards_report():
    """Loads the standards report dataset."""
    try:
        print(f"[INFO] Loading standards report from: {STANDARDS_FILE}")
        return pd.read_csv(STANDARDS_FILE)
    except Exception as e:
        print(f"[ERROR] Could not load standards report: {e}")
        return pd.DataFrame()
