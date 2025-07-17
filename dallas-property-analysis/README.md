## dallas_compute_3vars.py
This file combines Dallas parcel data (market value and build year) with Microsoft's GlobalMLBuildingFootprints (location) 
To run you must need: 
- have Texas data from Microsoft downloaded and converted to Dallas
- have Dallas county parcels downloaded
- Change pathways

## dallas_from_texas.py 
File converts Microsoft data from all of texas, to just Dallas. 

## dallas_histogram.py
After running dallas_compute_3vars.py, this file returns a histogram showcasing build_dates of properties 
Only 11% of build dates are within the parcels dataset and an outside source will be needed 

## dallas_parcel_info.py 
Opens up the dallas parcels and shows what infomation is in the columns 

## dallas_visualized.py 
Gives a visualization of the "dallas_compute_3vars" output, showcasing that the coordinates are indeed corret. 

## What we have vs what we need 
What we have 
- locations
- market values
- 11% of construction dates
  
Missing 
- roof types
- The rest of construction dates
- building height

### Dependencies
Python Libraries:
* geopandas
* pandas
* shapely
* json
* matplotlib
