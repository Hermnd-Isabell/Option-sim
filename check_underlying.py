import pandas as pd
import os

log = []
def print_log(msg):
    log.append(msg)
    print(msg)

try:
    f = "data/510050_SH/2022/options_2022-01-04.parquet"
    if os.path.exists(f):
        df = pd.read_parquet(f)
        total = len(df)
        valid = df['underlying_close'].dropna().count()
        print_log(f"PARQUET: Total={total}, Valid={valid}")
        if valid > 0:
            print_log(f"Sample: {df['underlying_close'].dropna().iloc[0]}")
    else:
        print_log("Parquet not found")

    f_feather = "data/50ETF/Filtered_OptionPrice_2020_2022.feather"
    if os.path.exists(f_feather):
        df = pd.read_feather(f_feather)
        print_log(f"FEATHER: Cols={list(df.columns)}")
        if 'underlying_close' in df.columns:
            print_log(f"FEATHER Valid={df['underlying_close'].dropna().count()}")
    else:
        print_log("Feather not found")

except Exception as e:
    print_log(f"ERROR: {e}")

with open("check_output.txt", "w") as f:
    f.write("\n".join(log))
