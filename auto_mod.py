# To run this code you need to install the following dependencies:
# pip install google-genai praw python-dotenv pytz

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
reddit = praw.Reddit(
    client_id=os.getenv('YOUR_CLIENT_ID'),
    client_secret=os.getenv('YOUR_CLIENT_SECRET'),
    username=os.getenv('YOUR_USERNAME'),
    password=os.getenv('YOUR_PASSWORD'),
    user_agent='BrandPromoLocationBot/1.0'
)

try:
    print(f"Authenticated as: {reddit.user.me()}")
    print("Authentication successful!")
    
    try:
        subreddit = reddit.subreddit('disasterhazards')
        moderators = list(subreddit.moderator())
        mod_names = [mod.name for mod in moderators]
        print(f"Moderators of r/disasterhazards: {mod_names}")
        
        if str(reddit.user.me()) in mod_names:
            print("You have moderator permissions!")
        else:
            print("You don't have moderator permissions on this subreddit!")
            print("The bot will not be able to remove/approve posts.")
    except Exception as e:
        print(f"Error checking moderator status: {e}")
        
except Exception as e:
    print(f"Authentication failed: {e}")
    exit(1)

subreddit_name = 'disasterhazards'

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
    
    # Add search tool for Pro model analysis
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

def check_post_moderation(text):
    system_instruction = """You are a content moderator for a disaster hazards subreddit. Analyze posts and return JSON with these fields:
- city: true if mentions ANY specific geographic place name (city, town, village, district, state, region, landmark), false otherwise
- location: true if mentions any location/place (village, state, country, etc.), false otherwise
- promoting: true if promotes brands/products/services/businesses/companies/advertisements, false otherwise

Examples:
- 'Dharali Village, Uttarakhand' -> {"city": true, "location": true, "promoting": false}
- 'Flood in Mumbai today' -> {"city": true, "location": true, "promoting": false}
- 'Wayanad Landslides (Kerala, India)' -> {"city": true, "location": true, "promoting": false}
- 'Oregon (Doerner Fir Tree in Danger)' -> {"city": true, "location": true, "promoting": false}
- 'California wildfire spreading' -> {"city": true, "location": true, "promoting": false}
- 'Texas storm approaching' -> {"city": true, "location": true, "promoting": false}
- 'Earthquake in Tokyo yesterday' -> {"city": true, "location": true, "promoting": false}
- 'Disaster in northern region' -> {"city": false, "location": true, "promoting": false}
- 'Join our coaching classes' -> {"city": false, "location": false, "promoting": true}
- 'Buy our insurance product' -> {"city": false, "location": false, "promoting": true}

IMPORTANT: 
- State names (Oregon, California, Texas, Kerala, etc.) COUNT as cities for this purpose
- District names (Wayanad, etc.) COUNT as cities
- Any proper noun place name should be marked as city: true
- Only reject if there's NO specific place name at all (like "somewhere in north" or "general area")
- Geographic locations, villages, cities, states are NOT promotional content.
Only flag as promoting if it advertises businesses, products, or services.
Return only valid JSON, no markdown formatting."""
    
    result = call_gemini_api(f"Text to analyze: {text}", system_instruction)
    if result:
        return result.get('city', False), result.get('location', False), result.get('promoting', False)
    return False, False, True

def extract_disaster_info(text, submission):
    system_instruction = """You are a disaster intelligence analyst with access to real-time information. Extract detailed information from disaster-related posts and return JSON with these fields:
- place: The most specific location mentioned (format: 'City, Country' or 'Village, State, Country')
- region: The continental region (asia, europe, north_america, south_america, africa, oceania, antarctica)
- disaster_type: MUST be one of these 5 exact options: earthquake, flood, fire, storm, other
- urgency_level: Rate from 1-3 (1=low, 2=moderate, 3=high)
- confidence_level: Rate from 1-10 based on how credible the post seems and if there are previous cases
- sources: Array of VALID and ACCESSIBLE URLs/links to relevant news sources or information you found about this location/disaster

Use Google Search to find recent news about the mentioned location and disaster type to verify information and assess urgency.

Examples:
- 'Flood in Mumbai today' -> {"place": "Mumbai, India", "region": "asia", "disaster_type": "flood", "urgency_level": 3, "confidence_level": 8, "sources": ["https://timesofindia.com/mumbai-flood-alert", "https://ndtv.com/mumbai-weather"]}
- 'Earthquake hit Tokyo yesterday' -> {"place": "Tokyo, Japan", "region": "asia", "disaster_type": "earthquake", "urgency_level": 3, "confidence_level": 9, "sources": ["https://jma.go.jp/earthquake-report", "https://nhk.or.jp/earthquake-news"]}

IMPORTANT: 
- Use search tools to verify if the disaster is real and recent
- Provide ONLY valid, accessible, and working URLs/links in the sources array
- Test that URLs are reachable and contain relevant disaster information
- Do NOT include broken links, placeholder URLs, or inaccessible sources
- Check for official sources, news reports, government alerts
- Higher confidence for posts with corroborating evidence from multiple valid sources
- Lower confidence (4 or below) for posts that cannot be verified with reliable sources
- Higher urgency for ongoing/recent disasters affecting populated areas
- disaster_type must be exactly one of: earthquake, flood, fire, storm, other
Return only valid JSON, no markdown formatting."""
    
    result = call_gemini_api(f"Disaster text to analyze: {text}", system_instruction, model_name="gemini-2.5-pro", use_search=True)
    timestamp_info = get_indian_timestamp(submission)
    
    # Fixed disaster type options - only 5
    valid_disaster_types = ['earthquake', 'flood', 'fire', 'storm', 'other']
    
    if result:
        disaster_type = result.get('disaster_type', 'other')
        # Validate disaster type is in our fixed list
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

