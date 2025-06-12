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
* geopandas
* matplotlib
* Shapely
* Pathlib
* Datetime


### Executing program

To download wind/hail/tornado reports from 2004-present, run:   

```
python3 -W ignore read_storm_report_api.py
```
This will create 3 folders called hail_reports, wind_reports, tornado_reports, which contain daily data on severe convective storm observations.    
To download convective storm outlook shapefiles, run:

```
python3 -W ignore read_convective_outlook.py 2024
```

This will create a folder called convective_outlooks, which contain daily forecasts of the spatial area where convective storms may occur


To continue downloading if your convective outlooks were cutoff
```
python3 auto_detect_convective_outlook.py
```

To only download a single year
```
python3 auto_detect_convective_outlook.py {year}
```

To download from a specifc point
```
python3 auto_detect_convective_outlook.py {year} {month} {date}
```

