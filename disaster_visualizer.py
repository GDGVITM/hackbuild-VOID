"""
Enhanced Disaster Visualization System v2.3
Comprehensive HTML-based visualization tools for disaster data analysis
Now uses disaster_analysis.db format with HTML dashboards and Folium maps
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import seaborn as sns
from disaster_tracker import DisasterTracker
import folium
from folium import plugins
import sqlite3
import json
import os
from typing import Dict, List, Optional

class EnhancedDisasterVisualizer:
    def __init__(self, db_path: str = "disaster_analysis.db"):
        self.db_path = db_path
        self.init_database_if_needed()
        
        # Set up matplotlib style
        plt.style.use('default')
        sns.set_palette("husl")
        
        # Color mapping for disaster types
        self.disaster_colors = {
            'earthquake': '#FF6B6B',
            'flood': '#4ECDC4',
            'fire': '#FF8C42',
            'hurricane': '#A8E6CF',
            'tornado': '#FFD93D',
            'landslide': '#6C5B7B',
            'tsunami': '#88D8B0',
            'drought': '#FFAAA5',
            'cyclone': '#FF6B9D',
            'storm': '#95E1D3',
            'volcanic': '#F38BA8',
            'unknown': '#B8B8B8'
        }
        
        # Region colors
        self.region_colors = {
            'asia': '#FF6B6B',
            'europe': '#4ECDC4',
            'north_america': '#45B7D1',
            'south_america': '#96CEB4',
            'africa': '#FFEAA7',
            'oceania': '#DDA0DD',
            'antarctica': '#B8B8B8',
            'unknown': '#95A5A6'
        }

    def init_database_if_needed(self):
        """Initialize database if it doesn't exist"""
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disaster_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT UNIQUE,
                    title TEXT,
                    content TEXT,
                    author TEXT,
                    post_time TEXT,
                    place TEXT,
                    region TEXT,
                    disaster_type TEXT,
                    urgency_level INTEGER,
                    confidence_level INTEGER,
                    sources TEXT,
                    approved BOOLEAN,
                    latitude REAL,
                    longitude REAL,
                    severity_level TEXT,
                    affected_radius_km REAL,
                    source_platform TEXT,
                    hashtags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()

    def get_disaster_data(self, limit: int = 1000) -> List[Dict]:
        """Get disaster data from database with proper NULL value handling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE approved = 1 
            ORDER BY post_time DESC 
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            data = dict(zip(columns, row))
            
            # Handle NULL values with defaults
            data['latitude'] = data.get('latitude') or 0.0
            data['longitude'] = data.get('longitude') or 0.0
            data['severity_level'] = data.get('severity_level') or 'low'
            data['affected_radius_km'] = data.get('affected_radius_km') or 5.0
            data['source_platform'] = data.get('source_platform') or 'unknown'
            data['hashtags'] = data.get('hashtags') or ''
            data['region'] = data.get('region') or 'unknown'
            data['disaster_type'] = data.get('disaster_type') or 'unknown'
            data['place'] = data.get('place') or 'Unknown Location'
            data['urgency_level'] = data.get('urgency_level') or 1
            data['confidence_level'] = data.get('confidence_level') or 50
            data['author'] = data.get('author') or 'anonymous'
            data['title'] = data.get('title') or 'Untitled Alert'
            data['content'] = data.get('content') or 'No description available'
            
            # Parse post_time to timestamp if it's a string
            if isinstance(data['post_time'], str):
                try:
                    dt = datetime.fromisoformat(data['post_time'].replace('Z', '+00:00'))
                    data['utc_timestamp'] = dt.timestamp()
                except:
                    data['utc_timestamp'] = datetime.now().timestamp()
            elif not data.get('post_time'):
                # Handle NULL post_time
                data['post_time'] = datetime.now().isoformat()
                data['utc_timestamp'] = datetime.now().timestamp()
                
            results.append(data)
        
        conn.close()
        return results

    def create_comprehensive_html_dashboard(self, save_path: str = "disaster_dashboard.html"):
        """Create comprehensive HTML dashboard with all visualizations"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for dashboard")
            return None
        
        df = pd.DataFrame(disasters)
        
        # Calculate statistics
        total_disasters = len(disasters)
        disaster_types = df['disaster_type'].value_counts().to_dict()
        regions = df['region'].value_counts().to_dict()
        avg_confidence = df['confidence_level'].mean()
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Disaster Analysis Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    padding: 30px;
                    background: #f8f9fa;
                }}
                .stat-card {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    text-align: center;
                    transition: transform 0.3s ease;
                }}
                .stat-card:hover {{
                    transform: translateY(-5px);
                }}
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #ff6b6b;
                    margin-bottom: 10px;
                }}
                .stat-label {{
                    color: #666;
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .charts-container {{
                    padding: 30px;
                }}
                .chart-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 30px;
                    margin-bottom: 30px;
                }}
                .chart-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }}
                .chart-title {{
                    font-size: 1.2em;
                    font-weight: bold;
                    margin-bottom: 20px;
                    color: #333;
                }}
                .data-table {{
                    width: 100%;
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    margin-top: 30px;
                }}
                .data-table table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .data-table th {{
                    background: #ff6b6b;
                    color: white;
                    padding: 15px;
                    text-align: left;
                    font-weight: 600;
                }}
                .data-table td {{
                    padding: 12px 15px;
                    border-bottom: 1px solid #eee;
                }}
                .data-table tr:hover {{
                    background: #f8f9fa;
                }}
                .disaster-type {{
                    padding: 5px 10px;
                    border-radius: 15px;
                    color: white;
                    font-size: 0.8em;
                    font-weight: bold;
                }}
                .urgency-level {{
                    padding: 3px 8px;
                    border-radius: 10px;
                    color: white;
                    font-size: 0.7em;
                }}
                .urgency-1 {{ background: #28a745; }}
                .urgency-2 {{ background: #ffc107; color: #333; }}
                .urgency-3 {{ background: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Disaster Analysis Dashboard</h1>
                    <p>Real-time disaster monitoring and analysis system</p>
                    <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{total_disasters:,}</div>
                        <div class="stat-label">Total Disasters</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(disaster_types)}</div>
                        <div class="stat-label">Disaster Types</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(regions)}</div>
                        <div class="stat-label">Regions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{avg_confidence:.1f}%</div>
                        <div class="stat-label">Avg Confidence</div>
                    </div>
                </div>
                
                <div class="charts-container">
                    <div class="chart-grid">
                        <div class="chart-card">
                            <div class="chart-title">📊 Disasters by Type</div>
                            <canvas id="disasterTypeChart"></canvas>
                        </div>
                        <div class="chart-card">
                            <div class="chart-title">🌍 Disasters by Region</div>
                            <canvas id="regionChart"></canvas>
                        </div>
                        <div class="chart-card">
                            <div class="chart-title">📈 Monthly Trend</div>
                            <canvas id="trendChart"></canvas>
                        </div>
                        <div class="chart-card">
                            <div class="chart-title">⚡ Urgency Levels</div>
                            <canvas id="urgencyChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="data-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Type</th>
                                    <th>Location</th>
                                    <th>Urgency</th>
                                    <th>Confidence</th>
                                    <th>Author</th>
                                </tr>
                            </thead>
                            <tbody>
                                {self._generate_table_rows(disasters[:50])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <script>
                {self._generate_chart_scripts(disaster_types, regions, df)}
            </script>
        </body>
        </html>
        """
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Comprehensive HTML dashboard saved to {save_path}")
        return save_path

    def _generate_table_rows(self, disasters: List[Dict]) -> str:
        """Generate HTML table rows for disaster data"""
        rows = []
        for disaster in disasters:
            date_str = disaster.get('post_time', '')[:10] if disaster.get('post_time') else 'Unknown'
            disaster_type = disaster.get('disaster_type', 'unknown')
            place = disaster.get('place', 'Unknown')[:30]
            urgency = disaster.get('urgency_level', 1)
            confidence = disaster.get('confidence_level', 0)
            author = disaster.get('author', 'Unknown')[:20]
            
            # Color for disaster type
            color = self.disaster_colors.get(disaster_type.lower(), '#B8B8B8')
            
            row = f"""
            <tr>
                <td>{date_str}</td>
                <td><span class="disaster-type" style="background-color: {color}">{disaster_type.upper()}</span></td>
                <td title="{place}">{place}</td>
                <td><span class="urgency-level urgency-{urgency}">Level {urgency}</span></td>
                <td>{confidence}%</td>
                <td>{author}</td>
            </tr>
            """
            rows.append(row)
        
        return ''.join(rows)

    def _generate_chart_scripts(self, disaster_types: Dict, regions: Dict, df: pd.DataFrame) -> str:
        """Generate JavaScript for charts"""
        
        # Prepare monthly trend data
        df['post_time'] = pd.to_datetime(df['post_time'])
        monthly_counts = df.groupby(df['post_time'].dt.to_period('M')).size()
        months = [str(period) for period in monthly_counts.index[-12:]]  # Last 12 months
        counts = monthly_counts.values[-12:].tolist()
        
        # Urgency level distribution
        urgency_counts = df['urgency_level'].value_counts().sort_index()
        
        return f"""
        // Disaster Types Chart
        const ctx1 = document.getElementById('disasterTypeChart').getContext('2d');
        new Chart(ctx1, {{
            type: 'doughnut',
            data: {{
                labels: {list(disaster_types.keys())},
                datasets: [{{
                    data: {list(disaster_types.values())},
                    backgroundColor: [
                        '#FF6B6B', '#4ECDC4', '#FF8C42', '#A8E6CF', '#FFD93D', 
                        '#6C5B7B', '#88D8B0', '#FFAAA5', '#FF6B9D', '#95E1D3'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Regions Chart
        const ctx2 = document.getElementById('regionChart').getContext('2d');
        new Chart(ctx2, {{
            type: 'bar',
            data: {{
                labels: {list(regions.keys())},
                datasets: [{{
                    label: 'Count',
                    data: {list(regions.values())},
                    backgroundColor: '#4ECDC4'
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Monthly Trend Chart
        const ctx3 = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx3, {{
            type: 'line',
            data: {{
                labels: {months},
                datasets: [{{
                    label: 'Disasters',
                    data: {counts},
                    borderColor: '#FF6B6B',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Urgency Chart
        const ctx4 = document.getElementById('urgencyChart').getContext('2d');
        new Chart(ctx4, {{
            type: 'pie',
            data: {{
                labels: ['Level 1', 'Level 2', 'Level 3'],
                datasets: [{{
                    data: [{urgency_counts.get(1, 0)}, {urgency_counts.get(2, 0)}, {urgency_counts.get(3, 0)}],
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        """
    
    def create_enhanced_interactive_map(self, save_path: str = "enhanced_disaster_map.html"):
        """Create enhanced interactive map with disaster data from disaster_analysis.db"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for map")
            return None
        
        # Filter disasters with coordinates
        disasters_with_coords = [d for d in disasters if d.get('latitude') and d.get('longitude')]
        
        if not disasters_with_coords:
            print("No disasters with coordinates found for map")
            return None
        
        # Create base map centered on world view
        world_map = folium.Map(
            location=[20, 0],  # Center on equator
            zoom_start=2,
            tiles='OpenStreetMap'
        )
        
        # Add alternative tile layers
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Terrain',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        # Create marker cluster for better performance
        marker_cluster = plugins.MarkerCluster().add_to(world_map)
        
        # Add disaster markers
        for disaster in disasters_with_coords:
            disaster_type = disaster.get('disaster_type', 'unknown').lower()
            color = self.disaster_colors.get(disaster_type, '#B8B8B8')
            
            # Convert timestamp to readable date
            post_time = disaster.get('post_time', '')
            try:
                if isinstance(post_time, str):
                    disaster_date = datetime.fromisoformat(post_time.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    disaster_date = 'Unknown'
            except:
                disaster_date = 'Unknown'
            
            # Create enhanced popup content
            popup_content = f"""
            <div style="font-family: Arial; width: 350px; padding: 10px;">
                <h3 style="color: {color}; margin-bottom: 15px; border-bottom: 2px solid {color}; padding-bottom: 5px;">
                    🚨 {disaster_type.upper()} ALERT
                </h3>
                <div style="margin-bottom: 10px;">
                    <strong>📍 Location:</strong> {disaster.get('place', 'Unknown')}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>🌍 Region:</strong> {disaster.get('region', 'Unknown').title()}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>📅 Date:</strong> {disaster_date}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>🎯 Confidence:</strong> {disaster.get('confidence_level', 0)}%
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>⚡ Urgency:</strong> Level {disaster.get('urgency_level', 1)} of 3
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>👤 Author:</strong> {disaster.get('author', 'Unknown')}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>📱 Platform:</strong> {disaster.get('source_platform', 'Unknown')}
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>📄 Title:</strong> {disaster.get('title', 'No title')[:50]}...
                </div>
                <div style="margin-bottom: 10px;">
                    <strong>💬 Content:</strong> {disaster.get('content', 'No content')[:100]}...
                </div>
            </div>
            """
            
            # Create marker with appropriate icon
            urgency = disaster.get('urgency_level', 1)
            icon_color = 'red' if urgency == 3 else 'orange' if urgency == 2 else 'green'
            
            folium.Marker(
                location=[disaster['latitude'], disaster['longitude']],
                popup=folium.Popup(popup_content, max_width=400),
                tooltip=f"{disaster_type.title()} in {disaster.get('place', 'Unknown')}",
                icon=folium.Icon(color=icon_color, icon='exclamation-sign')
            ).add_to(marker_cluster)
        
        # Add statistics legend
        df = pd.DataFrame(disasters_with_coords)
        disaster_counts = df['disaster_type'].value_counts()
        region_counts = df['region'].value_counts()
        
        legend_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 300px; height: auto; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 15px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
        <h4 style="margin-top: 0; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 10px;">
            📊 Enhanced Disaster Statistics
        </h4>
        
        <div style="margin-bottom: 15px;">
            <strong>Total Disasters:</strong> {len(disasters_with_coords):,}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Top Disaster Types:</strong><br>
            {self._format_counts_for_legend(disaster_counts.head(5))}
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Regions:</strong><br>
            {self._format_counts_for_legend(region_counts.head(5))}
        </div>
        
        <div style="margin-bottom: 15px; font-size: 12px; color: #666;">
            <strong>Legend:</strong><br>
            🔴 High Urgency (Level 3)<br>
            🟠 Medium Urgency (Level 2)<br>
            🟢 Low Urgency (Level 1)
        </div>
        
        <div style="font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
            🗺️ Enhanced Map: OpenStreetMap<br>
            📡 Real-time disaster monitoring<br>
            🔄 Last Updated: {datetime.now().strftime('%H:%M:%S')}
        </div>
        </div>
        """
        
        world_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(world_map)
        
        # Add fullscreen plugin
        plugins.Fullscreen(
            position="topright",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True
        ).add_to(world_map)
        
        # Add measure control
        plugins.MeasureControl().add_to(world_map)
        
        # Save the map
        world_map.save(save_path)
        print(f"✅ Enhanced Interactive Map saved to {save_path}")
        print(f"📊 Map contains {len(disasters_with_coords)} disasters from {df['region'].nunique()} regions")
        
        return save_path

    def create_comprehensive_disaster_report(self, save_path: str = "disaster_report.html"):
        """Create comprehensive disaster analysis report as HTML"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for report")
            return None
        
        df = pd.DataFrame(disasters)
        
        # Analysis
        total_disasters = len(disasters)
        avg_confidence = df['confidence_level'].mean()
        most_common_type = df['disaster_type'].mode().iloc[0] if not df['disaster_type'].empty else 'Unknown'
        most_affected_region = df['region'].mode().iloc[0] if not df['region'].empty else 'Unknown'
        
        # Top disaster locations
        top_places = df['place'].value_counts().head(10).to_dict()
        
        # Recent trends
        df['post_time'] = pd.to_datetime(df['post_time'])
        recent_30_days = df[df['post_time'] >= (datetime.now() - pd.Timedelta(days=30))]
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Comprehensive Disaster Analysis Report</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: #333;
                }}
                .report-container {{ 
                    max-width: 1200px; 
                    margin: 20px auto; 
                    background: white; 
                    border-radius: 15px; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
                    color: white; 
                    padding: 40px; 
                    text-align: center; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 2.8em; 
                    font-weight: 300; 
                }}
                .summary {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; 
                    padding: 30px; 
                    background: #f8f9fa; 
                }}
                .summary-card {{ 
                    background: white; 
                    padding: 25px; 
                    border-radius: 10px; 
                    text-align: center; 
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    transition: transform 0.3s ease;
                }}
                .summary-card:hover {{ 
                    transform: translateY(-3px); 
                }}
                .summary-number {{ 
                    font-size: 2.2em; 
                    font-weight: bold; 
                    color: #ff416c; 
                    margin-bottom: 5px; 
                }}
                .section {{ 
                    padding: 30px; 
                    border-bottom: 1px solid #eee; 
                }}
                .section h2 {{ 
                    color: #2c3e50; 
                    border-bottom: 3px solid #ff416c; 
                    padding-bottom: 10px; 
                }}
                .analysis-grid {{ 
                    display: grid; 
                    grid-template-columns: 1fr 1fr; 
                    gap: 30px; 
                    margin-top: 20px; 
                }}
                .top-list {{ 
                    background: #f8f9fa; 
                    padding: 20px; 
                    border-radius: 10px; 
                }}
                .top-list ol {{ 
                    margin: 0; 
                    padding-left: 20px; 
                }}
                .top-list li {{ 
                    margin-bottom: 8px; 
                    padding: 8px; 
                    background: white; 
                    border-radius: 5px; 
                }}
                .disaster-badge {{ 
                    display: inline-block; 
                    padding: 4px 12px; 
                    border-radius: 15px; 
                    color: white; 
                    font-size: 0.8em; 
                    font-weight: bold; 
                    margin-right: 10px; 
                }}
                .recent-activity {{ 
                    background: #e3f2fd; 
                    padding: 20px; 
                    border-radius: 10px; 
                    border-left: 4px solid #2196f3; 
                }}
                .footer {{ 
                    background: #2c3e50; 
                    color: white; 
                    padding: 20px; 
                    text-align: center; 
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <h1>🚨 Disaster Analysis Report</h1>
                    <p>Comprehensive Analysis of Global Disaster Data</p>
                    <p>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <div class="summary-card">
                        <div class="summary-number">{total_disasters:,}</div>
                        <div>Total Disasters Tracked</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{len(df['disaster_type'].unique())}</div>
                        <div>Types of Disasters</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{len(df['region'].unique())}</div>
                        <div>Affected Regions</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-number">{avg_confidence:.1f}%</div>
                        <div>Average Confidence</div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📊 Key Findings</h2>
                    <div class="analysis-grid">
                        <div>
                            <h3>Most Common Disaster Type</h3>
                            <div class="disaster-badge" style="background: {self.disaster_colors.get(most_common_type.lower(), '#666')}">
                                {most_common_type.upper()}
                            </div>
                            <p>Accounts for {(df['disaster_type'] == most_common_type).sum()} incidents 
                            ({(df['disaster_type'] == most_common_type).mean()*100:.1f}% of all disasters)</p>
                        </div>
                        <div>
                            <h3>Most Affected Region</h3>
                            <div class="disaster-badge" style="background: {self.region_colors.get(most_affected_region.lower(), '#666')}">
                                {most_affected_region.upper()}
                            </div>
                            <p>Experienced {(df['region'] == most_affected_region).sum()} disasters 
                            ({(df['region'] == most_affected_region).mean()*100:.1f}% of all incidents)</p>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🏆 Top 10 Most Affected Locations</h2>
                    <div class="top-list">
                        <ol>
                            {self._generate_top_places_list(top_places)}
                        </ol>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📈 Recent Activity (Last 30 Days)</h2>
                    <div class="recent-activity">
                        <h3>🔥 {len(recent_30_days)} New Disasters Detected</h3>
                        <p><strong>Daily Average:</strong> {len(recent_30_days)/30:.1f} incidents per day</p>
                        <p><strong>Most Active Day:</strong> {recent_30_days.groupby(recent_30_days['post_time'].dt.date).size().idxmax() if not recent_30_days.empty else 'N/A'}</p>
                        <p><strong>Peak Activity:</strong> {recent_30_days.groupby(recent_30_days['post_time'].dt.date).size().max() if not recent_30_days.empty else 0} incidents</p>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🎯 Data Quality Metrics</h2>
                    <div class="analysis-grid">
                        <div>
                            <h3>Confidence Distribution</h3>
                            <p>High Confidence (80%+): {len(df[df['confidence_level'] >= 80])}</p>
                            <p>Medium Confidence (50-79%): {len(df[(df['confidence_level'] >= 50) & (df['confidence_level'] < 80)])}</p>
                            <p>Low Confidence (<50%): {len(df[df['confidence_level'] < 50])}</p>
                        </div>
                        <div>
                            <h3>Urgency Distribution</h3>
                            <p>Critical (Level 3): {len(df[df['urgency_level'] == 3])}</p>
                            <p>High (Level 2): {len(df[df['urgency_level'] == 2])}</p>
                            <p>Low (Level 1): {len(df[df['urgency_level'] == 1])}</p>
                        </div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>📡 Enhanced Disaster Alert System | Real-time Global Monitoring</p>
                    <p>Data Source: disaster_analysis.db | Total Records: {total_disasters:,}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Comprehensive disaster report saved to {save_path}")
        return save_path

    def _generate_top_places_list(self, top_places: Dict) -> str:
        """Generate HTML list for top places"""
        items = []
        for place, count in top_places.items():
            items.append(f"<li><strong>{place}</strong> - {count} incidents</li>")
        return ''.join(items)
    
    def create_disaster_frequency_plot(self, save_path: str = "disaster_frequency.png"):
        """Create disaster frequency plots"""
        disasters = self.tracker.get_all_disasters()
        
        if not disasters:
            print("No disaster data found for frequency plot")
            return None
        
        df = pd.DataFrame(disasters)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Disaster types frequency
        disaster_counts = df['disaster_type'].value_counts()
        colors = [self.disaster_colors.get(dt, '#B8B8B8') for dt in disaster_counts.index]
        
        bars1 = ax1.bar(disaster_counts.index, disaster_counts.values, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_title('Disaster Frequency by Type', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Disaster Type')
        ax1.set_ylabel('Number of Incidents')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Region frequency
        region_counts = df['region'].value_counts()
        colors2 = [self.region_colors.get(r, '#B8B8B8') for r in region_counts.index]
        
        bars2 = ax2.bar(region_counts.index, region_counts.values, color=colors2, alpha=0.8, edgecolor='black')
        ax2.set_title('Disaster Frequency by Region', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Region')
        ax2.set_ylabel('Number of Incidents')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Country frequency (top 10)
        country_counts = df['country'].value_counts().head(10)
        bars3 = ax3.barh(country_counts.index, country_counts.values, color='skyblue', alpha=0.8, edgecolor='black')
        ax3.set_title('Top 10 Countries by Disaster Frequency', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Number of Incidents')
        ax3.set_ylabel('Country')
        
        # Add value labels on bars
        for bar in bars3:
            width = bar.get_width()
            ax3.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                    f'{int(width)}', ha='left', va='center')
        
        # Monthly trend
        df['datetime'] = pd.to_datetime(df['utc_timestamp'], unit='s')
        df['month_year'] = df['datetime'].dt.to_period('M')
        monthly_counts = df.groupby('month_year').size()
        
        ax4.plot(monthly_counts.index.astype(str), monthly_counts.values, 
                marker='o', linewidth=2, markersize=6, color='red', alpha=0.8)
        ax4.set_title('Monthly Disaster Trend', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Month-Year')
        ax4.set_ylabel('Number of Incidents')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Frequency plot saved to {save_path}")
        return save_path
    
    def create_interactive_map(self, save_path: str = "disaster_map.html"):
        """Create an interactive map of disasters using Folium and OpenStreetMap"""
        disasters = self.tracker.get_all_disasters()
        
        if not disasters:
            print("No disaster data found for map")
            return None
        
        # Filter disasters with coordinates
        disasters_with_coords = [d for d in disasters if d['latitude'] and d['longitude']]
        
        if not disasters_with_coords:
            print("No disasters with coordinates found for map")
            return None
        
        # Create base map centered on world view
        world_map = folium.Map(
            location=[20, 0],  # Center on equator
            zoom_start=2,
            tiles='OpenStreetMap'
        )
        
        # Add alternative tile layers
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Terrain',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        # Color mapping for disaster types
        disaster_colors = {
            'earthquake': '#FF6B6B',
            'flood': '#4ECDC4',
            'fire': '#FF8C42',
            'hurricane': '#A8E6CF',
            'tornado': '#FFD93D',
            'landslide': '#6C5B7B',
            'tsunami': '#88D8B0',
            'drought': '#FFAAA5',
            'cyclone': '#FF6B9D',
            'storm': '#95E1D3',
            'volcanic': '#F38BA8',
            'unknown': '#B8B8B8'
        }
        
        # Add disaster markers to map
        for disaster in disasters_with_coords:
            disaster_type = disaster['disaster_type'].lower()
            color = disaster_colors.get(disaster_type, '#B8B8B8')
            
            # Convert timestamp to readable date
            disaster_date = datetime.fromtimestamp(disaster['utc_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            
            # Create popup content
            popup_content = f"""
            <div style="font-family: Arial; width: 300px;">
                <h4 style="color: {color}; margin-bottom: 10px;">
                    🚨 {disaster_type.upper()}
                </h4>
                <p><b>📍 Location:</b> {disaster['place']}</p>
                <p><b>🌍 Country:</b> {disaster['country']}</p>
                <p><b>📅 Date:</b> {disaster_date}</p>
                <p><b>📝 Source:</b> {disaster['post_author']}</p>
                <p><b>🔗 Details:</b> <a href="{disaster['post_url']}" target="_blank">View Post</a></p>
                <p><b>📰 Title:</b> {disaster['post_title'][:100]}...</p>
            </div>
            """
            
            # Create marker with custom icon
            marker = folium.CircleMarker(
                location=[disaster['latitude'], disaster['longitude']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=350),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.8,
                tooltip=f"{disaster_type.title()} in {disaster['place']}"
            )
            
            marker.add_to(world_map)
        
        # Add disaster type statistics
        df = pd.DataFrame(disasters_with_coords)
        disaster_counts = df['disaster_type'].value_counts()
        
        # Create legend
        legend_html = """
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 250px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;">
        <p style="font-weight: bold; margin-bottom: 10px;">📊 Disaster Statistics</p>
        """
        
        for disaster_type, count in disaster_counts.head(10).items():
            color = disaster_colors.get(disaster_type.lower(), '#B8B8B8')
            legend_html += f"""
            <p style="margin: 5px 0;">
                <span style="color: {color}; font-weight: bold;">●</span> 
                {disaster_type.title()}: {count}
            </p>
            """
        
        legend_html += f"""
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0;"><b>Total Disasters:</b> {len(disasters_with_coords)}</p>
        <p style="margin: 5px 0;"><b>Countries:</b> {df['country'].nunique()}</p>
        <p style="margin: 5px 0; font-size: 12px;">🗺️ Powered by OpenStreetMap</p>
        </div>
        """
        
        world_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(world_map)
        
        # Add fullscreen button
        plugins.Fullscreen(
            position="topright",
            title="Expand me",
            title_cancel="Exit me",
            force_separate_button=True
        ).add_to(world_map)
        
        # Add measure control
        plugins.MeasureControl().add_to(world_map)
        
        # Add marker cluster for better performance with many markers
        if len(disasters_with_coords) > 100:
            marker_cluster = plugins.MarkerCluster().add_to(world_map)
            
            for disaster in disasters_with_coords:
                disaster_type = disaster['disaster_type'].lower()
                color = disaster_colors.get(disaster_type, '#B8B8B8')
                disaster_date = datetime.fromtimestamp(disaster['utc_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                
                popup_content = f"""
                <div style="font-family: Arial; width: 300px;">
                    <h4 style="color: {color}; margin-bottom: 10px;">🚨 {disaster_type.upper()}</h4>
                    <p><b>📍 Location:</b> {disaster['place']}</p>
                    <p><b>🌍 Country:</b> {disaster['country']}</p>
                    <p><b>📅 Date:</b> {disaster_date}</p>
                    <p><b>📝 Source:</b> {disaster['post_author']}</p>
                    <p><b>🔗 Details:</b> <a href="{disaster['post_url']}" target="_blank">View Post</a></p>
                </div>
                """
                
                folium.Marker(
                    location=[disaster['latitude'], disaster['longitude']],
                    popup=folium.Popup(popup_content, max_width=350),
                    tooltip=f"{disaster_type.title()} in {disaster['place']}",
                    icon=folium.Icon(color='red', icon='exclamation-sign')
                ).add_to(marker_cluster)
        
        # Save the map
        world_map.save(save_path)
        print(f"✅ Interactive OpenStreetMap saved to {save_path}")
        print(f"📊 Map contains {len(disasters_with_coords)} disasters from {df['country'].nunique()} countries")
        
        return save_path
    
    def create_disaster_heatmap(self, save_path: str = "disaster_heatmap.png"):
        """Create a heatmap showing disaster patterns"""
        disasters = self.tracker.get_all_disasters()
        
        if not disasters:
            print("No disaster data found for heatmap")
            return None
        
        df = pd.DataFrame(disasters)
        df['datetime'] = pd.to_datetime(df['utc_timestamp'], unit='s')
        df['month'] = df['datetime'].dt.month_name()
        df['hour'] = df['datetime'].dt.hour
        
        # Create pivot table for heatmap
        heatmap_data = df.pivot_table(
            index='disaster_type', 
            columns='month', 
            values='id', 
            aggfunc='count', 
            fill_value=0
        )
        
        # Reorder months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        heatmap_data = heatmap_data.reindex(columns=[m for m in month_order if m in heatmap_data.columns])
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', 
                   cbar_kws={'label': 'Number of Incidents'})
        plt.title('Disaster Occurrence Heatmap by Type and Month', fontsize=16, fontweight='bold')
        plt.xlabel('Month')
        plt.ylabel('Disaster Type')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Heatmap saved to {save_path}")
        return save_path
    
    def generate_all_visualizations(self, days: int = 30):
        """Generate all visualization files"""
        print("🎨 Generating enhanced disaster visualizations...")
        
        plots_generated = []
        
        try:
            # Enhanced Interactive OpenStreetMap
            map_path = self.create_enhanced_interactive_map()
            if map_path:
                plots_generated.append(map_path)
                print(f"✅ OpenStreetMap HTML generated: {map_path}")
        except Exception as e:
            print(f"❌ Error creating enhanced map: {e}")
        
        try:
            # Comprehensive Disaster Report
            report_path = self.create_comprehensive_disaster_report()
            if report_path:
                plots_generated.append(report_path)
        except Exception as e:
            print(f"❌ Error creating disaster report: {e}")
        
        try:
            # Timeline plot
            timeline_path = self.create_timeline_plot(days)
            if timeline_path:
                plots_generated.append(timeline_path)
        except Exception as e:
            print(f"❌ Error creating timeline plot: {e}")
        
        try:
            # Frequency plot
            freq_path = self.create_disaster_frequency_plot()
            if freq_path:
                plots_generated.append(freq_path)
        except Exception as e:
            print(f"❌ Error creating frequency plot: {e}")
        
        try:
            # Heatmap
            heatmap_path = self.create_disaster_heatmap()
            if heatmap_path:
                plots_generated.append(heatmap_path)
        except Exception as e:
            print(f"❌ Error creating heatmap: {e}")
        
        print(f"\n✅ Generated {len(plots_generated)} visualization(s):")
        for plot in plots_generated:
            print(f"   📊 {plot}")
        
        return plots_generated

    def _format_counts_for_legend(self, counts):
        """Format counts for legend display"""
        formatted = []
        for item, count in counts.items():
            color = self.disaster_colors.get(item.lower(), '#666666')
            formatted.append(f'<span style="color: {color};">●</span> {item.title()}: {count}')
        return '<br>'.join(formatted)

    def create_timeline_plot(self, days: int = 30, save_path: str = "disaster_timeline.png"):
        """Create timeline plot from disaster_analysis.db data"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for timeline plot")
            return None
        
        df = pd.DataFrame(disasters)
        df['post_time'] = pd.to_datetime(df['post_time'])
        
        # Filter recent data
        cutoff_date = datetime.now() - pd.Timedelta(days=days)
        df = df[df['post_time'] >= cutoff_date]
        
        if df.empty:
            print(f"No disaster data found for last {days} days")
            return None
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Timeline by disaster type
        disaster_types = df['disaster_type'].unique()
        for i, disaster_type in enumerate(disaster_types):
            disaster_data = df[df['disaster_type'] == disaster_type]
            color = self.disaster_colors.get(disaster_type.lower(), '#B8B8B8')
            
            ax1.scatter(disaster_data['post_time'], 
                       [i] * len(disaster_data),
                       c=color, 
                       alpha=0.7, 
                       s=100, 
                       label=disaster_type.title(),
                       edgecolors='black',
                       linewidth=0.5)
        
        ax1.set_yticks(range(len(disaster_types)))
        ax1.set_yticklabels([dt.title() for dt in disaster_types])
        ax1.set_xlabel('Date')
        ax1.set_title(f'Disaster Timeline - Last {days} Days', fontsize=16, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # Timeline by region
        regions = df['region'].unique()
        for i, region in enumerate(regions):
            region_data = df[df['region'] == region]
            color = self.region_colors.get(region.lower(), '#B8B8B8')
            
            ax2.scatter(region_data['post_time'], 
                       [i] * len(region_data),
                       c=color, 
                       alpha=0.7, 
                       s=100, 
                       label=region.title(),
                       edgecolors='black',
                       linewidth=0.5)
        
        ax2.set_yticks(range(len(regions)))
        ax2.set_yticklabels([r.title() for r in regions])
        ax2.set_xlabel('Date')
        ax2.set_title(f'Disaster Timeline by Region - Last {days} Days', fontsize=16, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Timeline plot saved to {save_path}")
        return save_path

    def create_disaster_frequency_plot(self, save_path: str = "disaster_frequency.png"):
        """Create disaster frequency plots from disaster_analysis.db"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for frequency plot")
            return None
        
        df = pd.DataFrame(disasters)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Disaster types frequency
        disaster_counts = df['disaster_type'].value_counts()
        colors = [self.disaster_colors.get(dt.lower(), '#B8B8B8') for dt in disaster_counts.index]
        
        bars1 = ax1.bar(disaster_counts.index, disaster_counts.values, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_title('Disaster Frequency by Type', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Disaster Type')
        ax1.set_ylabel('Number of Incidents')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Region frequency
        region_counts = df['region'].value_counts()
        colors2 = [self.region_colors.get(r.lower(), '#B8B8B8') for r in region_counts.index]
        
        bars2 = ax2.bar(region_counts.index, region_counts.values, color=colors2, alpha=0.8, edgecolor='black')
        ax2.set_title('Disaster Frequency by Region', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Region')
        ax2.set_ylabel('Number of Incidents')
        ax2.tick_params(axis='x', rotation=45)
        
        # Urgency level distribution
        urgency_counts = df['urgency_level'].value_counts().sort_index()
        bars3 = ax3.barh(urgency_counts.index.astype(str), urgency_counts.values, 
                        color=['#28a745', '#ffc107', '#dc3545'][:len(urgency_counts)], alpha=0.8, edgecolor='black')
        ax3.set_title('Distribution by Urgency Level', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Number of Incidents')
        ax3.set_ylabel('Urgency Level')
        
        # Monthly trend
        df['post_time'] = pd.to_datetime(df['post_time'])
        df['month_year'] = df['post_time'].dt.to_period('M')
        monthly_counts = df.groupby('month_year').size()
        
        ax4.plot(monthly_counts.index.astype(str), monthly_counts.values, 
                marker='o', linewidth=2, markersize=6, color='red', alpha=0.8)
        ax4.set_title('Monthly Disaster Trend', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Month-Year')
        ax4.set_ylabel('Number of Incidents')
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Frequency plot saved to {save_path}")
        return save_path

    def create_disaster_heatmap(self, save_path: str = "disaster_heatmap.png"):
        """Create heatmap from disaster_analysis.db data"""
        disasters = self.get_disaster_data()
        
        if not disasters:
            print("No disaster data found for heatmap")
            return None
        
        df = pd.DataFrame(disasters)
        df['post_time'] = pd.to_datetime(df['post_time'])
        df['month'] = df['post_time'].dt.month_name()
        
        # Create pivot table for heatmap
        heatmap_data = df.pivot_table(
            index='disaster_type', 
            columns='month', 
            values='id', 
            aggfunc='count', 
            fill_value=0
        )
        
        # Reorder months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        heatmap_data = heatmap_data.reindex(columns=[m for m in month_order if m in heatmap_data.columns])
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, annot=True, fmt='d', cmap='YlOrRd', 
                   cbar_kws={'label': 'Number of Incidents'})
        plt.title('Disaster Occurrence Heatmap by Type and Month', fontsize=16, fontweight='bold')
        plt.xlabel('Month')
        plt.ylabel('Disaster Type')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"✅ Heatmap saved to {save_path}")
        return save_path

if __name__ == "__main__":
    # Test the enhanced visualizer
    print("🚀 Starting Enhanced Disaster Visualization System...")
    
    # Initialize database and create sample data if needed
    from database import create_database, create_sample_data, get_disaster_statistics
    
    try:
        create_database()
        
        # Check if we have data
        stats = get_disaster_statistics()
        if stats['total_disasters'] == 0:
            print("📊 No disaster data found in database.")
            print("   Add disaster data to generate visualizations.")
        else:
            # Initialize visualizer
            visualizer = EnhancedDisasterVisualizer()
            
            # Generate all visualizations
            plots = visualizer.generate_all_visualizations(days=30)
            
            # Print statistics
            disasters = visualizer.get_disaster_data()
            if disasters:
                df = pd.DataFrame(disasters)
                print(f"\n📈 Database Statistics:")
                print(f"   Total disasters tracked: {len(disasters):,}")
                print(f"   Disaster types: {df['disaster_type'].nunique()}")
                print(f"   Regions covered: {df['region'].nunique()}")
                print(f"   Average confidence: {df['confidence_level'].mean():.1f}%")
                print(f"\n🎯 Visualization Files Created:")
                for plot in plots:
                    print(f"   📄 {plot}")
            else:
                print("\n📈 No data found in database")
                print("   Add some disaster data first, then run visualizations.")
    
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        print("\nYou can still use the visualizer by adding data to disaster_analysis.db")