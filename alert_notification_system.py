"""
Real-Time Alert System
Push notifications and API endpoints for first responders and NGOs
"""

import json
import time
import threading
import requests
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import sqlite3
from simplified_disaster_ai import SimpleDisasterAlert, SimplifiedDisasterAI
import telebot
from twilio.rest import Client
import websockets
import asyncio
from queue import Queue
import pywhatkit as pwk  # For WhatsApp functionality
import geopy.distance
from geopy.geocoders import Nominatim

load_dotenv()

@dataclass
class AlertSubscription:
    """Alert subscription configuration with location-based targeting"""
    subscriber_id: str
    name: str
    contact_method: str  # 'email', 'sms', 'telegram', 'webhook', 'websocket', 'whatsapp'
    contact_address: str  # email, phone, telegram_id, webhook_url
    
    # Location-based filtering
    latitude: float = None  # User's location for proximity alerts
    longitude: float = None
    alert_radius_km: float = 100.0  # Alert radius in kilometers
    city: str = None
    state: str = None
    country: str = None
    
    # Filtering preferences
    disaster_types: List[str] = None  # Empty means all types
    regions: List[str] = None  # Empty means all regions
    countries: List[str] = None  # Empty means all countries
    min_confidence: float = 0.7
    min_urgency: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    alert_levels: List[str] = None  # 'info', 'warning', 'alert', 'emergency'
    
    # Notification preferences
    max_per_hour: int = 10  # Rate limiting
    quiet_hours: Dict[str, str] = None  # {'start': '22:00', 'end': '06:00'}
    language: str = 'english'
    emergency_override: bool = True  # Override quiet hours for critical alerts
    
    # Metadata
    created_at: float = None
    last_notified: float = 0
    notification_count: int = 0
    is_active: bool = True

