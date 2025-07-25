# SCS_API
Analysis of hazard data related to severe convective storms

## Getting Started
 This script uses data from the artemis cat bond deal directory
 * (https://www.artemis.bm/deal-directory/)    
 Data transcribed into the file cat_bond_database.xlsx by William Ratcliffe
 

### Dependencies

Python Libraries:

* requests
* csv
* zipfile
* time
* pandas
* numpy

### Executing program

To download daily from NOAA wind/hail/tornado reports from 2004-present, run:   

```
python3 -W ignore download_noaa_daily_storm_reports.py
```
This will create 3 folders called hail_reports, wind_reports, tornado_reports, which contain daily data on severe convective storm observations.    

To download annual NCEI reports from 1950-2024, run:

```
python3 -W ignore download_NCEI_storm_reports.py
```

This will create a NCEI_storm_reports folder with a CSV file for each year
It has been modified to only include severe convective storm events

To download convective storm outlook shapefiles, run:

```
python3 -W ignore download_convective_outlook.py
```

This will create a folder called convective_outlooks, which contain daily forecasts of the spatial area where convective storms may occur

To get the NCEI_PPH, run the cells in the PPH/PPH_NCEI.ipynb notebook. This will generate the csv files with the values for each day. Then the below cell will generate the annual mean events for each year. color coded.