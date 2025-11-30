"""
Tariff calculation and bill computation functions.

This module provides:
1. Pricing functions for different tariff structures (flat, TOU, dynamic)
2. Bill calculation utilities (single tariff or all tariffs)
3. Chunked processing for large datasets
4. Memory management helpers
"""

import pandas as pd
import numpy as np
import gc
from loadOEDIData import load_timeseries_for_buildings


# ===== PRICE DATA CACHE =====

class PriceDataCache:
    """
    Singleton-like cache for price data that needs to be loaded from disk.
    This prevents re-loading the same data on every tariff calculation.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._rtp_data = None
        self._initialized = True
    
    def get_rtp_data(self, rtp_csv: str = "RT_LMP_kWh.csv", verbose: bool = True) -> pd.DataFrame:
        """Load and cache RTP data, resampled to 15-minute intervals."""
        if self._rtp_data is None:
            if verbose:
                print(f"[PriceDataCache] Loading RTP data from {rtp_csv}...")
            rtp_df = pd.read_csv(rtp_csv, parse_dates=["timestamp"])
            rtp_df = rtp_df.set_index("timestamp").resample("15min").ffill()
            self._rtp_data = rtp_df
            if verbose:
                print(f"[PriceDataCache] RTP data cached ({len(self._rtp_data)} intervals)")
        return self._rtp_data
    
    def clear(self, verbose: bool = True):
        """Clear cached data to free memory if needed."""
        self._rtp_data = None
        if verbose:
            print("[PriceDataCache] Cache cleared")


# Global cache instance
_price_cache = PriceDataCache()


# ===== PRICING FUNCTIONS =====

def price_flat(ts_df: pd.DataFrame,
               meta_df: pd.DataFrame | None = None,
               base_rate: float = 0.119387342) -> pd.Series:
    """
    Flat tariff with seasonal rates (Massachusetts utility structure).

    Parameters
    ----------
    ts_df : DataFrame
        Must contain 'timestamp' and 'bldg_id' and 'kwh_total'.
    meta_df : DataFrame or None
        Not used in the simple version, but can be used if we ever want
        region- or customer-specific flat rates.
    base_rate : float
        Flat rate in $/kWh (not used; seasonal rates override).

    Returns
    -------
    Series of length len(ts_df) with the price for each row (interval).
    """
    time_windows = [
        ("2018-01-01", "2018-04-30", .12673),  # Jan 1–Apr 30
        ("2018-05-01", "2018-10-31", .10870),  # May 1–Oct 31
        ("2018-11-01", "2018-12-31", .13718)   # Nov 1–Dec 31
    ]

    # Pre-allocate array for better performance
    prices = np.zeros(len(ts_df), dtype=np.float64)
    timestamps = ts_df["timestamp"].values

    for start, end, rate in time_windows:
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        mask = (timestamps >= start_ts) & (timestamps < end_ts)
        prices[mask] = rate

    return pd.Series(prices, index=ts_df.index)


def price_tou_simple(ts_df: pd.DataFrame,
                     meta_df: pd.DataFrame | None = None,
                     offpeak_rate: float = 0.0991,
                     peak_rate: float = 0.1211,
                     peak_hours: tuple[int, int] = (8, 20),
                     conservation_rate: float = 0.6137,
                     conservation_hours: int = 8,
                     random_seed: int = 100) -> pd.Series:
    """
    Time-of-Use tariff with peak/off-peak pricing and conservation events.

    Parameters
    ----------
    ts_df : DataFrame
        Must contain 'timestamp' column.
    meta_df : DataFrame or None
        Optional metadata (not currently used).
    offpeak_rate : float
        Off-peak rate in $/kWh.
    peak_rate : float
        Peak rate in $/kWh (weekdays during peak hours).
    peak_hours : tuple[int, int]
        (start_hour, end_hour) for peak period (e.g., 8-20 means 8am-8pm).
    conservation_rate : float
        Special high rate during conservation events.
    conservation_hours : int
        Total hours of conservation events to randomly place.
    random_seed : int
        Random seed for reproducible conservation event placement.

    Returns
    -------
    Series of prices for each interval.
    """
    hours = ts_df["timestamp"].dt.hour.values
    is_weekend = ts_df["timestamp"].dt.weekday.values >= 5  # Saturday=5, Sunday=6
    start, end = peak_hours

    is_peak = (hours >= start) & (hours < end) & (~is_weekend)

    # Start with base TOU pricing (vectorized)
    prices = np.where(is_peak, peak_rate, offpeak_rate)

    # Apply conservation pricing to random peak intervals
    n_intervals = int(np.round(conservation_hours * 4))
    peak_indices = np.where(is_peak)[0]
    
    if len(peak_indices) > 0 and n_intervals > 0:
        # Find valid starting positions for conservation blocks
        max_start = len(prices) - n_intervals
        peak_set = set(peak_indices)
        
        # More efficient: only check positions that start in peak period
        possible_starts = []
        for idx in peak_indices:
            if idx <= max_start:
                # Check if entire block fits in peak hours
                if all((idx + k) in peak_set for k in range(n_intervals)):
                    possible_starts.append(idx)
        
        if possible_starts:
            # Shuffle and select non-overlapping blocks
            rng = np.random.default_rng(random_seed)
            rng.shuffle(possible_starts)
            
            num_trials = min(30, len(possible_starts))
            used = set()
            placed = 0
            
            for s in possible_starts:
                if placed >= num_trials:
                    break
                
                block = range(s, s + n_intervals)
                
                if not any(i in used for i in block):
                    prices[s : s + n_intervals] = conservation_rate
                    used.update(block)
                    placed += 1

    return pd.Series(prices, index=ts_df.index)


def price_dynamic_stub(ts_df: pd.DataFrame,
                       rtp_csv: str = "RT_LMP_kWh.csv",
                       meta_df: pd.DataFrame | None = None) -> pd.Series:
    """
    Dynamic pricing based on real-time locational marginal prices (LMP).

    Uses ISO New England real-time LMP data, resampled to 15-minute intervals.

    Parameters
    ----------
    ts_df : DataFrame
        Must contain 'timestamp' column.
    rtp_csv : str
        Path to CSV file with RTP data (columns: timestamp, RT_LMP_kWh).
    meta_df : DataFrame or None
        Optional metadata (not currently used).

    Returns
    -------
    Series of prices aligned with ts_df timestamps.
    """
    # Use cached RTP data instead of loading every time
    rtp_df = _price_cache.get_rtp_data(rtp_csv)
    
    # Align RTP prices with timestamps in ts_df
    rtp_aligned = rtp_df.reindex(ts_df["timestamp"].values, method="ffill")["RT_LMP_kWh"]

    return pd.Series(rtp_aligned.values, index=ts_df.index)


# ===== BILL CALCULATION =====

def apply_tariff(ts_df: pd.DataFrame,
                 price_func,
                 meta_df: pd.DataFrame | None = None,
                 tariff_name: str = "tariff") -> pd.DataFrame:
    """
    Apply a tariff pricing function to a load timeseries and compute annual bills.

    Parameters
    ----------
    ts_df : DataFrame
        Must contain at least:
          - 'bldg_id': building identifier
          - 'timestamp': datetime
          - 'kwh_total': total kWh in each 15-min interval
    price_func : callable
        Function with signature price_func(ts_df, meta_df=None, **kwargs)
        returning a Series of per-interval prices in $/kWh.
    meta_df : DataFrame or None
        Optional building-level metadata to pass into the pricing function.
        If used, meta_df should have a 'bldg_id' column.
    tariff_name : str
        Name of the tariff, used to label the 'annual_cost_<tariff_name>' column.

    Returns
    -------
    DataFrame with columns:
      - bldg_id
      - annual_kwh
      - annual_cost_<tariff_name>
    """
    # Compute price for each interval
    price_series = price_func(ts_df, meta_df=meta_df)
    
    # Cost per interval (vectorized, no intermediate column storage)
    cost_per_interval = ts_df["kwh_total"].values * price_series.values

    # Aggregate to annual per building
    annual = (
        pd.DataFrame({
            'bldg_id': ts_df["bldg_id"].values,
            'annual_kwh': ts_df["kwh_total"].values,
            f'annual_cost_{tariff_name}': cost_per_interval
        })
        .groupby("bldg_id", as_index=False)
        .sum()
    )

    return annual


def apply_all_tariffs(ts_df: pd.DataFrame,
                      meta_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Apply all tariffs (flat, TOU, dynamic) and return annual bills per building.

    This is the main function for computing bills across all pricing models.

    Parameters
    ----------
    ts_df : DataFrame
        Must contain 'bldg_id', 'timestamp', and 'kwh_total'.
    meta_df : DataFrame or None
        Optional building-level metadata.

    Returns
    -------
    DataFrame with one row per building:
        - bldg_id
        - annual_kwh
        - annual_cost_flat
        - annual_cost_tou
        - annual_cost_dynamic
    """
    # More memory-efficient: compute all tariffs in one pass through the data
    # Get building IDs and annual kWh once
    bldg_ids = ts_df["bldg_id"].values
    kwh_total = ts_df["kwh_total"].values
    
    # Compute prices for all tariffs
    prices_flat = price_flat(ts_df, meta_df=meta_df).values
    prices_tou = price_tou_simple(ts_df, meta_df=meta_df).values
    prices_dynamic = price_dynamic_stub(ts_df, meta_df=meta_df).values
    
    # Compute costs (vectorized)
    cost_flat = kwh_total * prices_flat
    cost_tou = kwh_total * prices_tou
    cost_dynamic = kwh_total * prices_dynamic
    
    # Create combined DataFrame for aggregation
    combined = pd.DataFrame({
        'bldg_id': bldg_ids,
        'annual_kwh': kwh_total,
        'annual_cost_flat': cost_flat,
        'annual_cost_tou': cost_tou,
        'annual_cost_dynamic': cost_dynamic
    })
    
    # Single groupby operation for all tariffs
    result = combined.groupby('bldg_id', as_index=False).sum()
    
    return result


