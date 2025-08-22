"""
Social Media Disaster Alert System - Multi-Platform Monitor
Real-time ingestion from Twitter/X, Reddit, and other social media platforms
"""

import tweepy
import praw
import requests
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import pytz
import re
import hashlib

load_dotenv()

@dataclass
class SocialMediaPost:
    """Standardized social media post structure"""
    platform: str  # 'twitter', 'reddit', 'telegram', etc.
    post_id: str
    content: str
    author: str
    timestamp: float
    location_raw: Optional[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    url: str = ""
    media_urls: List[str] = None
    engagement: Dict = None  # likes, retweets, comments
    verified_account: bool = False
    follower_count: int = 0

class SocialMediaMonitor:
    """Multi-platform social media monitor for disaster-related content"""
    
    def __init__(self, config_file: str = ".env"):
        """Initialize with API credentials"""
        load_dotenv(config_file)
        
        # Gemini AI setup
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        self.gemini_client = genai.Client(api_key=self.api_key)
        
        # Platform-specific setup
        self.twitter_api = None
        self.reddit_api = None
        
        self._setup_twitter()
        self._setup_reddit()
        
        # Disaster-related keywords for monitoring
        self.disaster_keywords = [
            'earthquake', 'flood', 'fire', 'hurricane', 'tornado', 'landslide',
            'tsunami', 'drought', 'cyclone', 'storm', 'volcanic', 'avalanche',
            'wildfire', 'bushfire', 'typhoon', 'blizzard', 'heatwave', 'coldwave',
            'emergency', 'disaster', 'evacuation', 'rescue', 'damaged', 'destroyed',
            'collapsed', 'injured', 'casualties', 'survivors', 'relief', 'aid',
            # Regional/Language variations
            'भूकंप', 'बाढ़', 'आग', 'तूफान', 'सुनामी',  # Hindi
            'terremoto', 'inundación', 'incendio', 'huracán',  # Spanish
            'tremblement', 'inondation', 'incendie', 'ouragan',  # French
        ]
        
        # Location extraction patterns
        self.location_patterns = [
            r'\b(?:in|at|near|from|@)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
            r'#([A-Za-z]+(?:[A-Z][a-z]+)*)',  # Hashtag locations
        ]
        
        print("🌐 Social Media Monitor initialized")
        print(f"   Tracking platforms: {'Twitter' if self.twitter_api else 'No Twitter'}, {'Reddit' if self.reddit_api else 'No Reddit'}")
        print(f"   Monitoring {len(self.disaster_keywords)} disaster keywords")
    
    def _setup_twitter(self):
        """Setup Twitter API v2 with Bearer Token (Free tier)"""
        try:
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if bearer_token:
                self.twitter_api = tweepy.Client(bearer_token=bearer_token)
                print("✅ Twitter API initialized")
            else:
                print("⚠️  Twitter Bearer Token not found - Twitter monitoring disabled")
        except Exception as e:
            print(f"❌ Twitter API setup failed: {e}")
    
    def _setup_reddit(self):
        """Setup Reddit API"""
        try:
            self.reddit_api = praw.Reddit(
                client_id=os.getenv('YOUR_CLIENT_ID'),
                client_secret=os.getenv('YOUR_CLIENT_SECRET'),
                username=os.getenv('YOUR_USERNAME'),
                password=os.getenv('YOUR_PASSWORD'),
                user_agent='DisasterMonitor/2.0'
            )
            print("✅ Reddit API initialized")
        except Exception as e:
            print(f"❌ Reddit API setup failed: {e}")
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#(\w+)', text)
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        return re.findall(r'@(\w+)', text)
    
    def extract_locations_from_text(self, text: str) -> List[str]:
        """Extract potential locations from text using regex patterns"""
        locations = []
        
        for pattern in self.location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if isinstance(matches[0], tuple) if matches else False:
                locations.extend([' '.join(match) for match in matches])
            else:
                locations.extend(matches)
        
        # Clean and filter locations
        cleaned_locations = []
        for loc in locations:
            cleaned = loc.strip().title()
            if len(cleaned) > 2 and cleaned not in cleaned_locations:
                cleaned_locations.append(cleaned)
        
        return cleaned_locations
    
    def classify_disaster_content(self, post: SocialMediaPost) -> Dict:
        """Classify if content is disaster-related and extract details"""
        system_instruction = """You are an advanced disaster intelligence AI. Analyze social media posts for disaster information and return JSON with these fields:

REQUIRED FIELDS:
- is_disaster_related: true/false - Is this about a real disaster/emergency?
- confidence_score: 0.0-1.0 - How confident are you this is genuine disaster content?
- disaster_type: Type of disaster (earthquake, flood, fire, hurricane, tornado, landslide, tsunami, drought, cyclone, storm, volcanic, etc.)
- urgency_level: 'low', 'medium', 'high', 'critical' - How urgent is the situation?
- is_rumor: true/false - Does this appear to be a rumor or unverified information?
- is_genuine: true/false - Does this appear to be a genuine report (not fake/satire)?
- location_extracted: Best guess at location mentioned
- severity_indicators: List of words/phrases indicating severity (injured, deaths, destroyed, etc.)
- time_sensitivity: 'real-time', 'recent', 'historical', 'future' - When is this happening?
- sentiment_score: -1.0 to 1.0 - Emotional tone (-1=very negative, 0=neutral, 1=positive)
- language_detected: Language of the content (en, hi, es, fr, etc.)

CLASSIFICATION RULES:
- Real disasters: actual events happening now or recently
- High confidence: specific location + disaster type + recent time indicators
- Low confidence: vague mentions, old news, or unclear context
- Mark as rumor if: "I heard", "someone said", "reportedly", no source
- Mark as fake if: clearly satirical, joke, meme, or promotional content
- Urgency based on: immediate danger, ongoing situation, need for help

Examples:
- "Major earthquake hits Tokyo, buildings collapsed, many injured" -> disaster_related=true, confidence=0.95, urgency='critical'
- "I think there might be a flood somewhere" -> disaster_related=true, confidence=0.2, is_rumor=true, urgency='low'
- "Buy our disaster insurance now!" -> disaster_related=false, confidence=0.0

Return only valid JSON, no markdown formatting."""
        
        # Prepare content with metadata
        content_with_context = f"""
Platform: {post.platform}
Content: {post.content}
Author: {post.author} (Verified: {post.verified_account})
Hashtags: {', '.join(post.hashtags or [])}
Location Raw: {post.location_raw or 'None'}
Engagement: {post.engagement or {}}
"""
        
        try:
            result = self._call_gemini_api(content_with_context, system_instruction)
            if result:
                return result
        except Exception as e:
            print(f"❌ Error in disaster classification: {e}")
        
        # Fallback classification
        return {
            'is_disaster_related': False,
            'confidence_score': 0.0,
            'disaster_type': 'unknown',
            'urgency_level': 'low',
            'is_rumor': True,
            'is_genuine': False,
            'location_extracted': post.location_raw or '',
            'severity_indicators': [],
            'time_sensitivity': 'unknown',
            'sentiment_score': 0.0,
            'language_detected': 'unknown'
        }
    
    def enhanced_location_extraction(self, post: SocialMediaPost, classification: Dict) -> Dict:
        """Enhanced location extraction using AI and multiple methods"""
        system_instruction = """You are a geographic intelligence specialist. Extract detailed location information from social media posts and return JSON with these fields:

REQUIRED FIELDS:
- country: Full country name
- state_province: State, province, or administrative region
- city: City, town, or locality
- coordinates: {"lat": latitude, "lon": longitude} if determinable, null otherwise
- region: Continental region (asia, europe, north_america, south_america, africa, oceania, antarctica)
- location_confidence: 0.0-1.0 - How confident are you about the location?
- location_source: 'text', 'hashtags', 'user_profile', 'metadata', 'inferred'
- alternative_locations: List of other possible locations if ambiguous
- formatted_address: "City, State, Country" format

EXTRACTION RULES:
- Use all available context: content, hashtags, user location
- For ambiguous cities, consider context clues
- If multiple locations mentioned, choose the most relevant to the disaster
- Coordinate estimation only for major cities/landmarks you're certain about
- Mark confidence low if location is vague or ambiguous

Examples:
- "Earthquake in Mumbai today" -> {"country": "India", "city": "Mumbai", "state_province": "Maharashtra", "region": "asia"}
- "#TokyoEarthquake trending" -> {"country": "Japan", "city": "Tokyo", "region": "asia", "location_source": "hashtags"}
- "Flood here in downtown" -> {"location_confidence": 0.1, "city": "", "location_source": "text"}

Return only valid JSON, no markdown formatting."""
        
        # Prepare content with all location clues
        location_context = f"""
Content: {post.content}
Hashtags: {', '.join(post.hashtags or [])}
Extracted Locations from Text: {', '.join(self.extract_locations_from_text(post.content))}
Raw Location Data: {post.location_raw or 'None'}
Disaster Type: {classification.get('disaster_type', 'unknown')}
Platform: {post.platform}
"""
        
        try:
            result = self._call_gemini_api(location_context, system_instruction)
            if result:
                return result
        except Exception as e:
            print(f"❌ Error in location extraction: {e}")
        
        # Fallback location extraction
        text_locations = self.extract_locations_from_text(post.content)
        return {
            'country': 'Unknown',
            'state_province': 'Unknown',
            'city': text_locations[0] if text_locations else 'Unknown',
            'coordinates': None,
            'region': 'unknown',
            'location_confidence': 0.2 if text_locations else 0.0,
            'location_source': 'text' if text_locations else 'none',
            'alternative_locations': text_locations[1:] if len(text_locations) > 1 else [],
            'formatted_address': ', '.join(filter(None, text_locations[:3])) if text_locations else 'Unknown'
        }
    
    def _call_gemini_api(self, text: str, system_instruction: str, model_name: str = "gemini-2.5-flash") -> Optional[Dict]:
        """Call Gemini API with error handling"""
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            system_instruction=[types.Part.from_text(text=system_instruction)],
        )
        
        try:
            response_chunks = []
            for chunk in self.gemini_client.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=generate_content_config,
            ):
                response_chunks.append(chunk.text)
            
            response_text = ''.join(response_chunks).strip()
            
            # Clean JSON response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
                
            return json.loads(response_text)
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return None
    
    def monitor_twitter_stream(self, callback_func) -> None:
        """Monitor Twitter for disaster-related tweets (requires Twitter API v2)"""
        if not self.twitter_api:
            print("❌ Twitter API not available")
            return
        
        try:
            # Note: Twitter API v2 Free tier has limited streaming
            # For production, you'd need elevated access
            print("🐦 Starting Twitter monitoring (simulated)...")
            
            # This is a placeholder - real implementation would use Twitter API v2 streaming
            # For demo purposes, we'll search recent tweets instead
            
            query = ' OR '.join(self.disaster_keywords[:10])  # Limit query length
            tweets = self.twitter_api.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                user_fields=['verified', 'public_metrics']
            )
            
            if tweets.data:
                for tweet in tweets.data:
                    try:
                        # Convert to standardized format
                        post = SocialMediaPost(
                            platform='twitter',
                            post_id=tweet.id,
                            content=tweet.text,
                            author=str(tweet.author_id),
                            timestamp=tweet.created_at.timestamp() if tweet.created_at else time.time(),
                            hashtags=self.extract_hashtags(tweet.text),
                            mentions=self.extract_mentions(tweet.text),
                            url=f"https://twitter.com/i/status/{tweet.id}",
                            engagement=tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                        )
                        
                        callback_func(post)
                        
                    except Exception as e:
                        print(f"❌ Error processing tweet: {e}")
                        
        except Exception as e:
            print(f"❌ Twitter monitoring error: {e}")
    
    def monitor_reddit_stream(self, callback_func, subreddits: List[str] = None) -> None:
        """Monitor Reddit for disaster-related posts"""
        if not self.reddit_api:
            print("❌ Reddit API not available")
            return
        
        if not subreddits:
            subreddits = ['disasterhazards', 'worldnews', 'news', 'emergencyservices', 'preppers']
        
        try:
            print(f"📱 Starting Reddit monitoring on: {', '.join(subreddits)}")
            
            # Monitor multiple subreddits
            subreddit_str = '+'.join(subreddits)
            subreddit = self.reddit_api.subreddit(subreddit_str)
            
            for submission in subreddit.stream.submissions(skip_existing=True):
                try:
                    # Check if disaster-related
                    content = submission.title + " " + (submission.selftext or "")
                    
                    # Quick keyword check before full processing
                    if any(keyword.lower() in content.lower() for keyword in self.disaster_keywords):
                        post = SocialMediaPost(
                            platform='reddit',
                            post_id=submission.id,
                            content=content,
                            author=str(submission.author) if submission.author else 'deleted',
                            timestamp=submission.created_utc,
                            url=f"https://reddit.com{submission.permalink}",
                            engagement={
                                'score': submission.score,
                                'upvote_ratio': submission.upvote_ratio,
                                'num_comments': submission.num_comments
                            }
                        )
                        
                        callback_func(post)
                        
                except Exception as e:
                    print(f"❌ Error processing Reddit post: {e}")
                    
        except Exception as e:
            print(f"❌ Reddit monitoring error: {e}")
    
    def generate_post_hash(self, post: SocialMediaPost) -> str:
        """Generate unique hash for post to avoid duplicates"""
        content_str = f"{post.platform}_{post.content}_{post.author}_{post.timestamp}"
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def start_monitoring(self, callback_func, platforms: List[str] = ['reddit']) -> None:
        """Start monitoring specified platforms"""
        print("🚀 Starting Social Media Disaster Monitoring...")
        print(f"   Platforms: {', '.join(platforms)}")
        print(f"   Keywords: {len(self.disaster_keywords)} disaster-related terms")
        
        threads = []
        
        if 'twitter' in platforms and self.twitter_api:
            twitter_thread = threading.Thread(
                target=self.monitor_twitter_stream, 
                args=(callback_func,),
                daemon=True
            )
            twitter_thread.start()
            threads.append(twitter_thread)
        
        if 'reddit' in platforms and self.reddit_api:
            reddit_thread = threading.Thread(
                target=self.monitor_reddit_stream, 
                args=(callback_func,),
                daemon=True
            )
            reddit_thread.start()
            threads.append(reddit_thread)
        
        print(f"✅ Monitoring started with {len(threads)} active threads")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(10)
                print(f"📊 Monitoring active... (Threads: {len([t for t in threads if t.is_alive()])})")
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

