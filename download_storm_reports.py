# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 13:38:26 2025

@author: amonkar

The objective of this script is to download the Strom Reports data from 1950-2024. 
The data are downloaded as individual zip files for each year. 
The files are unziped and the zipped files are deleted (Optional Key-Flag)
A single CSV file is compiled which consists of the Hail, Tornado and other reports from 1950-2021

The following will be customized
1. Working directory. Set location based on your folder structure. 
2. The file_pattern, the last number thread refers to the date when the files were updated. The current version c20250401 refers to the last updated on April 1st 2025. 

"""
#%%
# Load necessary libraries
import os
import requests
import gzip
import shutil
import pandas as pd
from tqdm import tqdm  # For progress tracking


# Set the working directory path
working_directory = r'C:\Users\amonkar\Documents\GitHub\SCS_API' #Set to your folder pathway
os.chdir(working_directory)


# Check if the storm directory exists
data_dir = "data/Storm_Reports"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"Created directory: {data_dir}")
else:
    print(f"Directory already exists: {data_dir}")


#%% DOWNLOAD THE STORM REPORTS DATASET

# Define the year range (Note:- The current year is not available)
start_year = 1950
end_year = 2025

# Loop through each year to download and process data
for year in range(start_year, end_year):
  
    # Construct the URL for the current year
    base_url = "https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/"
    file_pattern = f"StormEvents_details-ftp_v1.0_d{year}_c20250401.csv.gz"  #Note this URL might/change change so update accordingly
    
    if year == 2020:
        file_pattern = f"StormEvents_details-ftp_v1.0_d{year}_c20240620.csv.gz"
    
    # Combine the URLs
    year_url = base_url + file_pattern
    
    # File paths
    zip_file = f"data/Storm_Reports/StormEvents_{year}.csv.gz"
    csv_file = f"data/Storm_Reports/Storm_Reports_{year}.csv"
    
    # Try to download the file
    try:
        # Download the file
        print(f"Downloading data for {year}...")
        response = requests.get(year_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Save the downloaded file
        with open(zip_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the gzipped file
        with gzip.open(zip_file, 'rb') as f_in:
            with open(csv_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"Successfully downloaded and processed data for {year}")
        
    except Exception as e:
        # If there's an error (e.g., file not found), print a message
        print(f"Error processing year {year}: {str(e)}")

print("Download process completed.")

#%% Identity the event types across the years 
# The goal is to identify the event types assocaited with SCS events.
event_types_by_year = set()

for year in range(start_year, end_year):
    
    print(year)
    
    # Read the CSV file
    reports = pd.read_csv(f"data/Storm_Reports/Storm_Reports_{year}.csv")
    
    #Identify the unique storm tyes for that year
    event_types = reports['EVENT_TYPE'].unique()
    
    #Add to the main list
    event_types_by_year.update(event_types)
    

#Create the list of event types which qualify as SCS events
#Note:- Additional information on the storm reports classification is present here - https://www.ncdc.noaa.gov/stormevents/pd01016005curr.pdf
SCS_events = ['HAIL FLOODING','HAIL/ICY ROADS','Hail','High Wind','Lightning','Marine Hail',
              'Marine High Wind','Marine Lightning', 'Marine Strong Wind', 'Strong Wind',
              'THUNDERSTORM WIND/ TREE', 'THUNDERSTORM WIND/ TREES','THUNDERSTORM WINDS FUNNEL CLOU',
              'THUNDERSTORM WINDS HEAVY RAIN','THUNDERSTORM WINDS LIGHTNING', 'THUNDERSTORM WINDS/ FLOOD',
              'THUNDERSTORM WINDS/FLASH FLOOD','THUNDERSTORM WINDS/FLOODING', 'THUNDERSTORM WINDS/HEAVY RAIN',
              'TORNADO/WATERSPOUT', 'TORNADOES, TSTM WIND, HAIL', 'Thunderstorm Wind', 'Tornado', ]


#%% Create a single dataframe
combined_scs_report = []

# Subset to SCS Events types (Manually added above) -- CONFIRM TBD
for year in range(start_year, end_year):
    print(f"{year}...") 
    reports = pd.read_csv(f"data/Storm_Reports/Storm_Reports_{year}.csv") 
    filtered_reports = reports[reports['EVENT_TYPE'].isin(SCS_events)]
    combined_scs_report.append(filtered_reports)
    
#Combine the reports
combined_reports = pd.concat(combined_scs_report, ignore_index=True)   
combined_reports.to_csv("data/All_SCS_Reports.csv", index=False) 


# Calculate the fraction (percentage) of each event type
event_counts = combined_reports['EVENT_TYPE'].value_counts()
total_events = len(combined_reports)
event_fractions = round(100*event_counts / total_events,2)
    
    
    
    
    
    
    
    
    
    
    
    
    
    