"""
Comprehensive Convective Outlook Analysis Script
Recreates mean annual combined event day plots and performs detailed analysis
Author: Jim Nguyen
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import os
from datetime import datetime, timedelta
from matplotlib.patches import Patch
from matplotlib.colors import BoundaryNorm, ListedColormap
from sklearn.metrics import brier_score_loss
import warnings
warnings.filterwarnings('ignore')

class ConvectiveOutlookAnalyzer:
    """Main class for analyzing convective outlook and PPH data"""
    
    def __init__(self, convective_outlook_path="convective_outlooks_only1200z", 
                 pph_path="PPH/NCEI_PPH", grid_file="PPH/nam212.nc"):
        self.convective_outlook_path = convective_outlook_path
        self.pph_path = pph_path
        self.grid_file = grid_file
        
        # Load NAM-212 grid
        self.load_grid()
        
        # Define probability thresholds and mappings
        self.probability_mappings = {
            'slight': {'torn': 0.05, 'hail': 0.15, 'wind': 0.15},
            'moderate': {'torn': 0.30, 'hail': 0.30, 'wind': 0.30},
            'significant': {'torn': 0.10, 'hail': 0.10, 'wind': 0.10}
        }
        
        # Cities for plotting
        self.cities = {
            'Bismarck, ND': (-100.773703, 46.801942),
            'Minneapolis, MN': (-93.2650, 44.9778),
            'Albany, NY': (-73.7562, 42.6526),
            'Omaha, NE': (-95.9345, 41.2565),
            'Columbus, OH': (-82.9988, 39.9612),
            'Denver, CO': (-104.9903, 39.7392),
            'St. Louis, MO': (-90.1994, 38.6270),
            'Charlotte, NC': (-80.8431, 35.2271),
            'Oklahoma City, OK': (-97.5164, 35.4676),
            'Tuscaloosa, AL': (-87.5692, 33.2098),
            'San Antonio, TX': (-98.4936, 29.4241),
            'Orlando, FL': (-81.3792, 28.5383)
        }
        
        # Projections
        self.from_proj = ccrs.PlateCarree()
        self.projection = ccrs.AlbersEqualArea(
            central_longitude=-96, central_latitude=37.5,
            false_easting=0.0, false_northing=0.0,
            standard_parallels=(29.5, 45.5)
        )
        
    def load_grid(self):
        """Load NAM-212 grid coordinates"""
        try:
            grid_ds = xr.open_dataset(self.grid_file)
            self.lats = grid_ds["gridlat_212"].values
            self.lons = grid_ds["gridlon_212"].values
            print(f"Loaded grid with shape: {self.lats.shape}")
        except Exception as e:
            print(f"Error loading grid file: {e}")
            raise
    
    def standardize_crs(self, gdf):
        """Standardize CRS to WGS84"""
        if gdf.crs != "EPSG:4326":
            gdf = gdf.to_crs("EPSG:4326")
        return gdf
    
    def decode_dn_values(self, dn_values, hazard_type):
        """
        Decode DN values to probability percentages
        Different years may use different encodings
        """
        # Common DN to probability mapping
        dn_mapping = {
            0: 0,    # No risk
            2: 2,    # Marginal (2%)
            5: 5,    # Slight (5%)
            10: 10,  # Enhanced (10%)
            15: 15,  # Moderate (15%)
            30: 30,  # High (30%)
            45: 45,  # High (45%)
            60: 60   # High (60%)
        }
        
        # For significant files, assume 10% threshold
        if 'sig' in hazard_type:
            return [10 if dn > 0 else 0 for dn in dn_values]
        
        return [dn_mapping.get(dn, dn) for dn in dn_values]
    
    def rasterize_outlook_to_grid(self, shapefile_path, threshold_percent):
        """
        Rasterize convective outlook shapefile to NAM-212 grid
        Returns binary grid (1 where probability >= threshold, 0 otherwise)
        """
        if not os.path.exists(shapefile_path):
            return np.zeros_like(self.lats)
        
        try:
            # Read shapefile
            gdf = gpd.read_file(shapefile_path)
            if gdf.empty:
                return np.zeros_like(self.lats)
            
            # Standardize CRS
            gdf = self.standardize_crs(gdf)
            
            # Decode DN values to probabilities
            hazard_type = os.path.basename(shapefile_path).split('_')[-1].replace('.shp', '')
            gdf['probability'] = self.decode_dn_values(gdf['DN'].values, hazard_type)
            
            # Filter polygons that meet threshold
            gdf_threshold = gdf[gdf['probability'] >= threshold_percent]
            
            if gdf_threshold.empty:
                return np.zeros_like(self.lats)
            
            # Create binary grid using point-in-polygon
            result_grid = np.zeros_like(self.lats)
            
            # Create points from grid
            points = []
            indices = []
            for i in range(self.lats.shape[0]):
                for j in range(self.lats.shape[1]):
                    points.append((self.lons[i, j], self.lats[i, j]))
                    indices.append((i, j))
            
            # Convert to GeoDataFrame
            from shapely.geometry import Point
            points_gdf = gpd.GeoDataFrame(
                geometry=[Point(p) for p in points],
                crs="EPSG:4326"
            )
            
            # Spatial join to find points within polygons
            joined = gpd.sjoin(points_gdf, gdf_threshold, how='left', predicate='within')
            
            # Set grid values
            for idx, (i, j) in enumerate(indices):
                if not pd.isna(joined.iloc[idx]['index_right']):
                    result_grid[i, j] = 1
            
            return result_grid
            
        except Exception as e:
            print(f"Error processing {shapefile_path}: {e}")
            return np.zeros_like(self.lats)
    
    def get_outlook_files(self, year, month, day, hazard_type):
        """Get shapefile path for specific date and hazard type"""
        date_str = f"{year}{month:02d}{day:02d}"
        folder_path = f"{self.convective_outlook_path}/{year}/{month}/forecast_day1/day1otlk_{date_str}_1200"
        file_path = f"{folder_path}/day1otlk_{date_str}_1200_{hazard_type}.shp"
        return file_path
    
    def calculate_mean_annual_outlook_days(self, hazard_type, threshold_percent, start_year, end_year):
        """Calculate mean annual event days for convective outlooks"""
        print(f"Calculating mean annual days for {hazard_type} at {threshold_percent}% threshold")
        
        total_days_above_threshold = None
        days_processed = 0
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Get days in month
                if month in [1, 3, 5, 7, 8, 10, 12]:
                    days_in_month = 31
                elif month in [4, 6, 9, 11]:
                    days_in_month = 30
                else:  # February
                    days_in_month = 29 if year % 4 == 0 else 28
                
                for day in range(1, days_in_month + 1):
                    file_path = self.get_outlook_files(year, month, day, hazard_type)
                    
                    if os.path.exists(file_path):
                        grid = self.rasterize_outlook_to_grid(file_path, threshold_percent)
                        
                        if total_days_above_threshold is None:
                            total_days_above_threshold = np.zeros_like(grid)
                        
                        total_days_above_threshold += grid
                        days_processed += 1
        
        if days_processed == 0:
            print(f"No data found for {hazard_type}")
            return None
        
        num_years = end_year - start_year + 1
        mean_annual_days = total_days_above_threshold / num_years
        print(f"Processed {days_processed} days over {num_years} years")
        
        return mean_annual_days
    
    def load_pph_data(self, storm_type, year, month, day):
        """Load PPH data for specific date"""
        pph_file = f"{self.pph_path}/{storm_type}/pph_{year}_{month:02d}_{day:02d}.csv"
        
        if os.path.exists(pph_file):
            try:
                df = pd.read_csv(pph_file)
                return df.values
            except Exception as e:
                print(f"Error loading {pph_file}: {e}")
                return None
        return None
    
    def calculate_mean_annual_pph_days(self, storm_type, threshold, start_year, end_year):
        """Calculate mean annual event days for PPH data"""
        print(f"Calculating mean annual PPH days for {storm_type} at {threshold} threshold")
        
        total_days_above_threshold = None
        days_processed = 0
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
                if month == 2:
                    days_in_month = 29 if year % 4 == 0 else 28
                
                for day in range(1, days_in_month + 1):
                    pph_data = self.load_pph_data(storm_type, year, month, day)
                    
                    if pph_data is not None:
                        binary_data = (pph_data >= threshold).astype(int)
                        
                        if total_days_above_threshold is None:
                            total_days_above_threshold = np.zeros_like(binary_data)
                        
                        total_days_above_threshold += binary_data
                        days_processed += 1
        
        if days_processed == 0:
            print(f"No PPH data found for {storm_type}")
            return None
        
        num_years = end_year - start_year + 1
        mean_annual_days = total_days_above_threshold / num_years
        print(f"Processed {days_processed} PPH days over {num_years} years")
        
        return mean_annual_days
    
    def draw_geography(self, ax):
        """Add geographic features to map"""
        ax.add_feature(cfeature.OCEAN, color='lightblue', zorder=9)
        ax.add_feature(cfeature.LAND, color='darkgray', zorder=2)
        ax.add_feature(cfeature.BORDERS, linewidth=0.8, edgecolor='black', zorder=8)
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'), edgecolor='black', linewidth=0.8, zorder=9)
        ax.add_feature(cfeature.LAKES.with_scale('50m'), facecolor='lightblue', edgecolor='black', linewidth=0.8, zorder=9)
        ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=1.0, edgecolor='black', zorder=7)
        return ax
    
    def generate_legend(self, ax, title, bounds, colors, fontsize=13, propsize=13):
        """Create legend for plots"""
        legend_handles = []
        
        for i in range(len(bounds)):
            label = bounds[i]
            patch = Patch(facecolor=colors[i], edgecolor='k', label=label)
            legend_handles.append(patch)
        
        cax = ax.legend(handles=legend_handles, framealpha=1, title=title,
                       prop={'size': propsize}, ncol=3, loc=3)
        cax.set_zorder(10)
        cax.get_frame().set_edgecolor('k')
        cax.get_title().set_fontsize(f'{fontsize}')
        
        return ax
    
    def create_four_panel_plot(self, start_year, end_year, output_dir="convective_outlook_plots"):
        """Create 4-panel plot matching the research paper figure"""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Color schemes for each hazard type
        colors = {
            'torn': ['#ffffff', '#fdd49e', '#fdbb84', '#fc8d59', '#e34a33', '#b30000'],
            'hail': ['#ffffff', '#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443'],
            'wind': ['#ffffff', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c']
        }
        
        # Scales for plotting
        scales = {
            'torn_5': [0, 0.025, 1, 5, 20, 100],
            'torn_5_combined': [0, 0.025, 1, 5, 20, 100],
            'hail_15': [0, 0.025, 6, 12, 18, 100],
            'wind_15': [0, 0.025, 4, 12, 16, 100]
        }
        
        # Create figure with 2x2 subplots
        fig = plt.figure(figsize=(20, 16))
        
        # Panel (a): 5% Tornado, 15% Wind, or 15% Hail (1979-2018)
        print("Creating panel (a): Combined 5% Tornado, 15% Hail, 15% Wind")
        ax1 = plt.subplot(2, 2, 1, projection=self.projection)
        ax1.set_extent([-120, -73, 18.5, 52.5], crs=self.from_proj)
        ax1 = self.draw_geography(ax1)
        
        # Calculate combined data
        torn_data = self.calculate_mean_annual_outlook_days('torn', 5, start_year, end_year)
        hail_data = self.calculate_mean_annual_outlook_days('hail', 15, start_year, end_year)
        wind_data = self.calculate_mean_annual_outlook_days('wind', 15, start_year, end_year)
        
        if torn_data is not None and hail_data is not None and wind_data is not None:
            combined_data = np.maximum.reduce([torn_data, hail_data, wind_data])
            max_val = np.nanmax(combined_data)
            
            # Create CONUS mask
            conus_mask = ((self.lats >= 24.52) & (self.lats <= 49.385) & 
                         (self.lons >= -124.74) & (self.lons <= -66.95))
            
            masked_data = np.ma.masked_where((combined_data == 0) | (~conus_mask), combined_data)
            
            cmap = ListedColormap(colors['torn'])
            norm = BoundaryNorm(scales['torn_5_combined'], ncolors=cmap.N)
            
            mesh = ax1.pcolormesh(self.lons, self.lats, masked_data, 
                                transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=6)
            
            # Add cities and labels
            for city_name, city_loc in self.cities.items():
                ax1.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                        transform=self.from_proj, zorder=10)
                ax1.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                        transform=self.from_proj, zorder=10)
            
            # Add maximum markers
            y_max, x_max = np.where(combined_data == max_val)
            for i in range(len(y_max)):
                ax1.plot(self.lons[y_max[i], x_max[i]], self.lats[y_max[i], x_max[i]], 
                        "k+", mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
            
            ax1.text(0.025, 0.95, f"5% Tornado, 15% Wind, or 15% Hail ({start_year} - {end_year})", 
                    transform=ax1.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax1.text(0.025, 0.85, f"Max (+): {max_val:.1f}", 
                    transform=ax1.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax1.text(0.025, 0.05, "a)", transform=ax1.transAxes, fontsize=20, weight='bold')
            
            # Create legend
            labels = [f"≥ {val}" for val in scales['torn_5_combined'][1:-1]]
            self.generate_legend(ax1, "Mean Annual Combined Event Days", labels, colors['torn'][1:-1], fontsize=14, propsize=12)
        
        # Panel (b): 5% Tornado (1979-2018)
        print("Creating panel (b): 5% Tornado")
        ax2 = plt.subplot(2, 2, 2, projection=self.projection)
        ax2.set_extent([-120, -73, 18.5, 52.5], crs=self.from_proj)
        ax2 = self.draw_geography(ax2)
        
        if torn_data is not None:
            max_val = np.nanmax(torn_data)
            conus_mask = ((self.lats >= 24.52) & (self.lats <= 49.385) & 
                         (self.lons >= -124.74) & (self.lons <= -66.95))
            masked_data = np.ma.masked_where((torn_data == 0) | (~conus_mask), torn_data)
            
            cmap = ListedColormap(colors['torn'])
            norm = BoundaryNorm(scales['torn_5'], ncolors=cmap.N)
            
            mesh = ax2.pcolormesh(self.lons, self.lats, masked_data, 
                                transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=6)
            
            # Add maximum markers and cities
            y_max, x_max = np.where(torn_data == max_val)
            for i in range(len(y_max)):
                ax2.plot(self.lons[y_max[i], x_max[i]], self.lats[y_max[i], x_max[i]], 
                        "k+", mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
            
            for city_name, city_loc in self.cities.items():
                ax2.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                        transform=self.from_proj, zorder=10)
                ax2.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                        transform=self.from_proj, zorder=10)
            
            ax2.text(0.025, 0.95, f"5% Tornado ({start_year} - {end_year})", 
                    transform=ax2.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax2.text(0.025, 0.85, f"Max (+): {max_val:.1f}", 
                    transform=ax2.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax2.text(0.025, 0.05, "b)", transform=ax2.transAxes, fontsize=20, weight='bold')
            
            labels = [f"≥ {val}" for val in scales['torn_5'][1:-1]]
            self.generate_legend(ax2, "Mean Annual Event Days", labels, colors['torn'][1:-1], fontsize=14, propsize=12)
        
        # Panel (c): 15% Hail (1979-2018)
        print("Creating panel (c): 15% Hail")
        ax3 = plt.subplot(2, 2, 3, projection=self.projection)
        ax3.set_extent([-120, -73, 18.5, 52.5], crs=self.from_proj)
        ax3 = self.draw_geography(ax3)
        
        if hail_data is not None:
            max_val = np.nanmax(hail_data)
            conus_mask = ((self.lats >= 24.52) & (self.lats <= 49.385) & 
                         (self.lons >= -124.74) & (self.lons <= -66.95))
            masked_data = np.ma.masked_where((hail_data == 0) | (~conus_mask), hail_data)
            
            cmap = ListedColormap(colors['hail'])
            norm = BoundaryNorm(scales['hail_15'], ncolors=cmap.N)
            
            mesh = ax3.pcolormesh(self.lons, self.lats, masked_data, 
                                transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=6)
            
            # Add maximum markers and cities
            y_max, x_max = np.where(hail_data == max_val)
            for i in range(len(y_max)):
                ax3.plot(self.lons[y_max[i], x_max[i]], self.lats[y_max[i], x_max[i]], 
                        "k+", mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
            
            for city_name, city_loc in self.cities.items():
                ax3.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                        transform=self.from_proj, zorder=10)
                ax3.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                        transform=self.from_proj, zorder=10)
            
            ax3.text(0.025, 0.95, f"15% Hail ({start_year} - {end_year})", 
                    transform=ax3.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax3.text(0.025, 0.85, f"Max (+): {max_val:.1f}", 
                    transform=ax3.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax3.text(0.025, 0.05, "c)", transform=ax3.transAxes, fontsize=20, weight='bold')
            
            labels = [f"≥ {val}" for val in scales['hail_15'][1:-1]]
            self.generate_legend(ax3, "Mean Annual Event Days", labels, colors['hail'][1:-1], fontsize=14, propsize=12)
        
        # Panel (d): 15% Wind (1979-2018)
        print("Creating panel (d): 15% Wind")
        ax4 = plt.subplot(2, 2, 4, projection=self.projection)
        ax4.set_extent([-120, -73, 18.5, 52.5], crs=self.from_proj)
        ax4 = self.draw_geography(ax4)
        
        if wind_data is not None:
            max_val = np.nanmax(wind_data)
            conus_mask = ((self.lats >= 24.52) & (self.lats <= 49.385) & 
                         (self.lons >= -124.74) & (self.lons <= -66.95))
            masked_data = np.ma.masked_where((wind_data == 0) | (~conus_mask), wind_data)
            
            cmap = ListedColormap(colors['wind'])
            norm = BoundaryNorm(scales['wind_15'], ncolors=cmap.N)
            
            mesh = ax4.pcolormesh(self.lons, self.lats, masked_data, 
                                transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=6)
            
            # Add maximum markers and cities
            y_max, x_max = np.where(wind_data == max_val)
            for i in range(len(y_max)):
                ax4.plot(self.lons[y_max[i], x_max[i]], self.lats[y_max[i], x_max[i]], 
                        "k+", mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
            
            for city_name, city_loc in self.cities.items():
                ax4.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                        transform=self.from_proj, zorder=10)
                ax4.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                        transform=self.from_proj, zorder=10)
            
            ax4.text(0.025, 0.95, f"15% Wind ({start_year} - {end_year})", 
                    transform=ax4.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax4.text(0.025, 0.85, f"Max (+): {max_val:.1f}", 
                    transform=ax4.transAxes, fontsize=16, 
                    bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
            ax4.text(0.025, 0.05, "d)", transform=ax4.transAxes, fontsize=20, weight='bold')
            
            labels = [f"≥ {val}" for val in scales['wind_15'][1:-1]]
            self.generate_legend(ax4, "Mean Annual Event Days", labels, colors['wind'][1:-1], fontsize=14, propsize=12)
        
        plt.tight_layout()
        output_file = f"{output_dir}/mean_annual_combined_event_days_{start_year}-{end_year}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Saved 4-panel plot: {output_file}")
        plt.close()
    
    def create_individual_percentage_plots(self, start_year, end_year, output_dir="individual_outlook_plots"):
        """Create individual plots for each percentage threshold"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Define all thresholds to plot
        thresholds = {
            'torn': [5, 10, 15, 30, 60],
            'hail': [5, 10, 15, 30, 60], 
            'wind': [5, 10, 15, 30, 60],
            'sigtorn': [10],
            'sighail': [10],
            'sigwind': [10]
        }
        
        colors = {
            'torn': ['#ffffff', '#fdd49e', '#fdbb84', '#fc8d59', '#e34a33', '#b30000'],
            'hail': ['#ffffff', '#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443'],
            'wind': ['#ffffff', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c']
        }
        
        scales = {
            'torn': {5: [0, 0.025, 1, 5, 20, 100], 10: [0, 0.025, 0.5, 2, 10, 100], 
                    15: [0, 0.025, 0.5, 1, 5, 100], 30: [0, 0.025, 0.25, 0.5, 2, 100], 60: [0, 0.025, 0.1, 0.25, 1, 100]},
            'hail': {5: [0, 0.025, 2, 8, 20, 100], 10: [0, 0.025, 1, 4, 15, 100], 
                    15: [0, 0.025, 1, 3, 12, 100], 30: [0, 0.025, 0.5, 2, 8, 100], 60: [0, 0.025, 0.25, 1, 4, 100]},
            'wind': {5: [0, 0.025, 5, 15, 25, 100], 10: [0, 0.025, 3, 10, 20, 100], 
                    15: [0, 0.025, 2, 8, 16, 100], 30: [0, 0.025, 1, 4, 12, 100], 60: [0, 0.025, 0.5, 2, 8, 100]}
        }
        
        for hazard_type, threshold_list in thresholds.items():
            base_hazard = hazard_type.replace('sig', '')
            
            for threshold in threshold_list:
                print(f"Creating plot for {hazard_type} at {threshold}%")
                
                # Calculate data
                data = self.calculate_mean_annual_outlook_days(hazard_type, threshold, start_year, end_year)
                
                if data is not None:
                    # Create plot
                    fig = plt.figure(figsize=(15, 12))
                    ax = plt.subplot(1, 1, 1, projection=self.projection)
                    ax.set_extent([-120, -73, 18.5, 52.5], crs=self.from_proj)
                    ax = self.draw_geography(ax)
                    
                    max_val = np.nanmax(data)
                    conus_mask = ((self.lats >= 24.52) & (self.lats <= 49.385) & 
                                 (self.lons >= -124.74) & (self.lons <= -66.95))
                    masked_data = np.ma.masked_where((data == 0) | (~conus_mask), data)
                    
                    # Get appropriate scale and colors
                    if base_hazard in scales and threshold in scales[base_hazard]:
                        scale = scales[base_hazard][threshold]
                    else:
                        scale = [0, 0.025, 1, 5, 20, 100]
                    
                    cmap = ListedColormap(colors[base_hazard])
                    norm = BoundaryNorm(scale, ncolors=cmap.N)
                    
                    mesh = ax.pcolormesh(self.lons, self.lats, masked_data, 
                                       transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, zorder=6)
                    
                    # Add cities
                    for city_name, city_loc in self.cities.items():
                        ax.plot(city_loc[0], city_loc[1], 'w.', markersize=20, 
                               transform=self.from_proj, zorder=10)
                        ax.plot(city_loc[0], city_loc[1], 'k.', markersize=13, 
                               transform=self.from_proj, zorder=10)
                    
                    # Add maximum markers
                    y_max, x_max = np.where(data == max_val)
                    for i in range(len(y_max)):
                        ax.plot(self.lons[y_max[i], x_max[i]], self.lats[y_max[i], x_max[i]], 
                               "k+", mew=3, ms=20, transform=ccrs.PlateCarree(), zorder=20)
                    
                    # Add labels
                    hazard_name = {'torn': 'Tornado', 'hail': 'Hail', 'wind': 'Wind'}[base_hazard]
                    title = f"{threshold}% {hazard_name} ({start_year} - {end_year})"
                    if 'sig' in hazard_type:
                        title = f"Significant {hazard_name} ({start_year} - {end_year})"
                    
                    ax.text(0.025, 0.95, title, transform=ax.transAxes, fontsize=18, 
                           bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
                    ax.text(0.025, 0.85, f"Max (+): {max_val:.2f}", transform=ax.transAxes, fontsize=18, 
                           bbox=dict(facecolor='w', edgecolor='k', boxstyle='round'), zorder=15)
                    
                    # Add legend
                    labels = [f"≥ {val}" for val in scale[1:-1]]
                    self.generate_legend(ax, "Mean Annual Event Days", labels, colors[base_hazard][1:-1], fontsize=16, propsize=14)
                    
                    # Save plot
                    output_file = f"{output_dir}/{hazard_type}_{threshold}pct_{start_year}-{end_year}.png"
                    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
                    print(f"Saved: {output_file}")
                    plt.close()
    
    def calculate_area_coverage(self, start_year, end_year, output_dir="area_coverage_analysis"):
        """Calculate area coverage for PPH vs convective outlook by year and month"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        yearly_data = {}
        monthly_data = {}
        
        print("Calculating area coverage for PPH and convective outlook data...")
        
        hazard_mapping = {'torn': 'torn', 'hail': 'hail', 'wind': 'wind'}
        threshold_mapping = {'torn': 0.05, 'hail': 0.15, 'wind': 0.15}  # Slight risk thresholds
        
        for year in range(start_year, end_year + 1):
            yearly_data[year] = {'pph': {'torn': 0, 'hail': 0, 'wind': 0}, 
                                'outlook': {'torn': 0, 'hail': 0, 'wind': 0}}
            
            for month in range(1, 13):
                month_key = f"{year}-{month:02d}"
                monthly_data[month_key] = {'pph': {'torn': 0, 'hail': 0, 'wind': 0}, 
                                          'outlook': {'torn': 0, 'hail': 0, 'wind': 0}}
                
                # Get days in month
                days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
                if month == 2:
                    days_in_month = 29 if year % 4 == 0 else 28
                
                for day in range(1, days_in_month + 1):
                    for hazard in ['torn', 'hail', 'wind']:
                        # PPH area coverage
                        pph_data = self.load_pph_data(hazard, year, month, day)
                        if pph_data is not None:
                            threshold = threshold_mapping[hazard]
                            pph_binary = (pph_data >= threshold).astype(int)
                            pph_area = np.sum(pph_binary) * (40.0 ** 2)  # km²
                            yearly_data[year]['pph'][hazard] += pph_area
                            monthly_data[month_key]['pph'][hazard] += pph_area
                        
                        # Convective outlook area coverage
                        outlook_file = self.get_outlook_files(year, month, day, hazard)
                        if os.path.exists(outlook_file):
                            threshold_percent = threshold_mapping[hazard] * 100
                            outlook_grid = self.rasterize_outlook_to_grid(outlook_file, threshold_percent)
                            outlook_area = np.sum(outlook_grid) * (40.0 ** 2)  # km²
                            yearly_data[year]['outlook'][hazard] += outlook_area
                            monthly_data[month_key]['outlook'][hazard] += outlook_area
        
        # Create yearly plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        years = list(range(start_year, end_year + 1))
        
        for i, hazard in enumerate(['torn', 'hail', 'wind']):
            pph_areas = [yearly_data[year]['pph'][hazard] / 1e6 for year in years]  # Convert to 1000s km²
            outlook_areas = [yearly_data[year]['outlook'][hazard] / 1e6 for year in years]
            
            axes[i].plot(years, pph_areas, 'b-o', label='PPH', linewidth=2, markersize=6)
            axes[i].plot(years, outlook_areas, 'r-s', label='Convective Outlook', linewidth=2, markersize=6)
            axes[i].set_xlabel('Year')
            axes[i].set_ylabel('Total Area Coverage (1000s km²)')
            axes[i].set_title(f'{hazard.title()} - Annual Area Coverage')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/annual_area_coverage_{start_year}-{end_year}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Create monthly plots
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        # Prepare monthly data
        months = sorted(monthly_data.keys())
        month_labels = [datetime.strptime(m, "%Y-%m").strftime("%Y-%m") for m in months]
        
        for i, hazard in enumerate(['torn', 'hail', 'wind']):
            pph_areas = [monthly_data[month]['pph'][hazard] / 1e6 for month in months]
            outlook_areas = [monthly_data[month]['outlook'][hazard] / 1e6 for month in months]
            
            axes[i].plot(range(len(months)), pph_areas, 'b-o', label='PPH', linewidth=1, markersize=3)
            axes[i].plot(range(len(months)), outlook_areas, 'r-s', label='Convective Outlook', linewidth=1, markersize=3)
            axes[i].set_xlabel('Month')
            axes[i].set_ylabel('Total Area Coverage (1000s km²)')
            axes[i].set_title(f'{hazard.title()} - Monthly Area Coverage')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
            
            # Set x-tick labels to show years only
            tick_positions = [i for i in range(0, len(months), 12)]
            tick_labels = [month_labels[i][:4] for i in tick_positions]
            axes[i].set_xticks(tick_positions)
            axes[i].set_xticklabels(tick_labels)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/monthly_area_coverage_{start_year}-{end_year}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved area coverage plots to {output_dir}/")
    
    def calculate_daily_overlap(self, start_year, end_year, output_dir="overlap_analysis"):
        """Calculate daily overlap between convective outlooks and PPH for slight risks"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("Calculating daily overlap between convective outlooks and PPH...")
        
        # Define outlook probability thresholds to check
        outlook_thresholds = [5, 10, 15, 30, 60]
        
        # Define PPH thresholds for slight risk
        pph_thresholds = {'torn': 0.05, 'hail': 0.15, 'wind': 0.15}
        
        # Store results
        overlap_results = {hazard: {thresh: [] for thresh in outlook_thresholds} for hazard in ['torn', 'hail', 'wind']}
        dates = []
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
                if month == 2:
                    days_in_month = 29 if year % 4 == 0 else 28
                
                for day in range(1, days_in_month + 1):
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    
                    for hazard in ['torn', 'hail', 'wind']:
                        # Load PPH data
                        pph_data = self.load_pph_data(hazard, year, month, day)
                        if pph_data is None:
                            continue
                        
                        # Create PPH slight risk mask
                        pph_threshold = pph_thresholds[hazard]
                        pph_mask = (pph_data >= pph_threshold).astype(int)
                        pph_total_area = np.sum(pph_mask)
                        
                        if pph_total_area == 0:
                            # No PPH events on this day
                            for thresh in outlook_thresholds:
                                overlap_results[hazard][thresh].append(0.0)
                            continue
                        
                        # Check overlap with different outlook thresholds
                        for outlook_thresh in outlook_thresholds:
                            outlook_file = self.get_outlook_files(year, month, day, hazard)
                            
                            if os.path.exists(outlook_file):
                                outlook_grid = self.rasterize_outlook_to_grid(outlook_file, outlook_thresh)
                                
                                # Calculate overlap
                                overlap = np.sum(pph_mask * outlook_grid)
                                overlap_fraction = overlap / pph_total_area if pph_total_area > 0 else 0.0
                                overlap_results[hazard][outlook_thresh].append(overlap_fraction)
                            else:
                                overlap_results[hazard][outlook_thresh].append(0.0)
                    
                    dates.append(date_str)
        
        # Save results to CSV
        for hazard in ['torn', 'hail', 'wind']:
            df_data = {'date': dates}
            for thresh in outlook_thresholds:
                df_data[f'overlap_{thresh}pct'] = overlap_results[hazard][thresh]
            
            df = pd.DataFrame(df_data)
            output_file = f"{output_dir}/daily_overlap_{hazard}_{start_year}-{end_year}.csv"
            df.to_csv(output_file, index=False)
            print(f"Saved overlap data: {output_file}")
        
        # Create summary statistics
        summary_stats = {}
        for hazard in ['torn', 'hail', 'wind']:
            summary_stats[hazard] = {}
            for thresh in outlook_thresholds:
                data = overlap_results[hazard][thresh]
                summary_stats[hazard][thresh] = {
                    'mean': np.mean(data),
                    'median': np.median(data),
                    'std': np.std(data),
                    'min': np.min(data),
                    'max': np.max(data)
                }
        
        # Save summary statistics
        summary_df = []
        for hazard in ['torn', 'hail', 'wind']:
            for thresh in outlook_thresholds:
                stats = summary_stats[hazard][thresh]
                summary_df.append({
                    'hazard': hazard,
                    'outlook_threshold': thresh,
                    'mean_overlap': stats['mean'],
                    'median_overlap': stats['median'],
                    'std_overlap': stats['std'],
                    'min_overlap': stats['min'],
                    'max_overlap': stats['max']
                })
        
        summary_df = pd.DataFrame(summary_df)
        summary_file = f"{output_dir}/overlap_summary_statistics_{start_year}-{end_year}.csv"
        summary_df.to_csv(summary_file, index=False)
        print(f"Saved summary statistics: {summary_file}")
        
        # Create visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for i, hazard in enumerate(['torn', 'hail', 'wind']):
            means = [summary_stats[hazard][thresh]['mean'] for thresh in outlook_thresholds]
            stds = [summary_stats[hazard][thresh]['std'] for thresh in outlook_thresholds]
            
            axes[i].errorbar(outlook_thresholds, means, yerr=stds, marker='o', capsize=5, linewidth=2, markersize=8)
            axes[i].set_xlabel('Convective Outlook Threshold (%)')
            axes[i].set_ylabel('Mean Overlap Fraction')
            axes[i].set_title(f'{hazard.title()} - PPH vs Outlook Overlap')
            axes[i].grid(True, alpha=0.3)
            axes[i].set_ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/overlap_summary_plot_{start_year}-{end_year}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved overlap analysis to {output_dir}/")
    
    def calculate_brier_scores(self, start_year, end_year, output_dir="brier_analysis"):
        """Calculate Brier Scores for convective outlooks and PPH"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        print("Calculating Brier Scores for convective outlooks and PPH...")
        
        # Define thresholds
        probability_thresholds = [0.05, 0.10, 0.15, 0.30, 0.60]
        hazards = ['torn', 'hail', 'wind']
        
        brier_results = {}
        
        for hazard in hazards:
            print(f"Processing {hazard}...")
            brier_results[hazard] = {'outlook': {}, 'pph': {}}
            
            for prob_threshold in probability_thresholds:
                outlook_forecasts = []
                pph_forecasts = []
                observed = []
                
                for year in range(start_year, end_year + 1):
                    for month in range(1, 13):
                        days_in_month = 31 if month in [1, 3, 5, 7, 8, 10, 12] else 30
                        if month == 2:
                            days_in_month = 29 if year % 4 == 0 else 28
                        
                        for day in range(1, days_in_month + 1):
                            # Load observed data (using storm reports as truth)
                            pph_data = self.load_pph_data(hazard, year, month, day)
                            if pph_data is None:
                                continue
                            
                            # Create binary observation (any storm report in grid cell)
                            obs_binary = (pph_data > 0).astype(int)
                            
                            # Get outlook forecast
                            outlook_file = self.get_outlook_files(year, month, day, hazard)
                            if os.path.exists(outlook_file):
                                # Get probability grid from outlook
                                outlook_prob_grid = self.get_probability_grid(outlook_file, hazard)
                                
                                # Flatten grids for scoring
                                obs_flat = obs_binary.flatten()
                                outlook_flat = outlook_prob_grid.flatten()
                                pph_flat = pph_data.flatten()
                                
                                # Convert PPH to probabilities (normalize by maximum value in reasonable range)
                                pph_prob_flat = np.clip(pph_flat / np.percentile(pph_flat[pph_flat > 0], 95) if np.any(pph_flat > 0) else pph_flat, 0, 1)
                                
                                # Store for this threshold
                                observed.extend(obs_flat)
                                outlook_forecasts.extend(outlook_flat)
                                pph_forecasts.extend(pph_prob_flat)
                
                if len(observed) > 0:
                    # Calculate Brier Scores
                    outlook_brier = brier_score_loss(observed, outlook_forecasts)
                    pph_brier = brier_score_loss(observed, pph_forecasts)
                    
                    brier_results[hazard]['outlook'][prob_threshold] = outlook_brier
                    brier_results[hazard]['pph'][prob_threshold] = pph_brier
                    
                    print(f"  {prob_threshold*100}% threshold - Outlook BS: {outlook_brier:.4f}, PPH BS: {pph_brier:.4f}")
        
        # Save results
        brier_df = []
        for hazard in hazards:
            for prob_threshold in probability_thresholds:
                if prob_threshold in brier_results[hazard]['outlook']:
                    brier_df.append({
                        'hazard': hazard,
                        'threshold': prob_threshold,
                        'outlook_brier_score': brier_results[hazard]['outlook'][prob_threshold],
                        'pph_brier_score': brier_results[hazard]['pph'][prob_threshold]
                    })
        
        brier_df = pd.DataFrame(brier_df)
        brier_file = f"{output_dir}/brier_scores_{start_year}-{end_year}.csv"
        brier_df.to_csv(brier_file, index=False)
        print(f"Saved Brier scores: {brier_file}")
        
        # Create visualization
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        
        for i, hazard in enumerate(hazards):
            hazard_data = brier_df[brier_df['hazard'] == hazard]
            
            axes[i].plot(hazard_data['threshold'] * 100, hazard_data['outlook_brier_score'], 
                        'r-o', label='Convective Outlook', linewidth=2, markersize=8)
            axes[i].plot(hazard_data['threshold'] * 100, hazard_data['pph_brier_score'], 
                        'b-s', label='PPH', linewidth=2, markersize=8)
            
            axes[i].set_xlabel('Probability Threshold (%)')
            axes[i].set_ylabel('Brier Score')
            axes[i].set_title(f'{hazard.title()} - Brier Score Comparison')
            axes[i].legend()
            axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/brier_scores_comparison_{start_year}-{end_year}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Saved Brier score analysis to {output_dir}/")
    
    def get_probability_grid(self, shapefile_path, hazard_type):
        """Extract probability values from shapefile and convert to grid"""
        if not os.path.exists(shapefile_path):
            return np.zeros_like(self.lats)
        
        try:
            gdf = gpd.read_file(shapefile_path)
            if gdf.empty:
                return np.zeros_like(self.lats)
            
            gdf = self.standardize_crs(gdf)
            gdf['probability'] = self.decode_dn_values(gdf['DN'].values, hazard_type)
            
            # Create probability grid
            prob_grid = np.zeros_like(self.lats)
            
            # For each grid point, find the highest probability polygon it falls within
            from shapely.geometry import Point
            for i in range(self.lats.shape[0]):
                for j in range(self.lats.shape[1]):
                    point = Point(self.lons[i, j], self.lats[i, j])
                    max_prob = 0
                    
                    for idx, row in gdf.iterrows():
                        if row['geometry'].contains(point):
                            max_prob = max(max_prob, row['probability'])
                    
                    prob_grid[i, j] = max_prob / 100.0  # Convert percentage to probability
            
            return prob_grid
            
        except Exception as e:
            print(f"Error processing {shapefile_path}: {e}")
            return np.zeros_like(self.lats)

def main():
    """Main execution function"""
    
    print("Starting Comprehensive Convective Outlook Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = ConvectiveOutlookAnalyzer()
    
    # Set analysis period
    start_year = 2010
    end_year = 2024
    
    print(f"Analysis period: {start_year} - {end_year}")
    print()
    
    # Create all required analyses
    try:
        # Task 1 & 2: Recreate the 4-panel plot from the image
        print("Task 1-2: Creating 4-panel mean annual combined event days plot...")
        analyzer.create_four_panel_plot(start_year, end_year)
        
        # Task 4 & 6: Create individual percentage plots
        print("\nTask 4 & 6: Creating individual percentage plots...")
        analyzer.create_individual_percentage_plots(start_year, end_year)
        
        # Task 5: Area coverage analysis
        print("\nTask 5: Calculating area coverage by year and month...")
        analyzer.calculate_area_coverage(start_year, end_year)
        
        # Task 7: Daily overlap calculation
        print("\nTask 7: Calculating daily overlap between outlooks and PPH...")
        analyzer.calculate_daily_overlap(start_year, end_year)
        
        # Task 8: Brier Score calculation
        print("\nTask 8: Calculating Brier Scores...")
        analyzer.calculate_brier_scores(start_year, end_year)
        
        print("\n" + "=" * 60)
        print("Analysis completed successfully!")
        print("Check the following directories for results:")
        print("- convective_outlook_plots/: 4-panel plot")
        print("- individual_outlook_plots/: Individual percentage plots")
        print("- area_coverage_analysis/: Area coverage line plots")
        print("- overlap_analysis/: Daily overlap analysis")
        print("- brier_analysis/: Brier Score comparison")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 