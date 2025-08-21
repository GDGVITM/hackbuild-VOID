# Disaster Hazards Auto-Moderation Bot

An intelligent Reddit moderation bot for disaster hazard subreddits that automatically approves or removes posts based on location content and promotional filtering.

## Features

- **Automated Content Moderation**: Analyzes posts for city/location information and promotional content
- **Disaster Intelligence**: Extracts detailed disaster information from approved posts
- **Real-time Processing**: Monitors both existing and new posts
- **AI-Powered Analysis**: Uses Google Gemini AI for content analysis

## Requirements

- Python 3.8+
- Reddit API credentials
- Google Gemini API key

## Installation

1. Install required packages:
```bash
pip install praw python-dotenv google-generativeai
```

2. Create a `.env` file with your credentials:
```
GEMINI_API_KEY=your_gemini_api_key
YOUR_CLIENT_ID=your_reddit_client_id
YOUR_CLIENT_SECRET=your_reddit_client_secret
YOUR_USERNAME=your_reddit_username
YOUR_PASSWORD=your_reddit_password
```

## Usage

Run the auto-moderation bot:
```bash
python auto_mod.py
```

The bot will:
1. Check existing unmoderated posts
2. Monitor for new posts in real-time
3. Approve posts with proper location information
4. Remove promotional content or posts lacking location data
5. Extract disaster intelligence from approved posts

## Post Approval Criteria

Posts are **approved** if they:
- Mention a specific city name
- Include location information (village, state, country)
- Are not promotional content

Posts are **rejected** if they:
- Promote brands/products/services
- Lack city information
- Lack location information

## Disaster Intelligence

For approved posts, the bot extracts:
- **Place**: Specific location (City, Country format)
- **Region**: Continental region (asia, europe, etc.)
- **Disaster Type**: Type of disaster (earthquake, flood, fire, etc.)

## Files

- `auto_mod.py` - Main auto-moderation script
- `reddit.py` - Reddit post fetcher (15-minute window)
- `.env` - Environment variables (ignored by git)
- `.gitignore` - Git ignore configuration

## Configuration

The bot is configured for the `disasterhazards` subreddit. To change the target subreddit, modify the `subreddit_name` variable in `auto_mod.py`.

## API Functions

### Core Functions
- `call_gemini_api(text, system_instruction, model_name)` - Reusable Gemini API interface
- `check_post_moderation(text)` - Moderation decision analysis
- `extract_disaster_info(text)` - Disaster information extraction

These functions can be imported and reused in other projects.
