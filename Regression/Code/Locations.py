import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from shapely.geometry import MultiPoint
from scipy.stats import gaussian_kde
from pathlib import Path

# ── Data ───────────────────────────────────────────────────────────────────────
df  = pd.read_csv(Path(__file__).parent.parent / 'SCS_2015_2024_data.csv')
bdd = df[df['BDD'] == 1][['Begin_Date', 'centroid_lat', 'centroid_lon']].dropna()

target_date = 20160426
apr26 = bdd[bdd['Begin_Date'] == target_date]
other = bdd[bdd['Begin_Date'] != target_date]

# Hull around April 26 storm reports
reports  = pd.read_csv(Path(__file__).parent.parent.parent / 'data' / 'filtered' / 'Storm_Reports_2016_latlong.csv')
day_rpts = reports[(reports['MONTH_NUM'] == 4) & (reports['BEGIN_DAY'] == 26)].dropna(subset=['BEGIN_LAT', 'BEGIN_LON'])
apr26_hull = MultiPoint(list(zip(day_rpts['BEGIN_LON'], day_rpts['BEGIN_LAT']))).convex_hull.buffer(0.8)
ax26_hx, ax26_hy = apr26_hull.exterior.xy

# KDE contour enclosing ~75 % of the other BDD centroids
_pts  = np.vstack([other['centroid_lon'], other['centroid_lat']])
kde   = gaussian_kde(_pts, bw_method=0.25)
_lons = np.linspace(-122, -72, 300)
_lats = np.linspace(23,   50,  300)
_lg, _latg = np.meshgrid(_lons, _lats)
_z    = kde(np.vstack([_lg.ravel(), _latg.ravel()])).reshape(_lg.shape)
_level = np.percentile(kde(_pts), 25)

# ── Style constants ────────────────────────────────────────────────────────────
plate      = ccrs.PlateCarree()
projection = ccrs.AlbersEqualArea(central_longitude=-96, central_latitude=37.5,
                                  standard_parallels=(29.5, 45.5))
EXTENT     = [-120, -73, 18.5, 52.5]
FIREBRICK  = '#b30000'
FILL_COLOR = '#e34a33'

cities = {
    'Denver, CO':       (-104.9903, 39.7392),
    'Dallas, TX':       (-96.7977,  32.7815),
    'Oklahoma City, OK':(-97.5164,  35.4676),
    'St. Louis, MO':    (-90.1994,  38.6270),
    'Chicago, IL':      (-87.3954,  41.5205),
    'Minneapolis, MN':  (-93.2650,  44.9778),
    'Charlotte, NC':    (-80.8431,  35.2271),
    'Washington, DC':   (-77.0369,  38.9072),
}

def draw_geography(ax):
    ax.add_feature(cfeature.OCEAN,                       color='lightblue',  zorder=9)
    ax.add_feature(cfeature.LAND,                        color='white',      zorder=2)
    ax.add_feature(cfeature.BORDERS,                     linewidth=0.8, edgecolor='black', zorder=8)
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.8, edgecolor='black', zorder=9)
    ax.add_feature(cfeature.LAKES.with_scale('50m'),     facecolor='lightblue', edgecolor='black', linewidth=0.8, zorder=9)
    ax.set_extent(EXTENT, crs=plate)

def draw_states(ax):
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=1.0, edgecolor='black', zorder=7)

def add_cities(ax):
    for name, (lon, lat) in cities.items():
        ax.plot(lon, lat, 'w.', markersize=20, transform=plate, zorder=10)
        ax.plot(lon, lat, 'k.', markersize=13, transform=plate, zorder=10)

def title_box(ax, text):
    ax.text(0.025, 0.95, text, transform=ax.transAxes, fontsize=20,
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round'), zorder=15,
            verticalalignment='top')

def legend_box(ax, handles):
    leg = ax.legend(handles=handles, framealpha=1, prop={'size': 13},
                    ncol=3, loc=3)
    leg.set_zorder(10)
    leg.get_frame().set_edgecolor('black')


# ── Figure 1: April 26, 2016 centroid only ────────────────────────────────────
fig1 = plt.figure(figsize=(15, 15))
ax1  = fig1.add_subplot(1, 1, 1, projection=projection)
draw_geography(ax1)

ax1.fill(ax26_hx, ax26_hy, transform=plate, color=FILL_COLOR, alpha=0.25, zorder=5)
ax1.plot(ax26_hx, ax26_hy, transform=plate, color=FIREBRICK,  lw=2.0,    zorder=6)
ax1.scatter(day_rpts['BEGIN_LON'], day_rpts['BEGIN_LAT'],
            s=18, color=FILL_COLOR, alpha=0.7, transform=plate, zorder=9)
ax1.scatter(apr26['centroid_lon'], apr26['centroid_lat'],
            s=250, color=FIREBRICK, edgecolors='black', linewidths=1.0,
            transform=plate, zorder=11)

draw_states(ax1)
add_cities(ax1)
title_box(ax1, f'BDD Centroid — April 26, 2016  (n={len(day_rpts)} storm reports)')
legend_box(ax1, [
    mpatches.Patch(facecolor=FILL_COLOR, edgecolor='black', alpha=0.6, label=f'Storm Reports (n={len(day_rpts)})'),
    mpatches.Patch(facecolor=FILL_COLOR, edgecolor='black', alpha=0.3, label='Storm Extent'),
    mpatches.Patch(facecolor=FIREBRICK,  edgecolor='black',            label='BDD Centroid'),
])
plt.tight_layout()
plt.show()


# ── Figure 3: Other BDD centroids with KDE core region ────────────────────────
fig3 = plt.figure(figsize=(15, 15))
ax3  = fig3.add_subplot(1, 1, 1, projection=projection)
draw_geography(ax3)

ax3.contourf(_lg, _latg, _z, levels=[_level, _z.max()],
             colors=[FILL_COLOR], alpha=0.25, transform=plate, zorder=5)
ax3.contour(_lg, _latg, _z, levels=[_level],
            colors=[FIREBRICK], linewidths=2.0, transform=plate, zorder=6)
ax3.scatter(other['centroid_lon'], other['centroid_lat'],
            s=25, color=FILL_COLOR, alpha=0.7, transform=plate, zorder=9)
ax3.scatter(apr26['centroid_lon'], apr26['centroid_lat'],
            s=250, color=FIREBRICK, edgecolors='black', linewidths=1.0,
            transform=plate, zorder=11)

draw_states(ax3)
add_cities(ax3)
title_box(ax3, f'BDD Centroids Excluding April 26, 2016 — Core Region (n={len(other)})')
legend_box(ax3, [
    mpatches.Patch(facecolor=FILL_COLOR, edgecolor='black', alpha=0.6, label='BDD Centroids'),
    mpatches.Patch(facecolor=FILL_COLOR, edgecolor='black', alpha=0.4, label='Core Region (~75%)'),
    mpatches.Patch(facecolor=FIREBRICK,  edgecolor='black',            label='Apr 26 Centroid'),
])
plt.tight_layout()
plt.show()