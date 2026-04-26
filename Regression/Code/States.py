import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from pathlib import Path
import geopandas as gpd

#Paths
BDD_PATH     = Path(__file__).parent.parent / 'SCS_2015_2024_data.csv'
FILTERED_DIR = Path(__file__).parent.parent.parent / 'data' / 'filtered'

#Load BDD Information
bdd = pd.read_csv(BDD_PATH, dtype=str)
bdd["BDD"]        = pd.to_numeric(bdd["BDD"], errors="coerce").fillna(0)
bdd["Begin_Date"] = pd.to_datetime(bdd["Begin_Date"], format="%Y%m%d")
bdd["End_Date"]   = pd.to_datetime(bdd["End_Date"],   format="%Y%m%d")

bdd_events = bdd[bdd["BDD"] == 1].copy()
print(f"BDD event windows: {len(bdd_events)}")

bdd_dates = set()
for _, row in bdd_events.iterrows():
    d = row["Begin_Date"]
    while d <= row["End_Date"]:
        bdd_dates.add(d.date())
        d += pd.Timedelta(days=1)

print(f"Total BDD dates: {len(bdd_dates)}")

#Load Report Information
storms = pd.concat(
    [pd.read_csv(FILTERED_DIR / f"Storm_Reports_{yr}_latlong.csv", low_memory=False)
     for yr in range(2015, 2025)],
    ignore_index=True,
)
print(f"Storm reports loaded: {len(storms):,}")
print("Columns:", storms.columns.tolist())

# Build event_date
if "BEGIN_DATE" in storms.columns:
    storms["event_date"] = pd.to_datetime(storms["BEGIN_DATE"], errors="coerce").dt.date
elif {"YEAR", "MONTH_NUM", "BEGIN_DAY"}.issubset(storms.columns):
    storms["event_date"] = pd.to_datetime(
        storms["YEAR"].astype(str) + "-" +
        storms["MONTH_NUM"].astype(str).str.zfill(2) + "-" +
        storms["BEGIN_DAY"].astype(str).str.zfill(2),
        errors="coerce"
    ).dt.date
elif {"YEAR", "MONTH_NAME", "BEGIN_DAY"}.issubset(storms.columns):
    storms["event_date"] = pd.to_datetime(
        storms["YEAR"].astype(str) + " " +
        storms["MONTH_NAME"].astype(str) + " " +
        storms["BEGIN_DAY"].astype(str),
        format="%Y %B %d", errors="coerce"
    ).dt.date
else:
    raise ValueError("Cannot find date columns.")

state_col = next((c for c in storms.columns if c.upper() == "STATE"), None)
storms["state_clean"] = storms[state_col].str.strip().str.title()

event_col = next((c for c in storms.columns if "EVENT_TYPE" in c.upper()), None)
storms["event_type_upper"] = storms[event_col].str.strip().str.upper()

#Filter to BDD dates
storms_bdd = storms[storms["event_date"].isin(bdd_dates)].copy()
print(f"Storm reports on BDD dates: {len(storms_bdd):,}")

#Creating the different maps
subsets = {
    "All Reports":     storms_bdd,
    "Hail Reports":    storms_bdd[storms_bdd["event_type_upper"].str.contains("HAIL", na=False)],
    "Tornado Reports": storms_bdd[storms_bdd["event_type_upper"].str.contains("TORNADO", na=False)],
    "Wind Reports":    storms_bdd[storms_bdd["event_type_upper"].str.contains("WIND", na=False)],
}

CMAP = {
    "All Reports":     "Purples",
    "Hail Reports":    "Greens",
    "Tornado Reports": "Reds",
    "Wind Reports":    "Blues",
}

BAR_HEX = {
    "All Reports":     "#6A1B9A",
    "Hail Reports":    "#2E7D32",
    "Tornado Reports": "#B71C1C",
    "Wind Reports":    "#1565C0",
}

#Grouping by States
def state_counts(df_sub):
    return (
        df_sub.groupby("state_clean")
        .size()
        .reset_index(name="report_count")
        .sort_values("report_count", ascending=False)
    )

all_counts = {label: state_counts(df) for label, df in subsets.items()}

