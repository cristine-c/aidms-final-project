# Fairness and Efficiency in Energy Pricing Models
**Authors:** Cristine Chen (G), Clara Park (G), Manuel Valencia (G)

Historically, residential customers have paid for electricity using flat tariffs, where the price per kWh is constant over time. As renewables, virtual power plants (VPPs), and distributed energy resources (DERs) grow, utilities are shifting toward inclining block rates (IBR) and time-varying rates (TVR) such as time-of-use (ToU) and real-time pricing (RTP). Our project uses real load-profile data and utility rate structures to simulate household bills under multiple tariff types and evaluate both **efficiency** (e.g., cost recovery, peak reduction) and **fairness** (e.g., distribution of energy burdens across groups). This README outlines what data we need, what steps we’ll take, and which plots we should produce to answer our core research questions.

---

## Core Research Questions

**RQ1 — Pricing Model Comparison:**  
How do different retail electricity tariff structures (flat rate, time-of-use, dynamic/real-time pricing) affect total annual bills and the distribution of costs across households with different characteristics?

**RQ2 — Distributional Fairness:**  
How are electricity bills and energy burdens distributed across demographic groups (income levels, renter vs owner, urban/suburban/rural) under different pricing models?

---

## RQ1 – Pricing Model Comparison

**Goal:** Compare how different retail electricity tariff structures (flat rate, time-of-use, dynamic/real-time pricing) affect household-level annual bills using real load-profile data from Massachusetts residential buildings.

### A. Data Sources

- **Load profiles:** NREL ResStock AMY2018 dataset - 15-minute interval electricity consumption for 11,000+ Massachusetts residential buildings
- **Tariff structures:**
  - **Flat rate:** $0.233/kWh (Massachusetts average residential rate)
  - **Time-of-Use (TOU):** Daytime 8 AM-8 PM (\$0.1211/kWh), evenings/weekends/holidays (\$0.0991/kWh), peak events (\$0.6137/kWh for up to 8 hours on up to 30 Conservation Days per year, ~5 hours/week average)
  - **Dynamic pricing:** ISO New England real-time locational marginal pricing (RT-LMP) data aligned to 15-minute intervals

### B. Completed Analysis Steps

- [x] **Load and validate household data**  
  Loaded 11,000+ Massachusetts residential building load profiles (15-minute intervals, full year); validated data completeness and identified 500-building representative sample for initial analysis.

- [x] **Implement tariff calculators**  
  Built optimized vectorized bill calculation functions for flat, TOU, and dynamic pricing; implemented chunked processing for memory-efficient computation on full dataset.

- [x] **Compute annual bills under all tariffs**  
  Calculated total annual electricity costs for each household under all three pricing structures.

- [x] **Analyze bill distributions**  
  Generated summary statistics, histograms, and boxplots showing annual bill distributions across all households and by Federal Poverty Level groups.

- [x] **Compare tariff impacts**  
  Identified winners and losers under TOU vs flat and dynamic vs flat/TOU; quantified bill changes and percentage of households benefiting from each alternative tariff.

- [x] **Visualize cost per kWh**  
  Analyzed effective cost per kWh by income group for each tariff to understand rate progressivity.

### C. Completed Analysis

**Visualizations:**
- Annual bill distributions (histograms and boxplots) for all three tariffs
- Sample building time-series load profiles with overlaid pricing periods
- Annual bills by Federal Poverty Level (boxplots for each tariff)
- Cost per kWh by income group (boxplots showing effective rates)
- Winner/loser analysis comparing bill changes between tariffs
- Correlation analysis between tariff costs

**Analytical Methods:**
- Descriptive statistics (mean, median, percentiles) for annual bills under each tariff
- Comparative analysis identifying percentage of households that save/lose money under alternative tariffs
- Quantile-based analysis to exclude extreme outliers from visualizations
- Effective rate calculation (annual cost / annual kWh) to understand rate structure impacts

---

## RQ2 – Distributional Fairness Across Groups

