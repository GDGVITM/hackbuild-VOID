import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import time

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("Plotly not available. Using matplotlib for basic plotting.")

try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Folium not available. Using matplotlib for mapping.")

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    print("⚠️ Geopy not available. Install with: pip install geopy")

def get_last_24_hours_disasters():
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
            'id': row[0],
            'post_id': row[1],
            'title': row[2],
            'content': row[3],
            'author': row[4],
            'post_time': row[5],
            'place': row[7],
            'region': row[8],
            'disaster_type': row[9],
            'urgency_level': row[10],
            'confidence_level': row[11],
            'sources': json.loads(row[12]) if row[12] else [],
            'approved': bool(row[13])
        }
        disasters.append(disaster)
    
    return disasters

def get_disasters_by_region():
    disasters = get_last_24_hours_disasters()
    regions = defaultdict(list)
    
    for disaster in disasters:
        regions[disaster['region']].append(disaster)
    
    return dict(regions)

def get_disasters_by_type():
    disasters = get_last_24_hours_disasters()
    types = defaultdict(list)
    
    for disaster in disasters:
        types[disaster['disaster_type']].append(disaster)
    
    return dict(types)

def get_disasters_by_urgency():
    disasters = get_last_24_hours_disasters()
    urgency = defaultdict(list)
    
    for disaster in disasters:
        urgency_level = disaster['urgency_level']
        urgency_label = {1: 'low', 2: 'moderate', 3: 'high'}.get(urgency_level, 'unknown')
        urgency[urgency_label].append(disaster)
    
    return dict(urgency)

def get_disaster_statistics():
    disasters = get_last_24_hours_disasters()
    
    stats = {
        'total_disasters': len(disasters),
        'by_region': {},
        'by_type': {},
        'by_urgency': {},
        'average_confidence': 0
    }
    
    if disasters:
        region_counts = defaultdict(int)
        type_counts = defaultdict(int)
        urgency_counts = defaultdict(int)
        total_confidence = 0
        
        for disaster in disasters:
            region_counts[disaster['region']] += 1
            type_counts[disaster['disaster_type']] += 1
            urgency_level = disaster['urgency_level']
            urgency_label = {1: 'low', 2: 'moderate', 3: 'high'}.get(urgency_level, 'unknown')
            urgency_counts[urgency_label] += 1
            total_confidence += disaster['confidence_level']
        
        stats['by_region'] = dict(region_counts)
        stats['by_type'] = dict(type_counts)
        stats['by_urgency'] = dict(urgency_counts)
        stats['average_confidence'] = round(total_confidence / len(disasters), 2)
    
    return stats

def get_high_priority_disasters():
    disasters = get_last_24_hours_disasters()
    high_priority = [d for d in disasters if d['urgency_level'] == 3]
    return high_priority

def display_disaster_summary():
    print("\n" + "="*60)
    print("DISASTER MAP - LAST 24 HOURS SUMMARY")
    print("="*60)
    
    disasters = get_last_24_hours_disasters()
    stats = get_disaster_statistics()
    
    print(f"Total Approved Disasters: {stats['total_disasters']}")
    print(f"Average Confidence Level: {stats['average_confidence']}/10")
    
    print("\nBY REGION:")
    for region, count in stats['by_region'].items():
        print(f"  {region.title()}: {count}")
    
    print("\nBY DISASTER TYPE:")
    for disaster_type, count in stats['by_type'].items():
        print(f"  {disaster_type.title()}: {count}")
    
    print("\nBY URGENCY LEVEL:")
    for urgency, count in stats['by_urgency'].items():
        print(f"  {urgency.title()}: {count}")
    
    high_priority = get_high_priority_disasters()
    if high_priority:
        print(f"\nHIGH PRIORITY ALERTS ({len(high_priority)}):")
        for disaster in high_priority:
            print(f"  * {disaster['disaster_type'].title()} in {disaster['place']} (Confidence: {disaster['confidence_level']}/10)")
    else:
        print("\nNo high priority alerts in the last 24 hours")
    
    print("\n" + "="*60)

def export_disasters_json():
    disasters = get_last_24_hours_disasters()
    stats = get_disaster_statistics()
    
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'period': 'last_24_hours',
        'statistics': stats,
        'disasters': disasters
    }
    
    filename = f"disaster_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Disaster data exported to {filename}")
    return filename

