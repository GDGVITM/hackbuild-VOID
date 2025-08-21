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

def call_gemini_api(text, system_instruction, model_name="gemini-2.5-flash"):
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
    )
    
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
- city: true if mentions a specific city name, false otherwise
- location: true if mentions any location/place (village, state, country, etc.), false otherwise
- promoting: true if promotes brands/products/services/businesses/companies/advertisements, false otherwise

Examples:
- 'Dharali Village, Uttarakhand' -> {"city": true, "location": true, "promoting": false}
- 'Flood in Mumbai today' -> {"city": true, "location": true, "promoting": false}
- 'Join our coaching classes' -> {"city": false, "location": false, "promoting": true}
- 'Buy our insurance product' -> {"city": false, "location": false, "promoting": true}

Note: Geographic locations, villages, cities, states are NOT promotional content.
Only flag as promoting if it advertises businesses, products, or services.
Return only valid JSON, no markdown formatting."""
    
    result = call_gemini_api(f"Text to analyze: {text}", system_instruction)
    if result:
        return result.get('city', False), result.get('location', False), result.get('promoting', False)
    return False, False, True

def extract_disaster_info(text, submission):
    system_instruction = """You are a disaster intelligence analyst. Extract detailed information from disaster-related posts and return JSON with these fields:
- place: The most specific location mentioned (format: 'City, Country' or 'Village, State, Country')
- region: The continental region (asia, europe, north_america, south_america, africa, oceania, antarctica)
- disaster_type: MUST be one of these 5 exact options: earthquake, flood, fire, storm, other

Examples:
- 'Flood in Mumbai today' -> {"place": "Mumbai, India", "region": "asia", "disaster_type": "flood"}
- 'Earthquake hit Tokyo yesterday' -> {"place": "Tokyo, Japan", "region": "asia", "disaster_type": "earthquake"}
- 'Forest fire spreading in California right now' -> {"place": "California, USA", "region": "north_america", "disaster_type": "fire"}
- 'Hurricane approaching Florida' -> {"place": "Florida, USA", "region": "north_america", "disaster_type": "storm"}
- 'Cyclone hitting coast' -> {"place": "Coast", "region": "unknown", "disaster_type": "storm"}

IMPORTANT: disaster_type must be exactly one of: earthquake, flood, fire, storm, other
Map related disasters: hurricane/cyclone/tornado -> storm, wildfire/forest fire -> fire, landslide/tsunami/drought -> other
Return only valid JSON, no markdown formatting."""
    
    result = call_gemini_api(f"Disaster text to analyze: {text}", system_instruction)
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
            'timestamp_info': timestamp_info
        }
    return {
        'place': 'Unknown',
        'region': 'unknown', 
        'disaster_type': 'other',
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
        
        submission.mod.approve()
        
    time.sleep(1)