**Goal:** Analyze how different pricing models (flat, TOU, dynamic) distribute electricity bills and energy burdens across demographic household groups (income levels, tenure status, urban/suburban/rural) and identify which groups face disproportionate costs under each tariff structure.

### A. Data Sources

- **Load profiles and bills:** From RQ1 analysis (annual bills under flat, TOU, dynamic tariffs)
- **Demographic attributes** from NREL ResStock metadata:
  - Representative income (proxy for household income)
  - Federal Poverty Level categories (0-100%, 100-150%, 150-200%, 200-300%, 300-400%, 400%+)
  - Tenure status (owner vs. renter)
  - PUMA metro status (urban/principal city, suburban, rural/not in metro)
  - County and PUMA geographic identifiers
  - Building type (single-family detached/attached, multi-family, mobile home)

### B. Steps to Answer RQ2

- [x] **Create synthetic population with demographic attributes**  
  Used NREL ResStock metadata including representative income, federal poverty level, tenure status, PUMA metro status, building type, and county.

- [x] **Compute bills under multiple pricing models**  
  Computed annual bills for all households under flat, TOU, and dynamic tariff structures.

- [x] **Calculate energy burdens**  
  Computed PIU (Percentage of Income spent on Utilities) for each household under all three tariffs as `(annual_bill / annual_income) × 100%`.

- [x] **Segment households into groups**  
  Grouped households by:
  - Federal Poverty Level (0-100%, 100-150%, 150-200%, 200-300%, 300-400%, 400%+)
  - Tenure (owner vs. renter)
  - Metro status (urban/principal city, suburban/not in principal city, rural/not in metro)
  - Building type (single-family detached, single-family attached, multi-family, mobile home)

- [x] **Compute distributional statistics by group**  
  For each group and tariff, calculated:
  - Mean and median annual bills and PIU
  - Summary statistics (count, std, min, max)
  - Share of households with high energy burden (>3% and >6% PIU)
  - Bill and burden distributions with boxplots

- [x] **Identify disparities and vulnerable groups**  
  Identified key disparities:
  - 96.9% of 0-100% FPL households exceed 6% burden under flat tariff
  - Renters face 2× higher burden than owners (35.4% vs 17.2% exceed 6% under flat)
  - Rural households face highest burden (38.9% exceed 6% under flat vs 22.3% suburban)

- [x] **Analyze tariff progressivity**  
  Computed progressivity index (slope of cost vs. income relationship) showing flat rate is most progressive, dynamic pricing is least progressive.

- [x] **Create geographic visualizations**  
  Generated choropleth maps showing energy consumption and PIU across Massachusetts counties (13/14 with data) and PUMA regions (45/52 with data).
### C. Completed Analysis

**Energy Burden Calculations:**
- PIU (Percentage of Income for Utilities) calculated for all households under all three tariffs
- Formula: `(annual_bill / annual_income) × 100%`
- Summary statistics by Federal Poverty Level, tenure, and metro status
- Boxplots showing PIU distributions across demographic groups
- High-burden prevalence analysis using 3% and 6% thresholds
- PIU vs. income scatter plots to visualize inverse relationship

**Distributional Analysis:**
- PIU reduction analysis comparing dynamic/TOU vs. flat rates
- Building type analysis showing burden patterns across housing types
- Regional statistics aggregated by county (average energy consumption, total consumption, average PIU)
- Comparison of burden prevalence across tenure and metro status categories

**Geographic Visualizations:**
- County-level choropleth maps (4 maps: avg energy, total energy, PIU flat, PIU dynamic)
- PUMA-level choropleth maps (same 4 metrics at finer geographic resolution)
- Downloaded Census Bureau TIGER shapefiles for Massachusetts counties and PUMA boundaries
- Geographic matching logic to align building data with boundary files
- Summary tables showing statistics for regions with available data

**Progressivity Analysis:**
- Linear regression: Annual Cost = α + β·(Federal Poverty Level Group)
- Progressivity index calculated as slope (β) for each tariff
- Comparison showing relative progressivity across tariff structures
- Visualization of cost trends and progressivity index bars

