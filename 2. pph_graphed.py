import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from matplotlib.patches import Patch
from matplotlib.colors import BoundaryNorm, ListedColormap

"WIP"
"Code graphs the nam212_pph and attempts to replicate the Research paper's visualizations"
"All credit to the original research paper and its code can be found here"
url = 'https://github.com/ahaberlie/PPer_Climo'

# Load NAM-212 grid coordinates
grid_ds = xr.open_dataset("/Users/jacksonmorrissett/Research/nam212.nc") #Set to your folder pathway
lats = grid_ds["gridlat_212"].values
lons = grid_ds["gridlon_212"].values

# Use Albers Equal Area projection
from_proj = ccrs.PlateCarree()
projection = ccrs.AlbersEqualArea(central_longitude=-96, central_latitude=37.5, false_easting=0.0, 
                                 false_northing=0.0, standard_parallels=(29.5, 45.5), globe=None)

# Cities to plot
cities = {'Denver, CO': (-104.9903, 39.7392),
        'Omaha, NE': (-95.9345, 41.2565),
        'Columbus, OH': (-82.9988, 39.9612),
        'Albany, NY': (-73.7562, 42.6526),
        'Charlotte, NC': (-80.8431, 35.2271),
        'San Antonio, TX': (-98.4936, 29.4241),
        'Oklahoma City, OK': (-97.5164, 35.4676), 
        'Tuscaloosa, AL': (-87.5692, 33.2098), 
        'St. Louis, MO': (-90.1994, 38.6270),
        'Minneapolis, MN': (-93.2650, 44.9778), 
        'Orlando, FL': (-81.3792, 28.5383), 
        'Bismarck, ND': (-100.773703, 46.801942),
        'Washington, DC': (-77.0369, 38.9072)}

# Maps America
def draw_geography(ax):
    """Add geographic features to the map"""
    ax.add_feature(cfeature.OCEAN, color='lightblue', zorder=9)
    ax.add_feature(cfeature.LAND, color='darkgray', zorder=2)
    ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='black', zorder=8)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), edgecolor='black', linewidth=0.8, zorder=9)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), facecolor='lightblue', edgecolor='black', linewidth=0.8,zorder=9)
    return ax

# Creates the key 
def generate_legend(ax, title, bounds, colors, fontsize=13, propsize=13):
    legend_handles = []
    
    for i in range(len(bounds)):
        label = bounds[i]
        patch = Patch(facecolor=colors[i], edgecolor='k', label=label)
        legend_handles.append(patch)
    
    cax = ax.legend(handles=legend_handles, framealpha=1, title=title, 
                   prop={'size': propsize}, ncol=3, loc=3)
    cax.set_zorder(10)
    cax.get_frame().set_edgecolor('k')
    cax.get_title().set_fontsize('{}'.format(fontsize))
    
    return ax

# Visualizes the PPHs
def draw_pper_map(pper_subset, map_title, map_color_scale, map_colors):
    cmap = ListedColormap(map_colors)
    norm = BoundaryNorm(map_color_scale, ncolors=cmap.N)
    
    ax = plt.subplot(1, 1, 1, projection=projection)
    ax.set_extent([-120, -73, 18.5, 52.5], crs=from_proj)
    ax = draw_geography(ax)
    
    # Create CONUS mask - values outside CONUS will be masked
    conus_mask = ((lats >= 24.52) & (lats <= 49.385) & 
                  (lons >= -124.74) & (lons <= -66.95))
    
    # Mask both zero values AND values outside CONUS
    res = np.ma.masked_where((pper_subset.values == 0) | (~conus_mask), pper_subset.values)
    
    mmp = ax.pcolormesh(lons, lats, res, zorder=6, 
                       cmap=cmap, norm=norm, transform=ccrs.PlateCarree())
    
    # Add state lines above the data with more visible black color
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=1.0, edgecolor='black', zorder=7)
    
    labels = []
    for i in range(len(map_color_scale)-1):
        val1 = map_color_scale[i]
        labels.append("≥ {}".format(val1))
    
    legend_handles = generate_legend(ax, map_title, labels, map_colors, fontsize=25, propsize=25)
    
    return ax

# Calculates the mean annual event days
def calculate_mean_annual_days(storm_type, severity, start_year, end_year):
    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    days_processed = 0 
    total_days_above_threshold = None
    
    current_date = start_date 
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day

        csv_path = f"nam212_pph/{storm_type}/pph_{year}_{month:02d}_{day:02d}.csv"
        if not os.path.exists(csv_path):
            current_date += timedelta(days=1)
            continue

        try:
            df = pd.read_csv(csv_path)       
            pph_daily = (df.values >= severity).astype(int)

            if total_days_above_threshold is None:
                total_days_above_threshold = np.zeros_like(pph_daily)
            
            total_days_above_threshold += pph_daily
            days_processed += 1
            
        except Exception as e:
            print(f"Error processing {csv_path}: {e}")
            
        current_date += timedelta(days=1)
    
    if days_processed == 0:
        print(f"No data found for {storm_type} from {start_year} to {end_year}")
        return None
        
    num_years = end_year - start_year + 1
    mean_annual_days = total_days_above_threshold / num_years
    print(f"Processed {days_processed} days for {storm_type}, {num_years} years")
    return mean_annual_days

