"""
One-off: build income_acs_ca_2020_2024.csv from Census ACS B19013 files
in data/02-processed/COGS 108 data/productDownload_2026-02-18T022323/
"""
import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), "COGS 108 data", "productDownload_2026-02-18T022323")
OUT = os.path.join(os.path.dirname(__file__), "income_acs_ca_2020_2024.csv")

years = [2020, 2021, 2022, 2023, 2024]
frames = []
for year in years:
    path = os.path.join(BASE, f"ACSDT5Y{year}.B19013-Data.csv")
    if not os.path.isfile(path):
        print("Skip (not found):", path)
        continue
    df = pd.read_csv(path)
    # California counties: GEO_ID like 0500000US06xxxx
    df = df[df["GEO_ID"].astype(str).str.startswith("0500000US06")].copy()
    df["county"] = df["NAME"].str.replace(" County, California", "", regex=False)
    df["year"] = year
    df["median_household_income"] = pd.to_numeric(df["B19013_001E"], errors="coerce")
    df = df[["county", "year", "median_household_income"]].dropna(subset=["median_household_income"])
    frames.append(df)
    print(year, "rows", len(df))

out_df = pd.concat(frames, ignore_index=True)
out_df = out_df.drop_duplicates(subset=["county", "year"]).sort_values(["county", "year"]).reset_index(drop=True)
out_df.to_csv(OUT, index=False)
print("Saved:", OUT, "shape", out_df.shape)
