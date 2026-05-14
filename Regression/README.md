# 'SCS_2015_2024_data.csv' Explanation of Variables. 

## All the Columns 
- YEAR
- Begin_Date
- BDD
- BDD_Losses
- Hail_Pop_PPH_Sum
- Torn_Pop_PPH_Sum
- Wind_Pop_PPH_Sum
- All_Pop_PPH_Sum
- Hail_Building_PPH_Sum
- Torn_Building_PPH_Sum
- Wind_Building_PPH_Sum
- All_Building_PPH_Sum
- Num_Hail
- Num_Wind
- Num_Torn
- cat_risk 
- torn_prob
- wind_prob
- hail_prob
- centroid_lat 
- centroid_lat_center
- spread_lat
- centroid_lon
- centroid_lon_center
- spread_lon
- abs_days_from_may15
- abs_days_from_july1


## YEAR / Begin_Date (NOAA)
- YEAR: Contains the year in which the SCS events occurred. 
- Begin_Date: Contains the date in which the SCS event occurred, in YYYYMMDD format. Meaning 20150102 represents the storms on 2015 January 2nd

## BDD / BDD_Losses (NOAA) 
- BDD: Boolean indicator (0 or 1) for Billion Dollar Disaster events. 0 represents that there was no BDD were occurring on that date. 1 means a BDD event was occurring. This is the variable that our regression attempts to predict.
- BDD_Losses: If an event is BDD (1), records the losses of these events. Losses are reported in millions. Meaning, 2069.0 represents damages of 2.069.0 billion. If BDD was 0, then BDD_Losses will also show 0. This does not mean there were 0 dollars in damage, rather it did not meet the Billion Dollar threshold. For example, If a day had 500 million in damage, it would be excluded. Additional note, BDD_Losses are CPI-adjusted. To access the Unadjusted Cost, go to the source at the bottom.

It is important to note that BDD events are typically over the course of multiple days, for example from 20150407 to 20150409, the BDD_Losses of 2069.0 are cumulative of the three events, rather than losses of 2069.0 each day.

## PPH Data
Practically Perfect Hindcasts (PPHs) are found through NOAA Daily Storm reports. In this dataset we take these PPH grids, and weigh them by exposure data (Buildings and Population) into a similar sized grid through element-wise multiplication.

## PPH Weighted by Population (NOAA + Nasa) 
- Hail_Pop_PPH_Sum
- Torn_Pop_PPH_Sum
- Wind_Pop_PPH_Sum
- All_Pop_PPH_Sum

