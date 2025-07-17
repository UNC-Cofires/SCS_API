import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

"Code visualizes Dallas housing market values "
"with custom market value groups and scatter plot"
"to confirm that dallas_3var.geojson has the correct locations"

# Load your Dallas data
dallas = gpd.read_file("dallas_3var.geojson")

# Function to create market value groups with special 3M+ category
def create_market_groups(df, group_size=250000, cutoff_2_5m=2500000, cutoff_3m=3000000):
    """Create market value groups: $250k intervals up to 2.5M, then 3M+ group"""
    
    # Create bins from 0 to 2.5M in 250k increments
    bins = list(range(0, cutoff_2_5m + group_size, group_size))
    
    # Add the 3M+ category
    bins.append(cutoff_3m)
    bins.append(float('inf'))  # For everything above 3M
    
    # Create labels for each bin
    labels = []
    
    # Labels for 0 to 2.5M in 250k increments
    for i in range(len(bins)-3): 
        start = bins[i] // 1000  # Convert to thousands
        end = bins[i+1] // 1000
        labels.append(f'${start}k-${end}k')
    
    # Add labels for the higher ranges
    labels.append('$2.5M-$3M')
    labels.append('$3M+')
    
    # Create categorical column
    df['Market_Group'] = pd.cut(df['MKT_VALUE'], bins=bins, labels=labels, include_lowest=True)
    
    return df, bins, labels

# Apply custom grouping
dallas, bins, labels = create_market_groups(dallas, 250000)

# Create the plot
fig, ax = plt.subplots(figsize=(16, 12))

# Plot with Spectral colormap
dallas.plot(column='Market_Group',
            edgecolor='black',
            linewidth=0.3,
            alpha=0.8,
            legend=True,
            legend_kwds={"bbox_to_anchor": (1.05, 1),
                        "loc": 'upper left'},
            ax=ax,
            cmap='Spectral')

ax.set_title('Dallas Housing Market Values\n(Spectral Colormap)', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_axis_off()

plt.tight_layout()
plt.show()

# Print data
print("Market Value Group Distribution:")
print(dallas['Market_Group'].value_counts().sort_index())
print(f"Total properties: {len(dallas)}")
print(f"Average market value: ${dallas['MKT_VALUE'].mean():,.0f}")
print(f"Median market value: ${dallas['MKT_VALUE'].median():,.0f}")

# Create scatter plot of Market Value vs Year Built
fig, ax = plt.subplots(figsize=(15, 6))

# Remove any invalid year values
dallas_clean = dallas[(dallas['YEAR_BUILT'] >= 1800) & (dallas['YEAR_BUILT'] <= 2024)]

# Scatter plot of Market Value distribution by Year Built 
scatter = ax.scatter(dallas_clean['YEAR_BUILT'], dallas_clean['MKT_VALUE'], 
                     c=dallas_clean['MKT_VALUE'], cmap='plasma', alpha=0.6, s=20)
ax.set_xlabel('Year Built', fontsize=12)
ax.set_ylabel('Market Value ($)', fontsize=12)
ax.set_title('Market Value vs Year Built', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

# Add colorbar
plt.colorbar(scatter, ax=ax, label='Market Value ($)')

# Format y-axis to show currency
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))

plt.tight_layout()
plt.show()