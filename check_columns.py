import pandas as pd
pd.set_option('display.max_columns', None)
try:
    df = pd.read_parquet("data/510050_SH/2022/options_2022-01-04.parquet")
    print("ALL COLUMNS:")
    for col in df.columns:
        print(f"- {col}")
    print("SAMPLE ROW:")
    print(df.iloc[0])
except Exception as e:
    print(e)
