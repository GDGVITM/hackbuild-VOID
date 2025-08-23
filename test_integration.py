import requests
import json

# Test all API endpoints
endpoints = [
    'health',
    'posts', 
    'posts/recent',
    'posts/urgent',
    'stats',
    'map-data'
]

print('🧪 TESTING API INTEGRATION')
print('='*50)

for endpoint in endpoints:
    try:
        response = requests.get(f'http://localhost:8000/api/{endpoint}')
        data = response.json()
        
        if endpoint == 'health':
            print(f'✅ {endpoint}: {data["status"]} - DB: {data["database"]}')
        elif endpoint == 'stats':
            stats = data.get('stats', {})
            print(f'✅ {endpoint}: {stats.get("total_posts", 0)} total posts')
        elif 'posts' in endpoint:
            posts = data.get('posts', [])
            print(f'✅ {endpoint}: {len(posts)} posts found')
        elif endpoint == 'map-data':
            points = data.get('points', [])
            print(f'✅ {endpoint}: {len(points)} map points')
            
    except Exception as e:
        print(f'❌ {endpoint}: Error - {str(e)}')

print('='*50)
print('✅ Integration test complete!')
print('\n📊 SAMPLE DATA:')
# Show sample post data
try:
    response = requests.get('http://localhost:8000/api/posts/recent')
    posts = response.json().get('posts', [])
    if posts:
        sample = posts[0]
        print(f"🔥 Latest disaster: {sample['disaster_info']['type'].upper()}")
        print(f"📍 Location: {sample['location']['name']}")
        print(f"⚠️  Urgency: {sample['disaster_info']['urgency_level']}/3")
        print(f"🎯 Confidence: {sample['disaster_info']['confidence_level']}/10")
        print(f"🕐 Time: {sample['timestamp']}")
except:
    print("❌ Could not fetch sample data")

print('\n🗺️  MAP INTEGRATION:')
try:
    response = requests.get('http://localhost:8000/api/map-data')
    points = response.json().get('points', [])
    print(f"📍 {len(points)} disaster points ready for map display")
    
    # Show breakdown by disaster type
    types = {}
    for point in points:
        disaster_type = point.get('type', 'unknown')
        types[disaster_type] = types.get(disaster_type, 0) + 1
    
    for disaster_type, count in types.items():
        print(f"   {disaster_type}: {count} incidents")
        
except:
    print("❌ Could not fetch map data")
