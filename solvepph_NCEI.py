import numpy as np
import os
import pandas as pd
import xarray as xr

"Code finds PPH for NCEI Storm Reports, from 'filtered' folder"

"NAM211 : 80KM grids"
"NAM212 : 40KM grids"
"NAM215 : 20KM grids"
"NAM218 : 12KM grids"

"Before running, you must have adjusted the following "
"1) grid_spacing_km to match your grid spacing"
"2) Changed output folder name to match your grid spacing"
"3) Set the correct path for the grid file in the try block (grid_ds)"

sigma_grid_units = 10 # Change this to adjust the Gaussian spread
grid_spacing_km = 12 # Adjust this to match your grid spacing (e.g., 40 km for NAM-212)

# Create output directory
output_folder = "ncei_pph_nam218" # Change this to your desired output folder
os.makedirs(output_folder, exist_ok=True)

start_year = 1950 #starts at this year
end_year = 2025 #ends at beginning of this year

# Download desired grid size
url ='https://github.com/UNC-Cofires/SCS_API/tree/jack-workplace/grids'

try:
    grid_ds = xr.open_dataset("/Users/jacksonmorrissett/projects/Research/grids/nam218.nc") #Set to your folder pathway
    grid212_lat = grid_ds["gridlat"].values  # (ny, nx)
    grid212_lon = grid_ds["gridlon"].values  # (ny, nx)
    print(f"Loaded grid with shape: {grid212_lat.shape}")
except Exception as e:
    print(f"Error loading grid file: {e}")
    exit(1)

# Storm types (All different wind types under wind)
storm_types = {
    "Tornado": "torn",
    "Thunderstorm Wind": "wind",
    "High Wind": "wind",
    "Strong Wind": "wind",
    "Hail": "hail"
}

# Distance function for PPH
def euclidean_distance_km(grid_lat, grid_lon, report_lat, report_lon):
    lat_km = 111.32 * (grid_lat - report_lat)
    lon_km = 111.32 * np.cos(np.radians(report_lat)) * (grid_lon - report_lon)
    return np.sqrt(lat_km**2 + lon_km**2)

# Create output subfolders for each unique storm type
unique_storm_types = list(set(storm_types.values()))
for storm_type in unique_storm_types:
    output_subfolder = os.path.join(output_folder, storm_type)
    os.makedirs(output_subfolder, exist_ok=True)

# Process each year from 1950-2024
for year in range(start_year, end_year): 
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

        # Process each unique storm type
        for storm_type in unique_storm_types:
            print(f"  Processing {storm_type} reports...")
            
            # Filter data for all event types that map to this storm type
            event_types_for_storm = [event_type for event_type, mapped_type in storm_types.items() if mapped_type == storm_type]
            storm_data = data[data['EVENT_TYPE'].isin(event_types_for_storm)].copy()
            
            if len(storm_data) == 0:
                print(f"    No {storm_type} reports for {year}")
                continue
                
            print(f"    Found {len(storm_data)} {storm_type} reports")
            
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
                    daily_pph = (gauss_pref * gaussian_sum)
                    daily_pph =np.round(daily_pph,3)

                    # Saving
                    file_name_out = f"pph_{year}_{month:02d}_{int(day):02d}.csv"
                    output_file = os.path.join(output_subfolder, file_name_out)

                    try:
                        df = pd.DataFrame(daily_pph)
                        df.to_csv(output_file, index=False)
                        
                        print(f"    Calculated PPH for {storm_type} on {year}-{month:02d}-{int(day):02d} ({len(day_data)} reports)")
                        
                    except Exception as e:
                        print(f"    Error saving PPH for {year}-{month:02d}-{int(day):02d}: {e}")
                        continue

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        continue

print("\nNCEI PPH processing complete!")
