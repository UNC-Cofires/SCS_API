import requests
import csv
import time
import os
import pandas as pd
import numpy as np

url = 'https://spc.noaa.gov/climo/reports/'
os.makedirs('daily_reports/tornado_reports', exist_ok = True)
os.makedirs('daily_reports/wind_reports', exist_ok = True)
os.makedirs('daily_reports/hail_reports', exist_ok = True)
storm_types = ['torn', 'hail', 'wind',]
#SCS_events = ['Hail','High Wind','Strong Wind','Thunderstorm Wind', 'Tornado']
storm_dir_names = ['daily_reports/tornado_reports', 'daily_reports/wind_reports', 'daily_reports/hail_reports']
default_header = ['Time', 'F-Scale', 'Location', 'County', 'State', 'Lat', 'Lon', 'Comments']
retry_counter = 0
current_year = 25
current_month = 4
for year_use in range(25, 3, -1):
  for month_use in range(0, 12):
    monthly_vals = {}
    monthly_vals['torn'] = pd.DataFrame()
    monthly_vals['hail'] = pd.DataFrame()
    monthly_vals['wind'] = pd.DataFrame()
    for storm_type, stm_dir in zip(storm_types, storm_dir_names):
      try:
        old_file = pd.read_csv(os.path.join(stm_dir, storm_type + '_' + str(month_use + 1) + '_20' + str(year_use).zfill(2) + '.csv'))
        if len(old_file.index) > 0:
          read_month = False
        else:
          read_month = True
      except:
        read_month = True
      if year_use == current_year and (month_use + 1) > current_month:
        read_month = False
      elif year_use > current_year:
        read_month = False
      if read_month:          
        for day_use in range(0, 31):
          date_script = str(year_use).zfill(2) + str(month_use + 1).zfill(2) + str(day_use + 1).zfill(2)
          try:
            response = requests.get(url + date_script + '_rpts_' + storm_type + '.csv')
            retry_counter = 0
          except:
            retry_counter += 1
          if retry_counter > 0:
            while retry_counter < 5:
              print('sleeping before try number ' + str(retry_counter + 1) + ' of 5')
              time.sleep(60 * retry_counter)
              try:
                response = requests.get(url + date_script + '_rpts_' + storm_type + '.csv')
                retry_counter = 5
              except:
                retry_counter += 1
          if response.status_code == 200:
            decoded_content = response.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            storm_report_df = pd.DataFrame(cr)
            if len(storm_report_df.index) > 0:
              potential_columns = storm_report_df.iloc[0]
              use_default = False
              for col_use in potential_columns:
                try:
                  header_val = float(col_use)
                  use_default = True
                except:
                  pass
              if use_default:
                drop_list = []
                if len(storm_report_df.columns) > 8:
                  for colx in range(8, len(storm_report_df.columns)):
                    storm_report_df[storm_report_df.columns[7]] = storm_report_df[storm_report_df.columns[7]] + storm_report_df[storm_report_df.columns[colx]]
                    drop_list.append(storm_report_df.columns[colx])
                  storm_report_df = storm_report_df.drop(columns = drop_list)
                storm_report_df.columns = default_header
              else:
                storm_report_df.columns = storm_report_df.iloc[0]
                storm_report_df = storm_report_df[1:]
              storm_report_df['Day'] = np.ones(len(storm_report_df.index)) * (day_use+1)
              try:
                storm_report_df = storm_report_df.drop(columns=[None])
              except:
                pass
              monthly_vals[storm_type] = pd.concat([monthly_vals[storm_type], storm_report_df])
              monthly_vals[storm_type] = monthly_vals[storm_type].reset_index(drop = True)
        monthly_vals[storm_type].to_csv(os.path.join(stm_dir, storm_type + '_' + str(month_use + 1) + '_20' + str(year_use).zfill(2) + '.csv'))
        print(str(len(monthly_vals[storm_type].index)) + ' ' + storm_type + ' entries on : 20' + str(year_use).zfill(2) + ' ' + str(month_use + 1))

