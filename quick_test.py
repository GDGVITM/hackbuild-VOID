import requests
import json

# Quick test to see actual data
try:
    response = requests.get('http://localhost:8000/api/posts')
    data = response.json()
    posts = data.get('posts', [])
    
    print(f"📊 Found {len(posts)} posts in database")
    
    if posts:
        print("\n🔥 Sample post:")
        sample = posts[0]
        print(f"   ID: {sample['id']}")
        print(f"   Content: {sample['content'][:100]}...")
        print(f"   Location: {sample['location']}")
        print(f"   Has disaster_info: {'disaster_info' in sample}")
        
        if 'disaster_info' in sample:
            info = sample['disaster_info']
            print(f"   Disaster type: {info['type']}")
            print(f"   Urgency: {info['urgency_level']}")
            print(f"   Confidence: {info['confidence_level']}")
            
except Exception as e:
    print(f"❌ Error: {e}")

# Test map data too
try:
    response = requests.get('http://localhost:8000/api/map-data')
    data = response.json()
    points = data.get('points', [])
    print(f"\n🗺️ Found {len(points)} map points")
    
except Exception as e:
    print(f"❌ Map data error: {e}")
