import subprocess
from pathlib import Path

# --- CONFIG ---
STATE = "MA"                 # which state to sample from
N_FILES = 1000               # how many buildings to download
BASE = (
    "s3://oedi-data-lake/"
    "nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/"
    "2025/resstock_amy2018_release_1"
)

# where to store the sample locally - directly in OEDIDataset folder
LOCAL_DIR = Path(__file__).parent.parent / "OEDIDataset"
LOCAL_DIR.mkdir(parents=True, exist_ok=True)
print("Local download dir:", LOCAL_DIR)


def list_state_keys(state=STATE):
    """
    List all object keys (filenames) for a given state's individual-building
    timeseries, baseline upgrade=0.
    """
    prefix = f"{BASE}/timeseries_individual_buildings/by_state/upgrade=0/state={state}/"
    cmd = ["aws", "s3", "ls", prefix, "--no-sign-request"]

    print("Listing objects with:", " ".join(cmd))
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )

    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
    # lines look like: "2025-11-10 12:34:56  654321  1234567-0.parquet"
    keys = [ln.split()[-1] for ln in lines]
    print(f"Found {len(keys)} objects under state={state}")
    return keys


def aws_cp(s3_uri, dest_path):
    """Wrapper around 'aws s3 cp' using the public --no-sign-request flag."""
    cmd = ["aws", "s3", "cp", s3_uri, str(dest_path), "--no-sign-request"]
    print("Downloading:", s3_uri, "->", dest_path)
    subprocess.run(cmd, check=True)


# --- MAIN: list keys and download first N_FILES ---

all_keys = list_state_keys(STATE)

if len(all_keys) == 0:
    raise RuntimeError(f"No parquet files found for state={STATE}!")

sample_keys = all_keys[:N_FILES]
print(f"Downloading first {len(sample_keys)} files...")

for key in sample_keys:
    s3_uri = f"{BASE}/timeseries_individual_buildings/by_state/upgrade=0/state={STATE}/{key}"
    dest = LOCAL_DIR / key
    aws_cp(s3_uri, dest)

print("Done!")
