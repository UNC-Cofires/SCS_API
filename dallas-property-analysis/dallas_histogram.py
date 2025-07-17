import json
import matplotlib.pyplot as plt
from collections import defaultdict

"Code graphs a histogram of "
"Dallas parcels (year_built + market value) "
"and microsoft location data" 

# Adjustable parameters
file_path = "dallas_3var.geojson"
min_year = 1825
max_year = 2025
bin_size = 10

def load_geojson(file_path):
    """Load GeoJSON file and extract property data"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    properties = []
    for feature in data['features']:
        props = feature['properties']
        properties.append({
            'year_built': props.get('YEAR_BUILT'),
            'market_value': props.get('MKT_VALUE')
        })
    
    return properties

def clean_data(properties):
    """Clean and validate the data"""
    null_market = 0
    null_year = 0
    cleaned_data = []
    
    for prop in properties:
        try:
            year_built = int(prop['year_built'])
        except (ValueError, TypeError):
            null_year += 1
            continue
        
        try:
            market_value = float(prop['market_value'])
            if market_value <= 0:
                continue
        except (ValueError, TypeError):
            null_market += 1
            continue
        
        cleaned_data.append({
            'year_built': year_built,
            'market_value': market_value
        })
    
    return cleaned_data, null_market, null_year

def create_bins(data, bin_size, min_year, max_year):
    """Create histogram data with adjustable bins"""
    
    # Handle years 1000 and 9999
    special_years = defaultdict(int)
    regular_data = []
    
    for item in data:
        year = item['year_built']
        if year in [1000, 9999]:
            special_years[year] += 1
        else:
            regular_data.append(item)
    
    # Create bins from min_year to max_year
    bins = list(range(min_year, max_year + bin_size, bin_size))
    bin_counts = defaultdict(int)
    
    # Group regular data by bins
    for item in regular_data:
        year = item['year_built']
        if year < min_year or year >= max_year:
            continue
        
        bin_index = (year - min_year) // bin_size
        if bin_index < len(bins) - 1:
            bin_start = bins[bin_index]
            bin_counts[bin_start] += 1

    bin_labels = []
    bin_values = []
    
    for i in range(len(bins) - 1):
        bin_start = bins[i]
        bin_end = bins[i + 1]
        count = bin_counts[bin_start]
        
        bin_labels.append(f"{bin_start}-{bin_end-1}")
        bin_values.append(count)
    
    # Add special years as separate columns at the end
    for year in sorted(special_years.keys()):
        bin_labels.append(f"Year {year}")
        bin_values.append(special_years[year])
    
    return bin_labels, bin_values

def plot_count_by_year(file_path, bin_size, min_year, max_year):
    """Create a bar chart showing number of properties by year built with bins"""
    
    print("Loading data...")
    properties = load_geojson(file_path)
    cleaned_data, null_market, null_year = clean_data(properties)

    #Relay information about the data
    print(f"Found {len(properties)} features")
    print(f"Null/invalid year_built values: {null_year}")
    print(f"Null/invalid market_value values: {null_market}")
    print(f"After cleaning: {len(cleaned_data)} valid records")
    
    if len(cleaned_data) == 0:
        print("No data")
        return
    
    # Show year distribution
    years = [item['year_built'] for item in cleaned_data]
    print(f"Year range in data: {min(years)} - {max(years)}")
    
    # Count special years
    special_year_counts = {}
    for year in [1000, 9999]:
        count = years.count(year)
        if count > 0:
            special_year_counts[year] = count
    
    if special_year_counts:
        print("Special year codes found:")
        for year, count in special_year_counts.items():
            print(f"  Year {year}: {count} properties")

    # Create bins
    bin_labels, bin_values = create_bins(cleaned_data, bin_size, min_year, max_year)
    
    # Create the plot
    plt.figure(figsize=(14, 6))
    
    # Create bar chart
    bars = plt.bar(range(len(bin_labels)), bin_values, alpha=0.7, color='skyblue', edgecolor='navy')
    
    # Showcase special years with different colors
    for i, label in enumerate(bin_labels):
        if 'Year 1000' in label or 'Year 9999' in label:
            bars[i].set_color('orange')
            bars[i].set_alpha(0.8)
    
    # Add value labels on top of each bar
    for i, value in enumerate(bin_values):
        if value > 0:
            plt.text(i, value + max(bin_values) * 0.01, str(value), 
                    ha='center', va='bottom', fontsize=9)
    
    plt.xlabel('Year Built (Bins)', fontsize=12)
    plt.ylabel('Number of Properties', fontsize=12)
    plt.title('Number of Properties by Year Built', fontsize=14, fontweight='bold')
    
    plt.xticks(range(len(bin_labels)), bin_labels, rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Print statistics
    print("\nData Statistics:")
    print(f"Total properties: {len(cleaned_data)}")
    print(f"Year range: {min_year} - {max_year}")
    
    plt.show()

plot_count_by_year(file_path, bin_size, min_year, max_year)
