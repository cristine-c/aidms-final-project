import subprocess
from subprocess import CalledProcessError
from pathlib import Path

# ---------------- CONFIG ----------------
STATE = "MA"
YEAR = "2025"
DATASET_NAME = "resstock_amy2018_release_1"
BUCKET = "oedi-data-lake"

# Base key and URI for this dataset/year
BASE_KEY = (
    "nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/"
    f"{YEAR}/{DATASET_NAME}"
)
BASE_URI = f"s3://{BUCKET}/{BASE_KEY}"

# Local root: same OEDIDataset folder you used before
LOCAL_ROOT = Path(__file__).parent.parent / "OEDIDataset"
LOCAL_ROOT.mkdir(parents=True, exist_ok=True)

# Toggle what you want to download
DOWNLOAD_METADATA = True
DOWNLOAD_DICTIONARIES = True
DOWNLOAD_STATE_AGGREGATES = True   # state-level timeseries aggregates
DOWNLOAD_WEATHER = False           # set True if you also want weather CSVs

print("Using local root:", LOCAL_ROOT)
print("S3 base key      :", BASE_KEY)
print("S3 base URI      :", BASE_URI)


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a shell command and raise if it fails."""
    print("->", " ".join(cmd))
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def aws_cp(s3_uri: str, dest_path: Path) -> None:
    """Copy a single file from S3 to local."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["aws", "s3", "cp", s3_uri, str(dest_path), "--no-sign-request"]
    print("Downloading:", s3_uri, "->", dest_path)
    subprocess.run(cmd, check=True)


def aws_sync(s3_prefix_uri: str, dest_dir: Path) -> None:
    """Sync a folder prefix from S3 to local, but don't crash if it doesn't exist."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["aws", "s3", "sync", s3_prefix_uri, str(dest_dir), "--no-sign-request"]
    try:
        run_cmd(cmd)
    except CalledProcessError:
        print(f"WARNING: sync source not found or empty: {s3_prefix_uri} (skipping)")


def download_metadata():
    """
    Discover and download a useful metadata parquet file.

    For 2025 ResStock, metadata lives under:
      <BASE_KEY>/metadata_and_annual_results/

    'aws s3 ls' prints keys relative to the BUCKET, so we:
      1) list keys under that prefix
      2) look for a 'national/full/.../upgrade0.parquet' or similar
      3) fall back to the first .parquet if needed
    """
    meta_dir = LOCAL_ROOT / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    prefix_key = f"{BASE_KEY}/metadata_and_annual_results/"
    list_uri = f"s3://{BUCKET}/{prefix_key}"

    print("\n=== Discovering metadata files under ===")
    print("   ", list_uri)

    try:
        result = run_cmd(
            ["aws", "s3", "ls", list_uri, "--recursive", "--no-sign-request"]
        )
    except CalledProcessError:
        print("WARNING: No metadata_and_annual_results/ found for this dataset/year.")
        return

    lines = [ln for ln in result.stdout.splitlines() if ln.strip()]

    parquet_keys = []
    for ln in lines:
        parts = ln.split()
        if len(parts) < 4:
            continue
        key = parts[-1]  # full key relative to the bucket, e.g. nrel-pds-.../metadata_and_annual_results/...
        if key.lower().endswith(".parquet"):
            parquet_keys.append(key)

    if not parquet_keys:
        print("WARNING: No .parquet metadata files found under metadata_and_annual_results/")
        return

    print(f"Found {len(parquet_keys)} parquet metadata file(s). A few examples:")
    for k in parquet_keys[:10]:
        print("   ", k)

    # Prefer a national full baseline or upgrade0 file
    candidate = None
    for key in parquet_keys:
        if "metadata_and_annual_results/national" in key and "full/parquet" in key:
            if "upgrade0.parquet" in key or "baseline" in key:
                candidate = key
                break

    # If nothing matched that, just take the first .parquet as a generic fallback
    if candidate is None:
        candidate = parquet_keys[0]
        print("No obvious 'national/full/upgrade0' file found; using the first parquet as fallback.")

    print("Selected metadata file key:")
    print("   ", candidate)

    # Build full s3 URI using bucket + key (DO NOT prepend prefix again)
    s3_uri = f"s3://{BUCKET}/{candidate}"
    dest = meta_dir / Path(candidate).name

    aws_cp(s3_uri, dest)
    print("Metadata download complete ->", dest)


def download_dictionaries():
    """Download data/enumeration dictionaries and upgrades lookup, if present."""
    dict_dir = LOCAL_ROOT / "dictionaries"
    dict_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Downloading dictionaries ===")
    files = [
        ("data_dictionary.tsv", f"{BASE_URI}/data_dictionary.tsv"),
        ("enumeration_dictionary.tsv", f"{BASE_URI}/enumeration_dictionary.tsv"),
        ("upgrades_lookup.json", f"{BASE_URI}/upgrades_lookup.json"),
    ]
    for local_name, s3_uri in files:
        try:
            aws_cp(s3_uri, dict_dir / local_name)
        except CalledProcessError:
            print(f"WARNING: Dictionary file not found: {s3_uri} (skipping)")


def download_state_aggregates(state: str = STATE):
    """
    Download aggregate timeseries for your state (upgrade=0),
    by building type and end use.
    Useful for quick sanity checks and system-level plots.
    """
    agg_dir = (
        LOCAL_ROOT
        / "timeseries_aggregates"
        / "by_state"
        / f"state={state}"
    )
    s3_prefix_uri = f"{BASE_URI}/timeseries_aggregates/by_state/upgrade=0/state={state}/"

    print("\n=== Downloading state-level aggregates (if available) ===")
    aws_sync(s3_prefix_uri, agg_dir)


def download_weather(state: str = STATE):
    """
    Download AMY2018 weather CSVs for your state.
    Optional, but handy if you later want to relate load to temperature, etc.
    """
    weather_dir = LOCAL_ROOT / "weather" / "amy2018" / f"state={state}"
    s3_prefix_uri = f"{BASE_URI}/weather/amy2018/state={state}/"

    print("\n=== Downloading weather (AMY2018) (if available) ===")
    aws_sync(s3_prefix_uri, weather_dir)


if __name__ == "__main__":
    if DOWNLOAD_METADATA:
        download_metadata()

    if DOWNLOAD_DICTIONARIES:
        download_dictionaries()

    if DOWNLOAD_STATE_AGGREGATES:
        download_state_aggregates(STATE)

    if DOWNLOAD_WEATHER:
        download_weather(STATE)

    print("\nAll requested downloads complete.")