class AlertNotificationSystem:
    """Comprehensive alert and notification system"""
    
    def __init__(self):
        """Initialize notification system with multiple channels"""
        load_dotenv()
        
        # Initialize AI system
        self.ai_system = SimplifiedDisasterAI()
        
        # Notification channels setup
        self.setup_email()
        self.setup_telegram()
        self.setup_sms()
        self.setup_whatsapp()
        self.setup_webhook()
        self.setup_geocoding()
        
        # Subscription management
        self.subscriptions: Dict[str, AlertSubscription] = {}
        self.load_subscriptions()
        
        # Alert queue for processing
        self.alert_queue = Queue()
        self.notification_threads = []
        
        # Flask API for external integrations
        self.api_app = Flask(__name__)
        self.setup_api_routes()
        
        # WebSocket connections for real-time updates
        self.websocket_clients = set()
        
        # Statistics
        self.notification_stats = {
            'total_sent': 0,
            'by_channel': {'email': 0, 'sms': 0, 'telegram': 0, 'webhook': 0, 'websocket': 0},
            'failed': 0,
            'rate_limited': 0
        }
        
        print("🚨 Alert Notification System initialized")
        print(f"   Available channels: {self.get_available_channels()}")
    
    def setup_email(self):
        """Setup email notification service"""
        try:
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
            self.email_user = os.getenv('EMAIL_USER')
            self.email_password = os.getenv('EMAIL_PASSWORD')
            
            if self.email_user and self.email_password:
                self.email_enabled = True
                print("   ✅ Email notifications enabled")
            else:
                self.email_enabled = False
                print("   ⚠️ Email notifications disabled (credentials missing)")
        except Exception as e:
            self.email_enabled = False
            print(f"   ❌ Email setup failed: {e}")
    
    def setup_telegram(self):
        """Setup Telegram bot for notifications"""
        try:
            self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if self.telegram_token:
                self.telegram_bot = telebot.TeleBot(self.telegram_token)
                self.telegram_enabled = True
                print("   ✅ Telegram notifications enabled")
            else:
                self.telegram_enabled = False
                print("   ⚠️ Telegram notifications disabled (token missing)")
        except Exception as e:
            self.telegram_enabled = False
            print(f"   ❌ Telegram setup failed: {e}")
    
    def setup_sms(self):
        """Setup SMS notifications via Twilio"""
        try:
            self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            if self.twilio_sid and self.twilio_token:
                self.twilio_client = Client(self.twilio_sid, self.twilio_token)
                self.sms_enabled = True
                print("   ✅ SMS notifications enabled")
            else:
                self.sms_enabled = False
                print("   ⚠️ SMS notifications disabled (Twilio credentials missing)")
        except Exception as e:
            self.sms_enabled = False
            print(f"   ❌ SMS setup failed: {e}")
    
    def setup_webhook(self):
        """Setup webhook notifications"""
        self.webhook_enabled = True
        print("   ✅ Webhook notifications enabled")
    
    def setup_whatsapp(self):
        """Setup WhatsApp notifications using pywhatkit"""
        try:
            # WhatsApp Web setup (requires manual QR code scan first time)
            self.whatsapp_enabled = True
            print("   ✅ WhatsApp notifications enabled")
            print("   ℹ️  Note: First-time setup requires QR code scan in WhatsApp Web")
        except Exception as e:
            self.whatsapp_enabled = False
            print(f"   ❌ WhatsApp setup failed: {e}")
    
    def setup_geocoding(self):
        """Setup geocoding service for location-based alerts"""
        try:
            self.geolocator = Nominatim(user_agent="disaster_alert_system")
            self.geocoding_enabled = True
            print("   ✅ Geocoding service enabled")
        except Exception as e:
            self.geocoding_enabled = False
            print(f"   ❌ Geocoding setup failed: {e}")
    
    def get_available_channels(self) -> List[str]:
        """Get list of available notification channels"""
        channels = ['websocket']  # Always available
        
        if self.email_enabled:
            channels.append('email')
        if self.telegram_enabled:
            channels.append('telegram')
        if self.sms_enabled:
            channels.append('sms')
        if hasattr(self, 'whatsapp_enabled') and self.whatsapp_enabled:
            channels.append('whatsapp')
        if self.webhook_enabled:
            channels.append('webhook')
        
        return channels
    
    def load_subscriptions(self):
        """Load subscriptions from database"""
        try:
            conn = sqlite3.connect('alert_subscriptions.db')
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscriber_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    contact_method TEXT NOT NULL,
                    contact_address TEXT NOT NULL,
                    disaster_types TEXT,
                    regions TEXT,
                    countries TEXT,
                    min_confidence REAL DEFAULT 0.7,
                    min_urgency TEXT DEFAULT 'medium',
                    alert_levels TEXT,
                    max_per_hour INTEGER DEFAULT 10,
                    quiet_hours TEXT,
                    language TEXT DEFAULT 'english',
                    created_at REAL,
                    last_notified REAL DEFAULT 0,
                    notification_count INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            # Load existing subscriptions
            cursor.execute('SELECT * FROM subscriptions WHERE is_active = 1')
            for row in cursor.fetchall():
                columns = [desc[0] for desc in cursor.description]
                sub_data = dict(zip(columns, row))
                
                # Parse JSON fields
                for json_field in ['disaster_types', 'regions', 'countries', 'alert_levels', 'quiet_hours']:
                    if sub_data[json_field]:
                        sub_data[json_field] = json.loads(sub_data[json_field])
                
                sub_data['is_active'] = bool(sub_data['is_active'])
                
                subscription = AlertSubscription(**sub_data)
                self.subscriptions[subscription.subscriber_id] = subscription
            
            conn.close()
            print(f"   📋 Loaded {len(self.subscriptions)} active subscriptions")
            
        except Exception as e:
            print(f"   ❌ Error loading subscriptions: {e}")
    
    def save_subscription(self, subscription: AlertSubscription):
        """Save subscription to database with proper null handling"""
        try:
            conn = sqlite3.connect('alert_subscriptions.db')
            cursor = conn.cursor()
            
            # Ensure all fields have proper defaults
            disaster_types_json = json.dumps(subscription.disaster_types) if subscription.disaster_types else json.dumps([])
            regions_json = json.dumps(subscription.regions) if subscription.regions else json.dumps([])
            countries_json = json.dumps(subscription.countries) if subscription.countries else json.dumps([])
            alert_levels_json = json.dumps(subscription.alert_levels) if subscription.alert_levels else json.dumps([])
            quiet_hours_json = json.dumps(subscription.quiet_hours) if subscription.quiet_hours else json.dumps({})
            
            min_confidence = subscription.min_confidence if subscription.min_confidence is not None else 0.7
            min_urgency = subscription.min_urgency if subscription.min_urgency else 'medium'
            max_per_hour = subscription.max_per_hour if subscription.max_per_hour is not None else 10
            language = subscription.language if subscription.language else 'english'
            created_at = subscription.created_at if subscription.created_at is not None else time.time()
            last_notified = subscription.last_notified if subscription.last_notified is not None else 0
            notification_count = subscription.notification_count if subscription.notification_count is not None else 0
            is_active = 1 if subscription.is_active else 0
            
            cursor.execute('''
                INSERT OR REPLACE INTO subscriptions VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            ''', (
                subscription.subscriber_id,
                subscription.name,
                subscription.contact_method,
                subscription.contact_address,
                disaster_types_json,
                regions_json,
                countries_json,
                min_confidence,
                min_urgency,
                alert_levels_json,
                max_per_hour,
                quiet_hours_json,
                language,
                created_at,
                last_notified,
                notification_count,
                is_active
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error saving subscription: {e}")
            import traceback
            traceback.print_exc()
    
    def subscribe(self, name: str, contact_method: str, contact_address: str, 
                 preferences: Dict = None) -> str:
        """Add new alert subscription"""
        import uuid
        
        subscriber_id = str(uuid.uuid4())
        
        subscription = AlertSubscription(
            subscriber_id=subscriber_id,
            name=name,
            contact_method=contact_method,
            contact_address=contact_address,
            created_at=time.time()
        )
        
        # Apply preferences if provided
        if preferences:
            for key, value in preferences.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
        
        self.subscriptions[subscriber_id] = subscription
        self.save_subscription(subscription)
        
        print(f"✅ New subscription added: {name} ({contact_method})")
        return subscriber_id
    
    def add_subscription(self, subscription: AlertSubscription) -> str:
        """Add subscription object directly"""
        if subscription.created_at is None:
            subscription.created_at = time.time()
        
        # Add missing attributes if needed
        if not hasattr(subscription, 'is_active'):
            subscription.is_active = True
        if not hasattr(subscription, 'last_notified'):
            subscription.last_notified = 0
        if not hasattr(subscription, 'notification_count'):
            subscription.notification_count = 0
        
        self.subscriptions[subscription.subscriber_id] = subscription
        self.save_subscription(subscription)
        print(f"✅ Subscription added: {subscription.name} ({subscription.subscriber_id})")
        return subscription.subscriber_id
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """Remove subscription"""
        if subscriber_id in self.subscriptions:
            self.subscriptions[subscriber_id].is_active = False
            self.save_subscription(self.subscriptions[subscriber_id])
            del self.subscriptions[subscriber_id]
            print(f"✅ Subscription removed: {subscriber_id}")
            return True
        return False
    
    def calculate_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two geographic coordinates in kilometers"""
        try:
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                return float('inf')  # Return infinite distance if coordinates missing
            
            coord1 = (lat1, lon1)
            coord2 = (lat2, lon2)
            return geopy.distance.distance(coord1, coord2).kilometers
        except:
            return float('inf')
    
    def get_alert_coordinates(self, alert) -> tuple:
        """Extract coordinates from alert location"""
        try:
            if hasattr(alert, 'latitude') and hasattr(alert, 'longitude'):
                return alert.latitude, alert.longitude
            
            # Try to geocode the location if coordinates not available
            if hasattr(self, 'geolocator') and alert.location:
                location = self.geolocator.geocode(alert.location)
                if location:
                    return location.latitude, location.longitude
            
            return None, None
        except:
            return None, None
    
    def should_notify_subscriber(self, subscription: AlertSubscription, alert) -> bool:
        """Check if subscriber should receive this alert"""
        # Check if subscription is active
        if not subscription.is_active:
            return False
        
        # Check minimum confidence
        if alert.confidence_score < subscription.min_confidence:
            return False
        
        # Check minimum urgency
        urgency_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        min_urgency_level = urgency_levels.get(subscription.min_urgency, 1)
        
        # Handle both simple and advanced alert types
        alert_urgency = 'high' if alert.confidence_score > 0.9 else 'medium' if alert.confidence_score > 0.7 else 'low'
        if hasattr(alert, 'urgency_level'):
            alert_urgency = alert.urgency_level
        
        alert_urgency_level = urgency_levels.get(alert_urgency, 0)
        if alert_urgency_level < min_urgency_level:
            return False
        
        # Check disaster types filter
        if subscription.disaster_types and alert.disaster_type not in subscription.disaster_types:
            return False
        
        # Location-based proximity filtering
        if subscription.latitude is not None and subscription.longitude is not None:
            alert_lat, alert_lon = self.get_alert_coordinates(alert)
            if alert_lat is not None and alert_lon is not None:
                distance_km = self.calculate_distance_km(
                    subscription.latitude, subscription.longitude,
                    alert_lat, alert_lon
                )
                if distance_km > subscription.alert_radius_km:
                    return False
        
        # City/State/Country location matching
        if subscription.city and alert.location:
            if subscription.city.lower() not in alert.location.lower():
                return False
        
        if subscription.state and hasattr(alert, 'state') and alert.state:
            if subscription.state.lower() != alert.state.lower():
                return False
        
        if subscription.country and hasattr(alert, 'country') and alert.country:
            if subscription.country.lower() != alert.country.lower():
                return False
        
        # Skip region and country filters for simple alerts
        # Check alert levels filter - use confidence-based mapping for simple alerts
        if subscription.alert_levels:
            alert_level = 'emergency' if alert.confidence_score > 0.9 else 'alert' if alert.confidence_score > 0.7 else 'warning'
            if hasattr(alert, 'alert_level'):
                alert_level = alert.alert_level
            if alert_level not in subscription.alert_levels:
                return False
        
        # Rate limiting check
        current_hour = time.time() // 3600
        last_notified_hour = getattr(subscription, 'last_notified', 0) // 3600
        
        if current_hour == last_notified_hour:
            hourly_count = getattr(subscription, '_hourly_count', 0)
            if hourly_count >= subscription.max_per_hour:
                self.notification_stats['rate_limited'] += 1
                return False
        else:
            subscription._hourly_count = 0
        
        # Quiet hours check (unless emergency override)
        if subscription.quiet_hours and not getattr(subscription, 'emergency_override', False):
            current_time = datetime.now().strftime('%H:%M')
            start_time = subscription.quiet_hours.get('start', '22:00')
            end_time = subscription.quiet_hours.get('end', '06:00')
            
            # Simple time range check - could be enhanced for timezone handling
            if start_time <= current_time or current_time <= end_time:
                # Allow critical alerts during quiet hours if emergency_override is True
                if alert.confidence_score < 0.95:
                    return False
        
        return True
    
    def format_alert_message(self, alert: SimpleDisasterAlert, language: str = 'english') -> Dict[str, str]:
        """Format alert message in specified language"""
        
        # Urgency emojis
        urgency_emojis = {
            'low': '🔵',
            'medium': '🟡', 
            'high': '🟠',
            'critical': '🔴'
        }
        
        # Alert level emojis
        level_emojis = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'alert': '🚨',
            'emergency': '🆘'
        }
        
        urgency_emoji = urgency_emojis.get(alert.urgency_level, '⚪')
        level_emoji = level_emojis.get(alert.alert_level, '📢')
        
        if language == 'english':
            subject = f"{level_emoji} {alert.alert_level.upper()}: {alert.disaster_type.title()} Alert"
            
            message = f"""
{level_emoji} DISASTER ALERT {level_emoji}

🌍 Location: {alert.formatted_address}
⚡ Type: {alert.disaster_type.title()}
{urgency_emoji} Urgency: {alert.urgency_level.upper()}
📊 Confidence: {alert.confidence_score:.1%}
⏰ Time: {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')}

📱 Source: {alert.platform.title()}
👤 Reporter: {alert.author}
{'✅ Verified' if alert.is_genuine else '⚠️ Unverified'}

📄 Report:
{alert.content}

🆔 Alert ID: {alert.alert_id[:8]}

---
🌍 Disaster Alert System
Real-time monitoring powered by AI
"""
        
        # Add other languages as needed
        else:
            subject = f"{level_emoji} ALERT: {alert.disaster_type.title()}"
            message = f"{level_emoji} {alert.disaster_type.title()} in {alert.formatted_address}\nConfidence: {alert.confidence_score:.1%}\n\n{alert.content}"
        
        return {
            'subject': subject,
            'message': message
        }
    
    def send_email_notification(self, subscription: AlertSubscription, alert: SimpleDisasterAlert):
        """Send email notification"""
        if not self.email_enabled:
            return False
        
        try:
            formatted = self.format_alert_message(alert, subscription.language)
            
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = subscription.contact_address
            msg['Subject'] = formatted['subject']
            
            msg.attach(MIMEText(formatted['message'], 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            self.notification_stats['by_channel']['email'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Email notification failed: {e}")
            return False
    
    def send_telegram_notification(self, subscription: AlertSubscription, alert: SimpleDisasterAlert):
        """Send Telegram notification"""
        if not self.telegram_enabled:
            return False
        
        try:
            formatted = self.format_alert_message(alert, subscription.language)
            
            self.telegram_bot.send_message(
                chat_id=subscription.contact_address,
                text=formatted['message'],
                parse_mode='Markdown'
            )
            
            self.notification_stats['by_channel']['telegram'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Telegram notification failed: {e}")
            return False
    
    def send_sms_notification(self, subscription: AlertSubscription, alert: SimpleDisasterAlert):
        """Send SMS notification"""
        if not self.sms_enabled:
            return False
        
        try:
            formatted = self.format_alert_message(alert, subscription.language)
            
            # Truncate for SMS length limit
            sms_message = formatted['message'][:160] + "..." if len(formatted['message']) > 160 else formatted['message']
            
            self.twilio_client.messages.create(
                body=sms_message,
                from_=self.twilio_phone,
                to=subscription.contact_address
            )
            
            self.notification_stats['by_channel']['sms'] += 1
            return True
            
        except Exception as e:
            print(f"❌ SMS notification failed: {e}")
            return False
    
    def send_whatsapp_notification(self, subscription: AlertSubscription, alert):
        """Send WhatsApp message notification"""
        if not hasattr(self, 'whatsapp_enabled') or not self.whatsapp_enabled:
            return False
        
        try:
            formatted = self.format_alert_message(alert, subscription.language)
            
            # Format phone number for WhatsApp (must include country code)
            phone_number = subscription.contact_address
            if not phone_number.startswith('+'):
                phone_number = '+' + phone_number.replace('-', '').replace(' ', '')
            
            # Enhanced message with disaster details
            whatsapp_message = f"""🚨 DISASTER ALERT 🚨

{formatted['subject']}

📍 Location: {alert.location}
📊 Confidence: {alert.confidence_score:.0%}
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{formatted['message']}

Stay safe and follow local emergency guidelines!

---
Disaster Alert System"""
            
            # Send WhatsApp message instantly (current time)
            import datetime as dt
            now = dt.datetime.now()
            
            # Use pywhatkit to send WhatsApp message
            pwk.sendwhatmsg(phone_number, whatsapp_message, now.hour, now.minute + 1)
            
            self.notification_stats['by_channel']['whatsapp'] = self.notification_stats['by_channel'].get('whatsapp', 0) + 1
            print(f"✅ WhatsApp message scheduled for {phone_number}")
            return True
            
        except Exception as e:
            print(f"❌ WhatsApp notification failed: {e}")
            return False
    
    def send_webhook_notification(self, subscription: AlertSubscription, alert: SimpleDisasterAlert):
        """Send webhook notification"""
        try:
            payload = {
                'alert': asdict(alert),
                'timestamp': time.time(),
                'subscriber': subscription.subscriber_id
            }
            
            response = requests.post(
                subscription.contact_address,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.notification_stats['by_channel']['webhook'] += 1
                return True
            else:
                print(f"❌ Webhook failed with status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Webhook notification failed: {e}")
            return False
    
    async def send_websocket_notification(self, alert: SimpleDisasterAlert):
        """Send WebSocket notification to all connected clients"""
        if not self.websocket_clients:
            return
        
        try:
            payload = json.dumps({
                'type': 'disaster_alert',
                'alert': asdict(alert),
                'timestamp': time.time()
            })
            
            # Send to all connected clients
            disconnected = set()
            for client in self.websocket_clients:
                try:
                    await client.send(payload)
                    self.notification_stats['by_channel']['websocket'] += 1
                except:
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
            
        except Exception as e:
            print(f"❌ WebSocket notification failed: {e}")
    
    def process_alert_notifications(self, alert: SimpleDisasterAlert):
        """Process notifications for a single alert"""
        notifications_sent = 0
        
        for subscription in self.subscriptions.values():
            if self.should_notify_subscriber(subscription, alert):
                success = False
                
                # Send via appropriate channel
                if subscription.contact_method == 'email':
                    success = self.send_email_notification(subscription, alert)
                elif subscription.contact_method == 'telegram':
                    success = self.send_telegram_notification(subscription, alert)
                elif subscription.contact_method == 'sms':
                    success = self.send_sms_notification(subscription, alert)
                elif subscription.contact_method == 'whatsapp':
                    success = self.send_whatsapp_notification(subscription, alert)
                elif subscription.contact_method == 'webhook':
                    success = self.send_webhook_notification(subscription, alert)
                
                if success:
                    # Update subscription stats
                    subscription.last_notified = time.time()
                    subscription.notification_count += 1
                    subscription._hourly_count = getattr(subscription, '_hourly_count', 0) + 1
                    self.save_subscription(subscription)
                    notifications_sent += 1
                    self.notification_stats['total_sent'] += 1
                else:
                    self.notification_stats['failed'] += 1
        
        # Send WebSocket notifications
        asyncio.run(self.send_websocket_notification(alert))
        
        print(f"📤 Sent {notifications_sent} notifications for {alert.disaster_type} in {alert.formatted_address}")
        return notifications_sent
    
    def setup_api_routes(self):
        """Setup Flask API routes for external integration"""
        
        @self.api_app.route('/api/subscribe', methods=['POST'])
        def api_subscribe():
            """API endpoint to add new subscription"""
            try:
                data = request.get_json()
                
                required_fields = ['name', 'contact_method', 'contact_address']
                for field in required_fields:
                    if field not in data:
                        return jsonify({'error': f'Missing required field: {field}'}), 400
                
                preferences = {k: v for k, v in data.items() if k not in required_fields}
                subscriber_id = self.subscribe(
                    data['name'],
                    data['contact_method'], 
                    data['contact_address'],
                    preferences
                )
                
                return jsonify({
                    'success': True,
                    'subscriber_id': subscriber_id,
                    'message': 'Subscription created successfully'
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.api_app.route('/api/unsubscribe/<subscriber_id>', methods=['DELETE'])
        def api_unsubscribe(subscriber_id):
            """API endpoint to remove subscription"""
            if self.unsubscribe(subscriber_id):
                return jsonify({'success': True, 'message': 'Subscription removed'})
            else:
                return jsonify({'error': 'Subscription not found'}), 404
        
        @self.api_app.route('/api/alerts', methods=['GET'])
        def api_get_alerts():
            """API endpoint to get recent alerts"""
            try:
                hours = int(request.args.get('hours', 24))
                min_confidence = float(request.args.get('min_confidence', 0.5))
                
                alerts = self.ai_system.get_active_alerts(hours=hours, min_confidence=min_confidence)
                
                return jsonify({
                    'success': True,
                    'count': len(alerts),
                    'alerts': [asdict(alert) for alert in alerts]
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.api_app.route('/api/stats', methods=['GET'])
        def api_get_stats():
            """API endpoint to get notification statistics"""
            return jsonify({
                'success': True,
                'notification_stats': self.notification_stats,
                'active_subscriptions': len(self.subscriptions),
                'available_channels': self.get_available_channels()
            })
        
        @self.api_app.route('/api/test_alert', methods=['POST'])
        def api_test_alert():
            """API endpoint to send test alert"""
            if request.args.get('key') != os.getenv('API_TEST_KEY', 'test123'):
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Create test alert
            test_alert = SimpleDisasterAlert(
                alert_id="test_" + str(int(time.time())),
                platform="api_test",
                post_id="test",
                content="This is a test disaster alert to verify notification system.",
                author="System",
                timestamp=time.time(),
                disaster_type="test",
                confidence_score=1.0,
                urgency_level="high",
                severity_score=0.8,
                country="Test Country",
                state_province="Test State",
                city="Test City",
                coordinates={"lat": 0.0, "lon": 0.0},
                location_confidence=1.0,
                formatted_address="Test City, Test State, Test Country",
                language="english",
                sentiment_score=0.0,
                is_genuine=True,
                is_rumor=False,
                misinformation_risk=0.0,
                engagement_score=0.5,
                viral_potential=0.3,
                verification_status="verified",
                verification_sources=["system_test"],
                alert_level="alert",
                created_at=time.time(),
                updated_at=time.time(),
                related_alerts=[],
                media_urls=[],
                hashtags=["test"],
                mentions=[]
            )
            
            notifications_sent = self.process_alert_notifications(test_alert)
            
            return jsonify({
                'success': True,
                'message': 'Test alert sent',
                'notifications_sent': notifications_sent
            })
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.websocket_clients.add(websocket)
        print(f"🔌 New WebSocket client connected. Total: {len(self.websocket_clients)}")
        
        try:
            await websocket.wait_closed()
        finally:
            self.websocket_clients.remove(websocket)
            print(f"🔌 WebSocket client disconnected. Total: {len(self.websocket_clients)}")
    
    def start_background_services(self):
        """Start background services"""
        # Start Flask API
        api_thread = threading.Thread(
            target=lambda: self.api_app.run(host='0.0.0.0', port=5000, debug=False),
            daemon=True
        )
        api_thread.start()
        print("🌐 API server started on http://0.0.0.0:5000")
        
        # Start WebSocket server
        try:
            websocket_thread = threading.Thread(
                target=lambda: asyncio.run(
                    websockets.serve(self.websocket_handler, "localhost", 8765)
                ),
                daemon=True
            )
            websocket_thread.start()
            print("🔌 WebSocket server started on ws://localhost:8765")
        except Exception as e:
            print(f"⚠️ WebSocket server failed to start: {e}")
    
    def monitor_and_notify(self):
        """Main monitoring loop"""
        print("🔄 Starting alert monitoring and notification service...")
        
        # Start background services
        self.start_background_services()
        
        last_check = time.time()
        
        try:
            while True:
                current_time = time.time()
                
                # Check for new alerts every 30 seconds
                if current_time - last_check >= 30:
                    try:
                        # Get recent alerts
                        recent_alerts = self.ai_system.get_active_alerts(hours=1, min_confidence=0.3)
                        
                        # Process new alerts (simplified - in real implementation, track processed alerts)
                        for alert in recent_alerts:
                            if alert.timestamp > last_check:
                                self.process_alert_notifications(alert)
                        
                        last_check = current_time
                        
                    except Exception as e:
                        print(f"❌ Error in monitoring loop: {e}")
                
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Alert monitoring stopped by user")

# Test the notification system
if __name__ == "__main__":
    print("🧪 TESTING ALERT NOTIFICATION SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize notification system
        alert_system = AlertNotificationSystem()
        
        # Add test subscriptions
        test_subscribers = [
            {
                'name': 'Emergency Response Team',
                'contact_method': 'email',
                'contact_address': 'emergency@example.com',
                'preferences': {
                    'min_confidence': 0.8,
                    'min_urgency': 'high',
                    'alert_levels': ['alert', 'emergency']
                }
            },
            {
                'name': 'NGO Worker',
                'contact_method': 'telegram',
                'contact_address': '123456789',  # Telegram chat ID
                'preferences': {
                    'disaster_types': ['earthquake', 'flood', 'fire'],
                    'countries': ['India', 'Nepal', 'Bangladesh']
                }
            }
        ]
        
        for subscriber in test_subscribers:
            prefs = subscriber.pop('preferences', {})
            subscriber_id = alert_system.subscribe(**subscriber, preferences=prefs)
            print(f"✅ Added subscriber: {subscriber['name']} (ID: {subscriber_id[:8]}...)")
        
        print(f"\n📊 System Status:")
        print(f"   Active subscriptions: {len(alert_system.subscriptions)}")
        print(f"   Available channels: {alert_system.get_available_channels()}")
        print(f"   Notification stats: {alert_system.notification_stats}")
        
        # Start monitoring (this will run until interrupted)
        print(f"\n🚀 Starting monitoring service...")
        print(f"   API: http://localhost:5000")
        print(f"   WebSocket: ws://localhost:8765")
        print(f"   Press Ctrl+C to stop")
        
        alert_system.monitor_and_notify()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
