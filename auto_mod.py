import praw
import os
import time
from dotenv import load_dotenv
from analysis import get_indian_timestamp, call_gemini_api, extract_disaster_info
from database import store_analysis
from email_notifications import send_disaster_alert_email

def initialize_reddit():
    load_dotenv()
    
    reddit = praw.Reddit(
        client_id=os.getenv('YOUR_CLIENT_ID'),
        client_secret=os.getenv('YOUR_CLIENT_SECRET'),
        username=os.getenv('YOUR_USERNAME'),
        password=os.getenv('YOUR_PASSWORD'),
        user_agent='BrandPromoLocationBot/1.0'
    )
    
    try:
        username = reddit.user.me()
        print(f"Authenticated as: {username}")
        
        subreddit = reddit.subreddit('disasterhazards')
        moderators = [mod.name for mod in subreddit.moderator()]
        
        if str(username) in moderators:
            print("✅ Moderator permissions confirmed")
        else:
            print("⚠️ No moderator permissions - posts cannot be removed/approved")
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None
    
    return reddit

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

def process_single_post(submission):
    print(f"\n--- Processing Post ---")
    print(f"Title: {submission.title}")
    print(f"Author: {submission.author}")
    print(f"URL: https://reddit.com{submission.permalink}")
    
    timestamp_info = get_indian_timestamp(submission)
    print(f"Posted: {timestamp_info['formatted_ist']}")
    
    content = submission.title + " " + (submission.selftext or "")
    has_city, has_location, is_promo = check_post_moderation(content)
    
    print(f"Analysis - City: {has_city}, Location: {has_location}, Promotion: {is_promo}")
    
    approved = False
    
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
        
        disaster_info = {}
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
        
        if disaster_info['confidence_level'] <= 4:
            print(f"REJECTED: Low confidence level ({disaster_info['confidence_level']}/10)")
            removal_message = f"Your post was removed due to low credibility score ({disaster_info['confidence_level']}/10). Unable to verify the disaster information from reliable sources."
            submission.mod.remove()
            submission.mod.send_removal_message(
                message=removal_message,
                type="public"
            )
            approved = False
        else:
            submission.mod.approve()
            approved = True
            print(f"📧 Sending email alert to {disaster_info.get('region', 'unknown')} region...")
            send_disaster_alert_email(disaster_info, submission)
    
    store_analysis(submission, disaster_info, approved)
    return approved

def process_existing_posts(reddit, subreddit_name, limit=25):
    print(f"\nStarting auto-moderation for r/{subreddit_name}")
    print("Checking existing unmoderated posts first...")
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        print("Scanning recent posts...")
        for submission in subreddit.new(limit=limit):
            if submission.approved or submission.removed:
                continue
            
            process_single_post(submission)
            time.sleep(2)
            
    except Exception as e:
        print(f"Error processing existing posts: {e}")

def monitor_new_posts(reddit, subreddit_name):
    print("\nNow monitoring for new posts...")
    
    for submission in reddit.subreddit(subreddit_name).stream.submissions(skip_existing=True):
        process_single_post(submission)
        time.sleep(1)
