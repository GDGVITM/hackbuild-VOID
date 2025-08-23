import sqlite3
import json
from datetime import datetime

def create_database():
    conn = sqlite3.connect('disaster_analysis.db')
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
            approved BOOLEAN
        )
    ''')
    
    conn.commit()
    conn.close()

def store_analysis(submission, disaster_info, approved):
    if not approved:
        print(f"Skipping database storage for rejected post {submission.id}")
        return
    
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO disaster_posts 
            (post_id, title, content, author, post_time, place, region, 
             disaster_type, urgency_level, confidence_level, sources, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            submission.id,
            submission.title,
            submission.selftext,
            str(submission.author),
            datetime.fromtimestamp(submission.created_utc).isoformat(),
            disaster_info.get('place', ''),
            disaster_info.get('region', ''),
            disaster_info.get('disaster_type', ''),
            disaster_info.get('urgency_level', 0),
            disaster_info.get('confidence_level', 0),
            json.dumps(disaster_info.get('sources', [])),
            approved
        ))
        
        conn.commit()
        print(f"Stored analysis for approved post {submission.id} in database")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def get_all_analyses():
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts ORDER BY post_time DESC')
    results = cursor.fetchall()
    
    conn.close()
    return results

def get_analyses_by_disaster_type(disaster_type):
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts WHERE disaster_type = ? ORDER BY post_time DESC', (disaster_type,))
    results = cursor.fetchall()
    
    conn.close()
    return results

def get_high_urgency_posts():
    conn = sqlite3.connect('disaster_analysis.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM disaster_posts WHERE urgency_level = 3 ORDER BY post_time DESC')
    results = cursor.fetchall()
    
    conn.close()
    return results
