#!/usr/bin/env python3
"""
Turn-by-Turn Navigation Directions Generator
Converts route coordinates into human-readable step-by-step directions
"""

import math
from typing import List, Dict, Tuple

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing between two points in degrees (0-360)"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    diff_lon = math.radians(lon2 - lon1)
    
    x = math.sin(diff_lon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(diff_lon)
    
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def bearing_to_direction(bearing: float) -> str:
    """Convert bearing to cardinal direction"""
    directions = ['North', 'Northeast', 'East', 'Southeast', 'South', 'Southwest', 'West', 'Northwest']
    index = round(bearing / 45) % 8
    return directions[index]

def calculate_turn_angle(bearing1: float, bearing2: float) -> float:
    """Calculate turn angle between two bearings (-180 to 180)"""
    angle = bearing2 - bearing1
    if angle > 180:
        angle -= 360
    elif angle < -180:
        angle += 360
    return angle

def get_turn_instruction(turn_angle: float) -> str:
    """Convert turn angle to instruction"""
    abs_angle = abs(turn_angle)
    
    if abs_angle < 20:
        return "Continue straight"
    elif abs_angle < 45:
        return "Bear slight right" if turn_angle > 0 else "Bear slight left"
    elif abs_angle < 135:
        return "Turn right" if turn_angle > 0 else "Turn left"
    else:
        return "Make a sharp right turn" if turn_angle > 0 else "Make a sharp left turn"

def simplify_route_points(coordinates: List[List[float]], min_distance: float = 50) -> List[List[float]]:
    """Simplify route by removing points that are too close together"""
    if len(coordinates) < 2:
        return coordinates
    
    simplified = [coordinates[0]]
    
    for i in range(1, len(coordinates)):
        prev_lat, prev_lon = simplified[-1]
        curr_lat, curr_lon = coordinates[i]
        
        distance = calculate_distance(prev_lat, prev_lon, curr_lat, curr_lon)
        
        # Keep point if it's far enough or if it's the last point
        if distance >= min_distance or i == len(coordinates) - 1:
            simplified.append(coordinates[i])
    
    return simplified

def generate_turn_by_turn_directions(route_coords: List[List[float]], 
                                     segment_names: List[str] = None) -> List[Dict]:
    """
    Generate turn-by-turn directions from route coordinates
    
    Args:
        route_coords: List of [lat, lng] coordinates
        segment_names: Optional list of street names for each segment
        
    Returns:
        List of direction steps with instructions, distance, and bearing
    """
    if len(route_coords) < 2:
        return []
    
    # Simplify route to key turning points
    simplified_coords = simplify_route_points(route_coords, min_distance=30)
    
    directions = []
    total_distance = 0
    
    # Starting instruction
    if len(simplified_coords) >= 2:
        initial_bearing = calculate_bearing(
            simplified_coords[0][0], simplified_coords[0][1],
            simplified_coords[1][0], simplified_coords[1][1]
        )
        initial_direction = bearing_to_direction(initial_bearing)
        
        directions.append({
            'step': 1,
            'instruction': f"Head {initial_direction}",
            'distance': 0,
            'total_distance': 0,
            'coordinates': simplified_coords[0],
            'bearing': initial_bearing,
            'type': 'start'
        })
    
    # Generate turn instructions
    prev_bearing = initial_bearing if len(simplified_coords) >= 2 else 0
    step_num = 2
    
    for i in range(1, len(simplified_coords) - 1):
        curr_lat, curr_lon = simplified_coords[i]
        next_lat, next_lon = simplified_coords[i + 1]
        prev_lat, prev_lon = simplified_coords[i - 1]
        
        # Calculate distance from previous point
        segment_distance = calculate_distance(prev_lat, prev_lon, curr_lat, curr_lon)
        total_distance += segment_distance
        
        # Calculate bearing to next point
        curr_bearing = calculate_bearing(curr_lat, curr_lon, next_lat, next_lon)
        
        # Calculate turn angle
        turn_angle = calculate_turn_angle(prev_bearing, curr_bearing)
        
        # Only add instruction if there's a significant turn
        if abs(turn_angle) > 20:
            instruction = get_turn_instruction(turn_angle)
            
            # Add street name if available
            if segment_names and i < len(segment_names) and segment_names[i]:
                instruction += f" onto {segment_names[i]}"
            
            directions.append({
                'step': step_num,
                'instruction': instruction,
                'distance': round(segment_distance, 1),
                'total_distance': round(total_distance, 1),
                'coordinates': [curr_lat, curr_lon],
                'bearing': curr_bearing,
                'turn_angle': round(turn_angle, 1),
                'type': 'turn'
            })
            step_num += 1
        
        prev_bearing = curr_bearing
    
    # Final destination instruction
    if len(simplified_coords) >= 2:
        final_distance = calculate_distance(
            simplified_coords[-2][0], simplified_coords[-2][1],
            simplified_coords[-1][0], simplified_coords[-1][1]
        )
        total_distance += final_distance
        
        directions.append({
            'step': step_num,
            'instruction': "You have arrived at your destination",
            'distance': round(final_distance, 1),
            'total_distance': round(total_distance, 1),
            'coordinates': simplified_coords[-1],
            'bearing': prev_bearing,
            'type': 'destination'
        })
    
    return directions

def format_distance(meters: float) -> str:
    """Format distance in human-readable form"""
    if meters < 1000:
        return f"{int(meters)}m"
    else:
        return f"{meters/1000:.1f}km"

def get_direction_summary(directions: List[Dict]) -> Dict:
    """Get summary of the route directions"""
    if not directions:
        return {}
    
    total_distance = directions[-1]['total_distance'] if directions else 0
    num_turns = sum(1 for d in directions if d['type'] == 'turn')
    
    return {
        'total_steps': len(directions),
        'total_distance': total_distance,
        'total_distance_formatted': format_distance(total_distance),
        'num_turns': num_turns,
        'estimated_time_minutes': round(total_distance / 1000 / 5 * 60)  # Assuming 5 km/h walking speed
    }
