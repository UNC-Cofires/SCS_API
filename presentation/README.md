# Maps annualized hail and PPH values over a single day
Presentation_hail gives you 15% severity hail, using NOAA_pph, from 2012-2024, with points on Chicago, Denver, and Dallas 

presentation_oneday gives you the NOAA pph values for one specific day. 

## Getting Started
First, you must have ran "solvepph_noaa.py" and have gotten "noaa_pph" as an output folder
Then, you must have nam212.nc downloaded as well. This is the 40km grid spacing

Make sure you have both "noaa_pph" and "nam212.nc" within same folder as these files when you run them.

### Dependencies
Python Libraries:
* numpy
* os
* pandas
* xarray
* matplotlib
* cartopy
* datetime