# ===== CHUNKED PROCESSING FOR LARGE DATASETS =====

def compute_bills_chunked(
    ts_index: pd.DataFrame,
    elec_cols: list[str],
    meta_df: pd.DataFrame | None = None,
    chunk_size: int = 100,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Compute annual bills under all tariffs by processing buildings in chunks.

    Designed to handle large datasets (11,000+ buildings) efficiently.

    Parameters
    ----------
    ts_index : DataFrame
        Output of build_timeseries_index(), with at least:
          - 'building_id'
          - 'upgrade_id'
          - 'file_path'
    elec_cols : list of str
        Names of electricity end-use columns to sum into kwh_total.
    meta_df : DataFrame or None
        Optional building-level metadata (with 'bldg_id') to pass to tariffs.
    chunk_size : int
        How many buildings to process at a time.
    verbose : bool
        If True, print progress messages. Default is True.

    Returns
    -------
    DataFrame with one row per building:
        - bldg_id
        - annual_kwh
        - annual_cost_flat
        - annual_cost_tou
        - annual_cost_dynamic
    """
    n = len(ts_index)
    all_chunks = []

    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        sub_idx = ts_index.iloc[start:end]

        if verbose:
            print(f"[compute_bills_chunked] Buildings {start}–{end - 1} of {n}...")

        # Load timeseries for this chunk of buildings
        ts_chunk = load_timeseries_for_buildings(sub_idx, n_files=None, verbose=verbose)
        if ts_chunk.empty:
            continue

        # Ensure timestamp is datetime
        ts_chunk["timestamp"] = pd.to_datetime(ts_chunk["timestamp"])

        # Total whole-house kWh per interval
        ts_chunk["kwh_total"] = ts_chunk[elec_cols].sum(axis=1)

        # Apply all tariffs to this chunk
        bills_chunk = apply_all_tariffs(ts_chunk, meta_df=meta_df)

        all_chunks.append(bills_chunk)

        # Free memory from this chunk ASAP
        del ts_chunk, bills_chunk

    if not all_chunks:
        if verbose:
            print("[compute_bills_chunked] No chunks produced; returning empty DataFrame.")
        return pd.DataFrame()

    bills_all = pd.concat(all_chunks, ignore_index=True)
    return bills_all


# ===== MEMORY MANAGEMENT =====

def free_memory(verbose: bool = True):
    """
    Force garbage collection and clear the price cache.
    Use this between large operations if you're running low on memory.
    
    Parameters
    ----------
    verbose : bool
        If True, print progress messages. Default is True.
    """
    _price_cache.clear(verbose=verbose)
    gc.collect()
    if verbose:
        print("[free_memory] Memory freed")


def get_memory_usage():
    """
    Print approximate memory usage of key data structures.
    Requires the variables to be defined in the notebook scope.
    
    Note: This function uses globals() which only works in the notebook context.
    For accurate results, call this from within the notebook.
    """
    try:
        import sys
        
        if 'ts_sample' in globals():
            print(f"ts_sample: {sys.getsizeof(ts_sample) / 1024**2:.2f} MB")
        if 'meta_sample' in globals():
            print(f"meta_sample: {sys.getsizeof(meta_sample) / 1024**2:.2f} MB")
        if 'bills_with_meta' in globals():
            print(f"bills_with_meta: {sys.getsizeof(bills_with_meta) / 1024**2:.2f} MB")
        
        # Check cache status
        if _price_cache._rtp_data is not None:
            print(f"RTP cache: {sys.getsizeof(_price_cache._rtp_data) / 1024**2:.2f} MB")
        else:
            print("RTP cache: empty")
            
    except Exception as e:
        print(f"Could not compute memory usage: {e}")
