# Solving PPHs / Graphing PPHs
"solvepph_NCEI.py" / "solvepph_noaa.py" solves PPH for either NCEI or NOAA data. 

"pph_graphed" results in graphing these PPH values annualized over course of years. 

## Getting Started
First, you must have downloaded the storm reports from NOAA or NCEI. 
- NCEI : ("filtered" folder)
- NOAA : (tornado_reports, wind_reports, hail_reports)
  
Then, you must have your desired grid spacing downloaded (from the "grids" folder) and adjust "solvepph_XXXX.py" and the graphing code to reflect this. This can be done by adjusting "grid_ds" with the pathway to your grid. 

Next, adjust "sigma_grid_units" and "grid_spacing_km" in solvepph_XXXX to match your desired sigma value and the grid spacing chosen. 

If you wish to best reflect the research paper "Practically Perfect Hindcasts of Severe Convective Storms", in solvepph_NCEI / solvepph_noaa, keep "sigma_grid_units" * "grid_spacing_km" = 120. (ex, with 40km grids, we want sigma = 3). 

## Using the outputs 

I have already provided the outputs from NCEI and NOAA. The conditions I used can be found within the "README" in each folder.
- NCEI_pph_outputs : 1950 - 2024 
- NOAA_pph_outputs : January 1st 2025 - May 31st 2025 

When using "pph_annual_graph.py", assuming you wish to use 2025 data, it will automatically distinguish between the two. 
Ensure you have set the correct pathways set before running.

### Dependencies
Python Libraries:
* numpy
* os
* pandas
* xarray
* matplotlib
* cartopy
* datetime

