from geopy.distance import geodesic
from typing import List, Tuple
import pandas as pd

def calculate_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate distance between two points in meters using geodesic distance.
    
    Args:
        point1: Tuple of (latitude, longitude)
        point2: Tuple of (latitude, longitude)
    
    Returns:
        Distance in meters
    """
    return geodesic(point1, point2).meters

def check_proximity(route_points: List[Tuple[float, float]], 
                   zone_points: List[Tuple[float, float]], 
                   threshold: float = 5000) -> List[str]:
    """
    Check if any route point is within threshold distance of any animal zone.
    
    Args:
        route_points: List of (latitude, longitude) tuples for route points
        zone_points: List of (latitude, longitude) tuples for animal zones
        threshold: Distance threshold in meters (default: 5000m = 5km)
    
    Returns:
        List of alert messages
    """
    alerts = []
    
    # Load zone details for better alert messages
    try:
        zones_df = pd.read_csv('data/animal_zones.csv')
    except:
        zones_df = None
    
    for i, route_point in enumerate(route_points):
        for j, zone_point in enumerate(zone_points):
            distance = calculate_distance(route_point, zone_point)
            
            if distance <= threshold:
                if zones_df is not None and j < len(zones_df):
                    zone_info = zones_df.iloc[j]
                    alert_msg = (f"Route point near {zone_info['zone_name']} - "
                               f"{distance:.0f}m from {zone_info['animal_type']} habitat. "
                               f"Risk Level: {zone_info['risk_level'].upper()}. "
                               f"Peak Season: {zone_info['peak_season']}")
                else:
                    alert_msg = (f"Route point {i+1} is {distance:.1f}m from animal zone {j+1}. "
                               f"Coordinates: ({route_point[0]:.4f}, {route_point[1]:.4f})")
                alerts.append(alert_msg)
    
    return alerts

def find_nearest_zone(route_point: Tuple[float, float], 
                     zone_points: List[Tuple[float, float]]) -> Tuple[float, int]:
    """
    Find the nearest animal zone to a route point.
    
    Args:
        route_point: (latitude, longitude) of route point
        zone_points: List of (latitude, longitude) for animal zones
    
    Returns:
        Tuple of (min_distance, zone_index)
    """
    min_distance = float('inf')
    nearest_zone_idx = -1
    
    for i, zone_point in enumerate(zone_points):
        distance = calculate_distance(route_point, zone_point)
        if distance < min_distance:
            min_distance = distance
            nearest_zone_idx = i
    
    return min_distance, nearest_zone_idx