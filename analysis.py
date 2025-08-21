import praw
from google import genai
from google.genai import types
import os
import time
import json
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

def get_indian_timestamp(submission):
    ist = pytz.timezone('Asia/Kolkata')
    post_time_utc = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    post_time_ist = post_time_utc.astimezone(ist)
    
    return {
        'utc_timestamp': submission.created_utc,
        'utc_datetime': post_time_utc.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'ist_datetime': post_time_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
        'ist_date': post_time_ist.strftime('%Y-%m-%d'),
        'ist_time': post_time_ist.strftime('%H:%M:%S'),
        'day_of_week': post_time_ist.strftime('%A'),
        'formatted_ist': post_time_ist.strftime('%d %B %Y, %I:%M %p IST')
    }

def call_gemini_api(text, system_instruction, model_name="gemini-2.5-flash", use_search=False):
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=text),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        system_instruction=[
            types.Part.from_text(text=system_instruction),
        ],
        temperature=0.35,
    )
    
    if use_search and model_name == "gemini-2.5-pro":
        generate_content_config.tools = [
            types.Tool(google_search=types.GoogleSearch())
        ]
    
    try:
        response_chunks = []
        for chunk in client.models.generate_content_stream(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        ):
            response_chunks.append(chunk.text)
        
        response_text = ''.join(response_chunks).strip()
        
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
            
        return json.loads(response_text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def extract_disaster_info(text, submission):
    system_instruction = """You are a disaster intelligence analyst with access to real-time information. Extract detailed information from disaster-related posts and return JSON with these fields:
- place: The most specific location mentioned (format: 'City, Country' or 'Village, State, Country')
- region: The continental region (asia, europe, north_america, south_america, africa, oceania, antarctica)
- disaster_type: MUST be one of these 5 exact options: earthquake, flood, fire, storm, other
- urgency_level: Rate from 1-3 (1=low, 2=moderate, 3=high)
- confidence_level: Rate from 1-10 based on how credible the post seems and if there are previous cases
- sources: Array of Google search queries that users can search to find relevant news articles about this disaster

Use Google Search to find recent news about the mentioned location and disaster type to verify information and assess urgency.

Examples:
- 'Flood in Mumbai today' -> {"place": "Mumbai, India", "region": "asia", "disaster_type": "flood", "urgency_level": 3, "confidence_level": 8, "sources": ["Mumbai flood 2025 news", "Mumbai weather alert today", "Maharashtra flood update"]}
- 'Earthquake hit Tokyo yesterday' -> {"place": "Tokyo, Japan", "region": "asia", "disaster_type": "earthquake", "urgency_level": 3, "confidence_level": 9, "sources": ["Tokyo earthquake today news", "Japan earthquake alert 2025", "Tokyo seismic activity report"]}

IMPORTANT: 
- Use search tools to verify if the disaster is real and recent
- Provide Google search query strings that will help users find relevant news articles
- Include location name, disaster type, current year, and relevant keywords like "news", "alert", "update"
- Create 2-3 specific search queries that target official sources, news reports, government alerts
- Higher confidence for posts with corroborating evidence from multiple valid sources
- Lower confidence (4 or below) for posts that cannot be verified with reliable sources
- Higher urgency for ongoing/recent disasters affecting populated areas
- disaster_type must be exactly one of: earthquake, flood, fire, storm, other
Return only valid JSON, no markdown formatting."""
    
    result = call_gemini_api(f"Disaster text to analyze: {text}", system_instruction, model_name="gemini-2.5-pro", use_search=True)
    timestamp_info = get_indian_timestamp(submission)
    
    valid_disaster_types = ['earthquake', 'flood', 'fire', 'storm', 'other']
    
    if result:
        disaster_type = result.get('disaster_type', 'other')
        if disaster_type not in valid_disaster_types:
            disaster_type = 'other'
            
        return {
            'place': result.get('place', 'Unknown'),
            'region': result.get('region', 'unknown'),
            'disaster_type': disaster_type,
            'urgency_level': result.get('urgency_level', 1),
            'confidence_level': result.get('confidence_level', 1),
            'sources': result.get('sources', []),
            'timestamp_info': timestamp_info
        }
    return {
        'place': 'Unknown',
        'region': 'unknown', 
        'disaster_type': 'other',
        'urgency_level': 1,
        'confidence_level': 1,
        'sources': ['API call failed - unable to verify'],
        'timestamp_info': timestamp_info
    }
