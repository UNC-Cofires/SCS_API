import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import numpy as np
import pandas as pd
import os
from matplotlib.patches import Patch
from matplotlib.colors import BoundaryNorm, ListedColormap

"Before running, you must have adjusted the following "
"1) set the correct path for the grid spacing file (grid_ds)"
"2) Input day / storm type you wish to plot"
"3) Adjust file name for ncei_pph_namXXX output file in load_single_day_pph function"
"4) Adjust 'scales' in plot_single_day_pph function"

# Load grid coordinates
grid_ds = xr.open_dataset("/Users/jacksonmorrissett/Projects/Research/grids/nam215.nc") #Set to your folder pathway
lats = grid_ds["gridlat"].values
lons = grid_ds["gridlon"].values

target_year = 2014
target_month = 4
target_day = 3
storm_type = 'hail'  # Options: 'hail', 'tornado', 'wind'

# Load single day PPH data
def load_single_day_pph(storm_type, year, month, day):
    """Load PPH data for a single day"""
    csv_path = f"ncei_pph_nam215/{storm_type}/pph_{year}_{month:02d}_{day:02d}.csv" #Change to your grid_pathway
    
    if not os.path.exists(csv_path):
        print(f"Error: File {csv_path} not found")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully loaded data for {year}-{month:02d}-{day:02d}")
        print(f"Data shape: {df.shape}")
        print(f"PPH value range: {df.values.min():.3f} to {df.values.max():.3f}")
        return df.values
    except Exception as e:
        print(f"Error loading {csv_path}: {e}")
        return None

# Main plotting function for single day
def plot_single_day_pph(storm_type, year, month, day):
    """Plot PPH values for a single specific day"""
    
    # Set up figure parameters
    plt.rcParams['figure.figsize'] = 15, 15
    
    # Label positions
    plab_x = .025
    plab_y = .95
    citylab_x = .025
    citylab_y = .25
    
    # Color scheme for PPH values (percentages)
    pph_colors = ['#4d6dbd', '#4f9ac6', '#f0d55d', '#e07069', '#c7445d']
    
    # These correspond to realistic severe weather probability thresholds
    pph_scale = [0.001, 0.02, 0.04, 0.08, 0.1, 1.0]
    
    storm_names = {
        'hail': 'Hail',
        'tornado': 'Tornado', 
        'wind': 'Wind'
    }
    
    print(f"Loading PPH data for {storm_type} on {year}-{month:02d}-{day:02d}...")
    
    # Load the single day data
    pph_data = load_single_day_pph(storm_type, year, month, day)
    
    if pph_data is not None:
        # Convert to xarray DataArray
        dsub = xr.DataArray(pph_data, dims=['y', 'x'])
        
        # Create the map
        fig = plt.figure(figsize=(15, 15))
        
        title = f"PPH Values"
        storm_name = storm_names.get(storm_type, storm_type.title())
        
        ax = draw_pper_map(dsub, title, pph_scale, pph_colors)

        # Mark cities with standard markers
        for city_name, city_loc in cities.items():
            ax.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                   transform=from_proj, zorder=10)
            ax.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                   transform=from_proj, zorder=10)
            
        # Add main title
        date_str = f"{year}-{month:02d}-{day:02d}"
        main_title = f"{storm_name} PPH - {date_str}"
        txt = ax.text(plab_x, plab_y, main_title, 
              transform=ax.transAxes, fontsize=25, 
              bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
        
        return plt.show()
    else:
        print(f"Failed to load data for {storm_type} on {year}-{month:02d}-{day:02d}")
        return None
    
# Use Albers Equal Area projection
from_proj = ccrs.PlateCarree()
projection = ccrs.AlbersEqualArea(central_longitude=-96, central_latitude=37.5, false_easting=0.0, 
                                 false_northing=0.0, standard_parallels=(29.5, 45.5), globe=None)

# Cities to plot
cities = {'Denver, CO': (-104.9903, 39.7392),
        'Dallas, TX': (-96.7977, 32.7815),
        'Chicago, IL' : (-87.3954, 41.520480),
        }

# Target cities for value extraction
target_cities = ['Chicago, IL', 'Denver, CO', 'Dallas, TX']

# Function to find nearest grid point to a city
def find_nearest_grid_point(city_lon, city_lat, lons, lats):
    """Find the nearest grid point to a city location"""
    distances = np.sqrt((lons - city_lon)**2 + (lats - city_lat)**2)
    min_idx = np.unravel_index(distances.argmin(), distances.shape)
    return min_idx

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
    
    # Fixed legend labels - properly show meaningful thresholds
    labels = []
    for i in range(len(map_color_scale)-1):
        val1 = map_color_scale[i]
        val2 = map_color_scale[i+1]
        
        # Convert decimal values to percentages for display
        if val1 < 1:  # If values are decimals (0.15 = 15%)
            threshold_pct = int(val1 * 100)
            labels.append(f"≥ {threshold_pct}%")
        else:  # If values are already percentages
            labels.append(f"≥ {int(val1)}%")
    
    legend_handles = generate_legend(ax, map_title, labels, map_colors, fontsize=25, propsize=25)
    
    return ax

if __name__ == "__main__":
    # Plot the single day
    city_values = plot_single_day_pph(storm_type, target_year, target_month, target_day)
