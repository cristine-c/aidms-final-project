# Fairness and Efficiency in Energy Pricing Models
**Authors:** Cristine Chen (G), Clara Park (G), Manuel Valencia (G)

Historically, residential customers have paid for electricity using flat tariffs, where the price per kWh is constant over time. As renewables, virtual power plants (VPPs), and distributed energy resources (DERs) grow, utilities are shifting toward inclining block rates (IBR) and time-varying rates (TVR) such as time-of-use (ToU) and real-time pricing (RTP). Our project uses real load-profile data and utility rate structures to simulate household bills under multiple tariff types and evaluate both **efficiency** (e.g., cost recovery, peak reduction) and **fairness** (e.g., distribution of energy burdens across groups). This README outlines what data we need, what steps we’ll take, and which plots we should produce to answer our core research questions.

---

## Core Research Questions

1. **RQ1 — Pricing Model Comparison:**  
   How do different retail electricity tariff structures (flat rate, time-of-use, dynamic/real-time pricing) affect total annual bills and the distribution of costs across households with different characteristics?

2. **RQ2 — Distributional Fairness:**  
   How are electricity bills and energy burdens distributed across demographic groups (income levels, renter vs owner, urban/suburban/rural) under different pricing models?

3. **RQ3 — Risk, Volatility, and Trade-offs:**  
   Under (different pricing models), are there models that perform reasonably well on both efficiency and fairness, or are trade-offs unavoidable?

---

## RQ1 – Efficiency of Pricing Models

**Goal:** Compare different retail electricity tariff structures (flat rate, time-of-use, dynamic/real-time pricing) on household bill impacts and distributional outcomes using real load-profile data from Massachusetts residential buildings.

### A. Dataset / Feature Requirements

- Household-level time-series load profiles (15-min or hourly) for at least one representative year.
- Current tariff definitions for each pricing model:
  - **Flat rate:** single price per kWh (e.g., $0.12/kWh).
  - **IBR (Inclining Block Rate):** block thresholds (e.g., 0-500 kWh, 500-1000 kWh, >1000 kWh) and per-block prices.
  - **ToU (Time-of-Use):** on-peak, off-peak, and mid-peak time windows with associated prices (including weekday/weekend distinctions).
  - **RTP (Real-Time Pricing):** hourly price time series aligned with load data (from wholesale market or utility RTP tariff).
- System cost data:
  - Marginal generation cost ($/kWh) or time-varying wholesale electricity prices.
  - Capacity cost proxy ($/kW-month) for peak demand costs.
  - Total system costs for cost-recovery analysis.

### B. Steps to Answer RQ1

- [x] **Select region and sample households**  
  Selected Massachusetts (MA) residential buildings from NREL ResStock AMY2018 dataset; using 500-building sample with option to scale to full 11,000+ MA buildings.

- [x] **Gather current pricing data**  
  Obtained Massachusetts utility tariff structures for flat, ToU rates; collected ISONE real-time locational marginal pricing (RT-LMP) data for dynamic pricing analysis.

- [x] **Align and clean time series**  
  Loaded and validated 15-minute load profiles for each household with complete year of data; aligned timestamps with ToU windows and RTP prices, handling weekday/weekend distinctions.

- [x] **Implement tariff calculators**  
  Built modular pricing functions (flat, TOU, dynamic) with optimized vectorized operations; implemented generic bill calculator that processes all tariffs in single pass.

- [ ] **Compute economic efficiency metrics**  
  For each pricing model:
  - Aggregate household loads to compute system-level load curves.
  - Calculate total revenue from bills and total system costs.
  - Identify system peak demand and compare across tariffs.
  - Compute load-shifting metrics (peak-to-average ratio, load factor).

- [ ] **Compare and rank pricing models**  
  Build a summary table comparing efficiency metrics across all tariff types; identify which models best align revenue with costs and reduce peak demand.

### C. Metrics & Plots for RQ1

**Metrics (compute all 3):**
- **Cost recovery ratio:** `total_revenue / total_cost` for each pricing model (target: close to 1.0 for revenue neutrality).
- **Peak reduction (vs. flat baseline):** `(Peak_flat - Peak_tariff) / Peak_flat` × 100% for IBR, ToU, and RTP.
- **Economic efficiency score:** Combined metric incorporating cost recovery accuracy and peak reduction effectiveness.

**Additional metrics:**
- **Load factor:** `average_load / peak_load` by tariff (higher is better for grid efficiency).
- **Revenue volatility:** Standard deviation of monthly revenues across the year by tariff.
- **Price signal alignment:** Correlation between prices and system marginal costs (particularly for ToU and RTP).