# Main plotting function
def plot_pph_analysis(start_year, end_year, storm_configs):
    
    # Set up figure parameters
    plt.rcParams['figure.figsize'] = 15, 15
    
    # Label positions
    plab_x = .025
    plab_y = .95
    maxlab_x = .025
    maxlab_y = .24
    
    # Color schemes and scales for each storm type
    color_schemes = {
        'torn': ['#ffffff','#fdd49e','#fdbb84','#fc8d59','#e34a33','#b30000'],
        'hail': ['#ffffff','#d9f0a3','#addd8e','#78c679','#41ab5d','#238443'],  
        'wind': ['#ffffff','#c6dbef','#9ecae1','#6baed6','#3182bd','#08519c']
    }
    
    # Scales adjusted for PPH values
    scales = {
        'torn': {
            0.05: [0, 0.1, 0.5, 1.0, 2.0, 5.0, 100],
            0.15: [0, 0.5, 1.0, 2.0, 4.0, 8.0, 100],
            0.30: [0, 0.2, 0.5, 1.0, 2.0, 4.0, 100]
        },
        'hail': {
            0.05: [0, 0.5, 1.0, 2.0, 4.0, 8.0, 100],
            0.15: [0, 1.0, 2.0, 4.0, 8.0, 12.0, 100],
            0.30: [0, 0.5, 1.0, 2.0, 4.0, 6.0, 100]
        },
        'wind': {
            0.05: [0, 1.0, 2.0, 4.0, 8.0, 12.0, 100],
            0.15: [0, 2.0, 4.0, 8.0, 12.0, 16.0, 100],
            0.30: [0, 1.0, 2.0, 4.0, 6.0, 8.0, 100]
        }
    }
    
    storm_names = {
        'torn': 'Tornado',
        'hail': 'Hail', 
        'wind': 'Wind'
    }
    
    # Process each storm type
    for storm_type, severities in storm_configs.items():
        dy_colors = color_schemes[storm_type]
        
        for severity in severities:
            title = "Mean Annual Event Days"
            name = f"{severity*100:.0f}%"
            key = f'{name} {storm_names[storm_type]}'
            
            # Get appropriate scale
            if severity in scales[storm_type]:
                pper_scale = scales[storm_type][severity]
            else:
                # Fallback scale
                pper_scale = [0, 0.5, 1.0, 2.0, 4.0, 8.0, 100]
            
            print(f"Processing {storm_type} at {severity*100}% severity...")
            data = calculate_mean_annual_days(storm_type, severity, start_year, end_year)
            
            if data is not None:
                # Convert to xarray DataArray
                dsub = xr.DataArray(data, dims=['y', 'x'])
                
                # Find maximum locations
                max_val = np.nanmax(dsub.values)
                y_max, x_max = np.where(dsub.values == max_val)
                
                print(f"Maximum value: {max_val:.3f} at {len(y_max)} locations")
                
                # Create the map
                fig = plt.figure(figsize=(15, 15))
                ax = draw_pper_map(dsub, title, pper_scale, dy_colors)

                # Mark maximum locations with larger, bolder crosses
                for i in range(len(y_max)):
                    ax.plot(lons[y_max[i], x_max[i]], lats[y_max[i], x_max[i]], "k+", 
                           mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
                
                # Add cities with larger markers
                for city_name, city_loc in cities.items():
                    ax.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                           transform=from_proj, zorder=10)
                    ax.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                           transform=from_proj, zorder=10)
                    
                # Add text labels
                txt = ax.text(plab_x, plab_y, key + " ({} - {})".format(start_year, end_year), 
                      transform=ax.transAxes, fontsize=25, 
                      bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
                

                txt = ax.text(maxlab_x, maxlab_y, "Max (+): {:.2f}".format(float(max_val)), 
                      transform=ax.transAxes, fontsize=25, 
                      bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
                
                # Image saving line removed - plots will only display, not save
                
                plt.show()
                plt.close()
            else:
                print(f"No data available for {storm_type} at {severity*100}% threshold")

# Storm thresholds
storm_configs = {
    'torn': [0.05],    # 5% threshold
    'wind': [0.15],    # 15% threshold  
    'hail': [0.15]     # 15% threshold
}

# Years to analyze (adjust to match your available data)
start_year = 2012 
end_year = 2024

# Run the analysis
if __name__ == "__main__":
    plot_pph_analysis(start_year, end_year, storm_configs)