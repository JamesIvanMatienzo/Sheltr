    #!/usr/bin/env python3
"""
Sheltr Backend API Server
Integrates ML flood risk prediction with React Native frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import json
import os
from pathlib import Path
from typing import Optional
import geopandas as gpd
from shapely.geometry import Point
import warnings
warnings.filterwarnings('ignore')

# Import our ML components
from comprehensive_route_calculator import ComprehensiveFloodRiskRouter
from inference_script import FloodRiskInference, load_segment_predictions, score_route_safety
from navigation_directions import generate_turn_by_turn_directions, get_direction_summary

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Error handlers
@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler"""
    print(f"Error occurred: {str(e)}")
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

# Global variables for ML models
ml_inference = None
router = None
segments_data = None
safe_points_utm = None  # List of (x, y) tuples in EPSG:32651
segments_geometries = None  # GeoDataFrame with road geometries

def _read_safepoints_anywhere() -> Optional[gpd.GeoDataFrame]:
    """Try to read safepoints from a user-provided file or common defaults.

    Tries the following in order:
    - Environment variable SAFEPOINTS_PATH
    - POI files (pois_clipped_cleaned.shp, pois_clipped.shp)
    - safepoints.gpkg / safepoints.shp / safepoints.geojson / safepoints.csv in CWD
    CSV must contain 'latitude' and 'longitude' or 'lat'/'lon' columns.
    """
    candidates = []
    env_path = os.getenv("SAFEPOINTS_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path("pois_clipped_cleaned.shp"),
        Path("processed/pois/pois_clipped_cleaned.shp"),
        Path("pois_clipped.shp"),
        Path("../pois_clipped_cleaned.shp"),
        Path("../pois_clipped.shp"),
        Path("../processed/pois/pois_clipped_cleaned.shp"),
        Path("safepoints.gpkg"),
        Path("safepoints.shp"),
        Path("safepoints.geojson"),
        Path("safepoints.csv"),
    ])

    for p in candidates:
        try:
            if not p.exists():
                continue
            if p.suffix.lower() == ".csv":
                df = pd.read_csv(p)
                lat_col = next((c for c in df.columns if c.lower() in {"latitude", "lat"}), None)
                lon_col = next((c for c in df.columns if c.lower() in {"longitude", "lon", "lng"}), None)
                if not lat_col or not lon_col:
                    continue
                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                    crs="EPSG:4326",
                )
                return gdf
            else:
                gdf = gpd.read_file(p)
                # If no CRS, assume WGS84
                if gdf.crs is None:
                    gdf = gdf.set_crs("EPSG:4326", allow_override=True)
                return gdf
        except Exception:
            continue
    return None


def initialize_ml_models():
    """Initialize ML models and data"""
    global ml_inference, router, segments_data, segments_geometries
    
    print("Initializing ML models...")
    
    try:
        # Resolve project directories
        backend_dir = Path(__file__).resolve().parent
        project_root = backend_dir.parent
        data_dir = project_root / "data"
        models_dir = project_root / "models"
        
        # Load ML inference engine
        ml_inference = FloodRiskInference(
            model_path=str(models_dir / "rf_model_balanced.joblib"),
            scaler_path=str(models_dir / "scaler.joblib")
        )
        print("ML inference engine loaded successfully")
        
        # Initialize router
        router = ComprehensiveFloodRiskRouter(
            segments_file=str(data_dir / "segments_safe_min_dedup.csv"),
            graph_file=str(data_dir / "segments_graph_full.csv")
        )
        router.load_data()
        router.analyze_network_structure()
        print("Router initialized successfully")
        
        # Load segments data for quick lookup
        segments_data = pd.read_csv(data_dir / 'segments_safe_min_dedup.csv')
        segments_data['HubName'] = segments_data['HubName'].astype(str)
        print(f"Segments data loaded: {len(segments_data)} segments")
        
        # Load road geometries from GeoJSON
        try:
            segments_geometries = gpd.read_file(data_dir / 'segments_safe_min_dedup.geojson')
            segments_geometries['HubName'] = segments_geometries['HubName'].astype(str)
            print(f"Road geometries loaded: {len(segments_geometries)} segments with actual road shapes")
        except Exception as e:
            print(f"Warning: Could not load road geometries: {e}")
            segments_geometries = None

        # Load safepoints and project to EPSG:32651 (UTM Zone 51N)
        sp_gdf = _read_safepoints_anywhere()
        if sp_gdf is not None and not sp_gdf.empty:
            try:
                sp_utm = sp_gdf.to_crs("EPSG:32651")
                # Extract centroids for nearest search (handle both points and polygons)
                coords = []
                for geom in sp_utm.geometry:
                    if geom is not None:
                        if geom.geom_type == 'Point':
                            coords.append((geom.x, geom.y))
                        elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                            # Use centroid for polygons
                            centroid = geom.centroid
                            coords.append((centroid.x, centroid.y))
                
                if coords:
                    print(f"Safepoints loaded: {len(coords)} points")
                    # Store as list for fast nearest lookup
                    globals()["safe_points_utm"] = coords
                else:
                    print("Safepoints file has no valid geometries; skipping safepoints integration")
            except Exception as e:
                print(f"Failed to project safepoints to EPSG:32651: {e}")
        else:
            print("No safepoints file found. You can set SAFEPOINTS_PATH or place safepoints.gpkg/shp/geojson/csv in the project root.")
        
        return True
        
    except Exception as e:
        print(f"Error initializing ML models: {e}")
        return False

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'Sheltr Backend API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': [
            '/api/health',
            '/api/segments',
            '/api/predict',
            '/api/calculate-route',
            '/api/evacuation-centers',
            '/api/flood-risk'
        ]
    })

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ml_model_loaded': ml_inference is not None,
        'router_ready': router is not None,
        'segments_loaded': segments_data is not None
    })

