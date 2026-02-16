
import os
import sys

PROJECT_ROOT = r"e:\Codes\Option-sim-main"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DATASET_ID = "510050_SH"

def _get_dataset_dir(dataset_id: str) -> str:
    p1 = os.path.join(DATA_DIR, dataset_id)
    if os.path.exists(p1):
        return p1
    return os.path.join(DATA_DIR, "510050_SH")

def _get_all_dates(dataset_id: str = "510050_SH"):
    dates = []
    try:
        data_dir = _get_dataset_dir(dataset_id)
        print(f"Scanning directory: {data_dir}")
    except FileNotFoundError:
        return []

    if not os.path.exists(data_dir):
        return []
        
    for year_dir in os.listdir(data_dir):
        year_path = os.path.join(data_dir, year_dir)
        if os.path.isdir(year_path):
            print(f"Scanning year: {year_dir}")
            for file in os.listdir(year_path):
                if file.endswith(".parquet"):
                    date_str = file.replace(".parquet", "").replace("options_", "")
                    dates.append(date_str)
                    if date_str == "2020-07-11":
                        print(f"FOUND 2020-07-11 in {year_path}/{file}")
    
    dates.sort()
    return dates

if __name__ == "__main__":
    dates = _get_all_dates(DATASET_ID)
    print(f"Total dates found: {len(dates)}")
    if "2020-07-11" in dates:
        print("CONFIRMED: 2020-07-11 is in the list!")
    else:
        print("CONFIRMED: 2020-07-11 is NOT in the list.")