---

## Future Work

The following analyses could extend this work:

**System-Level Efficiency Analysis:**
- Aggregate household loads to compute system-level load curves
- Calculate peak demand reduction by tariff type
- Compute load factor and cost recovery metrics
- Analyze revenue volatility across tariffs
- Quantify price signal alignment with wholesale market costs

**Temporal Analysis:**
- Monthly and seasonal variation in bills and energy burdens
- Identify periods of peak financial hardship for vulnerable groups
- Analyze bill volatility under dynamic pricing across seasons

**Statistical Modeling:**
- Gini coefficient calculations for bills and energy burdens
- Formal variance decomposition (ANOVA) to quantify demographic factors' contribution to bill variation
- Intersectional analysis (e.g., low-income renters in rural areas)
- Demand response modeling with price elasticity assumptions

**Efficiency-Fairness Trade-offs:**
- Multi-criteria analysis combining efficiency metrics (from system analysis) with fairness metrics
- Pareto frontier identification for tariff design
- Sensitivity analysis on different policy weights

**Policy Extensions:**
- Hybrid tariff design (e.g., TOU with low-income discounts)
- Bill assistance program targeting based on burden analysis
- Rate design modifications to improve progressivity while maintaining efficiency

---

## Repository Structure

- **`RQ.ipynb`**: Main Jupyter notebook containing all data loading, bill calculations, distributional analysis, and visualizations
- **`loadOEDIData.py`**: Module for loading NREL ResStock metadata and time-series data
- **`tariff_calculator.py`**: Optimized bill calculation functions for flat, TOU, and dynamic pricing
- **`loadGeoData.py`**: Functions for loading Census Bureau shapefiles (counties and PUMA boundaries)
- **`GeoScript.py`**: Standalone script to download and extract geographic boundary data
- **`load_rtp.py`**: Script to convert ISO-NE RT-LMP data from Excel to CSV format
- **`OEDIDSampleScript.py`**: Script to download sample of individual building timeseries from NREL ResStock
- **`OEDIDExtrasScript.py`**: Script to download metadata, dictionaries, and state-level aggregates from NREL ResStock
- **`2018_smd_hourly.xlsx`**: ISO New England 2018 hourly RT-LMP data (source for dynamic pricing)
- **`RT_LMP_kWh.csv`**: Processed real-time locational marginal pricing data ($/kWh) for 2018
- **`README_OEDI.txt`**: Documentation for NREL ResStock dataset structure and data access
- **`OEDIDataset/`**: NREL ResStock data (downloaded via OEDIDSampleScript.py and OEDIDExtrasScript.py)
- **`Shapefiles/`**: Census geographic boundaries for Massachusetts (downloaded via GeoScript.py)

---

## Setup Instructions

1. **Clone repository**: Clone this repository inside a parent folder (e.g., `aidms/`). The scripts will create `OEDIDataset/` and `Shapefiles/` directories outside the git-tracked project folder to avoid syncing large data files.

2. **Install necessary libraries**: The project requires pandas, pyarrow, geopandas, numpy, and matplotlib. Install all dependencies with:
   ```
   pip install pandas pyarrow geopandas numpy matplotlib
   ```

3. **Download timeseries data**: Run `python OEDIDSampleScript.py` to download individual building timeseries (default: 100 buildings from Massachusetts). Edit `N_FILES` in the script to download more or fewer buildings.

4. **Download metadata**: Run `python OEDIDExtrasScript.py` to download ResStock metadata, data dictionaries, and state-level aggregates.

5. **Download shapefiles**: Run `python GeoScript.py` to download Census Bureau geographic boundaries for Massachusetts (counties and PUMA regions).

6. **Run analysis notebook**: Open `RQ.ipynb` and:
   - Edit Cell 6 to set the number of buildings to sample for analysis
   - Edit Cell 11: Set `load_full = True` to load all downloaded timeseries, or `False` to load only the sampled buildings

