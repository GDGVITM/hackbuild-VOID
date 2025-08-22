from google import genai
from google.genai import types
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import pytz

load_dotenv()

gemini_api_key = os.getenv('GEMINI_API_KEY')
pplx_api_key = os.getenv('PPLX_API_KEY')
gemini_client = genai.Client(api_key=gemini_api_key)

def clean_json_response(text):
    if text.startswith('```json'):
        return text.replace('```json', '').replace('```', '').strip()
    elif text.startswith('```'):
        return text.replace('```', '').strip()
    return text.strip()

def get_indian_timestamp(submission):
    ist = pytz.timezone('Asia/Kolkata')
    post_time_utc = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    post_time_ist = post_time_utc.astimezone(ist)
    
    return {
        'formatted_ist': post_time_ist.strftime('%d %B %Y, %I:%M %p IST')
    }

def call_gemini_api(text, system_instruction, model_name="gemini-2.5-flash", use_search=False):
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=text)])]
    
    config = types.GenerateContentConfig(
        system_instruction=[types.Part.from_text(text=system_instruction)],
        temperature=0.35,
    )
    
    if use_search and model_name == "gemini-2.5-pro":
        config.tools = [types.Tool(googleSearch=types.GoogleSearch())]
    
    try:
        response_chunks = []
        for chunk in gemini_client.models.generate_content_stream(model=model_name, contents=contents, config=config):
            if chunk.text:
                response_chunks.append(chunk.text)
        
        response_text = ''.join(response_chunks).strip()
        return json.loads(clean_json_response(response_text)) if response_text else None
        
    except Exception:
        return None

def call_perplexity_api(text, system_instruction, model_name="sonar"):
    try:
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {pplx_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model_name,
                'messages': [
                    {'role': 'system', 'content': system_instruction},
                    {'role': 'user', 'content': text}
                ],
                'temperature': 0.35,
                'max_tokens': 1500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            return json.loads(clean_json_response(content))
        return None
            
    except Exception:
        return None

def extract_disaster_info(text, submission):
    system_instruction = """You are a disaster intelligence analyst with access to real-time information. Extract detailed information from disaster-related posts and return JSON with these fields:
- place: The most specific location mentioned (format: 'City, Country' or 'Village, State, Country')
- region: The continental region (asia, europe, north_america, south_america, africa, oceania, antarctica)
- disaster_type: MUST be one of these 5 exact options: earthquake, flood, fire, storm, other
- urgency_level: Rate from 1-3 based on STRICT criteria:
  * 1 (LOW): Past events, minor incidents, no immediate threat, small scale
  * 2 (MODERATE): Recent events (24-48hrs), moderate impact, localized threat  
  * 3 (HIGH): Ongoing/current events, major impact, widespread threat, immediate danger
- confidence_level: Rate from 1-10 based on STRICT verification criteria:
  * 1-3 (LOW): Unverified social media posts, no credible sources, rumors
  * 4-6 (MEDIUM): Some verification, limited sources, partial confirmation
  * 7-10 (HIGH): Multiple reliable sources, official reports, confirmed by authorities
- sources: Array of actual working URLs/links to relevant news sources that verify this disaster

CRITICAL ASSESSMENT GUIDELINES:
- BE CONSERVATIVE with ratings - most posts should get urgency 1-2 and confidence 4-6
- Only assign urgency 3 for CURRENT, MAJOR disasters affecting large populations
- Only assign confidence 8+ when you find multiple official/government sources
- Social media posts without news verification should get confidence 3-5 maximum
- Historical events (older than 48 hours) should get urgency 1
- Assign confidence 1-2 if no reliable sources found during web search

Search the web to find recent news about the mentioned location and disaster type to verify information and assess urgency. Provide actual working URLs from reliable news sources.

Examples:
- 'Flood in Mumbai today' with multiple news sources -> {"place": "Mumbai, India", "region": "asia", "disaster_type": "flood", "urgency_level": 3, "confidence_level": 8, "sources": ["...news URLs..."]}
- 'Earthquake hit Tokyo yesterday' with official reports -> {"place": "Tokyo, Japan", "region": "asia", "disaster_type": "earthquake", "urgency_level": 2, "confidence_level": 9, "sources": ["...official URLs..."]}
- 'Fire near my house' with no news sources -> {"place": "Local Area", "region": "unknown", "disaster_type": "fire", "urgency_level": 1, "confidence_level": 3, "sources": []}
- 'Storm warning issued' with weather alerts -> {"place": "Region", "region": "...", "disaster_type": "storm", "urgency_level": 2, "confidence_level": 7, "sources": ["...weather URLs..."]}

IMPORTANT: 
- Default to LOWER ratings unless strong evidence supports higher ones
- Use web search to find and verify actual news URLs about the disaster
- Provide only working, accessible URLs from reliable news sources
- Include URLs from official sources, news reports, government alerts
- Higher confidence for posts with corroborating evidence from multiple valid sources
- Lower confidence (4 or below) for posts that cannot be verified with reliable sources
- Higher urgency for ongoing/recent disasters affecting populated areas
- disaster_type must be exactly one of: earthquake, flood, fire, storm, other
Return only valid JSON, no markdown formatting."""
    
    result = call_perplexity_api(f"Disaster text to analyze: {text}", system_instruction)
    
    if result:
        disaster_type = result.get('disaster_type', 'other')
        if disaster_type not in ['earthquake', 'flood', 'fire', 'storm', 'other']:
            disaster_type = 'other'
            
        return {
            'place': result.get('place', 'Unknown'),
            'region': result.get('region', 'unknown'),
            'disaster_type': disaster_type,
            'urgency_level': result.get('urgency_level', 1),
            'confidence_level': result.get('confidence_level', 1),
            'sources': result.get('sources', [])
        }
    
    return {
        'place': 'Unknown',
        'region': 'unknown', 
        'disaster_type': 'other',
        'urgency_level': 1,
        'confidence_level': 1,
        'sources': ['API call failed - unable to verify']
    }
