import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Polygon, Point, MultiPolygon, LineString

"Code uses Dallas parcels + Microsoft's GlobalMLBuildingFootprints. "
"Code returns Market Value, Year Built, and Geometry for Dallas County parcels."
"*** Dallas parcels have only 11% of build dates***   " 

# Load datasets
print("Loading datasets...")

#Set both paths below to your data files
parcels = gpd.read_file("/Users/jacksonmorrissett/Projects/Research/Dallas-housing/shp/stratmap24-landparcels_48113_dallas_202407.dbf")
microsoft = gpd.read_file("/Users/jacksonmorrissett/Projects/Research/Dallas.geojson")

def round_coordinates(geom, precision=6):
    """Round coordinates to specified decimal places"""
    if geom is None or geom.is_empty:
        return geom
        
    if geom.geom_type == 'Polygon':
        exterior = [(round(x, precision), round(y, precision)) for x, y in geom.exterior.coords]
        holes = []
        for interior in geom.interiors:
            hole_coords = [(round(x, precision), round(y, precision)) for x, y in interior.coords]
            holes.append(hole_coords)
        return Polygon(exterior, holes)
        
    elif geom.geom_type == 'Point':
        return Point(round(geom.x, precision), round(geom.y, precision))
        
    elif geom.geom_type == 'LineString':
        coords = [(round(x, precision), round(y, precision)) for x, y in geom.coords]
        return LineString(coords)
        
    elif geom.geom_type == 'MultiPolygon':
        polygons = []
        for poly in geom.geoms:
            polygons.append(round_coordinates(poly, precision))
        return MultiPolygon(polygons)
        
    return geom

# Ensure coordinates are same format
parcels_latlon = parcels.to_crs(epsg=4326)
bounds_latlon = microsoft.to_crs(epsg=4326)
parcels_latlon['geometry'] = parcels_latlon['geometry'].apply(lambda geom: round_coordinates(geom, 6))
bounds_latlon['geometry'] = bounds_latlon['geometry'].apply(lambda geom: round_coordinates(geom, 6))

# Ensure parcels are only within dallas county
dallas_bbox = box(-97.027500, 32.538500, -96.449000, 33.016500)
parcels_filtered = parcels_latlon[parcels_latlon.geometry.intersects(dallas_bbox)]

# Combine the two
print("combining datasets...")
gdf_joined = gpd.sjoin(bounds_latlon, parcels_filtered, how="left", predicate="intersects")

# Clean year built data
if 'YEAR_BUILT' in gdf_joined.columns:
    gdf_joined['YEAR_BUILT'] = pd.to_numeric(gdf_joined['YEAR_BUILT'], errors='coerce')

# Keep geometry (coordinates), market value, and build date.
new_cols = ['geometry']
if 'MKT_VALUE' in gdf_joined.columns:
    new_cols.append('MKT_VALUE')
if 'YEAR_BUILT' in gdf_joined.columns:
    new_cols.append('YEAR_BUILT')

# Create final result with only the requested data
result = gdf_joined[new_cols].copy()

# Saveing the result
result.to_file("dallas_3var.geojson", driver="GeoJSON")
print(f"Results saved with {len(result)} records")
print(f"Columns: {result.columns.tolist()}")
