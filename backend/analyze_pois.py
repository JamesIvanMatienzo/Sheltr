import geopandas as gpd
import sys

# Read POI file
poi_file = '../pois_clipped_cleaned.shp'
print(f"Reading {poi_file}...")
gdf = gpd.read_file(poi_file)

print(f"\nTotal POIs: {len(gdf)}")
print(f"Columns: {list(gdf.columns)}")
print(f"CRS: {gdf.crs}")

if 'fclass' in gdf.columns:
    print(f"\nfclass distribution:")
    print(gdf['fclass'].value_counts().head(30))
    
    # Check for evacuation-suitable types
    suitable_types = ['school', 'town_hall', 'community_centre', 'hospital', 
                     'sports_centre', 'stadium', 'university', 'college']
    
    filtered = gdf[gdf['fclass'].isin(suitable_types)]
    print(f"\nSuitable evacuation centers: {len(filtered)}")
    print(f"Types found: {filtered['fclass'].value_counts()}")
    
    # Sample some centers
    print(f"\nSample evacuation centers:")
    for idx, row in filtered.head(10).iterrows():
        name = row.get('name', 'Unnamed')
        fclass = row.get('fclass', 'unknown')
        geom = row.geometry
        if geom.geom_type == 'Point':
            print(f"  - {name} ({fclass}) at {geom.y:.4f}, {geom.x:.4f}")
