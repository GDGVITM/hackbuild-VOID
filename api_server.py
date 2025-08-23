from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import threading
import time
import os

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:5174"])

# Initialize geocoder for location data
geolocator = Nominatim(user_agent="disaster_map_app")

def get_coordinates_for_place(place):
    """Get latitude and longitude for a place name"""
    try:
        if not place or place.lower() in ['unknown', 'local area']:
            return None, None
        
        location = geolocator.geocode(place, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, GeocoderServiceError, Exception):
        return None, None

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('disaster_analysis.db')
    conn.row_factory = sqlite3.Row
    return conn

def convert_to_react_format(db_posts):
    """Convert database posts to React frontend format"""
    posts = []
    
    for post in db_posts:
        # Get coordinates for the place
        lat, lng = get_coordinates_for_place(post['place'])
        
        # Default to India center if no coordinates found
        if lat is None or lng is None:
            lat, lng = 20.5937, 78.9629  # Center of India
        
        # Parse sources
        try:
            sources = json.loads(post['sources']) if post['sources'] else []
        except:
            sources = []
        
        # Map disaster types to platforms for UI consistency
        platform_mapping = {
            'earthquake': 'twitter',
            'flood': 'facebook', 
            'fire': 'instagram',
            'storm': 'reddit',
            'other': 'twitter'
        }
        
        # Create urgency tags
        urgency_tags = []
        if post['urgency_level'] == 3:
            urgency_tags.append('#URGENT')
        elif post['urgency_level'] == 2:
            urgency_tags.append('#Alert')
        
        # Add disaster type and location tags
        disaster_tags = [f"#{post['disaster_type'].title()}", f"#{post['place'].replace(' ', '')}"]
        all_tags = urgency_tags + disaster_tags
        
        react_post = {
            'id': str(post['post_id']),
            'userHandle': f"@{post['author']}",
            'platform': platform_mapping.get(post['disaster_type'], 'twitter'),
            'content': f"{post['title']} - {post['content'] or 'Real-time disaster alert from Reddit monitoring system.'}",
            'imageUrl': None,  # Could be enhanced to include disaster images
            'tags': all_tags,
            'location': {
                'lat': lat,
                'lng': lng,
                'name': post['place']
            },
            'timestamp': datetime.fromisoformat(post['post_time']).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'upvotes': post['confidence_level'] * 3,  # Convert confidence to upvotes
            'downvotes': max(0, 10 - post['confidence_level']),
            'disaster_info': {
                'type': post['disaster_type'],
                'urgency_level': post['urgency_level'],
                'confidence_level': post['confidence_level'],
                'region': post['region'],
                'sources': sources
            }
        }
        posts.append(react_post)
    
    return posts

