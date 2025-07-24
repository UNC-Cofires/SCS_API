"""
Same as the other convective outlook but only geting 1200z day 1 to 1200z day 2 files
Only downloading day1otlk folders/filers also
From 2024 to 2010 inclusive because somehow earlier than that there's nothing to download
"""

import requests
import csv
import zipfile
import io
import os
import time

url = 'https://spc.noaa.gov/products/outlook/archive/'
# create directory to store downloaded data files
output_dir = 'convective_outlooks_only1200z'
os.makedirs(output_dir, exist_ok=True)

# loop through all the pages in the archive
for year_use in range(2024, 2009, -1):
    year_dir = os.path.join(output_dir, str(year_use))
    os.makedirs(year_dir, exist_ok=True)
    
    for month_use in range(0, 12):
        month_dir = os.path.join(year_dir, str(month_use + 1))
        os.makedirs(month_dir, exist_ok=True)
        file_read_failure = []
        
        for day_use in range(0, 31):
            date_script = str(year_use).zfill(4) + str(month_use + 1).zfill(2) + str(day_use + 1).zfill(2)
            print(f"Processing: {year_use} {month_use + 1} {day_use + 1}")
            
            # Only process forecast_day1 (forecast_day = 0)
            forecast_day = 0
            forecast_script = 'day' + str(forecast_day + 1) + 'otlk_'
            
            # Only process 12:00 (forecast_time = 12, minute_use = '00')
            forecast_time = 12
            minute_use = '00'
            forecast_check_top = str(forecast_time).zfill(2) + minute_use  # This creates '1200'
            
            full_url = url + '/' + str(year_use).zfill(4) + '/' + forecast_script + date_script + '_' + forecast_check_top + '-shp.zip'
            
            # for each page, make a new request to the API
            file_found = True
            try:
                response = requests.get(full_url)
            except:
                file_found = False
                
            if response.status_code == 200 and file_found:
                file_found = True
                try:
                    z = zipfile.ZipFile(io.BytesIO(response.content))
                except:
                    # this will error if you are rate limited by the API
                    # (in which case increase time.sleep(X) value of X)
                    file_found = False
                    print(f"  Failed to extract ZIP for {full_url}")
            
                # if data exists, store in directory
                if file_found:
                    forecast_dir = os.path.join(month_dir, 'forecast_day' + str(forecast_day + 1))
                    hour_dir = os.path.join(forecast_dir, forecast_script + date_script + '_' + forecast_check_top)
                    os.makedirs(forecast_dir, exist_ok=True)
                    os.makedirs(hour_dir, exist_ok=True)
                    
                    # Check if files already exist to avoid re-downloading
                    existing_files = os.listdir(hour_dir)
                    if existing_files:
                        print(f"  Skipping {hour_dir} - files already exist")
                    else:
                        z.extractall(hour_dir)
                        print(f"  Downloaded and extracted: {hour_dir}")
                else:
                    # make note of any file that did not download
                    filename = forecast_script + date_script + '_' + forecast_check_top + '-shp.zip'
                    file_read_failure.append(filename)
                    print(f"  Failed to download: {filename}")
            else:
                # File not found (404) or other error
                filename = forecast_script + date_script + '_' + forecast_check_top + '-shp.zip'
                print(f"  File not available: {filename} (Status: {response.status_code if 'response' in locals() else 'No response'})")
                
            # Add small delay to be respectful to the server
            #time.sleep(0.5)
        
        # Write error log for each month
        if file_read_failure:
            error_file = f'file_read_errors_{year_use}_{month_use + 1}.txt'
            with open(error_file, 'w') as file:
                for item in file_read_failure:
                    file.write(f"{item}\n")
            print(f"  Error log written: {error_file}")
        
        print(f"Completed month {month_use + 1} of year {year_use}")
        
    print(f"Completed year {year_use}")
    #time.sleep(2)  # Longer delay between years

print("Download completed!")