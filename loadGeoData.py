"""
loadGeoData.py - Load geographic boundary data for Massachusetts analysis

This module provides functions to load Census Bureau shapefiles downloaded by GeoScript.py
and prepare them for choropleth mapping and spatial analysis.

Usage:
    from loadGeoData import load_ma_counties, load_ma_puma
    
    ma_counties = load_ma_counties()
    ma_puma = load_ma_puma()
"""

import geopandas as gpd
from pathlib import Path


# ---------------- CONFIG ----------------
# Shapefiles root (sibling to aidms-final-project)
SHAPEFILES_ROOT = Path(__file__).parent.parent / "Shapefiles"

# Shapefile paths
COUNTY_SHP = SHAPEFILES_ROOT / "counties" / "cb_2022_us_county_500k.shp"
PUMA_SHP = SHAPEFILES_ROOT / "puma" / "tl_2020_25_puma10.shp"


def load_us_counties(verbose=True):
    """
    Load US county boundaries (all states).
    
    Parameters:
    -----------
    verbose : bool, default=True
        If True, print loading progress messages
        
    Returns:
    --------
    geopandas.GeoDataFrame
        All US county boundaries with columns:
        - STATEFP: State FIPS code (e.g., '25' for Massachusetts)
        - COUNTYFP: County FIPS code
        - NAME: County name
        - geometry: Polygon geometry
    """
    if verbose:
        print(f"Loading US county boundaries from: {COUNTY_SHP}")
    
    if not COUNTY_SHP.exists():
        raise FileNotFoundError(
            f"County shapefile not found: {COUNTY_SHP}\n"
            f"Please run GeoScript.py first to download the data."
        )
    
    counties = gpd.read_file(COUNTY_SHP)
    
    if verbose:
        print(f"✓ Loaded {len(counties):,} counties across all US states")
    
    return counties


def load_ma_counties(verbose=True):
    """
    Load Massachusetts county boundaries only.
    
    Parameters:
    -----------
    verbose : bool, default=True
        If True, print loading progress messages
        
    Returns:
    --------
    geopandas.GeoDataFrame
        Massachusetts county boundaries (14 counties)
    """
    counties = load_us_counties(verbose=verbose)
    
    # Filter for Massachusetts (STATEFP == '25')
    ma_counties = counties[counties['STATEFP'] == '25'].copy()
    
    if verbose:
        print(f"✓ Filtered to {len(ma_counties)} Massachusetts counties")
        print(f"  Counties: {', '.join(sorted(ma_counties['NAME'].tolist()))}")
    
    return ma_counties


def load_ma_puma(verbose=True):
    """
    Load Massachusetts PUMA (Public Use Microdata Area) boundaries.
    
    PUMAs are larger geographic areas used for Census data aggregation,
    providing a coarser regional view than counties.
    
    Parameters:
    -----------
    verbose : bool, default=True
        If True, print loading progress messages
        
    Returns:
    --------
    geopandas.GeoDataFrame
        Massachusetts PUMA boundaries with columns:
        - PUMACE10: PUMA code
        - NAMELSAD10: PUMA name
        - geometry: Polygon geometry
    """
    if verbose:
        print(f"Loading Massachusetts PUMA boundaries from: {PUMA_SHP}")
    
    if not PUMA_SHP.exists():
        raise FileNotFoundError(
            f"PUMA shapefile not found: {PUMA_SHP}\n"
            f"Please run GeoScript.py first to download the data."
        )
    
    puma = gpd.read_file(PUMA_SHP)
    
    if verbose:
        print(f"✓ Loaded {len(puma)} PUMA regions for Massachusetts")
    
    return puma


def load_all_geo_data(verbose=True):
    """
    Load all geographic boundary data (counties and PUMA).
    
    Parameters:
    -----------
    verbose : bool, default=True
        If True, print loading progress messages
        
    Returns:
    --------
    dict
        Dictionary with keys:
        - 'counties': All US counties GeoDataFrame
        - 'ma_counties': Massachusetts counties GeoDataFrame
        - 'ma_puma': Massachusetts PUMA GeoDataFrame
    """
    if verbose:
        print("=" * 80)
        print("LOADING GEOGRAPHIC BOUNDARY DATA")
        print("=" * 80)
        print()
    
    geo_data = {
        'counties': load_us_counties(verbose=verbose),
        'ma_counties': None,  # Will be filtered from counties
        'ma_puma': load_ma_puma(verbose=verbose)
    }
    
    # Filter MA counties from all counties
    if verbose:
        print()
    geo_data['ma_counties'] = geo_data['counties'][
        geo_data['counties']['STATEFP'] == '25'
    ].copy()
    
    if verbose:
        print(f"✓ Filtered to {len(geo_data['ma_counties'])} Massachusetts counties")
        print()
        print("=" * 80)
        print("GEOGRAPHIC DATA LOADED SUCCESSFULLY")
        print("=" * 80)
    
    return geo_data


# Convenience function for getting county name normalization
def get_county_name_variants(county_name):
    """
    Get common variants of a county name for matching.
    
    Handles variations like:
    - "Suffolk" vs "Suffolk County"
    - Different capitalizations
    
    Parameters:
    -----------
    county_name : str
        County name to normalize
        
    Returns:
    --------
    list of str
        List of possible name variants
    """
    variants = []
    
    # Add original
    variants.append(county_name)
    
    # Add with/without "County"
    if "County" in county_name:
        variants.append(county_name.replace(" County", ""))
    else:
        variants.append(f"{county_name} County")
    
    # Add lowercase versions
    variants.extend([v.lower() for v in variants])
    
    # Add title case versions
    variants.extend([v.title() for v in variants])
    
    return list(set(variants))  # Remove duplicates


if __name__ == "__main__":
    # Test loading
    print("Testing loadGeoData.py...")
    print()
    
    # Load MA counties
    ma_counties = load_ma_counties()
    print(f"\nMA Counties shape: {ma_counties.shape}")
    print(f"Columns: {list(ma_counties.columns)}")
    print(f"\nSample data:")
    print(ma_counties[['NAME', 'STATEFP', 'COUNTYFP']].head())
    
    print("\n" + "=" * 80 + "\n")
    
    # Load MA PUMA
    ma_puma = load_ma_puma()
    print(f"\nMA PUMA shape: {ma_puma.shape}")
    print(f"Columns: {list(ma_puma.columns)}")
    print(f"\nSample data:")
    print(ma_puma[['PUMACE10', 'NAMELSAD10']].head())