**Plots:**
- **Cost recovery comparison:** Bar chart showing revenue, cost, and revenue/cost ratio for each pricing model.
- **System peak demand:** Bar chart comparing peak demand (kW) across all four tariff types.
- **Aggregate load curves:** Line plots of average daily load profiles by tariff (overlay weekday/weekend if applicable).
- **Load factor by tariff:** Bar chart showing load factors for each pricing model.
- *(Optional)* **Efficiency scorecard:** Radar/spider chart comparing all four tariffs across multiple efficiency dimensions.

### D. Nice-to-Have Extras for RQ1 (If Time Allows)

- **Seasonal analysis:** Compare efficiency metrics across summer vs. winter months to assess seasonal performance differences.
- **Sensitivity analysis:** Test how efficiency metrics change with different cost assumptions (e.g., higher capacity costs, different marginal cost profiles).
- **Simple price elasticity:** Model modest demand response (5-10% of flexible load shifting) under ToU/RTP and recalculate efficiency gains.
- **Inter-utility comparison:** If data available, compare how the same tariff types perform in different utility service territories.
- **Marginal vs. average pricing:** Analyze efficiency differences between marginal-cost-based and average-cost-based rate structures.

---

## RQ2 – Distributional Fairness Across Groups

**Goal:** Analyze how different pricing models (flat, TOU, dynamic) distribute electricity bills and energy burdens across demographic household groups (income levels, tenure status, urban/suburban/rural) and identify which groups face disproportionate costs under each tariff structure.

### A. Dataset / Feature Requirements

- Same household load profiles as RQ1.
- Current pricing model data (focus on the dominant/default tariff in the study region, e.g., flat or ToU).
- Household demographic and structural attributes:
  - **Income level:** Annual household income or income bracket (e.g., <$25k, $25k-$50k, $50k-$100k, >$100k).
  - **Tenure status:** Renter vs. homeowner.
  - **Region/climate zone:** Geographic location or climate zone (e.g., hot-dry, cold, temperate).
  - **Building characteristics:** Square footage, age, insulation level (if available).
  - *(Optional)* Urban/suburban/rural classification.
- Income distribution data (e.g., from RECS, Census) to assign realistic income values.

**Minimum schema per household:**
```text
household_id
load_profile (time series)
annual_income
income_bracket (low/middle/high)
renter_owner
region/climate_zone
building_sqft
```

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
### C. Metrics & Plots for RQ2

**Metrics (compute all):**
- **Energy burden by group:** Mean and median `(annual_bill / annual_income) × 100%` for each demographic segment.
- **High-burden prevalence:** Fraction of households in each group with energy burden ≥6% and ≥10%.
- **Disparity ratios:**
  - Low-income vs. high-income average burden ratio.
  - Renter vs. owner average bill ratio.
  - Regional/climate burden differences.
- **Inequality metrics:**
  - Gini coefficient of bills across all households.
  - Gini coefficient of energy burdens.
  - Coefficient of variation of bills by group.

**Plots:**
- **Bill distribution:** Histogram or kernel density plot of annual bills across all households; optionally overlay by income group.
- **Average bills by income group:** Grouped bar chart showing mean annual bills for low/middle/high-income households.
- **Energy burden by group:** Grouped bar chart of mean energy burden (%) by income level, tenure status, and region.
- **High-burden households:** Stacked or grouped bar chart showing percentage of households exceeding 6% and 10% burden thresholds, by group.
- **Box plots by group:** Box-and-whisker plots of bill distributions for each demographic segment.
- *(Optional)* **Burden vs. consumption scatter:** Scatter plot of energy burden vs. total kWh consumption, colored by income group.
- *(Optional)* **Inequality summary:** Bar chart comparing Gini coefficients of bills and burdens.

### D. Nice-to-Have Extras for RQ2 (If Time Allows)

- **Intersectional analysis:** Examine intersections of demographics (e.g., low-income renters in hot climates) to identify most vulnerable subgroups.
- **Variance decomposition:** Use ANOVA or regression to quantify how much of the variation in bills/burdens is explained by income, tenure, region, building characteristics, etc.
- **Temporal patterns:** Analyze monthly bill and burden variations to identify seasonal hardship patterns.
- **Geographic visualization:** If spatial data available, create maps showing average bills or energy burdens by ZIP code, county, or climate zone.
- **Burden sensitivity:** Test how burden distributions change with different income data sources or burden thresholds.
- **Comparison to other utilities:** Compare distributional outcomes to similar studies or utility benchmarks to contextualize findings.

---

## RQ3 – Efficiency-Fairness Trade-offs

**Goal:** Evaluate whether different pricing models can achieve both efficiency (from RQ1) and fairness (from RQ2) simultaneously, or whether trade-offs between these objectives are unavoidable; identify which models (if any) perform reasonably well on both dimensions.

### A. Dataset / Feature Requirements

- All data from RQ1 and RQ2:
  - Household load profiles and demographic attributes.
  - Bills computed under all four pricing models (flat, IBR, ToU, RTP).
  - Efficiency metrics (cost recovery, peak reduction) from RQ1.
  - Fairness metrics (energy burdens, disparity ratios) from RQ2.
