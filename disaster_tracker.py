import sqlite3
import json
from datetime import datetime, timezone
import pytz
from typing import Dict, List, Optional, Tuple
import os

class DisasterTracker:
    def __init__(self, db_path: str = "disaster_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with disaster history table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disasters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                place TEXT NOT NULL,
                region TEXT NOT NULL,
                disaster_type TEXT NOT NULL,
                country TEXT NOT NULL,
                state_province TEXT NOT NULL,
                city TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                utc_timestamp REAL NOT NULL,
                ist_datetime TEXT NOT NULL,
                post_title TEXT NOT NULL,
                post_author TEXT NOT NULL,
                post_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_region ON disasters(region);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_disaster_type ON disasters(disaster_type);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON disasters(utc_timestamp);
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_country ON disasters(country);
        ''')
        
        conn.commit()
        conn.close()
    
    def add_disaster(self, disaster_info: Dict, post_info: Dict):
        """Add a new disaster record to the database with proper default handling"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Extract coordinates if available (you can extend this with geocoding)
            latitude, longitude = self.get_coordinates(disaster_info.get('place', 'Unknown'))
            
            # Ensure all required fields have defaults
            place = disaster_info.get('place', 'Unknown Location') or 'Unknown Location'
            region = disaster_info.get('region', 'unknown') or 'unknown'
            disaster_type = disaster_info.get('disaster_type', 'unknown') or 'unknown'
            country = disaster_info.get('country', 'Unknown') or 'Unknown'
            state_province = disaster_info.get('state_province', 'Unknown') or 'Unknown'
            city = disaster_info.get('city', 'Unknown') or 'Unknown'
            
            # Handle timestamp info with defaults
            timestamp_info = disaster_info.get('timestamp_info', {})
            utc_timestamp = timestamp_info.get('utc_timestamp', datetime.now().timestamp())
            ist_datetime = timestamp_info.get('ist_datetime', datetime.now().isoformat())
            
            # Handle post info with defaults
            post_title = post_info.get('title', f"{disaster_type.title()} Alert - {place}") or f"{disaster_type.title()} Alert - {place}"
            post_author = post_info.get('author', 'unknown') or 'unknown'
            post_url = post_info.get('url', '') or ''
            
            cursor.execute('''
                INSERT INTO disasters 
                (place, region, disaster_type, country, state_province, city, 
                 latitude, longitude, utc_timestamp, ist_datetime, 
                 post_title, post_author, post_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                place, region, disaster_type, country, state_province, city,
                latitude, longitude, utc_timestamp, ist_datetime,
                post_title, post_author, post_url
            ))
            
            conn.commit()
            disaster_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ Disaster record added to database (ID: {disaster_id})")
            return disaster_id
            
        except Exception as e:
            print(f"❌ Error adding disaster to database: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            conn.close()
            return None
    
    def get_coordinates(self, place: str) -> Tuple[Optional[float], Optional[float]]:
        """Get coordinates for a place (placeholder - you can integrate with geocoding API)"""
        # Basic coordinate mapping for common Indian locations
        coordinates_map = {
            "mumbai, india": (19.0760, 72.8777),
            "delhi, india": (28.6139, 77.2090),
            "kolkata, india": (22.5726, 88.3639),
            "chennai, india": (13.0827, 80.2707),
            "bangalore, india": (12.9716, 77.5946),
            "hyderabad, india": (17.3850, 78.4867),
            "pune, india": (18.5204, 73.8567),
            "ahmedabad, india": (23.0225, 72.5714),
            "andaman and nicobar islands, india": (11.7401, 92.6586),
            "kerala, india": (10.8505, 76.2711),
            "tamil nadu, india": (11.1271, 78.6569),
            "uttarakhand, india": (30.0668, 79.0193),
            "assam, india": (26.2006, 92.9376),
            "west bengal, india": (22.9868, 87.8550)
        }
        
        place_lower = place.lower()
        
        # Enhanced coordinate lookup with better defaults
        coords = coordinates_map.get(place_lower, None)
        if coords and coords != (None, None):
            return coords
            
        # Fuzzy matching for partial matches
        for location, coords in coordinates_map.items():
            if coords and coords != (None, None):
                if location in place_lower or any(word in place_lower for word in location.split()):
                    return coords
                    
        # Country-based defaults
        if any(country in place_lower for country in ['india', 'indian']):
            return 20.5937, 78.9629  # Center of India
        elif any(country in place_lower for country in ['china', 'chinese']):
            return 35.8617, 104.1954  # Center of China
        elif any(country in place_lower for country in ['usa', 'america', 'united states']):
            return 39.8283, -98.5795  # Center of USA
        elif any(country in place_lower for country in ['japan', 'japanese']):
            return 36.2048, 138.2529  # Center of Japan
        elif any(country in place_lower for country in ['uk', 'britain', 'england']):
            return 55.3781, -3.4360  # Center of UK
        
        # Default coordinates (0, 0) instead of None
        return 0.0, 0.0
    
    def get_disasters_by_region(self, region: str, limit: int = 100) -> List[Dict]:
        """Get disasters by region"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disasters 
            WHERE region = ? 
            ORDER BY utc_timestamp DESC 
            LIMIT ?
        ''', (region, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_disasters_by_type(self, disaster_type: str, limit: int = 100) -> List[Dict]:
        """Get disasters by type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disasters 
            WHERE disaster_type = ? 
            ORDER BY utc_timestamp DESC 
            LIMIT ?
        ''', (disaster_type, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_recent_disasters(self, days: int = 30, limit: int = 100) -> List[Dict]:
        """Get recent disasters within specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate timestamp for 'days' ago
        now = datetime.now(timezone.utc)
        days_ago = now.timestamp() - (days * 24 * 60 * 60)
        
        cursor.execute('''
            SELECT * FROM disasters 
            WHERE utc_timestamp >= ? 
            ORDER BY utc_timestamp DESC 
            LIMIT ?
        ''', (days_ago, limit))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_all_disasters(self, limit: int = 1000) -> List[Dict]:
        """Get all disasters from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM disasters 
            ORDER BY utc_timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
    
    def get_disaster_stats(self) -> Dict:
        """Get statistics about disasters in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total disasters
        cursor.execute('SELECT COUNT(*) FROM disasters')
        total_disasters = cursor.fetchone()[0]
        
        # Disasters by type
        cursor.execute('''
            SELECT disaster_type, COUNT(*) as count 
            FROM disasters 
            GROUP BY disaster_type 
            ORDER BY count DESC
        ''')
        disasters_by_type = dict(cursor.fetchall())
        
        # Disasters by region
        cursor.execute('''
            SELECT region, COUNT(*) as count 
            FROM disasters 
            GROUP BY region 
            ORDER BY count DESC
        ''')
        disasters_by_region = dict(cursor.fetchall())
        
        # Disasters by country
        cursor.execute('''
            SELECT country, COUNT(*) as count 
            FROM disasters 
            GROUP BY country 
            ORDER BY count DESC
        ''')
        disasters_by_country = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_disasters': total_disasters,
            'by_type': disasters_by_type,
            'by_region': disasters_by_region,
            'by_country': disasters_by_country
        }
    
    def export_to_json(self, filename: str = "disaster_data.json"):
        """Export all disaster data to JSON file"""
        disasters = self.get_all_disasters()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(disasters, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Data exported to {filename}")
        return filename

if __name__ == "__main__":
    # Initialize disaster tracker
    tracker = DisasterTracker()
    
    # Display current database statistics
    stats = tracker.get_disaster_stats()
    print("\nDatabase Statistics:")
    print(f"Total disasters: {stats['total_disasters']}")
    print(f"By type: {stats['by_type']}")
    print(f"By region: {stats['by_region']}")
    print(f"By country: {stats['by_country']}")