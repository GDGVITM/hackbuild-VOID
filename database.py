import sqlite3
import json
from datetime import datetime

def create_database():
    """Create enhanced disaster_analysis.db with extended schema"""
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    # Enhanced disaster_posts table with additional fields for visualization
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

def store_analysis(submission, disaster_info, approved):
    """Store disaster analysis with enhanced format and proper default handling"""
    if not approved:
        print(f"Skipping database storage for rejected post {submission.id}")
        return
    
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    try:
        # Extract coordinates if available, with proper defaults
        latitude = disaster_info.get('latitude') if disaster_info.get('latitude') is not None else 0.0
        longitude = disaster_info.get('longitude') if disaster_info.get('longitude') is not None else 0.0
        
        # Convert region to lowercase for consistency, with default
        region = disaster_info.get('region', 'unknown').lower() if disaster_info.get('region') else 'unknown'
        
        # Calculate severity level from urgency with proper default
        urgency_level = disaster_info.get('urgency_level', 2)
        if not urgency_level or not isinstance(urgency_level, (int, float)):
            urgency_level = 2
            
        if urgency_level >= 3:
            severity_level = 'critical'
        elif urgency_level >= 2:
            severity_level = 'high'
        else:
            severity_level = 'medium'
        
        # Ensure all required fields have defaults
        place = disaster_info.get('place', 'Unknown Location') or 'Unknown Location'
        disaster_type = disaster_info.get('disaster_type', 'unknown') or 'unknown'
        confidence_level = disaster_info.get('confidence_level', 50)
        if not isinstance(confidence_level, (int, float)) or confidence_level < 0:
            confidence_level = 50
        
        sources = disaster_info.get('sources', [])
        if not isinstance(sources, list):
            sources = []
            
        affected_radius_km = disaster_info.get('affected_radius_km', 25.0)
        if not isinstance(affected_radius_km, (int, float)) or affected_radius_km <= 0:
            affected_radius_km = 25.0
            
        hashtags = disaster_info.get('hashtags', [])
        if not isinstance(hashtags, list):
            hashtags = []
        
        cursor.execute('''
            INSERT OR REPLACE INTO disaster_posts 
            (post_id, title, content, author, post_time, place, region, 
             disaster_type, urgency_level, confidence_level, sources, approved,
             latitude, longitude, severity_level, affected_radius_km, source_platform, hashtags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission.id,
            submission.title or f"{disaster_type.title()} Alert - {place}",
            submission.selftext or f"Disaster alert for {disaster_type} in {place}",
            str(submission.author) if submission.author else 'unknown',
            datetime.fromtimestamp(submission.created_utc).isoformat() if hasattr(submission, 'created_utc') else datetime.now().isoformat(),
            place,
            region,
            disaster_type,
            int(urgency_level),
            int(confidence_level),
            json.dumps(sources),
            approved,
            latitude,
            longitude,
            severity_level,
            affected_radius_km,
            'reddit',  # Default source platform
            json.dumps(hashtags) if hashtags else json.dumps(['disaster', 'alert'])
        ))
        
        conn.commit()
        print(f"Stored enhanced analysis for approved post {submission.id} in database")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"Unexpected error in store_analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

def get_all_analyses():
    """Get all disaster analyses"""
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts ORDER BY post_time DESC')
    results = cursor.fetchall()
    
    conn.close()
    return results

def get_analyses_by_disaster_type(disaster_type):
    """Get analyses filtered by disaster type"""
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts WHERE disaster_type = ? ORDER BY post_time DESC', (disaster_type,))
    results = cursor.fetchall()
    
    conn.close()
    return results

def get_high_urgency_posts():
    """Get high urgency disaster posts"""
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts WHERE urgency_level >= 3 ORDER BY post_time DESC')
    results = cursor.fetchall()
    
    conn.close()
    return results

def get_disaster_statistics():
    """Get comprehensive disaster statistics from database"""
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    try:
        # Total disasters
        cursor.execute('SELECT COUNT(*) FROM disaster_posts WHERE approved = 1')
        total = cursor.fetchone()[0]
        
        # By disaster type
        cursor.execute('''
            SELECT disaster_type, COUNT(*) 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY disaster_type 
            ORDER BY COUNT(*) DESC
        ''')
        by_type = dict(cursor.fetchall())
        
        # By region
        cursor.execute('''
            SELECT region, COUNT(*) 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY region 
            ORDER BY COUNT(*) DESC
        ''')
        by_region = dict(cursor.fetchall())
        
        # By urgency level
        cursor.execute('''
            SELECT urgency_level, COUNT(*) 
            FROM disaster_posts 
            WHERE approved = 1 
            GROUP BY urgency_level 
            ORDER BY urgency_level
        ''')
        by_urgency = dict(cursor.fetchall())
        
        # Average confidence
        cursor.execute('SELECT AVG(confidence_level) FROM disaster_posts WHERE approved = 1')
        avg_confidence = cursor.fetchone()[0] or 0
        
        return {
            'total_disasters': total,
            'by_type': by_type,
            'by_region': by_region,
            'by_urgency': by_urgency,
            'avg_confidence': avg_confidence
        }
        
    except sqlite3.Error as e:
        print(f"Error getting statistics: {e}")
        return {}
    finally:
        conn.close()



if __name__ == "__main__":
    # Initialize database
    create_database()
    
    # Test statistics
    stats = get_disaster_statistics()
    print(f"\nDatabase Statistics:")
    print(f"Total disasters: {stats['total_disasters']}")
    print(f"By type: {stats['by_type']}")
    print(f"By region: {stats['by_region']}")
    print(f"By urgency: {stats['by_urgency']}")
    print(f"Average confidence: {stats['avg_confidence']:.1f}%")
