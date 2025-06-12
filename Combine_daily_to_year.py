import pandas as pd
import os


hail_path = "hail_reports/combined/"
wind_path = "wind_reports/combined/"
tor_path = "tornado_reports/combined/"

out_base = "Daily_combined"
os.makedirs(out_base, exist_ok=True)

for year in range(2005, 2025):
    combined_frames = []
    
    hail_file = f"hail_{year}_combined.csv"
    hail_fpath = os.path.join(hail_path, hail_file)
    if os.path.isfile(hail_fpath):
        df_hail = pd.read_csv(hail_fpath)
        df_hail["EVENT_TYPE"] = "Hail"
        combined_frames.append(df_hail)
    else:
        print(f"  (Hail file not found for {year}: {hail_fpath})")
    
    wind_file = f"wind_{year}_combined.csv"
    wind_fpath = os.path.join(wind_path, wind_file)
    if os.path.isfile(wind_fpath):
        df_wind = pd.read_csv(wind_fpath)
        df_wind["EVENT_TYPE"] = "Wind"
        combined_frames.append(df_wind)
    else:
        print(f"  (Wind file not found for {year}: {wind_fpath})")
    
    tor_file = f"torn_{year}_combined.csv"
    tor_fpath = os.path.join(tor_path, tor_file)
    if os.path.isfile(tor_fpath):
        df_tor = pd.read_csv(tor_fpath)
        df_tor["EVENT_TYPE"] = "Tornado"
        combined_frames.append(df_tor)
    else:
        print(f"  (Tornado file not found for {year}: {tor_fpath})")
    
    if combined_frames:
        df_year = pd.concat(combined_frames, axis=0, ignore_index=True)
        
        cols = df_year.columns.tolist()
        if "EVENT_TYPE" in cols:
            # move "EVENT_TYPE" to index 0
            cols.insert(0, cols.pop(cols.index("EVENT_TYPE")))
            df_year = df_year[cols]
        
        out_filename = f"Daily_combined_{year}.csv"
        out_path = os.path.join(out_base, out_filename)
        df_year.to_csv(out_path, index=False)
        print(f"Year {year}: wrote {len(df_year)} rows → {out_path}")
    
    else:
        print(f"Year {year}: no source files found; skipping.")