def get_disaster_coordinates():
    disasters = get_last_24_hours_disasters()
    coordinates = []
    
    for disaster in disasters:
        coord_data = {
            'place': disaster['place'],
            'region': disaster['region'],
            'disaster_type': disaster['disaster_type'],
            'urgency_level': disaster['urgency_level'],
            'confidence_level': disaster['confidence_level'],
            'title': disaster['title'],
            'post_id': disaster['post_id']
        }
        coordinates.append(coord_data)
    
    return coordinates

def create_interactive_regional_dashboard():
    """Create an interactive dashboard showing disasters by region"""
    if not PLOTLY_AVAILABLE:
        print("❌ Plotly not available. Installing...")
        return create_matplotlib_plots()
    
    disasters = get_last_24_hours_disasters()
    stats = get_disaster_statistics()
    
    if not disasters:
        print("No disaster data available for plotting.")
        return
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Disasters by Region', 'Disasters by Type', 
                       'Urgency Levels', 'Confidence vs Urgency'),
        specs=[[{"type": "bar"}, {"type": "pie"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # 1. Disasters by Region (Bar Chart)
    regions = list(stats['by_region'].keys())
    region_counts = list(stats['by_region'].values())
    
    fig.add_trace(
        go.Bar(x=regions, y=region_counts, name="Regional Distribution",
               marker_color='lightblue', showlegend=False),
        row=1, col=1
    )
    
    # 2. Disasters by Type (Pie Chart)
    disaster_types = list(stats['by_type'].keys())
    type_counts = list(stats['by_type'].values())
    
    fig.add_trace(
        go.Pie(labels=disaster_types, values=type_counts, name="Disaster Types",
               showlegend=False),
        row=1, col=2
    )
    
    # 3. Urgency Levels (Bar Chart)
    urgency_levels = list(stats['by_urgency'].keys())
    urgency_counts = list(stats['by_urgency'].values())
    
    colors = {'low': 'green', 'moderate': 'orange', 'high': 'red'}
    bar_colors = [colors.get(level, 'gray') for level in urgency_levels]
    
    fig.add_trace(
        go.Bar(x=urgency_levels, y=urgency_counts, name="Urgency Distribution",
               marker_color=bar_colors, showlegend=False),
        row=2, col=1
    )
    
    # 4. Confidence vs Urgency Scatter Plot
    confidence_levels = [d['confidence_level'] for d in disasters]
    urgency_nums = [d['urgency_level'] for d in disasters]
    places = [d['place'] for d in disasters]
    
    fig.add_trace(
        go.Scatter(x=confidence_levels, y=urgency_nums, mode='markers',
                  text=places, name="Confidence vs Urgency",
                  marker=dict(size=10, color=urgency_nums, colorscale='RdYlBu_r'),
                  showlegend=False),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        title_text="🌍 Disaster Analytics Dashboard - Last 24 Hours",
        title_x=0.5,
        height=800,
        showlegend=False
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Region", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_xaxes(title_text="Urgency Level", row=2, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    fig.update_xaxes(title_text="Confidence Level", row=2, col=2)
    fig.update_yaxes(title_text="Urgency Level", row=2, col=2)
    
    # Save and show
    filename = f"disaster_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    fig.write_html(filename)
    fig.show()
    
    print(f"✅ Interactive dashboard saved as {filename}")
    return filename

def create_world_disaster_map():
    disasters = get_last_24_hours_disasters()
    
    if not disasters:
        print("No disaster data available for mapping.")
        return
    
    if not FOLIUM_AVAILABLE:
        print("❌ Folium not available. Creating basic matplotlib map...")
        return create_basic_world_map()
    
    world_map = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles='CartoDB positron'
    )
    
    # Initialize geocoder
    if not GEOPY_AVAILABLE:
        print("❌ Geopy not available. Please install with: pip install geopy")
        return
    
    geolocator = Nominatim(user_agent="disaster_map_app")
    
    def get_city_coordinates(place_text):
        """Get coordinates using geopy geocoding service"""
        try:
            # Clean the place text
            place_clean = place_text.strip()
            
            # Try geocoding with a timeout
            location = geolocator.geocode(place_clean, timeout=10)
            
            if location:
                return location.latitude, location.longitude, location.address.split(',')[-1].strip()
            else:
                print(f"⚠️ Could not find coordinates for: {place_text}")
                return None, None, None
                
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"❌ Geocoding error for {place_text}: {e}")
            return None, None, None
        except Exception as e:
            print(f"❌ Unexpected error geocoding {place_text}: {e}")
            return None, None, None
    
    disaster_colors = {
        'earthquake': '#FF6B35',
        'flood': '#1E88E5', 
        'fire': '#E53935',
        'storm': '#8E24AA',
        'other': '#43A047'
    }
    
    for disaster in disasters:
        place_text = disaster['place']
        
        print(f"Geocoding: {place_text}")
        lat, lon, country = get_city_coordinates(place_text)
        
        # Add small delay to respect rate limits
        time.sleep(1)
        
        if lat and lon:
            disaster_type = disaster['disaster_type']
            urgency = disaster['urgency_level']
            confidence = disaster['confidence_level']
            region = disaster['region']
            
            hover_text = f"""
            🔥 {disaster_type.upper()} in {place_text}
            📍 {country}
            ⚠️ Urgency: {urgency}/3
            🎯 Confidence: {confidence}/10
            📅 {disaster['post_time'][:19].replace('T', ' ')}
            👤 by {disaster['author']}
            """
            
            popup_content = f"""
            <div style="width: 350px; font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; margin: -15px;">
                <h2 style="margin: 0 0 15px 0; color: #fff; text-align: center; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                    🌍 {place_text}
                </h2>
                
                <div style="background: rgba(255,255,255,0.9); color: #333; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                        <div style="text-align: center; background: {disaster_colors.get(disaster_type, '#666')}; color: white; padding: 8px; border-radius: 5px;">
                            <strong>{disaster_type.title()}</strong>
                        </div>
                        <div style="text-align: center; background: {'#e74c3c' if urgency == 3 else '#f39c12' if urgency == 2 else '#27ae60'}; color: white; padding: 8px; border-radius: 5px;">
                            Urgency: {urgency}/3
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div style="text-align: center; background: #3498db; color: white; padding: 8px; border-radius: 5px;">
                            Confidence: {confidence}/10
                        </div>
                        <div style="text-align: center; background: #9b59b6; color: white; padding: 8px; border-radius: 5px;">
                            {region.replace('_', ' ').title()}
                        </div>
                    </div>
                </div>
                
                <div style="background: rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; font-size: 13px;">
                    <p style="margin: 5px 0;"><strong>📰 Title:</strong> {disaster['title'][:80]}{'...' if len(disaster['title']) > 80 else ''}</p>
                    <p style="margin: 5px 0;"><strong>👤 Author:</strong> {disaster['author']}</p>
                    <p style="margin: 5px 0;"><strong>📅 Time:</strong> {disaster['post_time'][:19].replace('T', ' ')}</p>
                    <p style="margin: 5px 0;"><strong>🌍 Location:</strong> {country}</p>
                </div>
            </div>
            """
            
            marker_color = disaster_colors.get(disaster_type, '#808080')
            urgency_icons = {1: '⚠️', 2: '🔥', 3: '🚨'}
            
            # GPS-style pin marker
            gps_pin_html = f'''
            <div style="position: relative; width: 30px; height: 40px;">
                <!-- Pin body -->
                <div style="
                    position: absolute;
                    width: 30px;
                    height: 30px;
                    background: {marker_color};
                    border: 3px solid #ffffff;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    top: 0;
                    left: 0;
                "></div>
                <!-- Inner icon -->
                <div style="
                    position: absolute;
                    top: 6px;
                    left: 6px;
                    width: 18px;
                    height: 18px;
                    background: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 10px;
                    z-index: 10;
                    transform: rotate(45deg);
                ">{urgency_icons[urgency]}</div>
                <!-- Pin tip shadow -->
                <div style="
                    position: absolute;
                    bottom: -2px;
                    left: 13px;
                    width: 4px;
                    height: 4px;
                    background: rgba(0,0,0,0.2);
                    border-radius: 50%;
                    transform: scale(1, 0.5);
                "></div>
            </div>
            '''
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=400),
                tooltip=folium.Tooltip(hover_text, style="background-color: rgba(0,0,0,0.8); color: white; font-family: Arial; padding: 10px; border-radius: 8px; font-size: 12px; white-space: pre-line;"),
                icon=folium.DivIcon(
                    html=gps_pin_html,
                    icon_size=(30, 40),
                    icon_anchor=(15, 40)
                )
            ).add_to(world_map)
    
    legend_html = '''
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 200px; 
                background-color: white; border: 3px solid #2E86AB; z-index: 9999; 
                font-size: 14px; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
    <h4 style="margin-top: 0; color: #2E86AB; text-align: center;">Disaster Types</h4>
    '''
    
    for disaster_type, color in disaster_colors.items():
        legend_html += f'''
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div style="width: 18px; height: 18px; background-color: {color}; border: 1px solid black; margin-right: 8px; border-radius: 50%;"></div>
            <span style="font-size: 12px; font-weight: bold;">{disaster_type.title()}</span>
        </div>
        '''
    
    legend_html += '''
    <hr style="margin: 10px 0; border: 1px solid #2E86AB;">
    <div style="text-align: center; font-size: 11px; color: #666;">
        <p style="margin: 2px 0;"><strong>Urgency Levels:</strong></p>
        <p style="margin: 2px 0;">● Low | ●● Moderate | ●●● High</p>
        <p style="margin: 2px 0;">Size = Urgency + Confidence</p>
    </div>
    </div>
    '''
    
    world_map.get_root().html.add_child(folium.Element(legend_html))
    
    filename = "disaster_map.html"
    world_map.save(filename)
    
    print(f"World map updated: {filename}")
    print(f"Marked {len(disasters)} individual disasters")
    
    return filename

