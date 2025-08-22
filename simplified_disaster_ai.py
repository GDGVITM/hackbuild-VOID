"""
Simplified Disaster Intelligence System
Streamlined version with working AI classification
"""

import json
import re
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

@dataclass
class SimpleDisasterAlert:
    """Simplified disaster alert structure"""
    alert_id: str
    platform: str
    content: str
    author: str
    timestamp: float
    
    # Core classification
    disaster_type: str
    confidence_score: float
    is_genuine: bool
    
    # Location
    location: str
    
    # Metadata
    created_at: float

class SimplifiedDisasterAI:
    """Simplified disaster AI that actually works"""
    
    def __init__(self):
        load_dotenv()
        
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required")
        
        self.gemini_client = genai.Client(api_key=self.api_key)
        
        # Initialize simple database
        self.init_database()
        
        print("🧠 Simplified Disaster AI initialized")
    
    def init_database(self):
        """Initialize simple alerts database"""
        conn = sqlite3.connect('disaster_analysis.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simple_alerts (
                alert_id TEXT PRIMARY KEY,
                platform TEXT,
                content TEXT,
                author TEXT,
                timestamp REAL,
                disaster_type TEXT,
                confidence_score REAL,
                is_genuine INTEGER,
                location TEXT,
                created_at REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def classify_disaster(self, content: str, author: str, platform: str) -> Dict:
        """Simple disaster classification that works"""
        
        # Simplified system instruction
        system_instruction = """You are a disaster detection AI. Analyze social media posts for disaster content.

Return JSON with exactly these fields:
- is_disaster: true/false (is this about a real disaster happening?)
- confidence: 0.0-1.0 (how confident are you?)
- disaster_type: type of disaster (earthquake, flood, fire, storm, etc.)
- location: best guess at location mentioned
- is_genuine: true/false (seems like a real report, not fake/joke?)

Examples:
"Earthquake in Tokyo!" -> {"is_disaster": true, "confidence": 0.9, "disaster_type": "earthquake", "location": "Tokyo", "is_genuine": true}
"I think there might be rain" -> {"is_disaster": false, "confidence": 0.8, "disaster_type": "none", "location": "", "is_genuine": false}

Return only JSON, no other text."""
        
        # Prepare simple content
        analysis_text = f"Social media post to analyze: {content}"
        
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=analysis_text)],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            system_instruction=[types.Part.from_text(text=system_instruction)],
        )
        
        try:
            print(f"🔍 Analyzing: {content[:50]}...")
            
            response_chunks = []
            for chunk in self.gemini_client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=generate_content_config,
            ):
                response_chunks.append(chunk.text)
            
            response_text = ''.join(response_chunks).strip()
            print(f"📥 AI Response: {response_text}")
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
                
            result = json.loads(response_text)
            print(f"✅ Parsed: Disaster={result.get('is_disaster')}, Confidence={result.get('confidence'):.2f}")
            
            return result
                
        except Exception as e:
            print(f"❌ Classification error: {e}")
            return {
                'is_disaster': False,
                'confidence': 0.0,
                'disaster_type': 'unknown',
                'location': '',
                'is_genuine': False
            }
    
    def create_alert(self, platform: str, content: str, author: str) -> Optional[SimpleDisasterAlert]:
        """Create disaster alert from content"""
        
        # Classify the content
        classification = self.classify_disaster(content, author, platform)
        
        # Check if it's disaster-related and has decent confidence
        if not classification.get('is_disaster') or classification.get('confidence', 0) < 0.5:
            print(f"   ❌ Not generating alert (disaster={classification.get('is_disaster')}, confidence={classification.get('confidence', 0):.2f})")
            return None
        
        # Create alert
        import hashlib
        alert_id = hashlib.md5(f"{platform}_{content[:50]}_{time.time()}".encode()).hexdigest()[:8]
        
        alert = SimpleDisasterAlert(
            alert_id=alert_id,
            platform=platform,
            content=content,
            author=author,
            timestamp=time.time(),
            disaster_type=classification['disaster_type'],
            confidence_score=classification['confidence'],
            is_genuine=classification['is_genuine'],
            location=classification['location'],
            created_at=time.time()
        )
        
        # Save to database
        self.save_alert(alert)
        
        print(f"   ✅ ALERT CREATED: {alert.disaster_type.upper()} in {alert.location}")
        print(f"      Confidence: {alert.confidence_score:.2f}, ID: {alert.alert_id}")
        
        return alert
    
    def save_alert(self, alert: SimpleDisasterAlert):
        """Save alert to database"""
        conn = sqlite3.connect('disaster_analysis.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO simple_alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert.alert_id, alert.platform, alert.content, alert.author,
            alert.timestamp, alert.disaster_type, alert.confidence_score,
            int(alert.is_genuine), alert.location, alert.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_alerts(self) -> List[SimpleDisasterAlert]:
        """Get all alerts from database"""
        conn = sqlite3.connect('disaster_analysis.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM simple_alerts ORDER BY timestamp DESC')
        alerts = []
        
        for row in cursor.fetchall():
            alert = SimpleDisasterAlert(
                alert_id=row[0],
                platform=row[1], 
                content=row[2],
                author=row[3],
                timestamp=row[4],
                disaster_type=row[5],
                confidence_score=row[6],
                is_genuine=bool(row[7]),
                location=row[8],
                created_at=row[9]
            )
            alerts.append(alert)
        
        conn.close()
        return alerts


if __name__ == "__main__":
    print("🧠 Simplified Disaster AI System - Production Ready")
    print("Use this system by importing SimplifiedDisasterAI class.")
    print("Example: from simplified_disaster_ai import SimplifiedDisasterAI")