print(f"\nStarting auto-moderation for r/{subreddit_name}")
print("Checking existing unmoderated posts first...")

try:
    subreddit = reddit.subreddit(subreddit_name)
    
    print("Scanning recent posts...")
    for submission in subreddit.new(limit=25):
        if submission.approved or submission.removed:
            continue
            
        print(f"\n--- Processing Existing Post ---")
        print(f"Title: {submission.title}")
        print(f"Author: {submission.author}")
        print(f"URL: https://reddit.com{submission.permalink}")
        
        timestamp_info = get_indian_timestamp(submission)
        print(f"Posted: {timestamp_info['formatted_ist']}")
        
        content = submission.title + " " + (submission.selftext or "")
        has_city, has_location, is_promo = check_post_moderation(content)
        
        print(f"Analysis - City: {has_city}, Location: {has_location}, Promotion: {is_promo}")
        
        if is_promo or not has_city or not has_location:
            if is_promo:
                message = "Your post was removed because it promotes brands/products/services, which are not allowed."
                reason = "Promotion detected"
            elif not has_city and not has_location:
                message = "Your post was removed because it lacks city/location information."
                reason = "Missing city and location"
            elif not has_city:
                message = "Your post was removed because it lacks a city name."
                reason = "Missing city"
            elif not has_location:
                message = "Your post was removed because it lacks location information."
                reason = "Missing location"
            
            print(f"REJECTED: {reason}")
            print(f"Removal message: {message}")
            
            submission.mod.remove()
            submission.mod.send_removal_message(
                message=message,
                type="public"
            )
        else:
            print(f"APPROVED: Post meets all criteria")
            
            disaster_info = extract_disaster_info(content, submission)
            print(f"Place: {disaster_info['place']}")
            print(f"Region: {disaster_info['region']}")
            print(f"Disaster Type: {disaster_info['disaster_type']}")
            print(f"Urgency Level: {disaster_info['urgency_level']}/3")
            print(f"Confidence Level: {disaster_info['confidence_level']}/10")
            if disaster_info['sources']:
                print(f"Sources: {', '.join(disaster_info['sources'])}")
            else:
                print("Sources: No additional sources found")
            
            # Check confidence level - remove if 4 or below
            if disaster_info['confidence_level'] <= 4:
                print(f"REJECTED: Low confidence level ({disaster_info['confidence_level']}/10)")
                removal_message = f"Your post was removed due to low credibility score ({disaster_info['confidence_level']}/10). Unable to verify the disaster information from reliable sources."
                submission.mod.remove()
                submission.mod.send_removal_message(
                    message=removal_message,
                    type="public"
                )
            else:
                submission.mod.approve()
            
        time.sleep(2)
        
except Exception as e:
    print(f"Error processing existing posts: {e}")

print("\nNow monitoring for new posts...")

for submission in reddit.subreddit(subreddit_name).stream.submissions(skip_existing=True):
    print(f"\n--- Processing Post ---")
    print(f"Title: {submission.title}")
    print(f"Author: {submission.author}")
    print(f"URL: https://reddit.com{submission.permalink}")
    
    timestamp_info = get_indian_timestamp(submission)
    print(f"Posted: {timestamp_info['formatted_ist']}")
    
    content = submission.title + " " + (submission.selftext or "")
    has_city, has_location, is_promo = check_post_moderation(content)
    
    print(f"Analysis - City: {has_city}, Location: {has_location}, Promotion: {is_promo}")
    
    if is_promo or not has_city or not has_location:
        if is_promo:
            message = "Your post was removed because it promotes brands/products/services, which are not allowed."
            reason = "Promotion detected"
        elif not has_city and not has_location:
            message = "Your post was removed because it lacks city/location information."
            reason = "Missing city and location"
        elif not has_city:
            message = "Your post was removed because it lacks a city name."
            reason = "Missing city"
        elif not has_location:
            message = "Your post was removed because it lacks location information."
            reason = "Missing location"
        
        print(f"REJECTED: {reason}")
        print(f"Removal message: {message}")
        
        submission.mod.remove()
        submission.mod.send_removal_message(
            message=message,
            type="public"
        )
    else:
        print(f"APPROVED: Post meets all criteria")
        
        disaster_info = extract_disaster_info(content, submission)
        print(f"Place: {disaster_info['place']}")
        print(f"Region: {disaster_info['region']}")
        print(f"Disaster Type: {disaster_info['disaster_type']}")
        print(f"Urgency Level: {disaster_info['urgency_level']}/3")
        print(f"Confidence Level: {disaster_info['confidence_level']}/10")
        if disaster_info['sources']:
            print(f"Sources: {', '.join(disaster_info['sources'])}")
        else:
            print("Sources: No additional sources found")
        
        # Check confidence level - remove if 4 or below
        if disaster_info['confidence_level'] <= 4:
            print(f"REJECTED: Low confidence level ({disaster_info['confidence_level']}/10)")
            removal_message = f"Your post was removed due to low credibility score ({disaster_info['confidence_level']}/10). Unable to verify the disaster information from reliable sources."
            submission.mod.remove()
            submission.mod.send_removal_message(
                message=removal_message,
                type="public"
            )
        else:
            submission.mod.approve()
        
    time.sleep(1)