- Monthly bills per household and tariff for temporal analysis.
- Combined efficiency-fairness dataset linking each tariff to its performance on both dimensions.

**Minimum schema per (household, tariff):**
```text
household_id
tariff_type
monthly_bills[1..12]
annual_bill
annual_income
energy_burden
group_labels (income_group, renter_owner, region)
```

**Summary metrics per tariff:**
```text
tariff_type
cost_recovery_ratio
peak_reduction_pct
mean_energy_burden
energy_burden_disparity_ratio
high_burden_share
```

### B. Steps to Answer RQ3

- [ ] **Compile efficiency metrics from RQ1**  
  For each pricing model, collect key efficiency metrics (cost recovery ratio, peak reduction %, load factor).

- [ ] **Compile fairness metrics from RQ2**  
  For each pricing model, collect key fairness metrics (mean energy burden by income group, burden disparity ratio, high-burden share).

- [ ] **Normalize and score pricing models**  
  Create normalized scores (0-1 or 0-100) for each metric to enable comparison; optionally create composite efficiency and fairness scores.

- [ ] **Visualize efficiency-fairness trade-offs**  
  Plot pricing models on 2D scatter plots with efficiency on one axis and fairness on the other; identify Pareto-optimal or near-optimal models.

- [ ] **Assess trade-off severity**  
  Calculate correlations between efficiency and fairness metrics; determine if high-efficiency models systematically perform worse on fairness (negative correlation) or if some models achieve both.

- [ ] **Identify balanced pricing models**  
  Use multi-criteria decision analysis (e.g., weighted scoring, dominance analysis) to identify which models perform "reasonably well" on both objectives; test sensitivity to different weights on efficiency vs. fairness.

- [ ] **Analyze distributional impacts of efficient tariffs**  
  For the most economically efficient tariff(s), conduct detailed distributional analysis to understand which groups would benefit or suffer if that tariff were implemented universally.
### C. Metrics & Plots for RQ3

**Metrics:**
- **Composite efficiency score:** Weighted combination of cost recovery ratio and peak reduction (normalized).
- **Composite fairness score:** Weighted combination of mean energy burden, burden disparity ratio, and high-burden share (normalized, lower burden = higher score).
- **Trade-off ratio:** Ratio of efficiency score to fairness score for each tariff.
- **Pareto efficiency:** Identify tariffs that are not dominated by any other tariff on both dimensions.
- **Correlation coefficient:** Between efficiency and fairness scores across all tariff types.

**Plots:**
- **Efficiency vs. Fairness scatter plot:** X-axis = efficiency score, Y-axis = fairness score; plot all four pricing models; annotate Pareto-optimal models.
- **Multi-metric comparison:** Radar/spider chart comparing all four tariffs across 4-6 key metrics (cost recovery, peak reduction, mean burden, burden disparity, etc.).
- **Trade-off heatmap:** Heatmap showing each tariff's performance (color-coded) across efficiency and fairness dimensions.
- **Sensitivity analysis:** Line plots showing how tariff rankings change as weights on efficiency vs. fairness are varied.
- **Group-specific impacts:** For each tariff, show side-by-side bar charts of efficiency gains vs. fairness impacts (e.g., peak reduction % vs. burden increase % for low-income households).
- *(Optional)* **Scenario comparison:** Panel plots showing how trade-offs shift under different assumptions (e.g., with vs. without demand response, different cost structures).

### D. Nice-to-Have Extras for RQ3 (If Time Allows)

- **Multi-objective optimization framing:** Formulate as a constrained optimization problem (e.g., "maximize efficiency subject to fairness constraints") and identify feasible tariff designs.
- **Hybrid tariff design:** Explore whether combining elements of different tariffs (e.g., ToU with low-income discount, IBR with peak pricing) can improve trade-offs.
- **Stakeholder preference simulation:** Model how different stakeholder groups (utilities, low-income advocates, environmental groups) would rank tariffs based on their priorities.
- **Dynamic analysis:** Examine how efficiency-fairness trade-offs evolve over multiple years or under changing grid conditions (e.g., higher renewable penetration).
- **Policy constraint scenarios:** Test which tariffs meet specific policy goals (e.g., "≥15% peak reduction AND <20% of households with high burden").
- **Cost of fairness:** Quantify the efficiency loss (in $/year or % peak reduction) required to achieve specific fairness improvements.
- **Alternative fairness metrics:** Test how conclusions change using different fairness definitions (e.g., Rawlsian focus on worst-off group vs. utilitarian focus on average burden).

---

## How to Use This README

- Treat each RQ section as a **mini-project** with its own data needs, computation steps, metrics, and plots.
- At the start of the project, assign owners for each major chunk (e.g., data prep, tariff calculators, fairness metrics, plotting).
- As you work, add checkboxes and implementation notes under each step so the README becomes a living roadmap and progress tracker.


