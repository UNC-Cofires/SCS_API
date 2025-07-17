import geopandas as gpd
from shapely.geometry import box

"Code uses Microsoft Texas spatial data to "
"return Dallas County only."

#From microsoft spatial data, filter to Dallas County

gdf = gpd.read_file("Texas.geojson")

#dallas_county
minx, miny = -97.027500, 32.538500  # bottom-left
maxx, maxy = -96.449000, 33.016500  # top-right
dallas_bbox = box(minx, miny, maxx, maxy)

gdf_filtered = gdf[gdf.geometry.intersects(dallas_bbox)]
gdf_filtered.to_file("Dallas.geojson", driver="GeoJSON")
