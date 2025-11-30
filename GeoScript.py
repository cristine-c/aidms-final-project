"""
GeoScript.py - Download and prepare geographic boundary files for Massachusetts

This script downloads US Census Bureau shapefiles for creating choropleth maps:
1. County boundaries (fine resolution - 14 counties)
2. PUMA boundaries (coarse resolution - larger regions)

Files are downloaded, extracted, and organized in the 'Shapefiles/' directory
(sibling to aidms-final-project, same pattern as OEDIDataset).

Run this once before creating geographic visualizations.
"""

import urllib.request
import zipfile
from pathlib import Path


# ---------------- CONFIG ----------------
# Local root: Shapefiles folder outside the git repo (sibling to aidms-final-project)
LOCAL_ROOT = Path(__file__).parent.parent / "Shapefiles"
LOCAL_ROOT.mkdir(parents=True, exist_ok=True)

# Download URLs
# Counties: Cartographic boundary file (500k resolution)
COUNTY_URL = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_county_500k.zip"
# PUMA: TIGER/Line shapefile for Massachusetts (state code 25)
PUMA_URL = "https://www2.census.gov/geo/tiger/TIGER2020/PUMA/tl_2020_25_puma10.zip"

print(f"Using local root: {LOCAL_ROOT}")
print()


def download_file(url, destination):
    """Download a file from URL to destination path."""
    print(f"Downloading: {url}")
    print(f"Destination: {destination}")
    
    try:
        # Add headers to avoid redirects
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            with open(destination, 'wb') as out_file:
                out_file.write(response.read())
        
        file_size = destination.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"✓ Downloaded successfully ({file_size:.2f} MB)\n")
        
        # Verify it's actually a zip file
        if file_size < 0.1:
            print(f"⚠ Warning: File size suspiciously small ({file_size:.2f} MB)")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Download failed: {e}\n")
        return False


def extract_zip(zip_path, extract_to):
    """Extract ZIP file to specified directory."""
    print(f"Extracting: {zip_path.name}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Count extracted files
        extracted_files = list(extract_to.glob('*'))
        print(f"✓ Extracted {len(extracted_files)} files to {extract_to}\n")
        return True
    except Exception as e:
        print(f"✗ Extraction failed: {e}\n")
        return False


def main():
    """Main function to download and organize shapefile data."""
    
    print("=" * 80)
    print("GEOGRAPHIC BOUNDARY FILE DOWNLOAD SCRIPT")
    print("Massachusetts County and PUMA Shapefiles")
    print("=" * 80)
    print()
    
    # Create subdirectories
    counties_dir = LOCAL_ROOT / "counties"
    puma_dir = LOCAL_ROOT / "puma"
    counties_dir.mkdir(parents=True, exist_ok=True)
    puma_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created/verified directories\n")
    
    # Temporary ZIP file paths
    county_zip = LOCAL_ROOT / "counties.zip"
    puma_zip = LOCAL_ROOT / "puma.zip"
    
    print("-" * 80)
    print("STEP 1: Downloading County Boundaries (All US Counties)")
    print("-" * 80)
    if download_file(COUNTY_URL, county_zip):
        print("-" * 80)
        print("STEP 2: Extracting County Boundaries")
        print("-" * 80)
        extract_zip(county_zip, counties_dir)
        
        # Clean up ZIP file
        county_zip.unlink()
        print("✓ Cleaned up temporary ZIP file\n")
    
    print("-" * 80)
    print("STEP 3: Downloading PUMA Boundaries (Massachusetts Only)")
    print("-" * 80)
    if download_file(PUMA_URL, puma_zip):
        print("-" * 80)
        print("STEP 4: Extracting PUMA Boundaries")
        print("-" * 80)
        extract_zip(puma_zip, puma_dir)
        
        # Clean up ZIP file
        puma_zip.unlink()
        print("✓ Cleaned up temporary ZIP file\n")
    
    # Summary
    print("=" * 80)
    print("DOWNLOAD COMPLETE - SUMMARY")
    print("=" * 80)
    
    # Check county files
    county_shp = counties_dir / "cb_2022_us_county_500k.shp"
    if county_shp.exists():
        print(f"✓ County shapefile: {county_shp}")
        # List all county-related files
        county_files = list(counties_dir.glob("cb_2022_us_county_500k.*"))
        print(f"  - {len(county_files)} supporting files (.shx, .dbf, .prj, etc.)")
    else:
        print("✗ County shapefile not found")
    
    # Check PUMA files
    puma_shp = puma_dir / "tl_2020_25_puma10.shp"
    if puma_shp.exists():
        print(f"✓ PUMA shapefile: {puma_shp}")
        # List all PUMA-related files
        puma_files = list(puma_dir.glob("tl_2020_25_puma10.*"))
        print(f"  - {len(puma_files)} supporting files (.shx, .dbf, .prj, etc.)")
    else:
        print("✗ PUMA shapefile not found")

if __name__ == "__main__":
    main()
