import sqlite3
import json
from datetime import datetime, timedelta
import time

try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Folium not available. Install with: pip install folium")

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("Geopy not available. Install with: pip install geopy")

# Pre-cached coordinates for demo data locations (matching mockData.ts exactly)
DEMO_COORDINATES = {
    'Andheri East, Mumbai': (19.1197, 72.8697),
    'Marina Beach, Chennai': (13.0827, 80.2707),
    'Karol Bagh, New Delhi': (28.6519, 77.1909),
    'Electronic City, Bangalore': (12.8456, 77.6603),
    'Pune City, Maharashtra': (18.5204, 73.8567),
    'Howrah Bridge, Kolkata': (22.5726, 88.3639),
    'Hussain Sagar, Hyderabad': (17.4239, 78.4738),
    'Wayanad, Kerala': (11.6854, 76.1320),
    'Ankleshwar, Gujarat': (21.6270, 73.0151),
    'Jodhpur, Rajasthan': (26.2389, 73.0243)
}

# Fast demo data (exactly matching React mockData structure)
DEMO_DISASTERS = [
    {
        'id': 'demo_1',
        'title': 'Mumbai Flooding Emergency',
        'place': 'Andheri East, Mumbai',
        'disaster_type': 'flood',
        'urgency_level': 3,
        'confidence_level': 9,
        'content': 'URGENT: Heavy flooding in Andheri East! Water level reached knee-deep on main road. Traffic completely stopped.',
        'author': '@mumbai_citizen',
        'post_time': '2025-08-23T02:30:00Z',
        'coordinates': DEMO_COORDINATES['Andheri East, Mumbai']
    },
    {
        'id': 'demo_2',
        'title': 'Chennai Cyclone Alert',
        'place': 'Marina Beach, Chennai',
        'disaster_type': 'storm',
        'urgency_level': 3,
        'confidence_level': 9,
        'content': 'Very severe cyclonic storm approaching Chennai coast. Winds already reaching 80 kmph in coastal areas.',
        'author': '@chennai_alert',
        'post_time': '2025-08-23T01:45:00Z',
        'coordinates': DEMO_COORDINATES['Marina Beach, Chennai']
    },
    {
        'id': 'demo_3',
        'title': 'Delhi Market Fire',
        'place': 'Karol Bagh, New Delhi',
        'disaster_type': 'fire',
        'urgency_level': 3,
        'confidence_level': 8,
        'content': 'Massive fire broke out in Karol Bagh market! Thick black smoke visible from kilometers away.',
        'author': '@delhi_smoke',
        'post_time': '2025-08-23T01:15:00Z',
        'coordinates': DEMO_COORDINATES['Karol Bagh, New Delhi']
    },
    {
        'id': 'demo_4',
        'title': 'Bangalore Landslide Warning',
        'place': 'Electronic City, Bangalore',
        'disaster_type': 'landslide',
        'urgency_level': 2,
        'confidence_level': 8,
        'content': 'Heavy rains causing soil erosion near Electronic City. Multiple roads blocked, houses at risk.',
        'author': '@bengaluru_resident',
        'post_time': '2025-08-23T00:50:00Z',
        'coordinates': DEMO_COORDINATES['Electronic City, Bangalore']
    },
    {
        'id': 'demo_5',
        'title': 'Pune Earthquake Alert',
        'place': 'Pune City, Maharashtra',
        'disaster_type': 'earthquake',
        'urgency_level': 2,
        'confidence_level': 7,
        'content': 'Major earthquake felt in Pune! Buildings swaying, magnitude around 5.2. Aftershocks expected.',
        'author': '@pune_emergency',
        'post_time': '2025-08-23T00:20:00Z',
        'coordinates': DEMO_COORDINATES['Pune City, Maharashtra']
    },
    {
        'id': 'demo_6',
        'title': 'Kolkata Bridge Collapse',
        'place': 'Howrah Bridge, Kolkata',
        'disaster_type': 'other',
        'urgency_level': 3,
        'confidence_level': 8,
        'content': 'Bridge collapse on Howrah! People trapped underneath, rescue operations underway.',
        'author': '@kolkata_witness',
        'post_time': '2025-08-22T23:45:00Z',
        'coordinates': DEMO_COORDINATES['Howrah Bridge, Kolkata']
    },
    {
        'id': 'demo_7',
        'title': 'Hyderabad Flash Floods',
        'place': 'Hussain Sagar, Hyderabad',
        'disaster_type': 'flood',
        'urgency_level': 3,
        'confidence_level': 8,
        'content': 'Sudden water surge in Hussain Sagar area due to dam overflow. Low-lying areas getting submerged rapidly.',
        'author': '@hyderabad_floods',
        'post_time': '2025-08-22T23:20:00Z',
        'coordinates': DEMO_COORDINATES['Hussain Sagar, Hyderabad']
    },
    {
        'id': 'demo_8',
        'title': 'Kerala Landslides',
        'place': 'Wayanad, Kerala',
        'disaster_type': 'landslide',
        'urgency_level': 3,
        'confidence_level': 9,
        'content': 'Devastating landslides in Wayanad! Villages cut off completely, rescue helicopters deployed.',
        'author': '@kerala_floods',
        'post_time': '2025-08-22T22:55:00Z',
        'coordinates': DEMO_COORDINATES['Wayanad, Kerala']
    },
    {
        'id': 'demo_9',
        'title': 'Gujarat Chemical Leak',
        'place': 'Ankleshwar, Gujarat',
        'disaster_type': 'other',
        'urgency_level': 3,
        'confidence_level': 8,
        'content': 'Chemical plant explosion in GIDC Ankleshwar! Toxic gas leak, evacuation radius of 5km declared.',
        'author': '@gujarat_emergency',
        'post_time': '2025-08-22T22:30:00Z',
        'coordinates': DEMO_COORDINATES['Ankleshwar, Gujarat']
    },
    {
        'id': 'demo_10',
        'title': 'Rajasthan Heat Wave',
        'place': 'Jodhpur, Rajasthan',
        'disaster_type': 'other',
        'urgency_level': 2,
        'confidence_level': 7,
        'content': 'Extreme heat wave: Temperature crossed 48°C in Jodhpur! Multiple heat stroke cases reported.',
        'author': '@rajasthan_heat',
        'post_time': '2025-08-22T22:00:00Z',
        'coordinates': DEMO_COORDINATES['Jodhpur, Rajasthan']
    }
]

