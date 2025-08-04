# Severe Convective Storm Analysis Framework (SCS_API)

## Project Overview

A comprehensive geospatial analysis system for severe convective storm hazards with two primary components:

1. **Forecast Verification Framework**: Evaluates forecast skill through rigorous comparison of Practically Perfect Hindcasts (PPH) against operational Storm Prediction Center (SPC) convective outlooks. Processes multi-decadal datasets (2010-2024) to quantify forecasting performance using industry-standard verification metrics.

2. **Total Insured Value (TIV) Loss Model**: A machine learning-based catastrophe modeling system that predicts property-level insurance losses from hail events. Combines meteorological data (MESH radar, PPH forecasts), property characteristics (tax assessments, building features), and spatial factors to estimate percentage and dollar losses for individual properties.


## Architecture

### High-Level Design

```
Data Acquisition → Processing Pipeline → Verification Engine → Analysis & Visualization
      ↓                    ↓                    ↓                      ↓
  - NOAA/NCEI APIs    - Grid Alignment     - Brier Scores      - Comparative Maps
  - SPC Shapefiles    - Projection        - Performance       - Time Series  
  - Storm Reports       Handling            Diagrams          - Overlap Analysis
  - Property Data     - Feature            - TIV Loss         - Loss Predictions
  - MESH Radar          Engineering          Modeling          - Risk Assessment
```

### Core Components

1. **Data Acquisition Layer** (`download_*.py`): Retrieve data from NOAA, NCEI, and SPC data sources
2. **Spatial Processing Engine** (`hail_analysis.ipynb`): NAM212 grid operations with shapefile-to-grid conversion and projection management  
3. **Verification Framework** (`hail_validation.ipynb`): Statistical analysis engine implementing multiple verification metrics
4. **TIV Loss Model** (`TIV_model.ipynb`): Random Forest-based catastrophe model for property-level hail damage prediction
5. **Caching System** (`cache/`): Pickle-based persistence layer reducing computation time for iterative analysis

### Data Flow Architecture

- **NAM212 Grid System**: 129×185 cells at ~40km resolution covering CONUS
- **Temporal Alignment**: 1200z-1200z verification windows matching operational forecast cycles
- **Spatial Buffering**: 40km verification radius around storm reports following SPC standards
- **Fair Comparison Logic**: Ensures identical validation sets and climatological baselines across all models

## Installation & Setup

### System Requirements

- **Python**: 3.8+ (tested on 3.9-3.11)
- **Memory**: 16GB+ recommended for full dataset processing
- **Storage**: 50GB+ for complete historical data archive
- **OS**: macOS, Linux (Windows untested but likely compatible)

### Dependencies

```bash
# Core scientific computing stack
pip install numpy pandas xarray netcdf4

# Geospatial processing
pip install geopandas shapely pyproj cartopy

# Visualization and analysis
pip install matplotlib seaborn jupyter

# Statistical computing
pip install scikit-learn scipy tqdm

# Machine learning for TIV model
pip install xgboost lightgbm

# Data acquisition
pip install requests beautifulsoup4
```

### Environment Setup

1. **Clone Repository**:
   ```bash
   git clone https://github.com/UNC-Cofires/SCS_API.git
   cd SCS_API
   ```

2. **Configure Paths**: Update `BASE_PATH` in analysis notebooks to match your installation directory

3. **Create Directory Structure**:
   ```bash
   mkdir -p {cache,analysis_outputs/{figures,brier_analysis}}
   mkdir -p NCEI_storm_reports/{hail_filtered,sighail_filtered}
   mkdir -p PPH/{NCEI_PPH,Sighail_PPH}
   mkdir -p dallas_property_analysis/{tax_appraisal_value,building_footprints}
   mkdir -p radar_data
   ```

4. **Download Reference Grid**:
   Ensure `nam212.nc` coordinate reference file is available in the `PPH/` directory

## Usage Examples

### Data Acquisition

```bash
# Download historical storm reports (1950-2024)
python download_NCEI_storm_reports.py

# Download daily storm observations (2004-present)  
python download_noaa_daily_storm_reports.py

# Download SPC convective outlook shapefiles
python download_convective_outlook_only1200z.py
```

### PPH Generation

```python
# Execute in PPH/PPH_NCEI.ipynb notebook
# Generates daily probability grids from storm reports
# Accounts for full temporal extent of hail events (1200z-1200z)
# Output: daily CSV files with NAM212 grid probabilities
```

### Comparative Analysis

```python
# Launch hail_analysis.ipynb for comprehensive comparison
jupyter notebook hail_analysis.ipynb

# Key analysis components:
# 1. Mean annual event day maps (PPH vs Outlook)
# 2. Area coverage time series (monthly/yearly trends)
# 3. Daily spatial overlap analysis (Jaccard Index)
# 4. Statistical performance metrics
```

