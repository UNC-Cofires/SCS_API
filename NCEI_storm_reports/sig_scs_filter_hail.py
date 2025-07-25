import os
import pandas as pd

DATA_DIR = '/Users/jimnguyen/IRMII/SCS_API/NCEI_storm_reports'
OUTPUT_DIR = os.path.join(DATA_DIR, 'sig_hail_filtered')
os.makedirs(OUTPUT_DIR, exist_ok=True)

KEEP_TYPES = ['Hail']
COLUMNS_TO_KEEP = [
    'YEAR',
    'MONTH_NAME',
    'BEGIN_DAY',
    'END_DAY',  
    'EVENT_TYPE',
    'STATE',
    'CZ_TYPE',
    'CZ_NAME',
    'BEGIN_LAT',
    'BEGIN_LON',
    'END_LAT',
    'END_LON',
    'MAGNITUDE',
]

for year in range(2010, 2025):
    infile = f"Storm_Reports_{year}.csv"
    inpath = os.path.join(DATA_DIR, infile)
    
    if not os.path.isfile(inpath):
        continue
    
    df = pd.read_csv(inpath)
    
    # Only keep the SCS events
    df_twh = df[df['EVENT_TYPE'].isin(KEEP_TYPES)].copy()
    
    # Filter for magnitude 2 or above (handle missing/NaN values)
    df_twh = df_twh[
        (pd.to_numeric(df_twh['MAGNITUDE'], errors='coerce') >= 2) & 
        (df_twh['MAGNITUDE'].notna())
    ].copy()
    
    # Columns of concern to compare for now
    cols_existing = [c for c in COLUMNS_TO_KEEP if c in df_twh.columns]
    df_twh = df_twh[cols_existing]
    
    # Convert month alpha to numeric
    df_twh['MONTH_NUM'] = pd.to_datetime(
        df_twh['MONTH_NAME'], 
        format='%B'
    ).dt.month
    
    # Sort
    df_twh = df_twh.sort_values(
        by=['EVENT_TYPE', 'YEAR', 'MONTH_NUM', 'BEGIN_DAY'],
        ascending=[True, True, True, True]
    ).reset_index(drop=True)
    
    # to drop month number if you want
    # df_twh = df_twh.drop(columns='MONTH_NUM')
    
    outfile = f"Hail_Reports_SIG_{year}.csv"
    outpath = os.path.join(OUTPUT_DIR, outfile)
    df_twh.to_csv(outpath, index=False)
    print(f"Year {year}: {len(df_twh)} rows -> {outpath}")