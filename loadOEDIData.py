from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
import pyarrow.parquet as pq


# Adjust if needed: this assumes you keep using the same OEDIDataset folder
ROOT = Path(__file__).parent.parent / "OEDIDataset"


def load_metadata() -> Optional[pd.DataFrame]:
    """
    Load all metadata parquet files in OEDIDataset/metadata into a single DataFrame.
    Returns None if no metadata parquet files are found.
    """
    meta_dir = ROOT / "metadata"
    if not meta_dir.exists():
        print("[load_metadata] metadata directory does not exist:", meta_dir)
        return None

    parquet_files = sorted(meta_dir.glob("*.parquet"))
    if not parquet_files:
        print("[load_metadata] No .parquet files found in:", meta_dir)
        return None

    dfs = []
    for p in parquet_files:
        print(f"[load_metadata] Reading {p.name} ...")
        table = pq.read_table(p)
        dfs.append(table.to_pandas())

    meta_df = pd.concat(dfs, ignore_index=True)
    print("[load_metadata] Combined metadata shape:", meta_df.shape)
    return meta_df


def load_dictionaries() -> Dict[str, Optional[pd.DataFrame]]:
    """
    Load data_dictionary.tsv and enumeration_dictionary.tsv (if present)
    from OEDIDataset/dictionaries.
    Returns a dict of DataFrames (or None if file missing).
    """
    dict_dir = ROOT / "dictionaries"
    out: Dict[str, Optional[pd.DataFrame]] = {
        "data_dictionary": None,
        "enumeration_dictionary": None,
    }

    if not dict_dir.exists():
        print("[load_dictionaries] dictionaries directory does not exist:", dict_dir)
        return out

    data_dict_path = dict_dir / "data_dictionary.tsv"
    enum_dict_path = dict_dir / "enumeration_dictionary.tsv"

    # --- data_dictionary.tsv ---
    if data_dict_path.exists():
        print("[load_dictionaries] Reading data_dictionary.tsv ...")
        out["data_dictionary"] = pd.read_csv(
            data_dict_path, sep="\t", encoding="utf-8"
        )
        print(
            "[load_dictionaries] data_dictionary shape:",
            out["data_dictionary"].shape,
        )
    else:
        print("[load_dictionaries] data_dictionary.tsv not found")

    # --- enumeration_dictionary.tsv ---
    if enum_dict_path.exists():
        print("[load_dictionaries] Reading enumeration_dictionary.tsv ...")
        try:
            # try utf-8 first
            out["enumeration_dictionary"] = pd.read_csv(
                enum_dict_path, sep="\t", encoding="utf-8"
            )
        except UnicodeDecodeError:
            print(
                "[load_dictionaries] UTF-8 decode failed, retrying with latin-1 ..."
            )
            out["enumeration_dictionary"] = pd.read_csv(
                enum_dict_path, sep="\t", encoding="latin-1"
            )

        print(
            "[load_dictionaries] enumeration_dictionary shape:",
            out["enumeration_dictionary"].shape,
        )
    else:
        print("[load_dictionaries] enumeration_dictionary.tsv not found")

    return out


def build_timeseries_index() -> pd.DataFrame:
    """
    Build an index of the individual-building timeseries parquet files.

    Preferred folder layout (mirroring S3):

        OEDIDataset/
          timeseries_individual/
            by_state/
              upgrade=<upgrade_id>/
                state=<STATE>/
                  <building_id>-<upgrade_id>.parquet

    This function will:

      * search recursively under OEDIDataset/timeseries_individual/by_state
        if it exists, OR
      * fall back to searching for *.parquet directly under OEDIDataset
        (legacy layout) if the new tree is missing.

    Returns a DataFrame with columns:
      - building_id  (int or str)
      - upgrade_id   (int or str)
      - state        (str or None)
      - file_path    (Path)
    """
    ts_root = ROOT / "timeseries_individual" / "by_state"
    rows: List[Dict[str, Any]] = []

    if ts_root.exists():
        parquet_files = sorted(ts_root.glob("**/*.parquet"))
        print(
            f"[build_timeseries_index] Searching {len(parquet_files)} parquet files "
            f"under {ts_root} (recursive)"
        )
    else:
        # Legacy behavior: look for parquets directly under ROOT
        parquet_files = sorted(ROOT.glob("*.parquet"))
        print(
            f"[build_timeseries_index] timeseries_individual/by_state not found; "
            f"searching {len(parquet_files)} parquet files directly under {ROOT}"
        )

    for p in parquet_files:
        stem = p.stem  # expected "<building_id>-<upgrade_id>"
        parts = stem.split("-")
        if len(parts) != 2:
            print(f"[build_timeseries_index] Skipping unexpected file name: {p.name}")
            continue

        bldg_id_str, upgrade_str = parts
        # Parse building_id
        try:
            bldg_id = int(bldg_id_str)
        except ValueError:
            bldg_id = bldg_id_str  # fallback to string

        # Parse upgrade from filename
        try:
            upgrade_from_name: Any = int(upgrade_str)
        except ValueError:
            upgrade_from_name = upgrade_str

        # Try to infer state and upgrade from path segments
        state: Optional[str] = None
        upgrade_from_dir: Optional[Any] = None
        for part in p.parts:
            if part.startswith("state="):
                state = part.split("=", 1)[1]
            elif part.startswith("upgrade="):
                val = part.split("=", 1)[1]
                try:
                    upgrade_from_dir = int(val)
                except ValueError:
                    upgrade_from_dir = val

        # Prefer upgrade inferred from directory; fall back to filename
        upgrade_id = upgrade_from_dir if upgrade_from_dir is not None else upgrade_from_name

        rows.append(
            {
                "building_id": bldg_id,
                "upgrade_id": upgrade_id,
                "state": state,
                "file_path": p,
            }
        )

    ts_index = pd.DataFrame(rows)
    print("[build_timeseries_index] Found timeseries files:", ts_index.shape[0])
    return ts_index


