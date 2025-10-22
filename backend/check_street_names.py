import geopandas as gpd
import pandas as pd

# Check GeoJSON
print("Checking GeoJSON file...")
gdf = gpd.read_file('../data/segments_safe_min_dedup.geojson')
print(f"Columns: {list(gdf.columns)}")
print(f"\nSample data:")
print(gdf.head(3))

# Check if there are any name/street columns
name_cols = [col for col in gdf.columns if 'name' in col.lower() or 'street' in col.lower() or 'road' in col.lower()]
print(f"\nName-related columns: {name_cols}")
