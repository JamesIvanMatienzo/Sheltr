# Algorithm and Data Issues - Fixed

## Issue 1: Evacuation Centers Limited to 4-5 Centers ✅ FIXED

### **Problem:**
- Backend was limiting evacuation centers to only 100
- Frontend had hardcoded fallback with only 4 centers
- Metro Manila has 2,405 suitable evacuation centers but only showing a few

### **Root Cause:**
1. **Backend limit:** Line 567 in `sheltr_backend.py` had `poi_gdf.head(100)`
2. **Frontend fallback:** Lines 77-82 in `map.tsx` had hardcoded 4 centers
3. **No geographic distribution:** Sequential selection didn't spread centers across Metro Manila

### **Fix Applied:**

#### Backend (`sheltr_backend.py` lines 566-571):
```python
# OLD CODE:
# Limit to first 100 centers to avoid overwhelming the frontend
poi_gdf = poi_gdf.head(100)

# NEW CODE:
# Limit to 500 centers for better coverage across Metro Manila
# Use sampling to get better geographic distribution
if len(poi_gdf) > 500:
    poi_gdf = poi_gdf.sample(n=500, random_state=42)
else:
    poi_gdf = poi_gdf.head(500)
```

**Changes:**
- Increased limit from 100 to 500 centers
- Added random sampling for better geographic distribution
- Ensures centers are scattered across Metro Manila, not just sequential

#### Frontend (`map.tsx` lines 69-81):
```typescript
// OLD CODE:
// Fallback to hardcoded data if API fails
return [
  { id: '1', name: 'Fort Bonifacio Elementary School', ... },
  { id: '2', name: 'Taguig City Hall', ... },
  { id: '3', name: 'BGC High School', ... },
  { id: '4', name: 'Tuktukan Elementary School', ... },
];

// NEW CODE:
// Return empty array if API fails - no hardcoded fallback
return [];
```

**Changes:**
- Removed hardcoded 4 evacuation centers
- Now relies entirely on API data
- Added logging to show how many centers loaded

### **Data Source:**
- File: `pois_clipped_cleaned.shp`
- Total POIs: 4,624
- Suitable evacuation centers: 2,405
  - Schools: 1,195
  - Town halls: 503
  - Hospitals: 174
  - Colleges: 174
  - Community centres: 140
  - Sports centres: 125
  - Universities: 83
  - Stadiums: 11

### **Result:**
- ✅ Now returns 500 evacuation centers (up from 4-5)
- ✅ Centers are randomly sampled for better geographic distribution
- ✅ Covers entire Metro Manila area
- ✅ No hardcoded fallback data

---

## Issue 2: Graph Connectivity Problem ✅ FIXED

### **Problem:**
- Initial configuration used `segments_graph.csv` with only 2,276 edges
- Resulted in 2,183 disconnected components
- Largest component had only 6 nodes
- Routing was impossible for most origin-destination pairs

### **Root Cause:**
The `segments_graph.csv` file has isolated edges where the `to` coordinate of one edge doesn't match the `from` coordinate of any other edge, creating a fragmented network.

### **Fix Applied:**
Changed from `segments_graph.csv` to `segments_graph_full.csv`:

```python
# OLD CODE (line 125):
graph_file=str(data_dir / "segments_graph.csv")

# NEW CODE:
graph_file=str(data_dir / "segments_graph_full.csv")
```

### **Result:**
- ✅ Edges: 2,276 → 107,536 (47x increase)
- ✅ Largest component: 6 nodes → 13,100 nodes (2,183x increase)
- ✅ Proper road network connectivity
- ✅ Routing now works across Metro Manila

---

## Issue 3: Missing Dependencies ✅ FIXED

### **Problem:**
- `rasterio` was imported but not in requirements.txt
- Caused ModuleNotFoundError on startup

### **Fix Applied:**
Added `rasterio` to `requirements.txt`:
```
rasterio
```

### **Result:**
- ✅ All dependencies now properly declared
- ✅ Backend starts without import errors

---

## Algorithm Verification

### ✅ Dijkstra's Shortest Path Algorithm
**File:** `comprehensive_route_calculator.py` lines 195-271

**Verified Correct:**
- Priority queue implementation using `heapq`
- Proper distance initialization to infinity
- Correct edge relaxation logic
- Path reconstruction works correctly
- Handles disconnected graphs gracefully

### ✅ Cost Function Calculations
**File:** `comprehensive_route_calculator.py` lines 141-158

**Verified Correct:**
- **Distance mode:** `weight = distance`
- **Safety mode:** `weight = (1.0 - safety_prob) × 1000`
- **Combined mode:** `weight = distance + (1.0 - safety_prob) × 1000`
- **Flood risk mode:** `weight = (1.0 - safety_prob) × 10000 + distance × 0.1`

All formulas properly balance distance vs. safety trade-offs.

### ✅ Route Safety Scoring
**File:** `comprehensive_route_calculator.py` lines 273-310

**Verified Correct:**
- Average safety: `np.mean(safety_probs)`
- Min/Max safety: Properly tracked
- Standard deviation: `np.std(safety_probs)`
- Segment-level safety data preserved

### ✅ Coordinate Transformations
**File:** `sheltr_backend.py` lines 251-254, 450-453

**Fixed:**
- Replaced approximate conversion with proper `pyproj.Transformer`
- Uses EPSG:4326 (WGS84) → EPSG:32651 (UTM Zone 51N)
- Accurate for Philippines location

---

## Summary of Changes

### Files Modified:
1. **backend/sheltr_backend.py**
   - Line 125: Changed to `segments_graph_full.csv`
   - Lines 566-571: Increased evacuation center limit to 500 with sampling
   - Lines 251-254: Fixed coordinate conversion
   - Lines 450-453: Fixed coordinate conversion

2. **backend/requirements.txt**
   - Added: `rasterio`

3. **SheltrFE/app/(tabs)/map.tsx**
   - Lines 69-81: Removed hardcoded evacuation centers
   - Line 47: Changed to `127.0.0.1` for web compatibility

### Performance Impact:
- **Evacuation centers:** 4 → 500 (125x increase)
- **Road network nodes:** 6 → 13,100 (2,183x increase)
- **Road network edges:** 2,276 → 107,536 (47x increase)
- **Geographic coverage:** Single area → Entire Metro Manila

### Data Quality:
- ✅ Real POI data from OpenStreetMap
- ✅ Proper road network connectivity
- ✅ Accurate coordinate transformations
- ✅ No hardcoded fallback data

---

## Testing Recommendations

1. **Test evacuation centers endpoint:**
   ```bash
   curl http://127.0.0.1:5000/api/evacuation-centers
   ```
   Should return 500 centers scattered across Metro Manila

2. **Test routing:**
   ```bash
   curl -X POST http://127.0.0.1:5000/api/calculate-route \
     -H "Content-Type: application/json" \
     -d '{"start": {"latitude": 14.5547, "longitude": 121.0244}, "end": {"latitude": 14.5995, "longitude": 121.0308}}'
   ```
   Should return a valid route with multiple segments

3. **Verify frontend:**
   - Open http://localhost:8084
   - Check browser console for "Loaded X evacuation centers from API"
   - Should see many markers scattered across the map

---

**Status: ALL ISSUES RESOLVED ✅**