### Verification Workflow

```python
# Execute hail_validation.ipynb for rigorous skill assessment
# Implements fair comparison methodology with identical baselines
# Generates Brier Skill Scores, Performance Diagrams, ROC curves
# Provides seasonal and monthly resolution analysis
```

### TIV Loss Modeling

```python
# Launch TIV_model.ipynb for catastrophe loss modeling
jupyter notebook TIV_model.ipynb

# Model pipeline:
# 1. Property data integration (tax assessments, building footprints)
# 2. Weather feature extraction (MESH, PPH, NCEI reports) 
# 3. Feature engineering (12-dimensional feature vectors)
# 4. Random Forest training on synthetic loss targets
# 5. Property-level loss prediction and validation

# Key features:
# - Weather: MESH hail size, PPH probability, storm distance/duration
# - Property: Market value, age, construction quality, frame type
# - Building: Footprint area, complexity, local density
```

### TIV Model Architecture

The TIV loss model implements a Random Forest regressor with the following mathematical framework:

**Loss Prediction**: `TIV_Loss = F(X) × 100%` where F maps 12-dimensional feature vectors to loss percentages

**Feature Categories**:
- **Weather Features** (4D): MESH hail size, PPH probability, NCEI distance, storm duration
- **Property Features** (5D): Market value, building age, living area, construction quality, frame type  
- **Building Features** (3D): Footprint area, complexity ratio, local building density

**Training Labels**: Physics-based synthetic losses incorporating hail size thresholds, age vulnerability, construction factors, and exposure characteristics

**Validation**: Currently demonstrated on May 19-20, 2023 Texas hailstorm with Dallas County property data

## Testing & CI

### Verification Approach

**Statistical Validation**: All verification metrics cross-validated against published benchmarks. Brier Skill Scores tested against known climate datasets.

**Data Integrity**: Automated checks for grid alignment, coordinate system consistency, and temporal continuity.

**Performance Regression**: Benchmark tests for core processing functions to detect performance degradation.


## Architecture

### Grid

**NAM212**: 40km resolution provides optimal balance between computational efficiency and meteorological relevance. Grid spacing matches SPC's operational verification standards.

**Projection Handling**: Converts between Lambert Conformal Conic (2010-2019) and WGS84 (post-2020) coordinate systems ensures temporal consistency across projection changes.

### Verification Methodology

**Comparison Framework**: Identical validation sets and climatological baselines eliminate systematic bias in skill score comparisons.

**Multi-Metric Approach**: Combines probabilistic (Brier Skill Score) and categorical (Performance Diagram) verification for comprehensive assessment.

**Temporal Resolution**: Monthly analysis reveals seasonal patterns obscured in annual aggregates while maintaining statistical significance.

### TIV Model Methodology

**Synthetic Training Approach**: Model currently trained on physics-based synthetic loss labels rather than actual insurance claims, incorporating domain knowledge about hail damage patterns, building vulnerability, and exposure factors.

**Feature Engineering**: 12-dimensional feature vectors combining meteorological data (MESH, PPH, storm proximity), property characteristics (value, age, construction), and spatial factors (building density, footprint complexity).

**Machine Learning Architecture**: Random Forest regressor optimized for property-level loss prediction with hyperparameters tuned for generalization across property types and storm intensities.

**Current Limitations**: Single storm validation (May 2023 Texas event), Dallas County geographic scope, and synthetic rather than actual loss training data. Future development will incorporate multi-storm validation and actual insurance claim data.

## License & Attribution

### License
This project is available under the MIT License - see LICENSE file for details.

### Data Sources & Attribution

- **NCEI Storm Reports**: National Centers for Environmental Information storm database
- **SPC Convective Outlooks**: NOAA Storm Prediction Center operational forecasts  
- **NAM212 Grid**: North American Mesoscale model coordinate system
- **MESH Radar Data**: Multi-Radar Multi-Sensor maximum hail size estimates
- **Property Tax Data**: Dallas County Appraisal District (DCAD) assessments and building characteristics
- **Building Footprints**: Microsoft Global ML Building Footprints dataset
- **PPH Data**: Practically Perfect Hindcast probability grids
- **Artemis Cat Bond Data**: Referenced for historical context (see papers/ directory)

### Citation

If using this framework in research or operational applications, please cite:
```
SCS_API: Severe Convective Storm Analysis Framework
University of North Carolina Institute for Risk Management and Insurance Innovation
https://github.com/UNC-Cofires/SCS_API
```



        