def create_basic_world_map():
    """Fallback basic world map using matplotlib"""
    disasters = get_last_24_hours_disasters()
    
    if not disasters:
        print("No disaster data available for mapping.")
        return
    
    # Basic world coordinates
    region_coords = {
        'North_America': {'lat': 45.0, 'lon': -100.0},
        'Asia': {'lat': 30.0, 'lon': 100.0},
        'Europe': {'lat': 50.0, 'lon': 10.0},
        'South_America': {'lat': -15.0, 'lon': -60.0},
        'Africa': {'lat': 0.0, 'lon': 20.0},
        'Oceania': {'lat': -25.0, 'lon': 140.0}
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Simple world outline
    world_x = [-180, 180, 180, -180, -180]
    world_y = [-90, -90, 90, 90, -90]
    ax.plot(world_x, world_y, 'k-', linewidth=2)
    
    # Add continent rectangles
    continents = {
        'North America': [[-140, -60], [20, 70]],
        'South America': [[-80, -40], [-50, 10]], 
        'Europe': [[-10, 40], [40, 70]],
        'Africa': [[-20, 50], [-30, 35]],
        'Asia': [[40, 180], [10, 70]],
        'Oceania': [[110, 180], [-50, -10]]
    }
    
    for continent, [[x1, x2], [y1, y2]] in continents.items():
        ax.add_patch(plt.Rectangle((x1, y1), x2-x1, y2-y1,
                                 fill=False, edgecolor='gray', linewidth=1))
        ax.text((x1+x2)/2, (y1+y2)/2, continent,
               ha='center', va='center', fontsize=10, alpha=0.7)
    
    # Plot disasters
    colors = {'fire': 'red', 'flood': 'blue', 'earthquake': 'orange', 
             'storm': 'purple', 'other': 'green'}
    
    regional_data = defaultdict(list)
    for disaster in disasters:
        regional_data[disaster['region']].append(disaster)
    
    for region, disaster_list in regional_data.items():
        if region in region_coords:
            coord = region_coords[region]
            count = len(disaster_list)
            
            # Get most common disaster type
            types = [d['disaster_type'] for d in disaster_list]
            most_common = max(set(types), key=types.count)
            color = colors.get(most_common.lower(), 'black')
            
            # Plot marker
            size = 100 + (count * 50)
            ax.scatter(coord['lon'], coord['lat'], c=color, s=size, 
                      alpha=0.7, edgecolors='black', linewidth=2)
            
            # Add count label
            ax.annotate(f"{count}", (coord['lon'], coord['lat']),
                       xytext=(0, 0), textcoords='offset points',
                       ha='center', va='center', fontsize=12, fontweight='bold',
                       color='white')
    
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.set_title('World Disaster Map - Last 24 Hours\n(Size = Number of Disasters, Color = Most Common Type)', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add legend
    legend_elements = []
    for disaster_type, color in colors.items():
        legend_elements.append(plt.scatter([], [], c=color, s=100, 
                                         label=disaster_type.title(), alpha=0.7))
    
    ax.legend(handles=legend_elements, title="Disaster Types", 
             loc='lower left', bbox_to_anchor=(0.02, 0.02))
    
    plt.tight_layout()
    
    # Save
    filename = f"basic_world_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Basic world map saved as {filename}")
    return filename

def create_matplotlib_plots():
    """Create basic plots using matplotlib if plotly is not available"""
    disasters = get_last_24_hours_disasters()
    stats = get_disaster_statistics()
    
    if not disasters:
        print("No disaster data available for plotting.")
        return
    
    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('🌍 Disaster Analytics Dashboard - Last 24 Hours', fontsize=16)
    
    # 1. Disasters by Region
    regions = list(stats['by_region'].keys())
    region_counts = list(stats['by_region'].values())
    ax1.bar(regions, region_counts, color='lightblue')
    ax1.set_title('Disasters by Region')
    ax1.set_xlabel('Region')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Disasters by Type
    disaster_types = list(stats['by_type'].keys())
    type_counts = list(stats['by_type'].values())
    ax2.pie(type_counts, labels=disaster_types, autopct='%1.1f%%')
    ax2.set_title('Disasters by Type')
    
    # 3. Urgency Levels
    urgency_levels = list(stats['by_urgency'].keys())
    urgency_counts = list(stats['by_urgency'].values())
    colors = {'low': 'green', 'moderate': 'orange', 'high': 'red'}
    bar_colors = [colors.get(level, 'gray') for level in urgency_levels]
    ax3.bar(urgency_levels, urgency_counts, color=bar_colors)
    ax3.set_title('Urgency Levels')
    ax3.set_xlabel('Urgency Level')
    ax3.set_ylabel('Count')
    
    # 4. Confidence vs Urgency
    confidence_levels = [d['confidence_level'] for d in disasters]
    urgency_nums = [d['urgency_level'] for d in disasters]
    ax4.scatter(confidence_levels, urgency_nums, alpha=0.7, s=100)
    ax4.set_title('Confidence vs Urgency')
    ax4.set_xlabel('Confidence Level')
    ax4.set_ylabel('Urgency Level')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot
    filename = f"disaster_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"✅ Static plots saved as {filename}")
    return filename

def create_regional_analysis_report():
    """Create a detailed regional analysis with statistics"""
    print("\n" + "="*80)
    print("📊 DETAILED REGIONAL DISASTER ANALYSIS")
    print("="*80)
    
    disasters_by_region = get_disasters_by_region()
    
    for region, disasters in disasters_by_region.items():
        print(f"\n🌍 {region.upper().replace('_', ' ')}:")
        print(f"   Total Disasters: {len(disasters)}")
        
        # Group by disaster type in this region
        types_in_region = defaultdict(int)
        urgency_in_region = defaultdict(int)
        confidence_sum = 0
        
        for disaster in disasters:
            types_in_region[disaster['disaster_type']] += 1
            urgency_level = disaster['urgency_level']
            urgency_label = {1: 'low', 2: 'moderate', 3: 'high'}.get(urgency_level, 'unknown')
            urgency_in_region[urgency_label] += 1
            confidence_sum += disaster['confidence_level']
        
        avg_confidence = confidence_sum / len(disasters) if disasters else 0
        
        print(f"   Average Confidence: {avg_confidence:.1f}/10")
        print(f"   Disaster Types: {dict(types_in_region)}")
        print(f"   Urgency Distribution: {dict(urgency_in_region)}")
        
        # Show recent disasters in this region
        recent_disasters = sorted(disasters, key=lambda x: x['post_time'], reverse=True)[:3]
        print(f"   Recent Disasters:")
        for i, disaster in enumerate(recent_disasters, 1):
            print(f"     {i}. {disaster['disaster_type']} in {disaster['place']} "
                  f"(Urgency: {disaster['urgency_level']}/3)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    print("Starting Disaster Map Generation...")
    
    # Display summary first
    display_disaster_summary()
    
    # Generate the interactive map
    filename = create_world_disaster_map()
    
    if filename:
        print(f"Interactive map saved as: {filename}")
        print(f"Map generated successfully!")
        
        # Try to open in browser (optional)
        try:
            import webbrowser
            import os
            file_path = os.path.abspath(filename)
            print(f"File path: {file_path}")
            # Don't auto-open browser when called from API
            # webbrowser.open(f'file:///{file_path}')
        except Exception as e:
            print(f"Could not open browser: {e}")
    else:
        print("Failed to generate map")
        exit(1)