for label, counts in all_counts.items():
    print(f"{label}: {counts['report_count'].sum():,} reports across {len(counts)} states")

#CONUS
print("\nLoading US shapefile...")
url = "https://www2.census.gov/geo/tiger/GENZ2022/shp/cb_2022_us_state_20m.zip"
gdf_base = gpd.read_file(url)

CONUS_EXCLUDE = ["AK", "HI", "PR", "VI", "GU", "MP", "AS"]
gdf_conus = gdf_base[~gdf_base["STUSPS"].isin(CONUS_EXCLUDE)].copy()
print(f"CONUS states loaded: {len(gdf_conus)}")

#Bar chart
def bar_chart(counts, label, hex_color, top_n=20):
    top = counts.head(top_n)
    n   = len(top)
    bar_colors = [
        mcolors.to_rgba(hex_color, alpha=0.38 + 0.62 * (n - i) / n)
        for i in range(n)
    ]
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["state_clean"][::-1], top["report_count"][::-1],
            color=bar_colors[::-1], edgecolor="white", linewidth=0.5)
    ax.set_xlabel("Number of storm reports", fontsize=11)
    ax.set_title(f"{label}\nduring BDD event windows (2015–2024)",
                 fontsize=13, fontweight="bold")
    ax.xaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    mx = top["report_count"].max()
    for patch in ax.patches:
        v = int(patch.get_width())
        if v > 0:
            ax.text(v + mx * 0.008, patch.get_y() + patch.get_height() / 2,
                    f"{v:,}", va="center", fontsize=9)
    plt.tight_layout()
    plt.show()

for label, counts in all_counts.items():
    bar_chart(counts, label, BAR_HEX[label])

#CONUS Maps
def conus_map(counts, label, cmap_name):
    gdf = gdf_conus.merge(counts, left_on="NAME", right_on="state_clean", how="left")
    gdf["report_count"] = gdf["report_count"].fillna(0)
    unmatched = set(counts["state_clean"]) - set(gdf_conus["NAME"])
    if unmatched:
        print(f"WARNING [{label}]: storm states not matched to shapefile: {sorted(unmatched)}")

    vmax = gdf["report_count"].max()
    vmin = 0

    norm = mcolors.PowerNorm(gamma=0.5, vmin=vmin, vmax=vmax)
    cmap = plt.colormaps[cmap_name]

    fig, ax = plt.subplots(1, 1, figsize=(22, 14))
    fig.patch.set_facecolor("white")

    gdf.plot(
        column="report_count",
        ax=ax,
        cmap=cmap_name,
        norm=norm,
        edgecolor="#555555",
        linewidth=0.6,
        missing_kwds={"color": "#dcdcdc", "label": "No data"},
    )

    # State name + count labels
    for _, row in gdf.iterrows():
        if row.geometry is None:
            continue
        centroid = row.geometry.centroid
        count = int(row["report_count"])
        abbr  = row["STUSPS"]
        fill_color = cmap(norm(count))
        luminance  = 0.299 * fill_color[0] + 0.587 * fill_color[1] + 0.114 * fill_color[2]
        txt_color  = "white" if luminance < 0.45 else "#222222"

        ax.annotate(
            f"{abbr}\n{count:,}",
            xy=(centroid.x, centroid.y),
            ha="center", va="center",
            fontsize=7.5, fontweight="bold",
            color=txt_color,
            annotation_clip=True,
        )

    # Colorbar
    sm = cm.ScalarMappable(cmap=cmap_name, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, shrink=0.55, aspect=22, pad=0.02)
    cbar.set_label("Number of storm reports", fontsize=13)
    cbar.ax.tick_params(labelsize=11)

    ax.set_axis_off()
    ax.set_title(
        f"{label} by State during BDD Event Windows (2015–2024)",
        fontsize=18, fontweight="bold", pad=16, color="#1a1a1a"
    )

    ax.set_xlim(-130, -60)
    ax.set_ylim(22, 52)

    plt.tight_layout(pad=1.5)
    plt.show()

for label, counts in all_counts.items():
    conus_map(counts, label, CMAP[label])
