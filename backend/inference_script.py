#!/usr/bin/env python3
"""
Inference Script for Flood Risk Prediction
Loads trained model and scores new road segments
"""

import pandas as pd
import numpy as np
import joblib
import geopandas as gpd
import rasterio
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class FloodRiskInference:
    def __init__(self, model_path="rf_model.joblib", scaler_path="scaler.joblib"):
        """Initialize with trained model and scaler"""
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.feature_names = None
        
    def extract_features_from_segment(self, segment_data):
        """
        Extract features from a single road segment
        
        Args:
            segment_data: dict with keys:
                - HubName: unique road ID
                - geometry: shapely geometry
                - dist_to_river: distance to nearest river
                - elevation: DEM value at centroid
                - rainfall_mm_3h: rainfall value
                - hazard_status: 0-3 flood hazard level
                - dist_to_poi: distance to nearest evacuation center
                - landuse_features: dict of landuse presence (0/1)
        
        Returns:
            numpy array of features ready for prediction
        """
        # Base features
        features = [
            segment_data.get('HubName', 0),
            segment_data.get('dist_to_river', 0),
            segment_data.get('elevation', 0),
            segment_data.get('rainfall_mm_3h', 0),
            segment_data.get('hazard_status', 0),
            segment_data.get('dist_to_poi', 0)
        ]
        
        # Add landuse features (ensure consistent order)
        landuse_classes = [
            'park', 'retail', 'cemetery', 'industrial', 'commercial', 'forest',
            'recreation_ground', 'scrub', 'residential', 'farmland', 'grass',
            'military', 'meadow', 'farmyard', 'orchard', 'nature_reserve',
            'allotments', 'heath'
        ]
        
        landuse_features = segment_data.get('landuse_features', {})
        for landuse_class in landuse_classes:
            features.append(landuse_features.get(f'landuse_{landuse_class}', 0))
        
        return np.array(features).reshape(1, -1)
    
    def predict_single_segment(self, segment_data):
        """
        Predict safety for a single road segment
        
        Args:
            segment_data: dict with segment features
            
        Returns:
            dict with predictions:
                - pred_safe: 0 (unsafe) or 1 (safe)
                - pred_prob_safe: probability of being safe
                - pred_prob_unsafe: probability of being unsafe
        """
        # Extract features
        features = self.extract_features_from_segment(segment_data)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict
        pred_safe = self.model.predict(features_scaled)[0]
        pred_proba = self.model.predict_proba(features_scaled)[0]
        
        return {
            'pred_safe': int(pred_safe),
            'pred_prob_safe': float(pred_proba[1]),
            'pred_prob_unsafe': float(pred_proba[0])
        }
    
    def predict_multiple_segments(self, segments_data):
        """
        Predict safety for multiple road segments
        
        Args:
            segments_data: list of dicts, each with segment features
            
        Returns:
            list of dicts with predictions
        """
        predictions = []
        for segment in segments_data:
            pred = self.predict_single_segment(segment)
            pred['HubName'] = segment.get('HubName')
            predictions.append(pred)
        
        return predictions

def score_route_safety(route_segments, segment_predictions):
    """
    Score overall route safety based on segment predictions
    
    Args:
        route_segments: list of HubNames representing route
        segment_predictions: dict mapping HubName to prediction results
        
    Returns:
        dict with route safety metrics:
            - route_safe: 1 if all segments safe, 0 if any unsafe
            - route_score: average safety probability
            - unsafe_segments: list of unsafe segment IDs
            - safe_segments: list of safe segment IDs
    """
    safe_segments = []
    unsafe_segments = []
    safety_probs = []
    
    for segment_id in route_segments:
        if segment_id in segment_predictions:
            pred = segment_predictions[segment_id]
            safety_probs.append(pred['pred_prob_safe'])
            
            if pred['pred_safe'] == 1:
                safe_segments.append(segment_id)
            else:
                unsafe_segments.append(segment_id)
    
    route_safe = 1 if len(unsafe_segments) == 0 else 0
    route_score = np.mean(safety_probs) if safety_probs else 0.0
    
    return {
        'route_safe': route_safe,
        'route_score': float(route_score),
        'unsafe_segments': unsafe_segments,
        'safe_segments': safe_segments,
        'total_segments': len(route_segments),
        'unsafe_count': len(unsafe_segments),
        'safe_count': len(safe_segments)
    }

def load_segment_predictions(predictions_file="segments_safe_min.csv"):
    """
    Load pre-computed segment predictions for fast lookup
    
    Args:
        predictions_file: path to CSV with predictions
        
    Returns:
        dict mapping HubName to prediction results
    """
    df = pd.read_csv(predictions_file)
    predictions = {}
    
    for _, row in df.iterrows():
        predictions[str(row['HubName'])] = {
            'pred_safe': int(row['pred_safe']),
            'pred_prob_safe': float(row['pred_prob_safe']),
            'pred_prob_unsafe': 1.0 - float(row['pred_prob_safe'])
        }
    
    return predictions

def find_safe_alternative_routes(start_point, end_point, road_network, segment_predictions, max_alternatives=3):
    """
    Find safe alternative routes between two points
    
    Args:
        start_point: (lat, lon) or HubName
        end_point: (lat, lon) or HubName
        road_network: road network data
        segment_predictions: dict with segment safety predictions
        max_alternatives: maximum number of alternative routes to return
        
    Returns:
        list of route alternatives sorted by safety score
    """
    # This is a simplified version - in practice you'd use a routing library
    # like OSRM, GraphHopper, or NetworkX
    
    # Placeholder implementation
    alternatives = []
    
    # Example: find routes and score them
    # route1 = find_shortest_path(start_point, end_point, road_network)
    # route2 = find_alternative_path(start_point, end_point, road_network)
    # etc.
    
    # Score each route
    for route_segments in alternatives:
        route_score = score_route_safety(route_segments, segment_predictions)
        alternatives.append({
            'route_segments': route_segments,
            'route_score': route_score
        })
    
    # Sort by safety score (highest first)
    alternatives.sort(key=lambda x: x['route_score']['route_score'], reverse=True)
    
    return alternatives[:max_alternatives]

# Example usage
if __name__ == "__main__":
    # Initialize inference engine
    inference = FloodRiskInference()
    
    # Example: predict safety for a new segment
    sample_segment = {
        'HubName': '12345',
        'dist_to_river': 150.0,
        'elevation': 25.0,
        'rainfall_mm_3h': 50.0,
        'hazard_status': 1,
        'dist_to_poi': 200.0,
        'landuse_features': {
            'landuse_residential': 1,
            'landuse_commercial': 0,
            'landuse_park': 0
        }
    }
    
    # Predict safety
    prediction = inference.predict_single_segment(sample_segment)
    print("Segment prediction:", prediction)
    
    # Load existing predictions for route scoring
    segment_predictions = load_segment_predictions()
    
    # Example route scoring
    sample_route = ['12345', '67890', '11111']
    route_score = score_route_safety(sample_route, segment_predictions)
    print("Route safety score:", route_score)
