import numpy as np
import os
import pandas as pd
import xarray as xr

"Code finds PPH for NOAA Storm Reports, from "
"hail_reports, wind_reports, tornado_reports"

"NAM211 : 80KM grids"
"NAM212 : 40KM grids"
"NAM215 : 20KM grids"
"NAM218 : 12KM grids"

"Before running, you must have changed the following "
"1) Adjusted grid_spacing_km to match your desired grid spacing"
"2) Changed output folder name to match your grid spacing"
"3) Set the correct path for the grid file in the try block (grid_ds)"

grid_spacing_km = 10
sigma_grid_units = 12 # Change this to adjust the spread

# Create output directory
output_folder = "noaa_pph_nam218"
os.makedirs(output_folder, exist_ok=True)

start_year = 2025  #starts at 2025
end_year = 2026 #ends at last file in 2025

# Download and load grid 
url ='https://github.com/UNC-Cofires/SCS_API/tree/jack-workplace/grids'

try:
    #Set to your folder pathway below
    grid_ds = xr.open_dataset("/Users/jacksonmorrissett/projects/Research/grids/nam218.nc")
    grid212_lat = grid_ds["gridlat"].values  # (ny, nx)
    grid212_lon = grid_ds["gridlon"].values  # (ny, nx)
except Exception as e:
    print(f"Error loading grid file: {e}")
    exit(1)

storm_dirs = {
    "torn": "tornado_reports",
    "wind": "wind_reports",
    "hail": "hail_reports"
}

# Distance function for PPH
def euclidean_distance_km(grid_lat, grid_lon, report_lat, report_lon):
    lat_km = 111.32 * (grid_lat - report_lat)
    lon_km = 111.32 * np.cos(np.radians(report_lat)) * (grid_lon - report_lon)
    return np.sqrt(lat_km**2 + lon_km**2)

# Go through each storm type
for storm_type, folder in storm_dirs.items():
    print(f"\nProcessing {storm_type} reports...")
    
    # Create output subfolder for this storm type
    output_subfolder = os.path.join(output_folder, storm_type)
    os.makedirs(output_subfolder, exist_ok=True)
    
    for year in range(start_year, end_year):
        for month in range(1, 13):
            file_name = f"{storm_type}_{month}_{year}.csv"
            file_path = os.path.join(folder, file_name)
            
            if not os.path.exists(file_path):
                print(f"    File does not exist: {file_path}")
                continue

            try:
                # Read and clean data
                data = pd.read_csv(file_path)
                data['Lat'] = pd.to_numeric(data['Lat'], errors='coerce')
                data['Lon'] = pd.to_numeric(data['Lon'], errors='coerce')
                data['Day'] = pd.to_numeric(data['Day'], errors='coerce')
                
                # Remove rows with missing  data
                initial_count = len(data)
                data = data.dropna(subset=['Lat', 'Lon', 'Day'])

                # Filter to CONUS bounds
                conus_data = data[(data['Lat'] >= 24.52) & (data['Lat'] <= 49.385) &
                                 (data['Lon'] >= -124.74) & (data['Lon'] <= -66.95)]
                
                data = conus_data

                if len(data) == 0:
                    print(f"    No valid data for {year}-{month:02d}")
                    continue

                # Process each day
                for day in sorted(data['Day'].unique()):
                    day_data = data[data['Day'] == day]
                    
                    if len(day_data) == 0:
                        continue
                    
                    # Initialize the sum for PPH
                    gaussian_sum = np.zeros_like(grid212_lat, dtype=np.float64)

                    # Compute the PPH 
                    for _, row in day_data.iterrows():
                        d_km = euclidean_distance_km(
                            grid212_lat, grid212_lon,
                            row['Lat'], row['Lon']
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
                        
                        print(f"Calculated PPH for {storm_type} on {year}-{month:02d}-{int(day):02d} ")
                        
                    except Exception as e:
                        print(f"    Error saving PPH for {year}-{month:02d}-{int(day):02d}: {e}")
                        continue

            except Exception as e:
                print(f"    Error processing file {file_path}: {e}")
                continue

print("\nNOAA PPH processing complete!")