def load_timeseries_for_buildings(
    ts_index: pd.DataFrame,
    building_ids: Optional[List[int]] = None,
    n_files: Optional[int] = None,
) -> pd.DataFrame:
    """
    Load timeseries for a subset of buildings into a single pandas DataFrame.

    Parameters
    ----------
    ts_index : DataFrame
        Output of build_timeseries_index() with columns:
        ['building_id', 'upgrade_id', 'file_path', 'state'].
    building_ids : list[int] or None
        If provided, restrict to this set of building IDs.
    n_files : int or None
        If provided, load at most n_files buildings (helpful to avoid
        loading too many into memory at once).

    Returns
    -------
    DataFrame with columns including:
      - building_id
      - upgrade_id
      - (plus original columns from each parquet, e.g. Time/TimeUTC/TimeDST, out.*)
    """
    subset = ts_index.copy()

    if building_ids is not None:
        subset = subset[subset["building_id"].isin(building_ids)]

    if n_files is not None:
        subset = subset.head(n_files)

    dfs = []
    for _, row in subset.iterrows():
        path = row["file_path"]
        bldg_id = row["building_id"]
        upgrade_id = row["upgrade_id"]

        print(f"[load_timeseries_for_buildings] Reading {path.name} ...")
        table = pq.read_table(path)
        df = table.to_pandas()

        # Attach building info to each row
        df["bldg_id"] = bldg_id  # keep original naming you used downstream
        df["building_id"] = bldg_id
        df["upgrade_id"] = upgrade_id

        dfs.append(df)

    if not dfs:
        print("[load_timeseries_for_buildings] No files selected, returning empty DataFrame")
        return pd.DataFrame()

    ts_df = pd.concat(dfs, ignore_index=True)
    print("[load_timeseries_for_buildings] Combined timeseries shape:", ts_df.shape)
    return ts_df


def load_state_aggregates(state: str = "MA") -> Optional[pd.DataFrame]:
    """
    Load state-level aggregate timeseries for a given state (if present).

    Files live under:
      OEDIDataset/timeseries_aggregates/by_state/state=XX/*.csv

    Returns
    -------
    DataFrame or None if no files found.
    """
    agg_dir = ROOT / "timeseries_aggregates" / "by_state" / f"state={state}"
    if not agg_dir.exists():
        print("[load_state_aggregates] Aggregate directory does not exist:", agg_dir)
        return None

    csv_files = sorted(agg_dir.glob("*.csv"))
    if not csv_files:
        print("[load_state_aggregates] No CSV aggregate files found in:", agg_dir)
        return None

    dfs = []
    for p in csv_files:
        print(f"[load_state_aggregates] Reading {p.name} ...")
        df = pd.read_csv(p)
        df["source_file"] = p.name
        dfs.append(df)

    agg_df = pd.concat(dfs, ignore_index=True)
    print("[load_state_aggregates] Combined aggregate shape:", agg_df.shape)
    return agg_df


def load_all() -> Dict[str, Any]:
    """
    Convenience function to load:
      - metadata
      - dictionaries
      - timeseries index (any states present under timeseries_individual/by_state)
      - state aggregates for MA by default

    Returns a dict:
      {
        "metadata": DataFrame or None,
        "data_dictionary": DataFrame or None,
        "enumeration_dictionary": DataFrame or None,
        "timeseries_index": DataFrame,
        "state_aggregates": DataFrame or None,
      }
    """
    print("=== Loading OEDI dataset pieces ===")
    meta_df = load_metadata()
    dicts = load_dictionaries()
    ts_index = build_timeseries_index()
    agg_df = load_state_aggregates(state="MA")

    all_data: Dict[str, Any] = {
        "metadata": meta_df,
        "data_dictionary": dicts.get("data_dictionary"),
        "enumeration_dictionary": dicts.get("enumeration_dictionary"),
        "timeseries_index": ts_index,
        "state_aggregates": agg_df,
    }

    print("=== Done loading OEDI dataset pieces ===")
    return all_data


if __name__ == "__main__":
    # Example usage when you run this script directly:
    all_data = load_all()

    meta = all_data["metadata"]
    ts_index = all_data["timeseries_index"]

    print("\n--- Quick peek ---")
    if meta is not None:
        print("Metadata columns (first 10):", list(meta.columns[:10]))
        print(meta.head())

    print("\nTimeseries index (first 5):")
    print(ts_index.head())

    # Load a small sample of timeseries for exploration
    print("\nLoading timeseries for first 3 buildings in the index...")
    sample_ts = load_timeseries_for_buildings(ts_index, n_files=3)
    print(sample_ts.head())