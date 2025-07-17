import geopandas as gpd

"Code shows what data the Dallas parcels contains" 

# Load the parcel dataset
parcels = gpd.read_file("/Users/jacksonmorrissett/Projects/Research/Dallas-housing/shp/stratmap24-landparcels_48113_dallas_202407.dbf")

print("DATASET OVERVIEW")
print(f"Total rows: {len(parcels)}")
print(f"Total columns: {len(parcels.columns)}")

print("ALL COLUMN NAMES + DATA TYPES")
for i, col in enumerate(parcels.columns, 1):
    print(f"{i:2d}. {col}")

print("COLUMN DATA TYPES")
print(parcels.dtypes)