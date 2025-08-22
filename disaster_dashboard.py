"""
Real-Time Disaster Dashboard
Interactive web dashboard for monitoring disaster alerts and analytics
Uses Folium with OpenStreetMap for enhanced map visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Optional
import folium
from streamlit_folium import st_folium
import altair as alt
from advanced_disaster_intelligence import AdvancedDisasterIntelligence, DisasterAlert
import threading
import asyncio

# Page configuration
st.set_page_config(
    page_title="🌍 Disaster Alert Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .alert-emergency {
        background-color: #ff4444;
        color: white;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    .alert-critical {
        background-color: #ff8800;
        color: white;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    .alert-warning {
        background-color: #ffaa00;
        color: white;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    .alert-info {
        background-color: #0088cc;
        color: white;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    .stAlert > div {
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

class DisasterDashboard:
    """Real-time disaster monitoring dashboard"""
    
    def __init__(self):
        """Initialize dashboard with AI system"""
        try:
            self.ai_system = AdvancedDisasterIntelligence()
            self.last_refresh = time.time()
            
            # Initialize session state
            if 'auto_refresh' not in st.session_state:
                st.session_state.auto_refresh = True
            if 'refresh_interval' not in st.session_state:
                st.session_state.refresh_interval = 30  # seconds
            if 'alert_threshold' not in st.session_state:
                st.session_state.alert_threshold = 0.5
            
        except Exception as e:
            st.error(f"Failed to initialize AI system: {e}")
            self.ai_system = None
    
    def load_alerts_data(self, hours: int = 24, min_confidence: float = 0.5) -> pd.DataFrame:
        """Load alerts data as DataFrame"""
        if not self.ai_system:
            return pd.DataFrame()
        
        try:
            alerts = self.ai_system.get_active_alerts(hours=hours, min_confidence=min_confidence)
            
            if not alerts:
                return pd.DataFrame()
            
            # Convert alerts to DataFrame
            data = []
            for alert in alerts:
                data.append({
                    'alert_id': alert.alert_id,
                    'timestamp': alert.timestamp,
                    'datetime': datetime.fromtimestamp(alert.timestamp),
                    'platform': alert.platform,
                    'disaster_type': alert.disaster_type,
                    'country': alert.country,
                    'state_province': alert.state_province,
                    'city': alert.city,
                    'formatted_address': alert.formatted_address,
                    'confidence_score': alert.confidence_score,
                    'severity_score': alert.severity_score,
                    'urgency_level': alert.urgency_level,
                    'alert_level': alert.alert_level,
                    'language': alert.language,
                    'sentiment_score': alert.sentiment_score,
                    'is_genuine': alert.is_genuine,
                    'is_rumor': alert.is_rumor,
                    'misinformation_risk': alert.misinformation_risk,
                    'viral_potential': alert.viral_potential,
                    'verification_status': alert.verification_status,
                    'content': alert.content[:100] + "..." if len(alert.content) > 100 else alert.content,
                    'author': alert.author,
                    'coordinates': alert.coordinates
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            st.error(f"Error loading alerts data: {e}")
            return pd.DataFrame()
    
    def create_alert_level_color(self, level: str) -> str:
        """Get color for alert level"""
        colors = {
            'emergency': '#ff4444',
            'alert': '#ff8800',
            'warning': '#ffaa00',
            'info': '#0088cc'
        }
        return colors.get(level, '#888888')
    
    def render_metrics_overview(self, df: pd.DataFrame):
        """Render key metrics overview"""
        st.subheader("📊 Key Metrics")
        
        if df.empty:
            st.info("No alerts data available")
            return
        
        # Calculate metrics
        total_alerts = len(df)
        high_confidence = len(df[df['confidence_score'] >= 0.7])
        emergency_alerts = len(df[df['alert_level'] == 'emergency'])
        verified_genuine = len(df[df['is_genuine'] == True])
        
        # Display in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Active Alerts",
                value=total_alerts,
                delta=f"+{len(df[df['timestamp'] >= time.time() - 3600])}" if total_alerts > 0 else None
            )
        
        with col2:
            st.metric(
                label="High Confidence",
                value=high_confidence,
                delta=f"{(high_confidence/total_alerts*100):.1f}%" if total_alerts > 0 else "0%"
            )
        
        with col3:
            st.metric(
                label="Emergency Level",
                value=emergency_alerts,
                delta="🚨" if emergency_alerts > 0 else None
            )
        
        with col4:
            st.metric(
                label="Verified Genuine",
                value=verified_genuine,
                delta=f"{(verified_genuine/total_alerts*100):.1f}%" if total_alerts > 0 else "0%"
            )
    
    def render_live_alerts_feed(self, df: pd.DataFrame):
        """Render live alerts feed"""
        st.subheader("🚨 Live Alerts Feed")
        
        if df.empty:
            st.info("No active alerts to display")
            return
        
        # Sort by timestamp and confidence
        df_sorted = df.sort_values(['timestamp', 'confidence_score'], ascending=[False, False])
        
        # Show latest 10 alerts
        for idx, alert in df_sorted.head(10).iterrows():
            alert_color = self.create_alert_level_color(alert['alert_level'])
            
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="background-color: {alert_color}; color: white; padding: 0.5rem; 
                                border-radius: 0.25rem; text-align: center; font-weight: bold;">
                        {alert['alert_level'].upper()}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    **{alert['disaster_type'].title()}** in **{alert['formatted_address']}**
                    
                    *{alert['content']}*
                    
                    **Source:** {alert['platform']} • **Author:** {alert['author']} • 
                    **Time:** {alert['datetime'].strftime('%H:%M:%S')} • 
                    **Confidence:** {alert['confidence_score']:.2f}
                    """)
                
                with col3:
                    if alert['is_genuine']:
                        st.success("✅ Genuine")
                    elif alert['is_rumor']:
                        st.warning("⚠️ Rumor")
                    else:
                        st.info("❓ Unverified")
                
                st.divider()
    
    def render_world_map(self, df: pd.DataFrame):
        """Render interactive world map with alerts using Folium and OpenStreetMap"""
        st.subheader("🌍 Global Disaster Map")
        
        if df.empty:
            st.info("No alerts with location data available")
            return
        
        # Filter alerts with coordinates
        df_with_coords = df[df['coordinates'].notna()].copy()
        
        if df_with_coords.empty:
            st.info("No alerts with coordinate data available")
            return
        
        # Extract coordinates
        coords_data = []
        for idx, row in df_with_coords.iterrows():
            if isinstance(row['coordinates'], dict) and 'lat' in row['coordinates']:
                coords_data.append({
                    'lat': row['coordinates']['lat'],
                    'lon': row['coordinates']['lon'],
                    'disaster_type': row['disaster_type'],
                    'location': row['formatted_address'],
                    'confidence': row['confidence_score'],
                    'alert_level': row['alert_level'],
                    'content': row['content'],
                    'timestamp': row['datetime'],
                    'author': row['author'],
                    'platform': row['platform']
                })
        
        if not coords_data:
            st.info("No valid coordinate data found")
            return
        
        # Create Folium map
        map_center = [20, 0]  # World center
        disaster_map = folium.Map(
            location=map_center,
            zoom_start=2,
            tiles='OpenStreetMap'
        )
        
        # Add alternative tile layers
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite View',
            overlay=False,
            control=True
        ).add_to(disaster_map)
        
        # Color mapping for alert levels
        alert_colors = {
            'emergency': '#ff4444',
            'alert': '#ff8800',
            'warning': '#ffaa00', 
            'info': '#0088cc',
            'critical': '#8B0000',
            'high': '#FF4500',
            'medium': '#FFA500',
            'low': '#32CD32'
        }
        
        # Add markers for each alert
        for alert in coords_data:
            color = alert_colors.get(alert['alert_level'].lower(), '#666666')
            
            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 350px;">
                <h4 style="color: {color}; margin-bottom: 10px;">
                    🚨 {alert['disaster_type'].upper()} ALERT
                </h4>
                <div style="background-color: {color}; color: white; padding: 5px 10px; 
                           border-radius: 3px; margin-bottom: 10px; font-weight: bold;">
                    {alert['alert_level'].upper()} LEVEL
                </div>
                <p><strong>📍 Location:</strong> {alert['location']}</p>
                <p><strong>🎯 Confidence:</strong> {alert['confidence']:.2%}</p>
                <p><strong>⏰ Time:</strong> {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>👤 Author:</strong> {alert['author']}</p>
                <p><strong>📱 Platform:</strong> {alert['platform']}</p>
                <p><strong>📋 Content:</strong></p>
                <div style="background-color: #f5f5f5; padding: 8px; border-radius: 3px; 
                           font-style: italic; max-height: 100px; overflow-y: auto;">
                    {alert['content'][:200]}...
                </div>
            </div>
            """
            
            # Determine marker size based on confidence
            radius = max(6, min(15, alert['confidence'] * 20))
            
            # Add marker
            folium.CircleMarker(
                location=[alert['lat'], alert['lon']],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=400),
                color='white',
                weight=2,
                fillColor=color,
                fillOpacity=0.8,
                tooltip=f"{alert['disaster_type'].title()} - {alert['alert_level'].upper()}"
            ).add_to(disaster_map)
        
        # Add statistics to map
        total_alerts = len(coords_data)
        alert_levels = {}
        disaster_types = {}
        
        for alert in coords_data:
            level = alert['alert_level']
            dtype = alert['disaster_type']
            alert_levels[level] = alert_levels.get(level, 0) + 1
            disaster_types[dtype] = disaster_types.get(dtype, 0) + 1
        
        # Create legend
        legend_html = f"""
        <div style="position: fixed; 
                   top: 10px; right: 10px; width: 300px; 
                   background-color: white; border: 2px solid grey; 
                   z-index: 9999; font-size: 14px; padding: 15px; 
                   border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
        
        <h4 style="margin-top: 0; color: #333;">📊 Live Disaster Alerts</h4>
        
        <div style="margin-bottom: 15px;">
            <strong>Total Alerts: {total_alerts}</strong>
        </div>
        
        <div style="margin-bottom: 15px;">
            <strong>Alert Levels:</strong><br>
        """
        
        for level, count in sorted(alert_levels.items(), key=lambda x: ['emergency', 'alert', 'warning', 'info'].index(x[0]) if x[0] in ['emergency', 'alert', 'warning', 'info'] else 999):
            color = alert_colors.get(level, '#666666')
            legend_html += f"""
            <span style="color: {color}; font-weight: bold;">●</span> 
            {level.title()}: {count}<br>
            """
        
        legend_html += """
        </div>
        
        <div style="margin-bottom: 10px;">
            <strong>Disaster Types:</strong><br>
        """
        
        for dtype, count in sorted(disaster_types.items(), key=lambda x: x[1], reverse=True)[:5]:
            legend_html += f"• {dtype.title()}: {count}<br>"
        
        legend_html += f"""
        </div>
        
        <div style="font-size: 12px; color: #666; border-top: 1px solid #eee; padding-top: 10px;">
            🗺️ Map: OpenStreetMap<br>
            📡 Real-time disaster monitoring
        </div>
        
        </div>
        """
        
        disaster_map.get_root().html.add_child(folium.Element(legend_html))
        
        # Add layer control
        folium.LayerControl().add_to(disaster_map)
        
        # Display the map in Streamlit
        st_folium(disaster_map, width=700, height=500)
    
    def render_analytics_charts(self, df: pd.DataFrame):
        """Render analytics charts"""
        st.subheader("📈 Analytics Dashboard")
        
        if df.empty:
            st.info("No data available for analytics")
            return
        
        # Create tabs for different analytics
        tab1, tab2, tab3, tab4 = st.tabs(["Disaster Types", "Geographic Distribution", "Timeline", "Confidence Analysis"])
        
        with tab1:
            # Disaster types distribution
            disaster_counts = df['disaster_type'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_bar = px.bar(
                    x=disaster_counts.index,
                    y=disaster_counts.values,
                    title="Alerts by Disaster Type",
                    labels={'x': 'Disaster Type', 'y': 'Number of Alerts'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                fig_pie = px.pie(
                    values=disaster_counts.values,
                    names=disaster_counts.index,
                    title="Disaster Types Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab2:
            # Geographic distribution
            col1, col2 = st.columns(2)
            
            with col1:
                country_counts = df['country'].value_counts().head(10)
                fig_country = px.bar(
                    x=country_counts.values,
                    y=country_counts.index,
                    orientation='h',
                    title="Top 10 Countries by Alert Count"
                )
                st.plotly_chart(fig_country, use_container_width=True)
            
            with col2:
                platform_counts = df['platform'].value_counts()
                fig_platform = px.pie(
                    values=platform_counts.values,
                    names=platform_counts.index,
                    title="Alerts by Platform"
                )
                st.plotly_chart(fig_platform, use_container_width=True)
        
        with tab3:
            # Timeline analysis
            df['hour'] = df['datetime'].dt.hour
            hourly_counts = df.groupby('hour').size()
            
            fig_timeline = px.line(
                x=hourly_counts.index,
                y=hourly_counts.values,
                title="Alert Activity by Hour of Day",
                labels={'x': 'Hour', 'y': 'Number of Alerts'}
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Alert levels over time
            alert_level_timeline = df.groupby(['datetime', 'alert_level']).size().unstack(fill_value=0)
            if not alert_level_timeline.empty:
                fig_levels = px.area(
                    alert_level_timeline,
                    title="Alert Levels Over Time"
                )
                st.plotly_chart(fig_levels, use_container_width=True)
        
        with tab4:
            # Confidence analysis
            col1, col2 = st.columns(2)
            
            with col1:
                fig_conf_hist = px.histogram(
                    df,
                    x='confidence_score',
                    nbins=20,
                    title="Confidence Score Distribution"
                )
                st.plotly_chart(fig_conf_hist, use_container_width=True)
            
            with col2:
                fig_conf_disaster = px.box(
                    df,
                    x='disaster_type',
                    y='confidence_score',
                    title="Confidence Score by Disaster Type"
                )
                fig_conf_disaster.update_xaxes(tickangle=45)
                st.plotly_chart(fig_conf_disaster, use_container_width=True)
    
    def render_alert_details_table(self, df: pd.DataFrame):
        """Render detailed alerts table"""
        st.subheader("📋 Detailed Alerts Table")
        
        if df.empty:
            st.info("No alerts to display")
            return
        
        # Select columns to display
        display_columns = [
            'datetime', 'disaster_type', 'formatted_address', 'confidence_score',
            'alert_level', 'urgency_level', 'platform', 'is_genuine', 'language'
        ]
        
        # Filter and display
        display_df = df[display_columns].copy()
        display_df['datetime'] = display_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            column_config={
                'confidence_score': st.column_config.ProgressColumn(
                    "Confidence",
                    help="AI Confidence Score",
                    min_value=0.0,
                    max_value=1.0,
                ),
                'alert_level': st.column_config.SelectboxColumn(
                    "Alert Level",
                    help="Calculated Alert Level",
                    options=['info', 'warning', 'alert', 'emergency']
                )
            }
        )
    
    def render_sidebar_controls(self):
        """Render sidebar controls"""
        st.sidebar.header("🔧 Dashboard Controls")
        
        # Time range selection
        time_options = {
            "Last 1 Hour": 1,
            "Last 6 Hours": 6,
            "Last 24 Hours": 24,
            "Last 3 Days": 72,
            "Last Week": 168
        }
        
        selected_time = st.sidebar.selectbox(
            "Time Range",
            options=list(time_options.keys()),
            index=2  # Default to 24 hours
        )
        hours = time_options[selected_time]
        
        # Confidence threshold
        confidence_threshold = st.sidebar.slider(
            "Minimum Confidence Score",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.alert_threshold,
            step=0.1,
            help="Filter alerts by minimum confidence score"
        )
        st.session_state.alert_threshold = confidence_threshold
        
        # Auto-refresh controls
        st.sidebar.subheader("🔄 Auto Refresh")
        
        auto_refresh = st.sidebar.checkbox(
            "Enable Auto Refresh",
            value=st.session_state.auto_refresh
        )
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.sidebar.slider(
                "Refresh Interval (seconds)",
                min_value=10,
                max_value=300,
                value=st.session_state.refresh_interval,
                step=10
            )
            st.session_state.refresh_interval = refresh_interval
            
            # Auto-refresh logic
            current_time = time.time()
            if current_time - self.last_refresh >= refresh_interval:
                self.last_refresh = current_time
                st.rerun()
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now"):
            st.rerun()
        
        # Statistics
        if self.ai_system:
            st.sidebar.subheader("📊 System Statistics")
            try:
                stats = self.ai_system.get_alert_statistics()
                st.sidebar.metric("Total Alerts", stats.get('total_alerts', 0))
                st.sidebar.metric("Last 24h", stats.get('last_24h', 0))
                st.sidebar.metric("Avg Confidence", f"{stats.get('avg_confidence', 0):.2f}")
            except Exception as e:
                st.sidebar.error(f"Error loading stats: {e}")
        
        return hours, confidence_threshold
    
    def render_status_indicators(self):
        """Render system status indicators"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if self.ai_system:
                st.success("🤖 AI System: Online")
            else:
                st.error("🤖 AI System: Offline")
        
        with col2:
            if time.time() - self.last_refresh < 60:
                st.success(f"⏰ Last Update: {int(time.time() - self.last_refresh)}s ago")
            else:
                st.warning(f"⏰ Last Update: {int((time.time() - self.last_refresh)/60)}m ago")
        
        with col3:
            if st.session_state.auto_refresh:
                st.info("🔄 Auto Refresh: Enabled")
            else:
                st.info("🔄 Auto Refresh: Disabled")
    
    def run(self):
        """Run the dashboard"""
        # Header
        st.title("🌍 Real-Time Disaster Alert Dashboard")
        st.markdown("*AI-Powered Social Media Disaster Monitoring System*")
        
        # Status indicators
        self.render_status_indicators()
        
        # Sidebar controls
        hours, confidence_threshold = self.render_sidebar_controls()
        
        # Load data
        with st.spinner("Loading alerts data..."):
            df = self.load_alerts_data(hours=hours, min_confidence=confidence_threshold)
        
        if df.empty:
            st.warning("No alerts found matching the current filters.")
            st.info("Try reducing the confidence threshold or expanding the time range.")
        else:
            # Main dashboard content
            self.render_metrics_overview(df)
            
            st.divider()
            
            # Create main content columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                self.render_world_map(df)
                self.render_analytics_charts(df)
            
            with col2:
                self.render_live_alerts_feed(df)
            
            st.divider()
            
            # Detailed table at bottom
            self.render_alert_details_table(df)
        
        # Footer
        st.divider()
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8em; margin-top: 2rem;'>
            🌍 Disaster Alert Dashboard • Powered by Gemini AI • Real-time Social Media Monitoring
        </div>
        """, unsafe_allow_html=True)

# Main execution
def main():
    """Main dashboard execution"""
    try:
        dashboard = DisasterDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Dashboard initialization failed: {e}")
        st.info("Please check your API credentials and database connection.")

if __name__ == "__main__":
    main()