These use population data, aggregated by Nasa via (https://www.earthdata.nasa.gov/data/projects/gpw). Using our desired grid size, we tally the population counts within the grid cells. These use population counts from 2020, the midpoint between our years of interest (2015-2024)

## PPH Weighted by Buildings (NOAA + Microsoft)
- Hail_Building_PPH_Sum
- Torn_Building_PPH_Sum
- Wind_Building_PPH_Sum
- All_Building_PPH_Sum

These use building data, aggregated by Microsoft Satellite data via (https://github.com/microsoft/USBuildingFootprints). Using our desired grid size, we tally the buildings within the grid cells and measure the total surface area of the roofs. 

In our Regression, we found that using Population weighted, rather than building weighted, proved to be more effective in predicting BDD. Subsequently, Our Building_PPH_Sums aren't in the final product, but could perhaps be useful in other contexts.

## Number of reports (NOAA)
- Num_Hail
- Num_Wind
- Num_Torn

NOAA counts the number of each type of report for each day. On 20150102, Num_Wind has 7.0 meaning there were 7 reports of Straight-line winds. On the same day, Num_Hail has 0, meaning there were 0 hail reports. 

## Convective Outlooks (NOAA) 
- cat_risk: Variable that ranges from 0 - 6, with 0 representing no outlooks were issued, while 6 represents a very large risk of storms occurring.
- torn_prob
- wind_prob
- hail_prob

All of these are sourced from NOAA convective outlooks. Typically, Outlooks represent the forecast the day before the storm event occurs, but in this dataset these variables are for this day. Meaning, on 20150102, cat_risk being 1 means the day prior predicted this, rather than it representing the day after 20150102.

torn_prob, wind_prob, and hail_prob represents the probability / percent chance that one of these events occurs within 25 miles of a given point, with 2–60% for tornado, and 5–60% for wind/hail.

In our Regression, we only use cat_risk, as the other three variables are virtually absorbed. 

## Locations (NOAA) 
- centroid_lat 
- centroid_lat_center
- spread_lat
- centroid_lon
- centroid_lon_center
- spread_lon

I would look at All_Centroid_Locations.png, in Figures -> locations for visual. 

centroid_lat / centroid_lon: the average latitude / longitude of all the reports on that day. 

centroid_lat_center / centroid_lon_center: The deviation of that day's storm centroid from the 2015–2024 average centroid latitude/longitude. Looking at All_Centroid_Locations.png, we can see a majority of BDD reports are relatively clustered.

spread_lat / spread_lon: Standard deviation of the latitude/longitude across all storm reports on that day, measuring how geographically dispersed the day's storm activity was.

The Regression uses 'centroid_lat_center', 'centroid_lon_center', and 'log_spread_lat' (a simple log of spread_lat). This is because storms closer to the core region and more geographically spread are more likely to hit densely insured areas across multiple states, increasing the probability of a BDD.

## Seasonality 
- abs_days_from_may15
- abs_days_from_july1

I would look at Seasonality and Average Reports folders in Figures. Typically Hail and Tornadoes peak around May 15th, while Wind peaks around July 1st. Including these "days_from" allows our results to be normally distributed and to account for seasonality. 

In the Regression, 'abs_days_from_may15' is used standalone, while 'abs_days_from_july1' is multiplied by 'Num_Wind' and the result is used.

# Summary of Data sources 

Data sources are from the following. In the cases of the PPHs, you need the data from that source to run the code that creates them. Furthermore, I would have the 'filtered' dataset from Jim's code downloaded, but simply  contains all the report types and locations

- YEAR                      : NOAA, from Begin_Date
- Begin_Date                : NOAA, https://www.ncei.noaa.gov/access/billions/events
- BDD                       : NOAA, https://www.ncei.noaa.gov/access/billions/events
- BDD_Losses                : NOAA, https://www.ncei.noaa.gov/access/billions/events
- Hail_Pop_PPH_Sum          : NASA, https://www.earthdata.nasa.gov/data/projects/gpw
- Torn_Pop_PPH_Sum          : NASA, https://www.earthdata.nasa.gov/data/projects/gpw
- Wind_Pop_PPH_Sum          : NASA, https://www.earthdata.nasa.gov/data/projects/gpw
- All_Pop_PPH_Sum           : NASA, https://www.earthdata.nasa.gov/data/projects/gpw
- Hail_Building_PPH_Sum     : MSFT, https://github.com/microsoft/USBuildingFootprints
- Torn_Building_PPH_Sum     : MSFT, https://github.com/microsoft/USBuildingFootprints
- Wind_Building_PPH_Sum     : MSFT, https://github.com/microsoft/USBuildingFootprints
- All_Building_PPH_Sum      : MSFT, https://github.com/microsoft/USBuildingFootprints
- Num_Hail                  : NOAA, Filtered dataset
- Num_Wind                  : NOAA, Filtered dataset
- Num_Torn                  : NOAA, Filtered dataset
- cat_risk                  : NOAA, https://www.spc.noaa.gov/products/outlook/archive
- torn_prob                 : NOAA, https://www.spc.noaa.gov/products/outlook/archive
- wind_prob                 : NOAA, https://www.spc.noaa.gov/products/outlook/archive
- hail_prob                 : NOAA, https://www.spc.noaa.gov/products/outlook/archive
- centroid_lat              : NOAA, Filtered dataset
- centroid_lat_center       : NOAA, Filtered dataset
- spread_lat                : NOAA, Filtered dataset
- centroid_lon              : NOAA, Filtered dataset
- centroid_lon_center       : NOAA, Filtered dataset
- spread_lon                : NOAA, Filtered dataset
- abs_days_from_may15       : Self
- abs_days_from_july1       : Self

Both the NASA population data and the Microsoft Building data turned into grids are located in MiscData. The raw data is very large. Otherwise, the code downloading "Begin_Date, BDD, BDD_Losses", and the "cat_risk, torn_prob, wind_prob, hail_prob" will be seperately uploaded. 


