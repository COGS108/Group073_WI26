"""Patch 02-EDACheckpoint.ipynb to use 2020-2024 data in Section 1 and Section 2."""
import json
from pathlib import Path

NB_PATH = Path("02-EDACheckpoint.ipynb")

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Section 1: replace block from key_cols/date_cols/last_col through zhvi_uc definition
SECTION1_OLD = '''key_cols = ["RegionID", "RegionName", "State", "CountyName", "Metro", "county"]
date_cols = [c for c in zhvi_ca.columns if c not in key_cols]
last_col = date_cols[-1]

zhvi_uc = (
    zhvi_ca[zhvi_ca["county"].isin(uc_counties)]
    .loc[:, ["county", last_col]]
    .rename(columns={last_col: "home_value"})
)'''

SECTION1_NEW = '''key_cols = ["RegionID", "RegionName", "State", "CountyName", "Metro", "county"]
date_cols = [c for c in zhvi_ca.columns if c not in key_cols]
target_years = ["2020", "2021", "2022", "2023", "2024"]
year_cols = [c for c in date_cols if any(c.startswith(y + "-") for y in target_years)]
if year_cols:
    zhvi_ca = zhvi_ca.copy()
    zhvi_ca["home_value_2020_2024"] = zhvi_ca[year_cols].mean(axis=1)
    value_col = "home_value_2020_2024"
    value_label = "2020-2024 average"
else:
    value_col = date_cols[-1]
    value_label = value_col

zhvi_uc = (
    zhvi_ca[zhvi_ca["county"].isin(uc_counties)]
    .loc[:, ["county", value_col]]
    .rename(columns={value_col: "home_value"})
)'''

SECTION1_TITLE_OLD = 'plt.title(f"Affordability in UC-Adjacent Counties (using {last_col} values and 2022 income)")'
SECTION1_TITLE_NEW = 'plt.title(f"Affordability in UC-Adjacent Counties (using {value_label} values and 2022 income)")'

# Section 2: use processed zhvi and 2020-2024 columns
SECTION2_OLD = '''## YOUR CODE HERE
import pandas as pd
import matplotlib.pyplot as plt

income = pd.read_csv("data/02-processed/income_limits_ca_2022.csv")
zillow = pd.read_csv("data/00-raw/Zip_Zhvi_SingleFamilyResidence_2018.csv")

print("Income shape:", income.shape)
print("Zillow shape:", zillow.shape)

zillow_ca = zillow[zillow["State"] == "CA"]

price_col = zillow_ca.columns[-1]

zillow_ca = zillow_ca[["CountyName", price_col]]
zillow_ca = zillow_ca.rename(columns={
    "CountyName": "county",
    price_col: "home_value"
})

zillow_county = zillow_ca.groupby("county")["home_value"].mean().reset_index()
zillow_county["county"] = zillow_county["county"].str.replace(" County", "", regex=False)

merged = pd.merge(income, zillow_county, on="county", how="inner")

plt.figure(figsize=(7,5))
plt.scatter(merged["median_household_income"], merged["home_value"])
plt.xlabel("Median Household Income (USD)")
plt.ylabel("Average Home Value (USD)")
plt.title("Income vs Home Value (CA Counties)")
plt.show()

corr = merged["median_household_income"].corr(merged["home_value"])
print("Correlation:", corr)'''

SECTION2_NEW = '''import pandas as pd
import matplotlib.pyplot as plt

income = pd.read_csv("data/02-processed/income_limits_ca_2022.csv")
zillow_ca = pd.read_csv("data/02-processed/zhvi_sfr_zip_ca_2018.csv")

print("Income shape:", income.shape)
print("Zillow shape:", zillow_ca.shape)

key_cols = ["RegionID", "RegionName", "State", "CountyName", "Metro"]
date_cols = [c for c in zillow_ca.columns if c not in key_cols]
target_years = ["2020", "2021", "2022", "2023", "2024"]
year_cols = [c for c in date_cols if any(c.startswith(y + "-") for y in target_years)]
if year_cols:
    zillow_ca = zillow_ca.copy()
    zillow_ca["home_value_2020_2024"] = zillow_ca[year_cols].mean(axis=1)
    value_col = "home_value_2020_2024"
    value_label = "2020-2024 average"
else:
    value_col = date_cols[-1]
    value_label = value_col

zillow_ca["county"] = zillow_ca["CountyName"].str.replace(" County", "", regex=False)
zillow_county = zillow_ca.groupby("county")[value_col].mean().reset_index()
zillow_county = zillow_county.rename(columns={value_col: "home_value"})

merged = pd.merge(income, zillow_county, on="county", how="inner")

plt.figure(figsize=(7,5))
plt.scatter(merged["median_household_income"], merged["home_value"])
plt.xlabel("Median Household Income (USD)")
plt.ylabel("Average Home Value (USD)")
plt.title(f"Income vs Home Value (CA Counties, {value_label})")
plt.show()

corr = merged["median_household_income"].corr(merged["home_value"])
print("Correlation:", corr)'''

def get_source_text(cell):
    if cell["cell_type"] != "code":
        return None
    return "".join(cell.get("source", []))

def to_source(s):
    lines = s.split("\n")
    out = [ln + "\n" for ln in lines[:-1]]
    if lines[-1]:
        out.append(lines[-1] + "\n")
    return out

updated = 0
for i, cell in enumerate(nb["cells"]):
    src = get_source_text(cell)
    if not src:
        continue
    if "uc_counties" in src and "last_col = date_cols[-1]" in src and "Affordability in UC-Adjacent" in src:
        if SECTION1_OLD in src:
            src = src.replace(SECTION1_OLD, SECTION1_NEW)
            src = src.replace(SECTION1_TITLE_OLD, SECTION1_TITLE_NEW)
            cell["source"] = to_source(src)
            updated += 1
            print("Patched Section 1 code cell at index", i)
    if "zillow = pd.read_csv(\"data/00-raw/Zip_Zhvi" in src and "price_col = zillow_ca.columns[-1]" in src:
        if "YOUR CODE HERE" in src and "Income vs Home Value (CA Counties)" in src:
            cell["source"] = to_source(SECTION2_NEW)
            updated += 1
            print("Patched Section 2 code cell at index", i)

print("Updated", updated, "cells")

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2, ensure_ascii=False)

print("Saved", NB_PATH)