@app.route('/api/segments')
def get_segments():
    """Get all road segments with safety predictions"""
    try:
        if segments_data is None:
            return jsonify({'error': 'Segments data not loaded'}), 500
        
        # Convert to GeoJSON format for frontend
        segments_geojson = {
            'type': 'FeatureCollection',
            'features': []
        }
        
        for _, segment in segments_data.iterrows():
            feature = {
                'type': 'Feature',
                'properties': {
                    'id': segment['HubName'],
                    'safe': int(segment['pred_safe']),
                    'safety_prob': float(segment['pred_prob_safe']),
                    'risk_level': 'high' if segment['pred_safe'] == 0 else 'low'
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [0, 0]  # Placeholder - would need actual coordinates
                }
            }
            segments_geojson['features'].append(feature)
        
        return jsonify(segments_geojson)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict', methods=['POST'])
def predict_flood_risk_api():
    """Predict flood risk for given coordinates"""
    try:
        data = request.get_json()
        
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Latitude and longitude required'}), 400
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        
        # Convert to UTM coordinates using proper projection
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
        utm_x, utm_y = transformer.transform(lng, lat)
        
        # Find nearest segment
        if segments_data is not None:
            # Simple distance calculation to find nearest segment
            distances = np.sqrt((segments_data.get('x', 0) - utm_x)**2 + (segments_data.get('y', 0) - utm_y)**2)
            nearest_idx = distances.idxmin()
            nearest_segment = segments_data.iloc[nearest_idx]
            
            prediction = {
                'safe': int(nearest_segment['pred_safe']),
                'safety_probability': float(nearest_segment['pred_prob_safe']),
                'risk_level': 'high' if nearest_segment['pred_safe'] == 0 else 'low',
                'segment_id': nearest_segment['HubName']
            }
        else:
            # Fallback prediction
            prediction = {
                'safe': 1,
                'safety_probability': 0.8,
                'risk_level': 'low',
                'segment_id': 'unknown'
            }
        
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calculate-route', methods=['POST'])
def calculate_route():
    """Calculate optimal route between two points"""
    try:
        data = request.get_json()
        
        if not data or 'start' not in data:
            return jsonify({'error': 'Start coordinates required'}), 400
        
        start = data['start']
        end = data.get('end')
        cost_function = data.get('cost_function', 'combined')
        
        if router is None:
            return jsonify({'error': 'Router not initialized'}), 500
        
        # Validate start coordinates
        if 'latitude' not in start or 'longitude' not in start:
            return jsonify({'error': 'Start coordinates must include latitude and longitude'}), 400
        
        # Convert coordinates to UTM-approx strings expected by router (x,y)
        def latlng_to_utm_xy(lat_val: float, lng_val: float) -> str:
            try:
                # Use proper UTM conversion for Philippines (Zone 51N)
                from pyproj import Transformer
                transformer = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
                ux, uy = transformer.transform(lng_val, lat_val)
                return f"{ux},{uy}"
            except Exception as e:
                raise ValueError(f"Invalid coordinates: {e}")

        start_coords = latlng_to_utm_xy(float(start['latitude']), float(start['longitude']))

        if end is not None and 'latitude' in end and 'longitude' in end:
            end_coords = latlng_to_utm_xy(float(end['latitude']), float(end['longitude']))
        else:
            # If end is not supplied, use nearest safepoint to the user
            if safe_points_utm:
                sx, sy = map(float, start_coords.split(','))
                # Find nearest safepoint by Euclidean distance in UTM
                dmin = float('inf')
                ex, ey = None, None
                for (px, py) in safe_points_utm:
                    d = (px - sx) * (px - sx) + (py - sy) * (py - sy)
                    if d < dmin:
                        dmin = d
                        ex, ey = px, py
                if ex is not None and ey is not None:
                    end_coords = f"{ex},{ey}"
                else:
                    return jsonify({'error': 'No valid safepoints available'}), 500
            else:
                return jsonify({'error': 'No safepoints configured. Provide "end" or configure safepoints.'}), 400
        
        # Calculate route
        route = router.find_optimal_route(start_coords, end_coords, cost_function)
        
        if not route['success']:
            return jsonify({'error': route['message']}), 400
        
        print(f"Route found with {len(route.get('path', []))} nodes")
        print(f"Segments geometries available: {segments_geometries is not None}")
        print(f"Path details available: {'path_details' in route}")
        if 'path_details' in route:
            print(f"Number of segments in path: {len(route['path_details'].get('segments', []))}")
        
        # Extract actual road geometries from segments for curved paths
        route_coords = []
        
        if segments_geometries is not None and 'path_details' in route and 'segments' in route['path_details']:
            # Use actual road geometries for accurate visualization
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)
            
            # Create a deep copy to avoid iteration issues
            import copy
            segments_list = copy.deepcopy(route['path_details']['segments'])
            print(f"Extracting geometries for {len(segments_list)} segments")
            
            for idx, segment in enumerate(segments_list):
                try:
                    segment_id = str(segment.get('segment_id', ''))
                    if not segment_id:
                        continue
                        
                    # Find geometry for this segment
                    matching_geoms = segments_geometries[segments_geometries['HubName'] == segment_id]
                    
                    if len(matching_geoms) > 0:
                        geom = matching_geoms.iloc[0].geometry
                        # Extract coordinates from the geometry
                        if geom.geom_type == 'MultiLineString':
                            for line in geom.geoms:
                                coords_list = list(line.coords)
                                for coord in coords_list:
                                    lng, lat = transformer.transform(coord[0], coord[1])
                                    route_coords.append([lat, lng])
                        elif geom.geom_type == 'LineString':
                            coords_list = list(geom.coords)
                            for coord in coords_list:
                                lng, lat = transformer.transform(coord[0], coord[1])
                                route_coords.append([lat, lng])
                    else:
                        # Fallback: use segment endpoints if geometry not found
                        from_node = segment.get('from', '')
                        to_node = segment.get('to', '')
                        if from_node and to_node:
                            try:
                                fx, fy = map(float, from_node.split(','))
                                tx, ty = map(float, to_node.split(','))
                                lng1, lat1 = transformer.transform(fx, fy)
                                lng2, lat2 = transformer.transform(tx, ty)
                                route_coords.append([lat1, lng1])
                                route_coords.append([lat2, lng2])
                            except Exception as fallback_err:
                                print(f"Fallback error for segment {segment_id}: {fallback_err}")
                except Exception as e:
                    print(f"Error processing segment {idx}: {e}")
                    import traceback
                    traceback.print_exc()
            
            print(f"Extracted {len(route_coords)} coordinate points")
        else:
            # Fallback: use node coordinates if geometries not available
            def utm_xy_to_latlng(utm_str: str) -> list:
                try:
                    ux, uy = map(float, utm_str.split(','))
                    from pyproj import Transformer
                    transformer = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)
                    lng, lat = transformer.transform(ux, uy)
                    return [lat, lng]
                except Exception as e:
                    print(f"Error converting {utm_str}: {e}")
                    return None
            
            for node in route['path']:
                coords = utm_xy_to_latlng(node)
                if coords:
                    route_coords.append(coords)
        
        # Generate turn-by-turn directions
        directions = []
        directions_summary = {}
        if route_coords and len(route_coords) >= 2:
            try:
                directions = generate_turn_by_turn_directions(route_coords)
                directions_summary = get_direction_summary(directions)
                print(f"Generated {len(directions)} turn-by-turn directions")
            except Exception as e:
                print(f"Error generating directions: {e}")
        
        # Format response for frontend
        route_response = {
            'route': route_coords,  # Now in [[lat, lng], [lat, lng], ...] format with curves
            'totalDistance': route['total_distance'] / 1000,  # Convert meters to km
            'safetyScore': route['avg_safety'],
            'floodRisk': 1.0 - route['avg_safety'],  # Convert safety to risk
            'numSegments': route['num_segments'],
            'costFunction': cost_function,
            'segments': route['path_details']['segments'] if 'path_details' in route else [],
            'directions': directions,  # Turn-by-turn navigation
            'directionsSummary': directions_summary  # Route summary
        }
        
        return jsonify(route_response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nearest-safe-route', methods=['POST'])
def nearest_safe_route():
    """Route from user's location to the nearest safepoint.

    Request JSON body: { "latitude": <float>, "longitude": <float>, "cost_function": "combined" }
    """
    try:
        data = request.get_json()
        if not data or 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'Latitude and longitude required'}), 400

        if router is None:
            return jsonify({'error': 'Router not initialized'}), 500

        lat = float(data['latitude'])
        lng = float(data['longitude'])
        cost_function = data.get('cost_function', 'combined')

        # Convert to UTM using proper projection
        from pyproj import Transformer
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
        ux, uy = transformer.transform(lng, lat)
        start_coords = f"{ux},{uy}"

        if not safe_points_utm:
            return jsonify({'error': 'No safepoints configured. Set SAFEPOINTS_PATH or place a safepoints file in the project root.'}), 500

        # Find nearest safepoint
        dmin = float('inf')
        ex, ey = None, None
        for (px, py) in safe_points_utm:
            d = (px - ux) * (px - ux) + (py - uy) * (py - uy)
            if d < dmin:
                dmin = d
                ex, ey = px, py
        end_coords = f"{ex},{ey}"

        # Calculate route
        route = router.find_optimal_route(start_coords, end_coords, cost_function)
        if not route['success']:
            return jsonify({'error': route['message']}), 400

        # Extract actual road geometries from segments for curved paths
        route_coords = []
        
        if segments_geometries is not None and 'path_details' in route and 'segments' in route['path_details']:
            # Use actual road geometries for accurate visualization
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)
            
            # Create a deep copy to avoid iteration issues
            import copy
            segments_list = copy.deepcopy(route['path_details']['segments'])
            
            for idx, segment in enumerate(segments_list):
                try:
                    segment_id = str(segment.get('segment_id', ''))
                    if not segment_id:
                        continue
                        
                    # Find geometry for this segment
                    matching_geoms = segments_geometries[segments_geometries['HubName'] == segment_id]
                    
                    if len(matching_geoms) > 0:
                        geom = matching_geoms.iloc[0].geometry
                        # Extract coordinates from the geometry
                        if geom.geom_type == 'MultiLineString':
                            for line in geom.geoms:
                                coords_list = list(line.coords)
                                for coord in coords_list:
                                    lng, lat = transformer.transform(coord[0], coord[1])
                                    route_coords.append([lat, lng])
                        elif geom.geom_type == 'LineString':
                            coords_list = list(geom.coords)
                            for coord in coords_list:
                                lng, lat = transformer.transform(coord[0], coord[1])
                                route_coords.append([lat, lng])
                    else:
                        # Fallback: use segment endpoints if geometry not found
                        from_node = segment.get('from', '')
                        to_node = segment.get('to', '')
                        if from_node and to_node:
                            try:
                                fx, fy = map(float, from_node.split(','))
                                tx, ty = map(float, to_node.split(','))
                                lng1, lat1 = transformer.transform(fx, fy)
                                lng2, lat2 = transformer.transform(tx, ty)
                                route_coords.append([lat1, lng1])
                                route_coords.append([lat2, lng2])
                            except Exception as fallback_err:
                                print(f"Fallback error for segment {segment_id}: {fallback_err}")
                except Exception as e:
                    print(f"Error processing segment {idx}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            # Fallback: use node coordinates if geometries not available
            def utm_xy_to_latlng(utm_str: str) -> list:
                try:
                    ux, uy = map(float, utm_str.split(','))
                    from pyproj import Transformer
                    transformer = Transformer.from_crs("EPSG:32651", "EPSG:4326", always_xy=True)
                    lng, lat = transformer.transform(ux, uy)
                    return [lat, lng]
                except Exception as e:
                    print(f"Error converting {utm_str}: {e}")
                    return None
            
            for node in route['path']:
                coords = utm_xy_to_latlng(node)
                if coords:
                    route_coords.append(coords)

        # Generate turn-by-turn directions
        directions = []
        directions_summary = {}
        if route_coords and len(route_coords) >= 2:
            try:
                directions = generate_turn_by_turn_directions(route_coords)
                directions_summary = get_direction_summary(directions)
                print(f"Generated {len(directions)} turn-by-turn directions")
            except Exception as e:
                print(f"Error generating directions: {e}")

        route_response = {
            'route': route_coords,  # Now in [[lat, lng], [lat, lng], ...] format with curves
            'totalDistance': route['total_distance'] / 1000,  # Convert meters to km
            'safetyScore': route['avg_safety'],
            'floodRisk': 1.0 - route['avg_safety'],
            'numSegments': route['num_segments'],
            'costFunction': cost_function,
            'segments': route['path_details']['segments'] if 'path_details' in route else [],
            'directions': directions,  # Turn-by-turn navigation
            'directionsSummary': directions_summary  # Route summary
        }
        return jsonify(route_response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/evacuation-centers')
def get_evacuation_centers():
    """Get evacuation centers data from POI files"""
    try:
        # Load POI data as evacuation centers
        poi_gdf = _read_safepoints_anywhere()
        if poi_gdf is not None and not poi_gdf.empty:
            # Filter for suitable evacuation center types
            suitable_types = ['school', 'town_hall', 'community_centre', 'hospital', 
                            'sports_centre', 'stadium', 'university', 'college']
            
            if 'fclass' in poi_gdf.columns:
                poi_gdf = poi_gdf[poi_gdf['fclass'].isin(suitable_types)]
                print(f"Filtered to {len(poi_gdf)} suitable evacuation centers")
            
            # Limit to 500 centers for better coverage across Metro Manila
            # Use sampling to get better geographic distribution
            if len(poi_gdf) > 500:
                poi_gdf = poi_gdf.sample(n=500, random_state=42)
            else:
                poi_gdf = poi_gdf.head(500)
            
            centers = []
            # Ensure POI data is in WGS84 for the frontend
            if poi_gdf.crs is None:
                poi_gdf = poi_gdf.set_crs("EPSG:4326", allow_override=True)
            elif poi_gdf.crs.to_string() != "EPSG:4326":
                poi_gdf = poi_gdf.to_crs("EPSG:4326")
            
            for idx, row in poi_gdf.iterrows():
                # Convert to lat/lng for frontend
                geom = row.geometry
                if geom is not None:
                    # Handle both points and polygons
                    if geom.geom_type == 'Point':
                        lng, lat = geom.x, geom.y
                    elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                        centroid = geom.centroid
                        lng, lat = centroid.x, centroid.y
                    else:
                        continue
                    
                    center = {
                        'id': str(idx),
                        'name': row.get('name', f'Evacuation Center {idx}'),
                        'latitude': lat,
                        'longitude': lng,
                        'capacity': row.get('capacity', 500),
                        'safety_score': row.get('safety_score', 0.8)
                    }
                    centers.append(center)
            
            if centers:
                return jsonify(centers)
        
        # Return empty list if no POI data available
        return jsonify([])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flood-risk')
def get_flood_risk():
    """Return flood risk overlay lines. Placeholder until hazard lines are available."""
    try:
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather')
def get_weather():
    """Get weather data (placeholder - would integrate with weather API)"""
    try:
        # This would typically integrate with a weather API
        weather_data = {
            'temperature': 28.5,
            'humidity': 75,
            'precipitation': 0.0,
            'wind_speed': 12.3,
            'conditions': 'Partly Cloudy',
            'timestamp': '2025-01-21T10:00:00Z'
        }
        
        return jsonify(weather_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications')
def get_notifications():
    """Get flood risk notifications"""
    try:
        notifications = [
            {
                'id': '1',
                'title': 'Flood Risk Alert',
                'message': 'High flood risk detected in your area. Consider alternative routes.',
                'type': 'warning',
                'timestamp': '2025-01-21T09:30:00Z',
                'priority': 'high'
            },
            {
                'id': '2',
                'title': 'Route Update',
                'message': 'Safer route available to your destination.',
                'type': 'info',
                'timestamp': '2025-01-21T09:15:00Z',
                'priority': 'medium'
            }
        ]
        
        return jsonify(notifications)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("SHELTR BACKEND API SERVER")
    print("=" * 60)
    
    # Initialize ML models
    if initialize_ml_models():
        print("All systems initialized successfully")
        print("Starting Flask server...")
        print("API available at: http://localhost:5000")
        print("Frontend should connect to: http://localhost:5000")
        
        # Start Flask server
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        print("Failed to initialize ML models")
        print("Please check that all required files are present:")
        print("- rf_model_balanced.joblib")
        print("- scaler.joblib")
        print("- segments_safe_min_dedup.csv")
        print("- segments_graph.csv")


