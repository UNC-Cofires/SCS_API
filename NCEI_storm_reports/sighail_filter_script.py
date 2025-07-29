import os
import pandas as pd
import numpy as np

DATA_DIR = '/Users/jimnguyen/IRMII/SCS_API/NCEI_storm_reports'
OUTPUT_DIR = os.path.join(DATA_DIR, 'sighail_filtered')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEEP_TYPES = ['Hail']

COLUMNS_TO_KEEP = [
    'BEGIN_DATE_TIME',
    'END_DATE_TIME',
    'EVENT_TYPE',
    'BEGIN_LAT',
    'BEGIN_LON',
    'END_LAT',
    'END_LON',
    'MAGNITUDE'
]

for year in range(2010, 2025):
    infile = f"Storm_Reports_{year}.csv"
    inpath = os.path.join(DATA_DIR, infile)
    
    if not os.path.isfile(inpath):
        print(f"File not found: {inpath}")
        continue
    
    df = pd.read_csv(inpath)
    
    # Only keep the hail events
    df_hail = df[df['EVENT_TYPE'].isin(KEEP_TYPES)].copy()
    
    if len(df_hail) == 0:
        print(f"Year {year}: No hail events found")
        continue
    # Filter for magnitude 2 or above (handle missing/NaN values)
    df_hail = df_hail[
        (pd.to_numeric(df_hail['MAGNITUDE'], errors='coerce') >= 2) & 
        (df_hail['MAGNITUDE'].notna())
    ].copy()
    
    # Filter for columns that exist
    cols_existing = [c for c in COLUMNS_TO_KEEP if c in df_hail.columns]
    df_hail = df_hail[cols_existing]
    
    # Convert numeric columns to proper types
    df_hail['BEGIN_LAT'] = pd.to_numeric(df_hail['BEGIN_LAT'], errors='coerce')
    df_hail['BEGIN_LON'] = pd.to_numeric(df_hail['BEGIN_LON'], errors='coerce')
    df_hail['END_LAT'] = pd.to_numeric(df_hail['END_LAT'], errors='coerce')
    df_hail['END_LON'] = pd.to_numeric(df_hail['END_LON'], errors='coerce')
    
    # Create averaged lat/lon coordinates
    # For events with missing END coordinates, use BEGIN coordinates
    df_hail['END_LAT'] = df_hail['END_LAT'].fillna(df_hail['BEGIN_LAT'])
    df_hail['END_LON'] = df_hail['END_LON'].fillna(df_hail['BEGIN_LON'])
    
    # Calculate averaged coordinates
    df_hail['LAT'] = (df_hail['BEGIN_LAT'] + df_hail['END_LAT']) / 2
    df_hail['LON'] = (df_hail['BEGIN_LON'] + df_hail['END_LON']) / 2

    
    # Sort by the correct column name (MONTH_NUM, not MONTH)
    df_hail = df_hail.sort_values(
        by=['BEGIN_DATE_TIME'],
        ascending=[True]
    ).reset_index(drop=True)
    #df_hail.drop(['MONTH_NAME','BEGIN_LAT','BEGIN_LON','END_LAT','END_LON'], axis=1, inplace=True)
    # df.drop('col2', axis=1, inplace=True)
    df_hail = df_hail.drop(columns=['BEGIN_LAT','BEGIN_LON','END_LAT','END_LON'])


    # Optional: Drop original coordinate columns if you only want averaged ones
    # df_hail = df_hail.drop(columns=['BEGIN_LAT', 'BEGIN_LON', 'END_LAT', 'END_LON'])
    
    # Save the filtered data
    outfile = f"Sighail_Reports_{year}.csv"
    outpath = os.path.join(OUTPUT_DIR, outfile)
    df_hail.to_csv(outpath, index=False)
    

    print(f"  - Saved to: {outpath}")