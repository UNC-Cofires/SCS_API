import numpy as np
import os
import pandas as pd
import xarray as xr
from multiprocessing import Pool, cpu_count

"Code finds PPH for NCEI Storm Reports, from 'filtered' folder"

"NAM211 : 80KM grids"
"NAM212 : 40KM grids"
"NAM215 : 20KM grids"
"NAM218 : 12KM grids"

#Change pathway on grid_ds on line 28
#Change pathway on file_path for storm reports on line 67
#Change grid spacing such that your grid size * sigma = 120

grid_spacing_km = 20
sigma_grid_units = 6

output_folder = "ncei_pph_nam215"
os.makedirs(output_folder, exist_ok=True)

start_year = 1950
end_year = 2026

try: 
    grid_ds = xr.open_dataset("/Users/jacksonmorrissett/Projects/Research/PPHs/grids/nam215.nc")
    grid_lat = grid_ds["gridlat"].values.astype(np.float32)
    grid_lon = grid_ds["gridlon"].values.astype(np.float32)
except Exception as e:
    print(f"Error loading grid file: {e}")
    exit(1)

storm_types = {
    "Tornado": "torn",
    "Thunderstorm Wind": "wind",
    "High Wind": "wind",
    "Strong Wind": "wind",
    "Hail": "hail"
}

unique_storm_types = list(set(storm_types.values()))
for st in unique_storm_types:
    os.makedirs(os.path.join(output_folder, st), exist_ok=True)


def compute_daily_pph_vectorized(report_lats, report_lons, grid_lat, grid_lon, grid_spacing_km, sigma_grid_units):
    rlat = report_lats[:, np.newaxis, np.newaxis].astype(np.float32)
    rlon = report_lons[:, np.newaxis, np.newaxis].astype(np.float32)

    lat_km = 111.32 * (grid_lat - rlat)                                        
    lon_km = 111.32 * np.cos(np.radians(rlat)) * (grid_lon - rlon)            
    d_km   = np.sqrt(lat_km**2 + lon_km**2)                                    

    d_grid = d_km / grid_spacing_km
    gaussians = np.exp(-0.5 * (d_grid / sigma_grid_units) ** 2)               
    gaussian_sum = gaussians.sum(axis=0)                                        

    gauss_pref = np.float32(1.0 / (2.0 * np.pi * sigma_grid_units**2))
    return np.round(gauss_pref * gaussian_sum, 3)


def process_storm_year(args):
    year, storm_type, event_types, grid_lat, grid_lon, grid_spacing_km, sigma_grid_units, output_folder = args

    file_path = f"/Users/jacksonmorrissett/Projects/Research/data/filtered/Storm_Reports_{year}_latlong.csv"
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        return

    try:
        data = pd.read_csv(file_path)
        for col in ['BEGIN_LAT', 'BEGIN_LON', 'BEGIN_DAY', 'MONTH_NUM']:
            data[col] = pd.to_numeric(data[col], errors='coerce')
        data = data.dropna(subset=['BEGIN_LAT', 'BEGIN_LON', 'BEGIN_DAY', 'MONTH_NUM', 'EVENT_TYPE'])

        # Filter to CONUS
        data = data[
            (data['BEGIN_LAT'] >= 24.52) & (data['BEGIN_LAT'] <= 49.385) &
            (data['BEGIN_LON'] >= -124.74) & (data['BEGIN_LON'] <= -66.95)
        ]

        storm_data = data[data['EVENT_TYPE'].isin(event_types)]
        if storm_data.empty:
            return

        output_subfolder = os.path.join(output_folder, storm_type)

        for month in range(1, 13):
            month_data = storm_data[storm_data['MONTH_NUM'] == month]
            if month_data.empty:
                continue

            for day in sorted(month_data['BEGIN_DAY'].unique()):
                day_data = month_data[month_data['BEGIN_DAY'] == day]
                if day_data.empty:
                    continue

                daily_pph = compute_daily_pph_vectorized(
                    day_data['BEGIN_LAT'].values,
                    day_data['BEGIN_LON'].values,
                    grid_lat, grid_lon,
                    grid_spacing_km, sigma_grid_units
                )

                out_file = os.path.join(output_subfolder, f"pph_{year}_{month:02d}_{int(day):02d}.csv")
                pd.DataFrame(daily_pph).to_csv(out_file, index=False)
                print(f"  Saved {storm_type} {year}-{month:02d}-{int(day):02d} ({len(day_data)} reports)")

    except Exception as e:
        print(f"Error in ({year}, {storm_type}): {e}")


if __name__ == "__main__":
    storm_to_events = {}
    for event_type, st in storm_types.items():
        storm_to_events.setdefault(st, []).append(event_type)

    tasks = [
        (year, st, storm_to_events[st], grid_lat, grid_lon, grid_spacing_km, sigma_grid_units, output_folder)
        for year in range(start_year, end_year)
        for st in unique_storm_types
    ]

    n_workers = min(cpu_count(), len(tasks))
    print(f"Launching {n_workers} workers for {len(tasks)} tasks...")
    with Pool(processes=n_workers) as pool:
        pool.map(process_storm_year, tasks)

    print("\nNCEI PPH processing complete!")
