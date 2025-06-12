import requests
import csv
import zipfile
import io
import os
import time
import sys

url = 'https://spc.noaa.gov/products/outlook/archive/'
# create directory to store downloaded data files
output_dir = 'convective_outlooks'
os.makedirs(output_dir, exist_ok = True)


# added argumnt to specify the exact year to download
if len(sys.argv) > 1 and sys.argv[1].lower() != 'all':
    try:
        years_to_download = [int(sys.argv[1])]
    except ValueError:
        print(f"Invalid year: {sys.argv[1]}")
        sys.exit(1)
else:
    years_to_download = range(2025, 2000, -1)


# loop through all the pages in the archive
for year_use in years_to_download:
  year_dir = os.path.join(output_dir, str(year_use))
  os.makedirs(year_dir, exist_ok = True)
  for month_use in range(0, 12):
    month_dir = os.path.join(year_dir, str(month_use + 1))
    os.makedirs(month_dir, exist_ok = True)
    file_read_failure = []
    for day_use in range(0, 31):
      date_script = str(year_use).zfill(4) + str(month_use + 1).zfill(2) + str(day_use + 1).zfill(2)
      print(year_use, end = " ")
      print(month_use, end = " ")
      print(day_use)
      for forecast_day in range(0, 8):
        forecast_script = 'day' + str(forecast_day + 1) + 'otlk_'
        for forecast_time in range(0, 24):
          for minute_use in ['00', '30']:
            forecast_check_top = str(forecast_time).zfill(2) + minute_use
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
                # this will error if you are rate limited by ERCOT
                # API (in which case increase time.sleep(X) value of X
                file_found = False
            
              # if data exists, store in directory
              if file_found:
                forecast_dir = os.path.join(month_dir, 'forecast_day' + str(forecast_day + 1))
                hour_dir = os.path.join(forecast_dir, forecast_script + date_script + '_' + forecast_check_top)
                os.makedirs(forecast_dir, exist_ok = True)
                os.makedirs(hour_dir, exist_ok = True)
                z.extractall(hour_dir)
              else:
                # make note of any file that did not download
                file_read_failure.append(filename)
                with open('file_read_errors_' + str(year_use) + '_' + str(month_use + 1) +'.txt', 'w') as file:
                  for item in file_read_failure:
                    file.write(f"{item}\n")
                