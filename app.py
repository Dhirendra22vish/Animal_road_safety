import streamlit as st
import pandas as pd
import folium
from folium import plugins
import numpy as np
import math
import time
import json
import os
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from utils.sound_alerts import play_audio_alert, get_species_sound_type
import base64
import io
import random
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="AI Animal Road Safety",
    page_icon="favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
# Simulation start ke time par ye add karo
if 'mobile_alerts' not in st.session_state:
    st.session_state.mobile_alerts = []
if 'enable_sms_alerts' not in st.session_state:
    st.session_state.enable_sms_alerts = True
if 'enable_emergency_sms' not in st.session_state:
    st.session_state.enable_emergency_sms = True
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False
if 'simulation_step' not in st.session_state:
    st.session_state.simulation_step = 0
if 'alert_log' not in st.session_state:
    st.session_state.alert_log = []
if 'eco_points' not in st.session_state:
    st.session_state.eco_points = 0
if 'alert_points' not in st.session_state:
    st.session_state.alert_points = []
if 'detected_animals' not in st.session_state:
    st.session_state.detected_animals = []
if 'last_alert_type' not in st.session_state:
    st.session_state.last_alert_type = None
if 'route_type' not in st.session_state:
    st.session_state.route_type = "normal"
if 'custom_route_points' not in st.session_state:
    st.session_state.custom_route_points = []
if 'map_click_points' not in st.session_state:
    st.session_state.map_click_points = []
if 'selected_route_mode' not in st.session_state:
    st.session_state.selected_route_mode = "preset"
if 'mobile_alerts' not in st.session_state:
    st.session_state.mobile_alerts = []
if 'emergency_contacts' not in st.session_state:
    st.session_state.emergency_contacts = [
        {"name": "Forest Department", "number": "+91-9876543210", "type": "official"},
        {"name": "Wildlife Rescue", "number": "+91-9876543211", "type": "rescue"},
        {"name": "Highway Patrol", "number": "+91-9876543212", "type": "patrol"}
    ]
if 'user_phone_number' not in st.session_state:
    st.session_state.user_phone_number = ""

# Import mobile alerts functions with Twilio
try:
    from utils.mobile_alerts import send_mobile_alert, send_emergency_sms, get_mobile_alerts, get_unread_count, sms_system
except ImportError as e:
    st.error(f"Mobile alerts module not found: {e}")
    # Fallback functions if mobile_alerts.py is not available
    def send_mobile_alert(alert_data, alert_type="warning"):
        alert_templates = {
            "warning": {
                "title": "🚨 WILDLIFE WARNING",
                "message": f"Animal crossing zone ahead: {alert_data.get('zone_name', 'Unknown')}. Reduce speed to {alert_data.get('recommended_speed', 30)} km/h. Distance: {alert_data.get('distance', 0)}km.",
                "priority": "medium"
            },
            "critical": {
                "title": "🚨 CRITICAL ALERT",
                "message": f"IMMEDIATE DANGER: {alert_data.get('species', 'wildlife').title()} detected at {alert_data.get('distance', 0)}km! STOP VEHICLE. Location: {alert_data.get('zone_name', 'Unknown')}.",
                "priority": "high"
            },
            "animal_detected": {
                "title": "🦌 ANIMAL DETECTED",
                "message": f"LIVE ANIMAL: {alert_data.get('species', 'wildlife').title()} spotted at {alert_data.get('distance_from_vehicle', 0)}km. Confidence: {alert_data.get('confidence', 0)*100}%. Take immediate precautions.",
                "priority": "high"
            },
            "emergency": {
                "title": "🚑 EMERGENCY ALERT",
                "message": f"WILDLIFE COLLISION RISK: {alert_data.get('species', 'wildlife').title()} in immediate path! EMERGENCY BRAKING REQUIRED.",
                "priority": "critical"
            }
        }
        
        template = alert_templates.get(alert_type, alert_templates["warning"])
        
        mobile_alert = {
            "id": len(st.session_state.mobile_alerts) + 1,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": template["title"],
            "message": template["message"],
            "type": alert_type,
            "priority": template["priority"],
            "species": alert_data.get('species', 'unknown'),
            "location": alert_data.get('zone_name', 'Unknown location'),
            "read": False
        }
        
        st.session_state.mobile_alerts.append(mobile_alert)
        
        # Keep only last 20 alerts
        if len(st.session_state.mobile_alerts) > 20:
            st.session_state.mobile_alerts = st.session_state.mobile_alerts[-20:]
        
        return mobile_alert
    
    def send_emergency_sms(alert_data) -> bool:
        """Send emergency SMS to contacts"""
        emergency_message = f"""
🚨 URGENT: Wildlife Emergency 🚨
Animal: {alert_data.get('species', 'wildlife').title()}
Location: {alert_data.get('zone_name', 'Unknown')}
Distance: {alert_data.get('distance', alert_data.get('distance_from_vehicle', 'Unknown'))}km
Time: {datetime.now().strftime('%H:%M:%S')}
Priority: CRITICAL - Immediate action required!
        """
        
        # Simulate sending to emergency contacts
        for contact in st.session_state.emergency_contacts:
            st.session_state.mobile_alerts.append({
                "id": len(st.session_state.mobile_alerts) + 1,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": f"📞 SMS Sent to {contact['name']}",
                "message": emergency_message,
                "type": "emergency_sms",
                "priority": "critical",
                "read": False
            })
        return True
    
    def get_mobile_alerts():
        return st.session_state.mobile_alerts
    
    def get_unread_count():
        return len([alert for alert in st.session_state.mobile_alerts if not alert.get('read', False)])
    
    # Fallback for sms_system
    class DummySmsSystem:
        def validate_phone_number(self, phone_number):
            # Simple validation for Indian numbers
            cleaned = ''.join(c for c in phone_number if c.isdigit())
            if len(cleaned) == 10:  # 9876543210
                return True
            elif len(cleaned) == 12 and cleaned.startswith('91'):  # 919876543210
                return True
            elif len(cleaned) == 13 and cleaned.startswith('91'):  # +919876543210
                return True
            return False
        
        def send_sms_alert(self, phone_number, alert_data, alert_type):
            print(f"📱 SMS SIMULATION to {phone_number}: {alert_data}")
            return True
        
        @property
        def is_initialized(self):
            return False
    
    sms_system = DummySmsSystem()

def simulate_push_notification(alert_data):
    """Simulate mobile push notification"""
    notification = {
        "id": f"push_{int(time.time())}",
        "timestamp": datetime.now().strftime('%H:%M:%S'),
        "title": "🐘 UP Animal Safety Alert",
        "body": f"{alert_data.get('species', 'wildlife').title()} detected nearby",
        "data": alert_data
    }
    return notification