@app.route('/api/posts')
def get_posts():
    """Get all approved disaster posts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE approved = 1 
            ORDER BY post_time DESC 
            LIMIT 100
        ''')
        
        db_posts = cursor.fetchall()
        conn.close()
        
        posts = convert_to_react_format(db_posts)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'total': len(posts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'posts': [],
            'total': 0
        }), 500

@app.route('/api/posts/recent')
def get_recent_posts():
    """Get posts from last 24 hours"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE approved = 1 AND post_time >= ?
            ORDER BY post_time DESC
        ''', (twenty_four_hours_ago,))
        
        db_posts = cursor.fetchall()
        conn.close()
        
        posts = convert_to_react_format(db_posts)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'total': len(posts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'posts': [],
            'total': 0
        }), 500

@app.route('/api/posts/urgent')
def get_urgent_posts():
    """Get high urgency posts (level 3)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE approved = 1 AND urgency_level = 3
            ORDER BY post_time DESC
        ''')
        
        db_posts = cursor.fetchall()
        conn.close()
        
        posts = convert_to_react_format(db_posts)
        
        return jsonify({
            'success': True,
            'posts': posts,
            'total': len(posts),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'posts': [],
            'total': 0
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get disaster statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total posts
        cursor.execute('SELECT COUNT(*) as total FROM disaster_posts WHERE approved = 1')
        total = cursor.fetchone()['total']
        
        # By disaster type
        cursor.execute('''
            SELECT disaster_type, COUNT(*) as count 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY disaster_type
        ''')
        by_type = {row['disaster_type']: row['count'] for row in cursor.fetchall()}
        
        # By urgency level
        cursor.execute('''
            SELECT urgency_level, COUNT(*) as count 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY urgency_level
        ''')
        by_urgency = {row['urgency_level']: row['count'] for row in cursor.fetchall()}
        
        # By region
        cursor.execute('''
            SELECT region, COUNT(*) as count 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY region
        ''')
        by_region = {row['region']: row['count'] for row in cursor.fetchall()}
        
        # Recent posts (last 24 hours)
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) as recent 
            FROM disaster_posts 
            WHERE approved = 1 AND post_time >= ?
        ''', (twenty_four_hours_ago,))
        recent = cursor.fetchone()['recent']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_posts': total,
                'recent_posts_24h': recent,
                'by_disaster_type': by_type,
                'by_urgency_level': by_urgency,
                'by_region': by_region
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {}
        }), 500

@app.route('/api/map-data')
def get_map_data():
    """Get disaster data formatted for map display"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent posts for map
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        
        cursor.execute('''
            SELECT * FROM disaster_posts 
            WHERE approved = 1 AND post_time >= ?
            ORDER BY urgency_level DESC, post_time DESC
        ''', (twenty_four_hours_ago,))
        
        db_posts = cursor.fetchall()
        conn.close()
        
        map_points = []
        for post in db_posts:
            lat, lng = get_coordinates_for_place(post['place'])
            
            if lat is not None and lng is not None:
                map_point = {
                    'id': post['post_id'],
                    'lat': lat,
                    'lng': lng,
                    'type': post['disaster_type'],
                    'urgency': post['urgency_level'],
                    'confidence': post['confidence_level'],
                    'place': post['place'],
                    'title': post['title'],
                    'timestamp': post['post_time'],
                    'author': post['author']
                }
                map_points.append(map_point)
        
        return jsonify({
            'success': True,
            'points': map_points,
            'total': len(map_points),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'points': [],
            'total': 0
        }), 500

@app.route('/api/generate-map', methods=['POST'])
def generate_map():
    """Generate disaster map using fast_map.py for better performance"""
    try:
        # Import map functionality
        import subprocess
        import os
        import shutil
        from datetime import datetime
        
        # Run the FAST map generation script
        result = subprocess.run(['python', 'fast_map.py'], 
                              capture_output=True, 
                              text=True, 
                              cwd=os.getcwd())
        
        if result.returncode == 0:
            # Look for generated HTML file
            current_dir = os.getcwd()
            map_file = 'disaster_map.html'
            
            if os.path.exists(map_file):
                map_path = os.path.abspath(map_file)
                
                # Copy to public/maps directory for serving
                public_maps_dir = os.path.join(current_dir, 'public', 'maps')
                os.makedirs(public_maps_dir, exist_ok=True)
                
                # Copy the file to public directory
                dest_path = os.path.join(public_maps_dir, map_file)
                shutil.copy2(map_file, dest_path)
                
                return jsonify({
                    'success': True,
                    'mapFilePath': map_path,
                    'mapFileName': map_file,
                    'publicMapPath': f'/maps/{map_file}',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Fast map with demo data generated successfully',
                    'generationTime': 'optimized for speed'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No map file generated',
                    'output': result.stdout,
                    'errors': result.stderr
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Fast map generation script failed',
                'output': result.stdout,
                'errors': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Fast map generation error: {str(e)}'
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected' if os.path.exists('disaster_analysis.db') else 'not_found'
    })

if __name__ == '__main__':
    print("🚀 Starting Disaster Alert API Server...")
    print("📊 Endpoints available:")
    print("   GET /api/posts - All approved disaster posts")
    print("   GET /api/posts/recent - Posts from last 24 hours")
    print("   GET /api/posts/urgent - High urgency posts")
    print("   GET /api/stats - Disaster statistics")
    print("   GET /api/map-data - Map visualization data")
    print("   POST /api/generate-map - Generate advanced disaster map")
    print("   GET /api/health - Health check")
    print("🌍 Server running on http://localhost:8000")
    
    app.run(host='0.0.0.0', port=8000, debug=True, threaded=True)