def get_database_disasters():
    """Get disasters from database quickly"""
    try:
        conn = sqlite3.connect('disaster_analysis.db')
        cursor = conn.cursor()
        
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE post_time >= ? AND approved = 1
            ORDER BY post_time DESC
        ''', (twenty_four_hours_ago,))
        
        results = cursor.fetchall()
        conn.close()
        
        disasters = []
        for row in results:
            disaster = {
                'id': f'db_{row[0]}',
                'title': row[2],
                'place': row[7],
                'disaster_type': row[9],
                'urgency_level': row[10],
                'confidence_level': row[11],
                'content': row[3],
                'author': row[4],
                'post_time': row[5],
                'coordinates': None  # Will geocode if needed
            }
            disasters.append(disaster)
        
        return disasters
    except Exception as e:
        print(f"Database error: {e}")
        return []

def get_cached_coordinates(place):
    """Get coordinates with caching for speed"""
    if place in DEMO_COORDINATES:
        return DEMO_COORDINATES[place]
    
    # For database places, use basic geocoding cache
    geocoding_cache = {
        'Drake Passage': (-58.5, -62.0),
        'Calistoga, Napa County, USA': (38.5797, -122.5808),
        'Dharali, Uttarkashi, India': (31.0189, 78.4501),
        'Beijing, China': (39.9042, 116.4074),
        'Vikhroli, Mumbai, India': (19.1073, 72.9250)
    }
    
    return geocoding_cache.get(place, (20.5937, 78.9629))  # Default to India center

def create_fast_disaster_map():
    """Create disaster map quickly with combined data"""
    if not FOLIUM_AVAILABLE:
        print("Folium not available")
        return None
    
    print("Generating fast map with combined data...")
    
    # Get both database and demo disasters
    db_disasters = get_database_disasters()
    all_disasters = db_disasters + DEMO_DISASTERS
    
    print(f"Total disasters to map: {len(all_disasters)} ({len(db_disasters)} from DB, {len(DEMO_DISASTERS)} demo)")
    
    # Create map centered on India (where most demo data is)
    world_map = folium.Map(
        location=[20.5937, 78.9629],  # India center
        zoom_start=5,
        tiles='CartoDB positron'
    )
    
    disaster_colors = {
        'earthquake': '#FF6B35',
        'flood': '#1E88E5', 
        'fire': '#E53935',
        'storm': '#8E24AA',
        'landslide': '#FF9800',
        'other': '#43A047'
    }
    
    # Add markers for all disasters
    for disaster in all_disasters:
        place_text = disaster['place']
        
        # Get coordinates (fast lookup)
        if disaster['coordinates']:
            lat, lon = disaster['coordinates']
        else:
            lat, lon = get_cached_coordinates(place_text)
        
        if lat and lon:
            disaster_type = disaster['disaster_type']
            urgency = disaster['urgency_level']
            confidence = disaster['confidence_level']
            
            # Create popup content
            popup_content = f"""
            <div style="width: 320px; font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: -15px;">
                <h3 style="margin: 0 0 15px 0; color: #fff; text-align: center;">
                    {place_text}
                </h3>
                
                <div style="background: rgba(255,255,255,0.9); color: #333; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                        <div style="text-align: center; background: {disaster_colors.get(disaster_type, '#666')}; color: white; padding: 8px; border-radius: 5px;">
                            <strong>{disaster_type.title()}</strong>
                        </div>
                        <div style="text-align: center; background: {'#e74c3c' if urgency == 3 else '#f39c12' if urgency == 2 else '#27ae60'}; color: white; padding: 8px; border-radius: 5px;">
                            Urgency: {urgency}/3
                        </div>
                    </div>
                    
                    <div style="text-align: center; background: #3498db; color: white; padding: 8px; border-radius: 5px; margin-bottom: 10px;">
                        Confidence: {confidence}/10
                    </div>
                </div>
                
                <div style="background: rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; font-size: 13px;">
                    <p style="margin: 5px 0;"><strong>Title:</strong> {disaster['title'][:60]}{'...' if len(disaster['title']) > 60 else ''}</p>
                    <p style="margin: 5px 0;"><strong>Author:</strong> {disaster['author']}</p>
                    <p style="margin: 5px 0;"><strong>Type:</strong> {'Demo Data' if disaster['id'].startswith('demo_') else 'Database'}</p>
                </div>
            </div>
            """
            
            marker_color = disaster_colors.get(disaster_type, '#808080')
            urgency_icons = {1: '⚠️', 2: '🔥', 3: '🚨'}
            
            # Create marker
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=400),
                tooltip=f"{disaster_type.title()} in {place_text} (Urgency: {urgency}/3)",
                icon=folium.Icon(
                    color='red' if urgency == 3 else 'orange' if urgency == 2 else 'green',
                    icon='exclamation-sign' if urgency == 3 else 'fire' if urgency == 2 else 'info-sign',
                    prefix='glyphicon'
                )
            ).add_to(world_map)
    
    # Add simple legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 180px; 
                background-color: white; border: 2px solid #2E86AB; z-index: 9999; 
                font-size: 12px; padding: 10px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
    <h4 style="margin-top: 0; color: #2E86AB; text-align: center;">Disaster Map</h4>
    <div><span style="color: red;">●</span> High Priority (3/3)</div>
    <div><span style="color: orange;">●</span> Moderate (2/3)</div>
    <div><span style="color: green;">●</span> Low Priority (1/3)</div>
    <hr style="margin: 8px 0;">
    <div style="font-size: 10px; text-align: center;">
        <strong>{} Total Disasters</strong><br>
        {} Database + {} Demo
    </div>
    </div>
    '''.format(len(all_disasters), len(db_disasters), len(DEMO_DISASTERS))
    
    world_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    filename = "disaster_map.html"
    world_map.save(filename)
    
    print(f"Fast map saved: {filename}")
    print(f"Total markers: {len(all_disasters)}")
    
    return filename

if __name__ == "__main__":
    print("Starting Fast Disaster Map Generation...")
    
    start_time = time.time()
    filename = create_fast_disaster_map()
    end_time = time.time()
    
    if filename:
        print(f"Map generated successfully in {end_time - start_time:.2f} seconds!")
        print(f"File: {filename}")
    else:
        print("Failed to generate map")
        exit(1)