# Sound Alert Functions
def get_alert_sound(alert_type="general"):
    """Generate base64 encoded alert sounds"""
    if alert_type == "critical":
        sound_html = """
        <audio id="criticalAlert" autoplay>
            <source src="https://cdn.pixabay.com/audio/2021/08/04/audio_12b0c7443c.mp3" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.getElementById('criticalAlert');
            audio.volume = 0.7;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    elif alert_type == "animal_detected":
        sound_html = """
        <audio id="animalAlert" autoplay>
            <source src="https://cdn.pixabay.com/audio/2021/08/04/audio_12b0c7443c.mp3" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.getElementById('animalAlert');
            audio.volume = 0.5;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    else:
        sound_html = """
        <audio id="generalAlert" autoplay>
            <source src="https://cdn.pixabay.com/audio/2021/08/04/audio_12b0c7443c.mp3" type="audio/mpeg">
        </audio>
        <script>
            var audio = document.getElementById('generalAlert');
            audio.volume = 0.3;
            audio.play().catch(function(e) {
                console.log('Audio play failed:', e);
            });
        </script>
        """
    
    return sound_html

def play_alert_sound(alert_type="general"):
    """Play alert sound based on alert type"""
    if st.session_state.last_alert_type != alert_type:
        st.session_state.last_alert_type = alert_type
        sound_html = get_alert_sound(alert_type)
        st.markdown(sound_html, unsafe_allow_html=True)

def play_audio_alert(alert_type="general"):
    """Display audio alert simulation"""
    alert_messages = {
        "general": "🔊 AUDIO ALERT: Animal crossing zone ahead. Reduce speed immediately!",
        "critical": "🚨 CRITICAL ALERT: Animal detected nearby! STOP IMMEDIATELY!",
        "animal_detected": "🚨 ANIMAL DETECTED: Wildlife spotted nearby! Emergency protocols activated!"
    }
    
    play_alert_sound(alert_type)
    
    st.markdown(f"""
    <div style="background: {'#ff4444' if alert_type == 'critical' else '#ff6b6b'}; 
                padding: 15px; 
                border-radius: 10px; 
                margin: 10px 0;
                color: white;
                text-align: center;
                font-weight: bold;">
        {alert_messages.get(alert_type, alert_messages["general"])}
        <br><small>🔔 Audio Alert Active - Sound Playing</small>
    </div>
    """, unsafe_allow_html=True)

# Data Loading Functions
@st.cache_data
def load_animal_zones():
    """Load animal crossing zones from CSV"""
    try:
        df = pd.read_csv('data/animal_zones.csv')
        return df
    except FileNotFoundError:
        # Create UP-specific sample data
        zones_data = {
            'name': [
                'Dudhwa Tiger Corridor',
                'Katarniaghat Elephant Zone', 
                'Kishanpur Deer Crossing',
                'Pilibhit Tiger Area',
                'Sohagi Barwa Sanctuary',
                'Chandrapur Bear Zone',
                'Ranipur Wildlife',
                'Nawabganj Bird Sanctuary',
                'Saman Sanctuary'
            ],
            'lat': [28.5000, 28.2833, 28.4333, 28.7000, 27.3000, 28.1000, 25.2500, 26.6167, 26.7500],
            'lon': [80.7000, 81.0167, 80.2833, 79.9000, 82.2000, 79.8000, 81.1500, 80.6500, 81.2500],
            'radius_km': [5.0, 3.0, 4.0, 2.5, 3.5, 4.5, 2.0, 3.0, 2.5],
            'species': ['tiger', 'elephant', 'deer', 'tiger', 'leopard', 'sloth_bear', 'deer', 'birds', 'nilgai'],
            'notes': [
                'Highway stretch near Dudhwa forest',
                'Seasonal elephant migration route',
                'Dense forest area crossing',
                'Tiger movement corridor', 
                'Leopard territory',
                'Bear habitat near villages',
                'Wildlife sanctuary crossing',
                'Bird migration area',
                'Grassland animal crossing'
            ]
        }
        return pd.DataFrame(zones_data)

@st.cache_data  
def load_incident_data():
    """Load past incident data for heatmap"""
    try:
        df = pd.read_csv('data/incidents.csv')
        return df
    except FileNotFoundError:
        # Create UP-specific incident data
        incidents_data = {
            'lat': [28.5000, 28.2833, 28.4333, 28.7000, 27.3000, 28.1000, 25.2500, 26.6167, 26.7500, 27.5000, 26.8500],
            'lon': [80.7000, 81.0167, 80.2833, 79.9000, 82.2000, 79.8000, 81.1500, 80.6500, 81.2500, 80.5000, 81.0000],
            'species': ['tiger', 'elephant', 'deer', 'tiger', 'leopard', 'sloth_bear', 'deer', 'birds', 'nilgai', 'elephant', 'tiger'],
            'severity': [5, 4, 3, 2, 4, 2, 3, 5, 3, 4, 2],
            'timestamp': [
                '2024-01-15 14:30:00', '2024-02-03 09:15:00', '2024-02-20 18:45:00',
                '2024-03-10 07:20:00', '2024-03-25 16:10:00', '2024-04-05 11:30:00',
                '2024-04-18 20:15:00', '2024-05-02 06:45:00', '2024-05-20 19:30:00',
                '2024-06-08 13:20:00', '2024-06-25 15:40:00'
            ]
        }
        return pd.DataFrame(incidents_data)

# Popular Locations Database for UP
def get_popular_locations():
    """Get dictionary of popular locations in Uttar Pradesh"""
    return {
        "Lucknow": (26.8467, 80.9462),
        "Kanpur": (26.4499, 80.3319),
        "Varanasi": (25.3176, 82.9739),
        "Agra": (27.1767, 78.0081),
        "Prayagraj": (25.4358, 81.8463),
        "Ghaziabad": (28.6692, 77.4538),
        "Meerut": (28.9845, 77.7064),
        "Dudhwa Tiger Reserve": (28.5000, 80.7000),
        "Katarniaghat Sanctuary": (28.2833, 81.0167),
        "Kishanpur Sanctuary": (28.4333, 80.2833),
        "Pilibhit Tiger Reserve": (28.7000, 79.9000),
        "Sohagi Barwa Sanctuary": (27.3000, 82.2000),
        "Chandrapur Area": (28.1000, 79.8000),
        "Ranipur Sanctuary": (25.2500, 81.1500),
        "Nawabganj Bird Sanctuary": (26.6167, 80.6500),
        "Saman Sanctuary": (26.7500, 81.2500),
        "Gorakhpur": (26.7606, 83.3732),
        "Jhansi": (25.4484, 78.5685),
        "Ayodhya": (26.7928, 82.1947),
        "Mathura": (27.4924, 77.6737)
    }