# Test the social media monitor
if __name__ == "__main__":
    print("🧪 TESTING SOCIAL MEDIA MONITOR")
    print("=" * 50)
    
    def test_callback(post: SocialMediaPost):
        """Test callback function for processing posts"""
        print(f"\n📨 NEW POST DETECTED:")
        print(f"   Platform: {post.platform}")
        print(f"   Author: {post.author}")
        print(f"   Content: {post.content[:100]}...")
        print(f"   Hashtags: {post.hashtags}")
        print(f"   URL: {post.url}")
        
        # Initialize monitor and process post
        monitor = SocialMediaMonitor()
        
        # Classify the content
        classification = monitor.classify_disaster_content(post)
        print(f"   🤖 AI Classification:")
        print(f"      Disaster Related: {classification['is_disaster_related']}")
        print(f"      Confidence: {classification['confidence_score']:.2f}")
        print(f"      Type: {classification['disaster_type']}")
        print(f"      Urgency: {classification['urgency_level']}")
        print(f"      Genuine: {classification['is_genuine']}")
        
        if classification['is_disaster_related'] and classification['confidence_score'] > 0.5:
            # Extract location
            location = monitor.enhanced_location_extraction(post, classification)
            print(f"   📍 Location Extraction:")
            print(f"      Address: {location['formatted_address']}")
            print(f"      Country: {location['country']}")
            print(f"      Confidence: {location['location_confidence']:.2f}")
    
    try:
        # Initialize monitor
        monitor = SocialMediaMonitor()
        
        # Start monitoring (will run until interrupted)
        monitor.start_monitoring(
            callback_func=test_callback,
            platforms=['reddit']  # Start with Reddit only for testing
        )
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()