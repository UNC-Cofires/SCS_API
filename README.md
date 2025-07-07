# Solving PPHs / Graphing PPHs
"solvepph_NCEI.py" / "solvepph_noaa.py" solves PPH for either NCEI or NOAA data. 

"pph_graphed" results in graphing these PPH values annualized over course of years. 

## Getting Started
First, you must have downloaded the storm reports from NOAA or NCEI. 
- NOAA : (tornado_reports, wind_reports, hail_reports)
- NCEI : ("filtered" folder)
  
Then, you must have your desired grid spacing downloaded (from the "grids" folder) and adjust "solvepph_XXXX.py" and the graphing code to reflect this. This can be done by adjusting "grid_ds" with the pathway to your grid. 

Next, adjust "sigma_grid_units" and "grid_spacing_km" in solvepph_XXXX to match your desired sigma value and the grid spacing chosen. 

If you wish to best reflect the research paper "Practically Perfect Hindcasts of Severe Convective Storms", in solvepph_NCEI / solvepph_noaa, keep "sigma_grid_units" * "grid_spacing_km" = 120. (ex, with 40km grids, we want sigma = 3). 

### Dependencies
Python Libraries:
* numpy
* os
* pandas
* xarray
* matplotlib
* cartopy
* datetime

