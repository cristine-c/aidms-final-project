import pandas as pd

# Load only the specific sheet you want
xlsx_file = "2018_smd_hourly.xlsx"
sheet_name = "NEMA"  # replace with the tab name you want
df = pd.read_excel(xlsx_file, sheet_name=sheet_name)

# Combine 'Date' and 'Hr_End' into a timestamp
# Assuming Hr_End is in hours like 1, 2, ..., 24
df["Hr_End"] = df["Hr_End"].astype(int)
df["timestamp"] = pd.to_datetime(df["Date"]) + pd.to_timedelta(df["Hr_End"] - 1, unit="h")

df["RT_LMP_kWh"] = df["RT_LMP"] / 1000.0  # Convert from $/MWh to $/kWh

# Output only what you need
df_out = df[["timestamp", "RT_LMP_kWh"]]

# Save
df_out.to_csv("RT_LMP_kWh.csv", index=False)