# QGIS Attribute Management Instructions for Flood Risk ML Dataset

## 🎯 **OVERVIEW**
This document provides specific instructions for managing attributes in QGIS to prepare your data for the Random Forest ML model.

## 📋 **CURRENT DATA STATUS**

### ✅ **READY TO USE (No Changes Needed)**
- **dist_to_river.gpkg**: Contains `HubName` and `HubDist` - Perfect!
- **flood_hazard.gpkg**: Contains `Var` (hazard levels 1-3) - Perfect!
- **dem_clipped_projected.tif**: Elevation data - Perfect!
- **chirps-v3.0.2024.070809101112.tif**: High-resolution rainfall data - Perfect!

### ⚠️ **NEEDS ATTRIBUTE MANAGEMENT**

## 🔧 **QGIS INSTRUCTIONS**

### 1. **ROADS_CLIPPED.SHP** - Add Road Classification

**Current Issue**: Only has geometry, no road attributes

**Actions in QGIS**:
1. Open `roads_clipped.shp` in QGIS
2. Open Attribute Table
3. Add new columns:
   - **road_type** (Text, 50): highway, primary, secondary, residential, etc.
   - **road_width** (Real, 10,2): width in meters
   - **surface_type** (Text, 30): paved, unpaved, concrete, asphalt
   - **lanes** (Integer): number of lanes

**How to Add Columns**:
- Right-click layer → Properties → Fields
- Click "Add Field" button
- Set field name, type, and length
- Click OK

**Manual Classification** (if needed):
- Use QGIS selection tools to select road segments by visual inspection
- Update attributes in the attribute table
- Or use the Field Calculator with expressions like:
  ```sql
  CASE 
    WHEN "width" > 20 THEN 'highway'
    WHEN "width" > 10 THEN 'primary'
    WHEN "width" > 6 THEN 'secondary'
    ELSE 'residential'
  END
  ```

### 2. **POIS_CLIPPED_CLEANED.SHP** - Add POI Categories

**Current Issue**: Has basic OSM data but needs evacuation-specific categories

**Actions in QGIS**:
1. Open `processed/pois/pois_clipped_cleaned.shp`
2. Add new columns:
   - **evac_capacity** (Integer): number of people it can accommodate
   - **evac_type** (Text, 30): school, church, community_center, government_building
   - **accessibility** (Text, 20): wheelchair_accessible, limited_access, no_access
   - **emergency_services** (Text, 50): medical, food, shelter, communication

**How to Classify**:
- Use the `fclass` field as a starting point
- Create a new field with Field Calculator:
  ```sql
  CASE 
    WHEN "fclass" = 'school' THEN 'school'
    WHEN "fclass" = 'place_of_worship' THEN 'church'
    WHEN "fclass" = 'community_centre' THEN 'community_center'
    ELSE 'other'
  END
  ```

### 3. **LANDUSE_CLIPPED.SHP** - Standardize Landuse Categories

**Current Issue**: OSM landuse categories may be too detailed for ML

**Actions in QGIS**:
1. Open `landuse_clipped.shp`
2. Add new column:
   - **landuse_simplified** (Text, 30): residential, commercial, industrial, agricultural, water, forest, open_space

**Simplification Rules**:
```sql
CASE 
  WHEN "fclass" IN ('residential', 'apartments', 'house') THEN 'residential'
  WHEN "fclass" IN ('commercial', 'retail', 'office') THEN 'commercial'
  WHEN "fclass" IN ('industrial', 'warehouse') THEN 'industrial'
  WHEN "fclass" IN ('farmland', 'farm', 'agricultural') THEN 'agricultural'
  WHEN "fclass" IN ('water', 'river', 'lake') THEN 'water'
  WHEN "fclass" IN ('forest', 'park', 'grass') THEN 'open_space'
  ELSE 'other'
END
```

### 4. **RIVERS_CLIPPED.SHP** - Add River Characteristics

**Current Issue**: Basic river data, needs flood risk indicators

**Actions in QGIS**:
1. Open `rivers_clipped.shp`
2. Add new columns:
   - **river_width** (Real, 10,2): width in meters
   - **flood_risk** (Text, 20): high, medium, low
   - **seasonal_variation** (Text, 20): high, medium, low

**How to Calculate**:
- Use the existing `width` field or calculate from geometry
- For flood risk, use Field Calculator:
  ```sql
  CASE 
    WHEN "width" > 50 THEN 'high'
    WHEN "width" > 20 THEN 'medium'
    ELSE 'low'
  END
  ```

## 🚫 **ATTRIBUTES TO DELETE**

### **IBTrACS Typhoon Data** - Remove Unnecessary Columns
The typhoon data has 180 columns, most are not needed for ML.

**Columns to KEEP**:
- `SID` (Storm ID)
- `NAME` (Storm Name)
- `LAT`, `LON` (Coordinates)
- `WMO_WIND` (Wind Speed)
- `WMO_PRES` (Pressure)
- `geometry`

**Columns to DELETE** (in QGIS):
1. Open `IBTrACS.last3years.list.v04r01.lines.shp`
2. Right-click → Properties → Fields
3. Select columns to delete (all the ones not listed above)
4. Click "Delete Field"

## 📊 **DATA VALIDATION STEPS**

### 1. **Check for Duplicates**
- Use Vector → Data Management Tools → Remove Duplicate Geometries
- Check for duplicate `HubName` values in `dist_to_river.gpkg`

### 2. **Check for Null Values**
- Open attribute tables
- Look for empty cells
- Use Field Calculator to fill nulls:
  ```sql
  CASE 
    WHEN "field_name" IS NULL THEN 'unknown'
    ELSE "field_name"
  END
  ```

### 3. **Check Data Ranges**
- Verify elevation values are reasonable (0-500m for Manila)
- Verify distance values are in meters
- Verify rainfall values are in mm

## 🎯 **FINAL RECOMMENDATIONS**

### **Priority 1 (Must Do)**:
1. Add road classification to `roads_clipped.shp`
2. Clean up typhoon data columns
3. Standardize landuse categories

### **Priority 2 (Should Do)**:
1. Add POI evacuation capacity
2. Add river flood risk indicators
3. Validate all data ranges

### **Priority 3 (Nice to Have)**:
1. Add road surface conditions
2. Add historical flood frequency
3. Add population density data

## 🔄 **WORKFLOW SUMMARY**

1. **Open QGIS**
2. **Load all shapefiles**
3. **Add required attributes** (follow instructions above)
4. **Validate data quality**
5. **Save all changes**
6. **Run the Python script** to create ML dataset

## ⚠️ **IMPORTANT NOTES**

- **Always backup** your original files before making changes
- **Use consistent field names** across all files
- **Check CRS** - all files should be in UTM Zone 51N (EPSG:32651)
- **Validate geometry** - use Vector → Geometry Tools → Check Validity

## 📁 **EXPECTED OUTPUT**

After following these instructions, your data will be ready for the Python ML script, which will create:
- `ml_flood_risk_dataset.csv` - For ML training
- `ml_flood_risk_dataset.gpkg` - For visualization

The final dataset will have all required features:
- HubName, rainfall_mm_3h, hazard_status, elevation
- dist_to_river, tracks, safe_status, dist_to_poi
- landuse features, road_type, evac_capacity, etc.

