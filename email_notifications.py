import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

REGION_EMAILS = {
    'asia': 'vihaan.ovalekar@gmail.com',
    'europe': 'electroknight999@gmail.com', 
    'north_america': 'yashpradhan0712@gmail.com',
    'south_america': 'southamerica-alerts@disasterwatch.org',
    'africa': 'africa-alerts@disasterwatch.org',
    'oceania': 'oceania-alerts@disasterwatch.org',
    'antarctica': 'antarctica-alerts@disasterwatch.org'
}

def send_disaster_alert_email(disaster_info, submission):
    try:
        region = disaster_info.get('region', '').lower()
        recipient_email = REGION_EMAILS.get(region, 'global-alerts@disasterwatch.org')
        
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL', 'bot@disasterwatch.org')
        sender_password = os.getenv('SENDER_PASSWORD', 'your_app_password')
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"DISASTER ALERT: {disaster_info.get('disaster_type', 'Unknown').title()} in {disaster_info.get('place', 'Unknown Location')}"
        
        urgency_text = {
            1: "LOW",
            2: "MODERATE", 
            3: "HIGH"
        }.get(disaster_info.get('urgency_level', 1), "UNKNOWN")
        
        body = f"""
DISASTER ALERT NOTIFICATION

LOCATION: {disaster_info.get('place', 'Unknown')}
REGION: {disaster_info.get('region', 'Unknown').title()}
DISASTER TYPE: {disaster_info.get('disaster_type', 'Unknown').title()}
URGENCY LEVEL: {urgency_text} ({disaster_info.get('urgency_level', 'Unknown')}/3)
CONFIDENCE LEVEL: {disaster_info.get('confidence_level', 'Unknown')}/10

POST DETAILS:
Title: {submission.title}
Author: {submission.author}
Reddit URL: https://reddit.com{submission.permalink}

SOURCES FOR VERIFICATION:
{chr(10).join([f"- {source}" for source in disaster_info.get('sources', [])])}

This alert was automatically generated from Reddit post analysis.
Please verify the information through official channels before taking action.

---
Disaster Watch Alert System
"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"✅ Email alert sent to {recipient_email} for {region} region")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Email authentication failed: {e}")
        print("💡 Gmail requires an App Password. Please:")
        print("   1. Enable 2-factor authentication on Gmail")
        print("   2. Generate an App Password at https://myaccount.google.com/apppasswords")
        print("   3. Update SENDER_PASSWORD in .env with the App Password")
        return False
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")
        return False

def send_test_email():
    test_disaster_info = {
        'place': 'Mumbai, India',
        'region': 'asia',
        'disaster_type': 'flood',
        'urgency_level': 3,
        'confidence_level': 8,
        'sources': ['Mumbai flood 2025 news', 'Maharashtra weather alert']
    }
    
    class MockSubmission:
        def __init__(self):
            self.title = "Test Flood Alert in Mumbai"
            self.author = "test_user"
            self.permalink = "/r/disasterhazards/test_post"
    
    mock_submission = MockSubmission()
    return send_disaster_alert_email(test_disaster_info, mock_submission)

def get_region_email(region):
    return REGION_EMAILS.get(region.lower(), 'global-alerts@disasterwatch.org')

def list_all_region_emails():
    print("Regional Email Configuration:")
    for region, email in REGION_EMAILS.items():
        print(f"  {region.title()}: {email}")
    print(f"  Default/Global: global-alerts@disasterwatch.org")
