import numpy as np
import os
import pandas as pd
import xarray as xr

"Code adapted for NOAA Storm Reports format"
"Processing Storm_Reports_YYYY_latlong.csv files from 1950-2024"

sigma_grid_units = 1.5
grid_spacing_km = 40.0   

# Download and Load NAM-212 grid 
url = 'https://github.com/ahaberlie/PPer_Climo/tree/master/data'
try:
    grid_ds = xr.open_dataset("/Users/jacksonmorrissett/projects/Research/nam212.nc") #Set to your folder pathway
    grid212_lat = grid_ds["gridlat_212"].values  # (ny, nx)
    grid212_lon = grid_ds["gridlon_212"].values  # (ny, nx)
    print(f"Loaded grid with shape: {grid212_lat.shape}")
except Exception as e:
    print(f"Error loading grid file: {e}")
    exit(1)

# Storm type mapping from EVENT_TYPE
storm_types = {
    "Tornado": "torn",
    "Thunderstorm Wind": "wind", 
    "Hail": "hail"
}

# Distance function for PPH
def euclidean_distance_km(grid_lat, grid_lon, report_lat, report_lon):
    lat_km = 111.32 * (grid_lat - report_lat)
    lon_km = 111.32 * np.cos(np.radians(report_lat)) * (grid_lon - report_lon)
    return np.sqrt(lat_km**2 + lon_km**2)

# Create output directory
output_folder = "ncei_pph"
os.makedirs(output_folder, exist_ok=True)

# Create output subfolders for each storm type
for storm_type in storm_types.values():
    output_subfolder = os.path.join(output_folder, storm_type)
    os.makedirs(output_subfolder, exist_ok=True)

# Process each year from 1950-2024
for year in range(1950, 2025):  #1950 to 2024 inclusive
    file_name = f"Storm_Reports_{year}_latlong.csv"
    file_path = os.path.join("filtered", file_name)
    
    if not os.path.exists(file_path):
        print(f"File does not exist: {file_path}")
        continue

    try:
        print(f"\nProcessing {file_path}...")
        
        # Read the data
        data = pd.read_csv(file_path)
        
        # Clean and convert data types
        data['BEGIN_LAT'] = pd.to_numeric(data['BEGIN_LAT'], errors='coerce')
        data['BEGIN_LON'] = pd.to_numeric(data['BEGIN_LON'], errors='coerce')
        data['BEGIN_DAY'] = pd.to_numeric(data['BEGIN_DAY'], errors='coerce')
        data['MONTH_NUM'] = pd.to_numeric(data['MONTH_NUM'], errors='coerce')
        
        # Remove rows with missing critical data
        initial_count = len(data)
        data = data.dropna(subset=['BEGIN_LAT', 'BEGIN_LON', 'BEGIN_DAY', 'MONTH_NUM', 'EVENT_TYPE'])
        if len(data) < initial_count:
            print(f"  Removed {initial_count - len(data)} rows with missing data")

        # Filter to CONUS bounds
        conus_data = data[(data['BEGIN_LAT'] >= 24.52) & (data['BEGIN_LAT'] <= 49.385) &
                         (data['BEGIN_LON'] >= -124.74) & (data['BEGIN_LON'] <= -66.95)]

        if len(conus_data) < len(data):
            print(f"  Filtered {len(data) - len(conus_data)} reports outside CONUS")
        
        data = conus_data

        if len(data) == 0:
            print(f"  No valid data for {year}")
            continue

        # Process each storm type
        for event_type, storm_type in storm_types.items():
            print(f"  Processing {event_type} reports...")
            
            # Filter data for this storm type
            storm_data = data[data['EVENT_TYPE'] == event_type].copy()
            
            if len(storm_data) == 0:
                print(f"    No {event_type} reports for {year}")
                continue
                
            print(f"    Found {len(storm_data)} {event_type} reports")
            
            # Get output subfolder for this storm type
            output_subfolder = os.path.join(output_folder, storm_type)
            
            # Process each month
            for month in range(1, 13):
                month_data = storm_data[storm_data['MONTH_NUM'] == month].copy()
                
                if len(month_data) == 0:
                    continue
                
                # Process each day in the month
                for day in sorted(month_data['BEGIN_DAY'].unique()):
                    day_data = month_data[month_data['BEGIN_DAY'] == day]
                    
                    if len(day_data) == 0:
                        continue
                    
                    # Initialize the sum for PPH
                    gaussian_sum = np.zeros_like(grid212_lat, dtype=np.float64)

                    # Compute the PPH 
                    for _, row in day_data.iterrows():
                        d_km = euclidean_distance_km(
                            grid212_lat, grid212_lon,
                            row['BEGIN_LAT'], row['BEGIN_LON']
                        )
                        
                        # Convert to grid units 
                        d_grid = d_km / grid_spacing_km
                        
                        # Summing the Nth terms 
                        gaussian_sum += np.exp(-0.5 * (d_grid / sigma_grid_units) ** 2)

                    # Apply prefactor: (1 / (2π sigma²)) 
                    gauss_pref = 1.0 / (2.0 * np.pi * sigma_grid_units**2)
                    daily_pph = gauss_pref * gaussian_sum
                    rounded_pph = np.round(daily_pph, 10)

                    # Saving
                    file_name_out = f"pph_{year}_{month:02d}_{int(day):02d}.csv"
                    output_file = os.path.join(output_subfolder, file_name_out)

                    try:
                        df = pd.DataFrame(rounded_pph)
                        df.to_csv(output_file, index=False)
                        
                        print(f"    Calculated PPH for {storm_type} on {year}-{month:02d}-{int(day):02d} ({len(day_data)} reports)")
                        
                    except Exception as e:
                        print(f"    Error saving PPH for {year}-{month:02d}-{int(day):02d}: {e}")
                        continue

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        continue

print("\nNOAA Storm Reports PPH processing complete!")