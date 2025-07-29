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


Folders descriptions:
**/analysis_outputs**
Stores the graphs from the analysis

**/cache**
Stores PKL cache data so you don't have to wait a million years everytime

**/NCEI_storm_reports**
    **/filtered**
    - Stores all the filtered storm reports wtih just the necessary columns
    - *Depreciated*
    **/hail_filtered**
    - Only has these columns for hail:[BEGIN_DATE_TIME, END_DATE_TIME, EVENT_TYPE, MAGNITUDE, LAT, LON]
    - The Lat Lon is average of the two
    **/sighail_filtered**
    - Same as hail_fitlered just 2inches and above hails 
    *All_SCS_Reports.csv*
    - Exactly what it sounds like
    *hail_filter_script.py*
    - Creates the hail_filtered csvs
    *sighail_filter_script.py*
    - Same, just for >2 inches hail

**/PPH**
    **/NCEI_PPH**
    - Stores all the storm events PPHs
    **/Sighail_PPH**
    - Stores the Sighail one who would've thought
    *PPH_NCEI.ipynb*
    - What changed from the Jack's old script:
        - 1200z-1200z
        - Accounts for all the time periods the hail existed not just that day
            - Increases the validity/brier score quite a bit
        - Instead of parsing the month name into the number, I realized they already have the Begin/End date so we're using that

**/Vertification**
    - All the notebooks used to verify data way at the beginning


        