# Utility Functions
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using geopy"""
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

def generate_route_points(start_lat, start_lon, end_lat, end_lon, num_points=100):
    """Generate interpolated route points"""
    lats = np.linspace(start_lat, end_lat, num_points)
    lons = np.linspace(start_lon, end_lon, num_points)
    return list(zip(lats, lons))

def generate_alert_route_points():
    """Generate a route that guarantees multiple animal alerts in UP"""
    alert_route_points = [
        # Start point - Lucknow
        (26.8467, 80.9462),
        
        # Approach Dudhwa Tiger Reserve
        (27.5000, 80.5000),
        (28.0000, 80.6000),
        
        # Pass through Dudhwa Tiger Zone
        (28.5000, 80.7000),
        (28.5500, 80.7500),
        
        # Approach Katarniaghat
        (28.3000, 80.9000),
        (28.2833, 81.0167),
        
        # Pass through Katarniaghat Elephant Zone
        (28.2500, 81.1000),
        
        # Approach Kishanpur
        (28.4000, 80.4000),
        (28.4333, 80.2833),
        
        # End point - Pilibhit
        (28.7000, 79.9000)
    ]
    
    detailed_route = []
    for i in range(len(alert_route_points) - 1):
        start = alert_route_points[i]
        end = alert_route_points[i + 1]
        
        segment_points = list(zip(
            np.linspace(start[0], end[0], 6),
            np.linspace(start[1], end[1], 6)
        ))
        detailed_route.extend(segment_points[:-1])
    
    detailed_route.append(alert_route_points[-1])
    return detailed_route

def generate_custom_route_points(click_points, points_per_segment=10):
    """Generate route points from custom clicked points"""
    if len(click_points) < 2:
        return []
    
    route_points = []
    for i in range(len(click_points) - 1):
        start = click_points[i]
        end = click_points[i + 1]
        
        segment_points = list(zip(
            np.linspace(start[0], end[0], points_per_segment),
            np.linspace(start[1], end[1], points_per_segment)
        ))
        route_points.extend(segment_points)
    
    return route_points

def check_animal_zones(lat, lon, zones_df, threshold_km=5):
    """Check for nearby animal crossing zones"""
    alerts = []
    for idx, zone in zones_df.iterrows():
        distance = calculate_distance(lat, lon, zone['lat'], zone['lon'])
        zone_radius = zone['radius_km']
        
        if distance <= zone_radius:
            risk_level = "CRITICAL"
            alert_distance = distance
        elif distance <= zone_radius + threshold_km:
            risk_level = "HIGH" if distance <= zone_radius + 2 else "MEDIUM"
            alert_distance = distance
        else:
            continue
            
        alerts.append({
            'zone_name': zone['name'],
            'species': zone['species'],
            'distance': round(alert_distance, 2),
            'risk_level': risk_level,
            'notes': zone['notes'],
            'recommended_speed': get_recommended_speed(zone['species'], alert_distance),
            'zone_radius': zone_radius
        })
    
    return sorted(alerts, key=lambda x: x['distance'])

def get_recommended_speed(species, distance):
    """Get recommended speed based on animal type and distance"""
    speed_map = {
        'tiger': 25, 'elephant': 20, 'leopard': 30, 'deer': 40,
        'wild_boar': 35, 'sloth_bear': 30, 'sambar': 40, 'bison': 25, 'nilgai': 35, 'birds': 50
    }
    base_speed = speed_map.get(species, 30)
    
    if distance < 1:
        return max(base_speed - 15, 15)
    elif distance < 3:
        return max(base_speed - 10, 20)
    elif distance < 5:
        return max(base_speed - 5, 25)
    return base_speed

def simulate_animal_detection(current_position, zones_df, detection_radius=2.0):
    """Simulate animal detection near current position"""
    detected_animals = []
    
    for idx, zone in zones_df.iterrows():
        distance = calculate_distance(current_position[0], current_position[1], zone['lat'], zone['lon'])
        
        if distance <= detection_radius:
            detection_chance = max(0.3, 1.0 - (distance / detection_radius)) 
            
            if random.random() < detection_chance:
                lat_offset = random.uniform(-0.01, 0.01)
                lon_offset = random.uniform(-0.01, 0.01)
                
                animal_position = {
                    'lat': zone['lat'] + lat_offset,
                    'lon': zone['lon'] + lon_offset,
                    'species': zone['species'],
                    'zone_name': zone['name'],
                    'detection_time': datetime.now().strftime('%H:%M:%S'),
                    'distance_from_vehicle': distance,
                    'confidence': round(random.uniform(0.85, 0.98), 2)
                }
                detected_animals.append(animal_position)
    
    return detected_animals

def get_species_emoji(species):
    """Get emoji for species"""
    emoji_map = {
        'tiger': '🐅', 'elephant': '🐘', 'leopard': '🐆', 'deer': '🦌',
        'wild_boar': '🐗', 'sloth_bear': '🐻', 'sambar': '🦌', 'bison': '🐃', 
        'nilgai': '🦌', 'birds': '🦅'
    }
    return emoji_map.get(species, '🐾')

def get_detection_color(species):
    """Get color for detected animal markers"""
    color_map = {
        'tiger': '#ff4444',
        'elephant': '#ff6b6b',  
        'leopard': '#ff8c00',
        'deer': '#ffa500',
        'wild_boar': '#ff7f50',
        'sloth_bear': '#dc143c',
        'sambar': '#b22222',
        'bison': '#8b0000',
        'nilgai': '#cd5c5c',
        'birds': '#4682b4'
    }
    return color_map.get(species, '#ff0000')

# Map Creation Functions
def create_map(zones_df, incidents_df, route_points=None, current_position=None, 
               show_heatmap=True, show_zones=True, show_route=True, detected_animals=None, 
               alert_points=None, click_points=None, enable_click=True):
    """Create the main folium map focused on Uttar Pradesh"""
    # Center map on Uttar Pradesh
    center_lat, center_lon = 27.1300, 80.7500
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Add Uttar Pradesh boundary outline
    up_boundary = [
        [30.3753, 77.7456],
        [28.2070, 77.7456],  
        [28.2070, 84.0833],
        [30.3753, 84.0833],
        [30.3753, 77.7456]
    ]
    
    folium.PolyLine(
        up_boundary,
        color='green',
        weight=3,
        opacity=0.5,
        tooltip="Uttar Pradesh Boundary"
    ).add_to(m)
    
    # Add click functionality for custom route planning
    if enable_click:
        m.add_child(folium.LatLngPopup())
    
    # Add custom route points if any
    if click_points and len(click_points) > 0:
        for i, point in enumerate(click_points):
            folium.Marker(
                location=point,
                popup=f"Route Point {i+1}",
                icon=folium.Icon(color='purple', icon='circle', prefix='fa'),
                tooltip=f"Custom Point {i+1}"
            ).add_to(m)
        
        if len(click_points) > 1:
            folium.PolyLine(
                click_points,
                color='purple',
                weight=3,
                opacity=0.7,
                dash_array='5, 10',
                popup='Custom Route Plan'
            ).add_to(m)
    
    # Add animal crossing zones
    if show_zones and zones_df is not None and not zones_df.empty:
        for idx, zone in zones_df.iterrows():
            try:
                folium.Circle(
                    location=[float(zone['lat']), float(zone['lon'])],
                    radius=float(zone['radius_km']) * 1000,
                    popup=folium.Popup(f"""
                        <div style="font-family: Arial; width: 200px;">
                            <h4 style="color: #d32f2f; margin: 0;">{get_species_emoji(zone['species'])} {zone['name']}</h4>
                            <hr style="margin: 5px 0;">
                            <p><b>Species:</b> {zone['species'].title().replace('_', ' ')}</p>
                            <p><b>Radius:</b> {zone['radius_km']} km</p>
                            <p><b>Notes:</b> {zone['notes']}</p>
                        </div>
                    """, max_width=250),
                    color='red',
                    fillColor='red',
                    fillOpacity=0.2,
                    weight=2
                ).add_to(m)
                
                folium.Marker(
                    location=[float(zone['lat']), float(zone['lon'])],
                    popup=f"{get_species_emoji(zone['species'])} {zone['name']}",
                    icon=folium.Icon(color='red', icon='warning-sign'),
                    tooltip=f"⚠️ {zone['species'].title()} Zone"
                ).add_to(m)
            except Exception as e:
                continue
    
    # Add detected animal points
    if detected_animals and len(detected_animals) > 0:
        for animal in detected_animals:
            try:
                folium.Marker(
                    location=[float(animal['lat']), float(animal['lon'])],
                    popup=folium.Popup(f"""
                        <div style="font-family: Arial; width: 250px; text-align: center;">
                            <h3 style="color: #ff0000; margin: 0;">🚨 ANIMAL DETECTED!</h3>
                            <hr style="margin: 8px 0;">
                            <div style="font-size: 2rem; margin: 10px 0;">{get_species_emoji(animal['species'])}</div>
                            <p><b>Species:</b> {animal['species'].title().replace('_', ' ')}</p>
                            <p><b>Zone:</b> {animal['zone_name']}</p>
                            <p><b>Detection Time:</b> {animal['detection_time']}</p>
                            <p><b>Distance from Vehicle:</b> {animal['distance_from_vehicle']:.1f} km</p>
                            <p><b>AI Confidence:</b> {animal['confidence']*100:.0f}%</p>
                            <div style="background: #ffe6e6; padding: 8px; border-radius: 5px; margin-top: 10px;">
                                <strong>⚠️ IMMEDIATE ACTION REQUIRED</strong>
                            </div>
                        </div>
                    """, max_width=300),
                    icon=folium.Icon(color='red', icon='exclamation-triangle'),
                    tooltip=f"🚨 {animal['species'].title()} DETECTED!"
                ).add_to(m)
                
                folium.Circle(
                    location=[float(animal['lat']), float(animal['lon'])],
                    radius=300,
                    color=get_detection_color(animal['species']),
                    fillColor=get_detection_color(animal['species']),
                    fillOpacity=0.4,
                    weight=3,
                    popup=f"🚨 {animal['species'].title()} Detection Zone"
                ).add_to(m)
            except Exception as e:
                continue
    
    # Add alert points trail
    if alert_points and len(alert_points) > 0:
        for point in alert_points:
            try:
                folium.CircleMarker(
                    location=[float(point['lat']), float(point['lon'])],
                    radius=8,
                    popup=f"Previous Alert: {point['species'].title()}",
                    color='darkred',
                    fillColor='red',
                    fillOpacity=0.7,
                    weight=2,
                    tooltip=f"⚠️ {point['species'].title()} alert point"
                ).add_to(m)
            except Exception as e:
                continue
    
    # Add incident heatmap
    if show_heatmap and incidents_df is not None and not incidents_df.empty:
        try:
            heat_data = [[float(row['lat']), float(row['lon']), float(row['severity'])] for idx, row in incidents_df.iterrows()]
            if heat_data:
                heat_layer = plugins.HeatMap(heat_data, radius=20, blur=15, max_zoom=1)
                heat_layer.add_to(m)
        except Exception as e:
            pass
    
    # Add route
    if show_route and route_points and len(route_points) >= 2:
        try:
            folium.PolyLine(
                route_points,
                color='blue',
                weight=4,
                opacity=0.8,
                popup='Planned Route'
            ).add_to(m)
            
            folium.Marker(
                location=route_points[0],
                popup='🏁 Start Point',
                icon=folium.Icon(color='green', icon='play'),
                tooltip='Start'
            ).add_to(m)
            
            folium.Marker(
                location=route_points[-1],
                popup='🏁 End Point',
                icon=folium.Icon(color='darkred', icon='stop'),
                tooltip='Destination'
            ).add_to(m)
        except Exception as e:
            pass
    
    # Add current vehicle position
    if current_position:
        try:
            folium.Marker(
                location=current_position,
                popup='🚗 Current Position',
                icon=folium.Icon(color='blue', icon='car'),
                tooltip='Vehicle Location'
            ).add_to(m)
            
            folium.Circle(
                location=current_position,
                radius=500,
                color='blue',
                fillColor='lightblue',
                fillOpacity=0.3,
                weight=1
            ).add_to(m)
        except Exception as e:
            pass
    
    # Add layer control
    try:
        folium.LayerControl().add_to(m)
    except:
        pass
    
    return m

def display_mobile_alert_preview():
    """Display mobile alert preview in sidebar"""
    st.sidebar.markdown("### 📱 Mobile Alert Preview")
    
    if st.session_state.mobile_alerts:
        latest_alert = st.session_state.mobile_alerts[-1]
        
        # Mobile phone mockup
        st.markdown("""
        <div style="border: 2px solid #333; border-radius: 20px; padding: 10px; background: #000; width: 250px; margin: 0 auto;">
            <div style="background: #111; border-radius: 10px; padding: 15px; color: white;">
                <div style="text-align: center; font-size: 12px; color: #ccc;">UP Animal Safety</div>
                <div style="font-weight: bold; color: #ff4444; margin: 10px 0;">{title}</div>
                <div style="font-size: 12px; color: #ccc;">{message}</div>
                <div style="font-size: 10px; color: #666; margin-top: 10px;">{timestamp}</div>
            </div>
        </div>
        """.format(
            title=latest_alert['title'],
            message=latest_alert['message'],
            timestamp=latest_alert['timestamp']
        ), unsafe_allow_html=True)
        
        # Show SMS status
        if latest_alert.get('sms_sent'):
            st.sidebar.success("📱 SMS: Delivered")
        else:
            st.sidebar.info("📱 SMS: Ready (enable in settings)")
    else:
        st.info("No alerts yet. Start simulation to see mobile alerts.")

def display_mobile_alerts_tab():
    """Display mobile alerts in a dedicated tab"""
    st.markdown("### 📱 Mobile Alert Center")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Alert History")
        if st.session_state.mobile_alerts:
            for alert in reversed(st.session_state.mobile_alerts):
                priority_color = {
                    "critical": "#ff4444",
                    "high": "#ff6b6b", 
                    "medium": "#ffa726"
                }.get(alert.get('priority', 'medium'), "#ffa726")
                
                sms_status = "✅ SMS Sent" if alert.get('sms_sent') else "📱 SMS Ready"
                
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-left: 4px solid {priority_color}; padding: 10px; margin: 5px 0; border-radius: 5px;">
                    <div style="font-weight: bold; color: {priority_color};">{alert['title']}</div>
                    <div style="font-size: 0.7rem; color: #666;">{alert['timestamp']} | {sms_status}</div>
                    <div style="margin-top: 5px; font-size: 0.8rem;">{alert['message']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No mobile alerts yet. Start simulation to see alerts.")
        
        if st.button("🗑️ Clear Alert History"):
            st.session_state.mobile_alerts = []
            st.rerun()
    
    with col2:
        st.markdown("#### Emergency Contacts")
        
        for contact in st.session_state.emergency_contacts:
            st.markdown(f"""
            <div style="border: 1px solid #e0e0e0; padding: 10px; margin: 5px 0; border-radius: 5px;">
                <div style="font-weight: bold;">{contact['name']}</div>
                <div style="font-size: 0.8rem; color: #666;">{contact['number']}</div>
                <div style="font-size: 0.7rem; color: #888; text-transform: uppercase;">{contact['type']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### SMS System Status")
        if sms_system.is_initialized:
            st.success("✅ Twilio SMS: ACTIVE")
            st.info("Real SMS alerts are enabled with Twilio")
        else:
            st.warning("📱 SMS Simulation Mode")
            st.info("Add Twilio credentials for real SMS alerts")
        
        st.markdown("#### Test Mobile Alert")
        test_alert_type = st.selectbox("Alert Type", ["warning", "critical", "animal_detected", "emergency"])
        if st.button("📲 Send Test Alert"):
            test_data = {
                'zone_name': 'Test Zone',
                'species': 'tiger',
                'distance': 1.5,
                'recommended_speed': 25,
                'distance_from_vehicle': 0.8,
                'confidence': 0.95
            }
            send_mobile_alert(test_data, test_alert_type)
            st.success("Test alert sent! Check alert history.")
            
            # Test SMS if phone number is available
            if st.session_state.user_phone_number and sms_system.validate_phone_number(st.session_state.user_phone_number):
                sms_success = sms_system.send_sms_alert(
                    st.session_state.user_phone_number, 
                    test_data, 
                    test_alert_type
                )
                if sms_success:
                    st.success("✅ Test SMS sent successfully!")
                else:
                    st.error("❌ Failed to send test SMS")

# Main Application
def main():
    st.markdown(
        """
        <style>
        .header-container {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 15px;
            text-align: left;
        }
        .header-container img {
            border-radius: 10px;
        }

        /* Mobile view */
        @media (max-width: 768px) {
            .header-container {
                flex-direction: column;
                justify-content: center;
                text-align: center;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 🔥 logo (local file) ko base64 embed karna safe hai
    import base64
    def get_base64_image(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    logo_base64 = get_base64_image("logo.png")

    st.markdown(
        f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_base64}" width="90">
            <div>
                <h1 class="main-header">AI Animal Road Safety System</h1>
                <p class="subtitle">
                    Uttar Pradesh Wildlife Protection • Real-time Collision Prevention • Smart Route Planning
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Load data
    zones_df = load_animal_zones()
    incidents_df = load_incident_data()
    popular_locations = get_popular_locations()
    
    # Sidebar Controls
    with st.sidebar: 
         
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown("# 🚗 Route Planning")
        
        # Sound Settings
        st.markdown("### 🔊 Sound Settings")
        enable_sounds = st.checkbox("Enable Alert Sounds", value=True)
        sound_volume = st.slider("Alert Volume", 0.1, 1.0, 0.7)
        
        # Mobile Alert Settings
        st.markdown("### 📱 Mobile Alerts")
        enable_sms_alerts = st.checkbox("Enable SMS Alerts", value=True)
        enable_push_notifications = st.checkbox("Enable Push Notifications", value=True)
        enable_emergency_sms = st.checkbox("Auto Emergency SMS", value=True)
        
        # SMS Configuration
        st.markdown("### 📱 SMS Configuration")
        user_phone = st.text_input(
            "Your Phone Number for Alerts",
            placeholder="+91 9876543210",
            help="Enter your phone number for SMS alerts",
            value=st.session_state.user_phone_number
        )

        if user_phone:
            st.session_state.user_phone_number = user_phone
            if sms_system.validate_phone_number(user_phone):
                st.success("✅ Valid phone number - Ready for SMS alerts!")
            else:
                st.warning("⚠️ Please check phone number format (e.g., +91 9876543210)")

        # Test SMS functionality
        if st.button("📲 Test SMS Alert"):
            if user_phone and sms_system.validate_phone_number(user_phone):
                test_data = {
                    'species': 'tiger',
                    'zone_name': 'Dudhwa Tiger Reserve',
                    'distance': 1.5,
                    'distance_from_vehicle': 0.8,
                    'confidence': 0.95,
                    'recommended_speed': 25
                }
                success = sms_system.send_sms_alert(user_phone, test_data, "warning")
                if success:
                    st.success("✅ Test SMS sent successfully!")
                else:
                    st.error("❌ Failed to send test SMS")
            else:
                st.error("Please enter a valid phone number first")
        
        # Display mobile alert preview
        display_mobile_alert_preview()
        
        st.markdown("### 🧭 Route Selection Mode")
        route_mode = st.radio("How do you want to plan your route?", 
                             ["📍 Preset Routes", "🗺️ Custom Map Selection", "🔢 Manual Coordinates"])
        
        st.session_state.selected_route_mode = route_mode
        
        st.markdown("### 🛣️ Route Type")
        route_type = st.radio("Choose route type:", 
                             ["Normal Route", "Alert Test Route (Guaranteed Alerts)"],
                             index=0 if st.session_state.route_type == "normal" else 1)
        
        st.session_state.route_type = "normal" if route_type == "Normal Route" else "alert"
        
        if st.session_state.route_type == "alert":
            st.warning("🚨 Alert Test Route Selected - This route will trigger multiple animal alerts!")
        
        if route_mode == "📍 Preset Routes":
            st.markdown("### 🏙️ Select UP Locations")
            
            col1, col2 = st.columns(2)
            with col1:
                start_location = st.selectbox("Start Location", list(popular_locations.keys()), 
                                            index=list(popular_locations.keys()).index("Lucknow"))
                start_lat, start_lon = popular_locations[start_location]
            
            with col2:
                end_location = st.selectbox("End Location", list(popular_locations.keys()), 
                                          index=list(popular_locations.keys()).index("Dudhwa Tiger Reserve"))
                end_lat, end_lon = popular_locations[end_location]
            
            st.markdown("### 🚀 Quick Presets")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Lucknow → Dudhwa"):
                    start_lat, start_lon = popular_locations["Lucknow"]
                    end_lat, end_lon = popular_locations["Dudhwa Tiger Reserve"]
                    st.rerun()
                
                if st.button("Kanpur → Katarniaghat"):
                    start_lat, start_lon = popular_locations["Kanpur"]
                    end_lat, end_lon = popular_locations["Katarniaghat Sanctuary"]
                    st.rerun()
            
            with col2:
                if st.button("Varanasi → Pilibhit"):
                    start_lat, start_lon = popular_locations["Varanasi"]
                    end_lat, end_lon = popular_locations["Pilibhit Tiger Reserve"]
                    st.rerun()
        
        elif route_mode == "🔢 Manual Coordinates":
            st.markdown("### 📍 Enter Coordinates")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Start Point**")
                start_lat = st.number_input("Start Latitude", value=26.8467, format="%.6f")
                start_lon = st.number_input("Start Longitude", value=80.9462, format="%.6f")
            
            with col2:
                st.markdown("**End Point**")
                end_lat = st.number_input("End Latitude", value=28.5000, format="%.6f")
                end_lon = st.number_input("End Longitude", value=80.7000, format="%.6f")
        
        else:
            st.markdown("### 🗺️ Custom Route Planning")
            st.info("👆 Click on the map to set your route points. Click multiple points to create a custom path.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Custom Route"):
                    st.session_state.map_click_points = []
                    st.session_state.custom_route_points = []
                    st.rerun()
            
            with col2:
                if st.button("✅ Confirm Custom Route") and len(st.session_state.map_click_points) >= 2:
                    st.session_state.custom_route_points = generate_custom_route_points(st.session_state.map_click_points)
                    st.success(f"Custom route created with {len(st.session_state.custom_route_points)} points!")
            
            if len(st.session_state.map_click_points) > 0:
                st.markdown(f"**📍 Route Points:** {len(st.session_state.map_click_points)}")
                for i, point in enumerate(st.session_state.map_click_points):
                    st.write(f"Point {i+1}: {point[0]:.4f}, {point[1]:.4f}")
            
            start_lat, start_lon = 26.8467, 80.9462
            end_lat, end_lon = 28.5000, 80.7000
        
        st.markdown("---")
        
        st.markdown("### 🎛️ Map Display")
        show_zones = st.checkbox("🎯 Show Animal Zones", value=True)
        show_heatmap = st.checkbox("🔥 Show Incident Heatmap", value=True)
        show_route = st.checkbox("🛣️ Show Route", value=True)
        show_detections = st.checkbox("🚨 Show Live Animal Detections", value=True)
        show_alert_trail = st.checkbox("📍 Show Alert History Trail", value=True)
        
        st.markdown("### ⚠️ Safety Settings")
        alert_threshold = st.slider("Alert Range (km)", min_value=1, max_value=10, value=3)
        auto_simulation = st.checkbox("🤖 Auto-advance Simulation", value=False)
        
        st.markdown("### 🎮 Simulation")
        
       if st.button("▶️ Start Route Simulation", use_container_width=True):
            st.session_state.simulation_running = True
            st.session_state.simulation_step = 0
            st.session_state.alert_log = []
            st.session_state.alert_points = []
            st.session_state.detected_animals = []
            st.session_state.last_alert_type = None
            st.session_state.mobile_alerts = []
            st.rerun()
        
        if st.button("⏸️ Pause Simulation", width="stretch"):
            st.session_state.simulation_running = False
        
        if st.button("🔄 Reset Simulation", width="stretch"):
            st.session_state.simulation_running = False
            st.session_state.simulation_step = 0
            st.session_state.alert_log = []
            st.session_state.alert_points = []
            st.session_state.detected_animals = []
            st.session_state.last_alert_type = None
            st.session_state.mobile_alerts = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate route points
    try:
        if st.session_state.selected_route_mode == "🗺️ Custom Map Selection" and st.session_state.custom_route_points:
            route_points = st.session_state.custom_route_points
            route_distance = calculate_distance(route_points[0][0], route_points[0][1], 
                                              route_points[-1][0], route_points[-1][1])
            st.info("🗺️ Custom Route Active - You created this route by clicking on the map!")
        
        elif st.session_state.route_type == "alert":
            route_points = generate_alert_route_points()
            route_distance = calculate_distance(route_points[0][0], route_points[0][1], 
                                              route_points[-1][0], route_points[-1][1])
            st.info("🚨 Alert Test Route Active - This route passes through multiple animal zones!")
        else:
            route_points = generate_route_points(start_lat, start_lon, end_lat, end_lon, 120)
            route_distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)
    except Exception as e:
        st.error(f"Route generation error: {e}")
        return
    
    # Main Content Layout
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    col_map, col_spacer, col_alerts = st.columns([2.5, 0.1, 1.2])
    
    with col_map:
        st.markdown("## 🗺️ Uttar Pradesh Route Map")
        
        if st.session_state.selected_route_mode == "🗺️ Custom Map Selection":
            if st.session_state.custom_route_points:
                st.success("🗺️ **Custom Route**: You created this route by clicking on the map!")
            else:
                st.info("🗺️ **Click on the map** to create your custom route. Click at least 2 points.")
        
        elif st.session_state.route_type == "alert":
            st.success("🎯 **Alert Test Route**: This route is designed to demonstrate multiple animal detection scenarios!")
        else:
            route_mode_display = {
                "📍 Preset Routes": "Preset Route",
                "🔢 Manual Coordinates": "Manual Coordinates Route"
            }
            st.info(f"📍 **{route_mode_display.get(st.session_state.selected_route_mode, 'Route')}**: {start_lat:.4f}, {start_lon:.4f} → {end_lat:.4f}, {end_lon:.4f}")
        
        current_position = None
        current_alerts = []
        
        if st.session_state.simulation_running:
            if auto_simulation:
                time.sleep(1)
                if st.session_state.simulation_step < len(route_points) - 1:
                    st.session_state.simulation_step += 2
                    st.rerun()
            
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            
            with sim_col1:
                if st.button("⏭️ Next Step") and st.session_state.simulation_step < len(route_points) - 1:
                    st.session_state.simulation_step += 3
                    st.rerun()
            
            with sim_col2:
                if st.button("⏩ Jump 10"):
                    st.session_state.simulation_step = min(
                        st.session_state.simulation_step + 10, 
                        len(route_points) - 1
                    )
                    st.rerun()
            
            with sim_col3:
                if st.button("🏁 To End"):
                    st.session_state.simulation_step = len(route_points) - 1
                    st.rerun()
            
            progress = st.session_state.simulation_step / max(len(route_points) - 1, 1)
            st.progress(progress, text=f"Journey Progress: {progress*100:.1f}%")
            
            if st.session_state.simulation_step < len(route_points):
                current_position = route_points[st.session_state.simulation_step]
                
                current_alerts = check_animal_zones(
                    current_position[0], current_position[1], 
                    zones_df, alert_threshold
                )
                
                new_detections = simulate_animal_detection(current_position, zones_df, detection_radius=3.0)
                
                for detection in new_detections:
                    is_new_detection = True
                    for existing in st.session_state.detected_animals:
                        if (existing['species'] == detection['species'] and 
                            calculate_distance(existing['lat'], existing['lon'], 
                                             detection['lat'], detection['lon']) < 0.5):
                            is_new_detection = False
                            break
                    
                    if is_new_detection:
                        st.session_state.detected_animals.append(detection)
                        st.session_state.alert_points.append({
                            'lat': detection['lat'],
                            'lon': detection['lon'], 
                            'species': detection['species'],
                            'timestamp': detection['detection_time']
                        })
                
                if current_alerts:
                    for alert in current_alerts:
                        log_entry = f"⚠️ {datetime.now().strftime('%H:%M:%S')} - {alert['risk_level']} ALERT: {alert['species'].title()} zone at {alert['distance']}km"
                        if log_entry not in st.session_state.alert_log:
                            st.session_state.alert_log.append(log_entry)
                            
                            # Send mobile alerts based on alert type
                            if enable_sms_alerts or enable_push_notifications:
                                if alert['risk_level'] == 'CRITICAL':
                                    mobile_alert = send_mobile_alert(alert, "critical")
                                    if enable_emergency_sms:
                                        send_emergency_sms(alert)
                                elif alert['risk_level'] == 'HIGH':
                                    mobile_alert = send_mobile_alert(alert, "warning")
                                else:
                                    mobile_alert = send_mobile_alert(alert, "warning")
                            
                            # Play alert sound if enabled
                            if enable_sounds:
                                if alert['risk_level'] == 'CRITICAL':
                                    play_audio_alert("critical")
                                else:
                                    play_audio_alert("general")
                            
                            if alert['risk_level'] == 'CRITICAL':
                                st.session_state.eco_points += 50
                            elif alert['risk_level'] == 'HIGH':
                                st.session_state.eco_points += 30
                            else:
                                st.session_state.eco_points += 10
                
                if new_detections:
                    for detection in new_detections:
                        detection_log = f"🚨 {detection['detection_time']} - ANIMAL DETECTED: {detection['species'].title()} at {detection['distance_from_vehicle']:.1f}km (Confidence: {detection['confidence']*100:.0f}%)"
                        st.session_state.alert_log.append(detection_log)
                        
                        # Send mobile alert for animal detection
                        if enable_sms_alerts or enable_push_notifications:
                            mobile_alert = send_mobile_alert(detection, "animal_detected")
                        
                        # Play animal detection sound if enabled
                        if enable_sounds:
                            play_audio_alert("animal_detected")
                        
                        st.session_state.eco_points += 75
                else:
                    safe_log = f"✅ {datetime.now().strftime('%H:%M:%S')} - Route segment clear"
                    if len(st.session_state.alert_log) == 0 or not st.session_state.alert_log[-1].startswith("✅"):
                        st.session_state.alert_log.append(safe_log)
        
        try:
            enable_map_clicks = (st.session_state.selected_route_mode == "🗺️ Custom Map Selection")
            
            map_obj = create_map(
                zones_df, incidents_df, 
                route_points if show_route else None, 
                current_position, 
                show_heatmap, show_zones, show_route,
                detected_animals=st.session_state.detected_animals if show_detections else None,
                alert_points=st.session_state.alert_points if show_alert_trail else None,
                click_points=st.session_state.map_click_points,
                enable_click=enable_map_clicks
            )
            
            st.markdown('<div style="border-radius: 15px; overflow: hidden; box-shadow: 0 15px 30px rgba(0,0,0,0.2);">', unsafe_allow_html=True)
            
            if enable_map_clicks:
                map_data = st_folium(map_obj, width=None, height=500, 
                                   returned_objects=["last_clicked"])
                
                if map_data and map_data.get("last_clicked"):
                    clicked_lat = map_data["last_clicked"]["lat"]
                    clicked_lon = map_data["last_clicked"]["lng"]
                    
                    new_point = (clicked_lat, clicked_lon)
                    if new_point not in st.session_state.map_click_points:
                        st.session_state.map_click_points.append(new_point)
                        st.rerun()
            else:
                st_folium(map_obj, width=None, height=500)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Map error: {e}")
    
    with col_alerts:
        st.markdown("## 🚨 Live Alert Dashboard")
        
        if st.session_state.route_type == "alert":
            st.markdown('<div class="warning-box">🚨 ALERT TEST ROUTE ACTIVE<br><small>Multiple animal zones will be encountered</small></div>', 
                      unsafe_allow_html=True)
        elif st.session_state.selected_route_mode == "🗺️ Custom Map Selection":
            st.markdown('<div class="info-box">🗺️ CUSTOM ROUTE MODE<br><small>You designed this route</small></div>', 
                      unsafe_allow_html=True)
        
        if st.session_state.simulation_running and current_alerts:
            st.markdown("### ⚠️ ACTIVE ALERTS")
            
            for alert in current_alerts:
                risk_color = {
                    "CRITICAL": "alert-box",
                    "HIGH": "alert-box", 
                    "MEDIUM": "warning-box"
                }.get(alert['risk_level'], "warning-box")
                
                st.markdown(f"""
                <div class="{risk_color}">
                    <h4>{get_species_emoji(alert['species'])} {alert['zone_name']}</h4>
                    <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                        <span><strong>Species:</strong></span>
                        <span>{alert['species'].title().replace('_', ' ')}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                        <span><strong>Distance:</strong></span>
                        <span>{alert['distance']} km</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                        <span><strong>Risk Level:</strong></span>
                        <span>{alert['risk_level']}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 0.3rem 0;">
                        <span><strong>Max Speed:</strong></span>
                        <span>{alert['recommended_speed']} km/h</span>
                    </div>
                    <hr style="margin: 0.5rem 0; border: 1px solid rgba(255,255,255,0.3);">
                    <p style="margin: 0; font-size: 0.85rem;"><strong>Action:</strong> {alert['notes']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Show alert status
            if enable_sounds:
                st.markdown(f"""
                <div style="background: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 10px 0;">
                    🔊 Alert Sounds: ACTIVE
                </div>
                """, unsafe_allow_html=True)
            
            if enable_sms_alerts:
                st.markdown(f"""
                <div style="background: #2196F3; color: white; padding: 10px; border-radius: 5px; text-align: center; margin: 5px 0;">
                    📱 SMS Alerts: ACTIVE
                </div>
                """, unsafe_allow_html=True)
                
        elif st.session_state.simulation_running:
            st.markdown('<div class="safe-box">✅ All Clear<br><small>No wildlife zones detected in range</small></div>', 
                      unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">📍 Start Simulation<br><small>Click "Start Route Simulation" to begin</small></div>', 
                      unsafe_allow_html=True)
        
        if st.session_state.eco_points > 0:
            st.markdown(f"""
            <div class="eco-points">
                🏆 Eco Points: {st.session_state.eco_points}
                <br><small>Earned for wildlife-safe driving!</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Mobile Alerts Preview
        if st.session_state.mobile_alerts:
            st.markdown("### 📱 Recent Mobile Alerts")
            recent_alerts = st.session_state.mobile_alerts[-3:]  # Show last 3 alerts
            for alert in reversed(recent_alerts):
                priority_color = {
                    "critical": "#ff4444",
                    "high": "#ff6b6b", 
                    "medium": "#ffa726"
                }.get(alert.get('priority', 'medium'), "#ffa726")
                
                st.markdown(f"""
                <div style="border-left: 4px solid {priority_color}; padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 5px;">
                    <div style="font-weight: bold; color: {priority_color};">{alert['title']}</div>
                    <div style="font-size: 0.8rem; color: #666;">{alert['timestamp']}</div>
                    <div style="margin-top: 5px; font-size: 0.9rem;">{alert['message']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 📊 Route Statistics")
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{route_distance:.1f}</div>
            <div class="metric-label">🛣️ Total Distance (km)</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-number">{len(zones_df)}</div>
            <div class="metric-label">🎯 Total Animal Zones</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.simulation_running and current_position:
            nearby_zones = len(current_alerts)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{nearby_zones}</div>
                <div class="metric-label">⚠️ Current Alerts</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.selected_route_mode == "🗺️ Custom Map Selection":
            st.markdown("### 🗺️ Custom Route Info")
            if st.session_state.map_click_points:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-number">{len(st.session_state.map_click_points)}</div>
                    <div class="metric-label">📍 Route Points</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-box">
                <strong>Custom Route Features:</strong><br>
                • Click anywhere on map to add points<br>
                • Create your own unique path<br>
                • Test different wildlife corridors<br>
                • Perfect for research and planning
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.route_type == "alert":
            st.markdown("### 🎯 Expected Alerts on This Route")
            expected_alerts = [
                "🐅 Dudhwa Tiger Corridor",
                "🐘 Katarniaghat Elephant Zone", 
                "🦌 Kishanpur Deer Crossing",
                "🐆 Pilibhit Tiger Area"
            ]
            for alert in expected_alerts:
                st.markdown(f"""
                <div class="species-card">
                    <span style="color: #ff6b6b;">⚠️</span> {alert}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 🦌 Wildlife Species")
        species_counts = zones_df['species'].value_counts()
        
        for species, count in species_counts.items():
            st.markdown(f"""
            <div class="species-card">
                <span style="float: right; font-weight: bold; color: #2E8B57;">{count}</span>
                <span>{get_species_emoji(species)} <strong>{str(species).title().replace('_', ' ')}</strong></span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 📜 Activity Log")
        
        if st.session_state.alert_log:
            for log_entry in st.session_state.alert_log[-5:]:
                log_class = "alert-log" if "ALERT" in log_entry else "safe-log"
                st.markdown(f'<div class="{log_class}">{log_entry}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box"><small>No activity yet - start simulation to see logs</small></div>', 
                      unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mobile Alerts Section
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown("## 📱 Mobile Alert System")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔊 Sound AI", "📱 Mobile Alerts", "🎮 Eco-Gaming", "📊 Analytics"])
    
    with tab1:
        st.markdown("### 🔊 Animal Sound AI Detection")
        
        if st.button("🎵 Test Alert Sounds"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔊 General Alert"):
                    play_audio_alert("general")
            
            with col2:
                if st.button("🚨 Critical Alert"):
                    play_audio_alert("critical")
            
            with col3:
                if st.button("🦌 Animal Detection"):
                    play_audio_alert("animal_detected")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Detected Sounds:**
            - 🐘 Elephant trumpets
            - 🐅 Tiger roars  
            - 🦌 Deer calls
            - 🐻 Bear growls
            """)
        
        with col2:
            st.markdown("""
            **AI Capabilities:**
            - Real-time audio analysis
            - Species identification
            - Distance estimation
            - Threat level assessment
            """)
    
    with tab2:
        display_mobile_alerts_tab()
    
    with tab3:
        st.markdown("### 🎮 Eco-Gaming & Rewards")
        
        leaderboard_data = [
            ("🥇 UP_Wildlife_Protector", 2450, "Tiger Guardian"),
            ("🥈 SafeRoutes_UP", 2100, "Elephant Friend"), 
            ("🥉 GreenCommuter_UP", 1875, "Deer Defender"),
            ("🏅 You", st.session_state.eco_points, "Getting Started" if st.session_state.eco_points < 100 else "Rising Star")
        ]
        
        st.markdown("**🏆 Top Eco-Drivers:**")
        for rank, (name, points, badge) in enumerate(leaderboard_data):
            st.markdown(f"""
            <div class="species-card" style="border-left-color: {'#FFD700' if rank == 0 else '#C0C0C0' if rank == 1 else '#CD7F32' if rank == 2 else '#2E8B57'};">
                <span style="float: right;"><strong>{points}</strong> pts</span>
                <span><strong>{name}</strong> - {badge}</span>
            </div>
            """, unsafe_allow_html=True)
        
        achievements = [
            ("🛡️ UP Route Protector", st.session_state.eco_points >= 100),
            ("🌟 Alert Responder", len(st.session_state.alert_log) >= 5),
            ("🚗 Simulation Expert", st.session_state.simulation_step > 50),
            ("🗺️ Custom Route Creator", st.session_state.selected_route_mode == "🗺️ Custom Map Selection" and len(st.session_state.map_click_points) >= 3)
        ]
        
        st.markdown("**🏅 Your Achievements:**")
        for badge, earned in achievements:
            color = "#2E8B57" if earned else "#cccccc"
            st.markdown(f'<div style="color: {color}; margin: 0.5rem 0;">{badge} {"✅" if earned else "🔒"}</div>', 
                       unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 📊 UP Wildlife Analytics")
        
        st.markdown("**🐾 Uttar Pradesh Wildlife Distribution:**")
        
        species_data = {
            'Species': ['Tiger', 'Elephant', 'Deer', 'Leopard', 'Sloth Bear', 'Birds', 'Nilgai'],
            'Zones': [2, 1, 2, 1, 1, 1, 1],
            'Risk Level': ['Critical', 'High', 'Medium', 'High', 'Medium', 'Low', 'Medium']
        }
        
        species_df = pd.DataFrame(species_data)
        st.dataframe(species_df, width="stretch")
        
        st.markdown("**🏞️ UP Protected Areas:**")
        st.markdown("""
        - Dudhwa Tiger Reserve
        - Katarniaghat Wildlife Sanctuary
        - Kishanpur Wildlife Sanctuary  
        - Pilibhit Tiger Reserve
        - Sohagi Barwa Sanctuary
        - Ranipur Wildlife Sanctuary
        - Nawabganj Bird Sanctuary
        - Saman Sanctuary
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🧭 Uttar Pradesh Route Selection Guide
    
    **📍 Preset Routes**: Quick selection from UP cities and wildlife sanctuaries
    **🗺️ Custom Map Selection**: Click on UP map to create your own route  
    **🔢 Manual Coordinates**: Enter exact coordinates for precision routing
    
    *Protecting Uttar Pradesh's rich wildlife heritage through smart technology!*
    """)
    
    # Add custom CSS for styling
    st.markdown("""
    <style>
    .main-header {
        color: #2E8B57;
        text-align: center;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .alert-box {
        background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #ff4444;
    }
    .warning-box {
        background: linear-gradient(45deg, #ffa726, #ffb74d);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #ff9800;
    }
    .safe-box {
        background: linear-gradient(45deg, #4CAF50, #66BB6A);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        border-left: 5px solid #2E8B57;
    }
    .info-box {
        background: #e3f2fd;
        color: #1976d2;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        border-left: 5px solid #2196f3;
    }
    .eco-points {
        background: linear-gradient(45deg, #FFD700, #FFEC8B);
        color: #8B7500;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        font-weight: bold;
        border: 2px solid #FFD700;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    .metric-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2E8B57;
    }
    .metric-label {
        color: #666;
        font-size: 0.9rem;
    }
    .species-card {
        background: white;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .alert-log {
        background: #ffebee;
        color: #c62828;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
        border-left: 3px solid #f44336;
    }
    .safe-log {
        background: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
        border-left: 3px solid #4caf50;
    }
    .audio-alert {
        background: #fff3e0;
        color: #ef6c00;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        border: 2px solid #ff9800;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    .sms-status {
        background: #e3f2fd;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        text-align: center;
        font-size: 0.8rem;
    }
    .sms-active {
        background: #4CAF50;
        color: white;
    }
    .sms-simulation {
        background: #FF9800;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
