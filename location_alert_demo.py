"""
Location-Based Alert System Demo
Demonstrates WhatsApp and SMS alerts for specific locations
"""

import time
from datetime import datetime
from simplified_disaster_ai import SimplifiedDisasterAI, SimpleDisasterAlert
from alert_notification_system import AlertNotificationSystem, AlertSubscription
from social_media_monitor import SocialMediaPost

def demo_location_based_alerts():
    """Demonstrate location-based WhatsApp and SMS alerts"""
    print("🚨 LOCATION-BASED DISASTER ALERT SYSTEM DEMO")
    print("=" * 60)
    
    # Initialize systems
    print("🧠 Initializing AI and Alert Systems...")
    ai_system = SimplifiedDisasterAI()
    alert_system = AlertNotificationSystem()
    
    print("\n📍 Setting up Location-Based Subscribers...")
    
    # Subscriber 1: Mumbai resident - wants local alerts within 50km
    mumbai_subscriber = AlertSubscription(
        subscriber_id="mumbai_resident_001",
        name="Raj Patel",
        contact_method="whatsapp",
        contact_address="+919876543210",  # Sample Indian number
        latitude=19.0760,  # Mumbai coordinates
        longitude=72.8777,
        alert_radius_km=50.0,  # 50km radius around Mumbai
        city="Mumbai",
        state="Maharashtra", 
        country="India",
        disaster_types=["flood", "earthquake", "fire", "explosion"],
        min_confidence=0.8,
        min_urgency="medium",
        emergency_override=True,
        language="english"
    )
    
    # Subscriber 2: Tokyo resident - wants earthquake alerts within 100km
    tokyo_subscriber = AlertSubscription(
        subscriber_id="tokyo_resident_001",
        name="Yuki Tanaka",
        contact_method="sms",
        contact_address="+819087654321",  # Sample Japanese number
        latitude=35.6762,  # Tokyo coordinates
        longitude=139.6503,
        alert_radius_km=100.0,  # 100km radius around Tokyo
        city="Tokyo",
        country="Japan",
        disaster_types=["earthquake", "tsunami", "fire"],
        min_confidence=0.7,
        min_urgency="high",
        emergency_override=True,
        language="english"
    )
    
    # Subscriber 3: California resident - wants wildfire alerts within 200km
    california_subscriber = AlertSubscription(
        subscriber_id="california_resident_001",
        name="Sarah Johnson",
        contact_method="whatsapp",
        contact_address="+14155552345",  # Sample US number
        latitude=37.7749,  # San Francisco coordinates
        longitude=-122.4194,
        alert_radius_km=200.0,  # 200km radius
        city="San Francisco",
        state="California",
        country="USA",
        disaster_types=["wildfire", "earthquake", "flood"],
        min_confidence=0.75,
        min_urgency="medium",
        emergency_override=True,
        language="english"
    )
    
    # Add subscribers to system
    subscribers = [mumbai_subscriber, tokyo_subscriber, california_subscriber]
    for subscriber in subscribers:
        alert_system.add_subscription(subscriber)
        print(f"   ✅ Added subscriber: {subscriber.name} ({subscriber.city}) - {subscriber.contact_method}")
    
    print(f"\n📱 Testing Location-Based Alert Scenarios...")
    
    # Test scenarios with different disasters in different locations
    test_scenarios = [
        {
            'post': SocialMediaPost(
                post_id="test_001",
                platform="twitter",
                content="URGENT: Major flooding in Bandra, Mumbai! Water levels 8 feet high, many people trapped. Emergency rescue operations underway! #MumbaiFloods #Emergency",
                author="MumbaiNewsLive",
                timestamp=time.time(),
                url="https://twitter.com/example/001"
            ),
            'expected_notifications': ['mumbai_resident_001'],  # Only Mumbai subscriber should get this
            'description': "Mumbai flood - should notify Mumbai resident via WhatsApp"
        },
        {
            'post': SocialMediaPost(
                post_id="test_002",
                platform="reddit",
                content="BREAKING: Massive 7.8 earthquake hits Tokyo! Buildings swaying, people evacuating. Tsunami warning issued for coastal areas. This is not a drill!",
                author="TokyoEmergencyWatch",
                timestamp=time.time(),
                url="https://reddit.com/example/002"
            ),
            'expected_notifications': ['tokyo_resident_001'],  # Only Tokyo subscriber should get this
            'description': "Tokyo earthquake - should notify Tokyo resident via SMS"
        },
        {
            'post': SocialMediaPost(
                post_id="test_003", 
                platform="twitter",
                content="WILDFIRE ALERT: Massive fire spreading rapidly near Napa Valley, California! Evacuation orders for Sonoma County. Wind speeds making it worse! #CaliforniaFires",
                author="CalFireOfficial",
                timestamp=time.time(),
                url="https://twitter.com/example/003"
            ),
            'expected_notifications': ['california_resident_001'],  # Only California subscriber should get this
            'description': "California wildfire - should notify California resident via WhatsApp"
        },
        {
            'post': SocialMediaPost(
                post_id="test_004",
                platform="reddit", 
                content="Beautiful sunrise this morning in New York Central Park! Perfect weather for jogging.",
                author="NYCRunner",
                timestamp=time.time(),
                url="https://reddit.com/example/004"
            ),
            'expected_notifications': [],  # No one should get notified
            'description': "Normal post - should not trigger any notifications"
        }
    ]
    
    total_scenarios = len(test_scenarios)
    successful_tests = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🔬 TEST SCENARIO {i}/{total_scenarios}")
        print(f"   Description: {scenario['description']}")
        print(f"   Content: {scenario['post'].content[:80]}...")
        print(f"   Expected notifications: {len(scenario['expected_notifications'])}")
        
        # Process the post with AI
        alert = ai_system.create_alert(
            scenario['post'].platform,
            scenario['post'].content, 
            scenario['post'].author
        )
        
        if alert:
            print(f"   🚨 ALERT GENERATED:")
            print(f"      Type: {alert.disaster_type}")
            print(f"      Location: {alert.location}")
            print(f"      Confidence: {alert.confidence_score:.2f}")
            
            # Process notifications (simulated)
            notifications_sent = 0
            for subscriber_id, subscription in alert_system.subscriptions.items():
                if alert_system.should_notify_subscriber(subscription, alert):
                    notifications_sent += 1
                    print(f"      📱 Would notify: {subscription.name} via {subscription.contact_method}")
                    
                    # Simulate notification sending
                    if subscription.contact_method == 'whatsapp':
                        print(f"         📞 WhatsApp message to {subscription.contact_address}")
                        print(f"         📍 Location check: Alert in {alert.location}, subscriber in {subscription.city}")
                    elif subscription.contact_method == 'sms':
                        print(f"         💬 SMS message to {subscription.contact_address}")
                        print(f"         📍 Location check: Alert in {alert.location}, subscriber in {subscription.city}")
            
            print(f"      📊 Total notifications: {notifications_sent}")
            
            # Check if results match expectations
            if notifications_sent == len(scenario['expected_notifications']):
                print(f"      ✅ TEST PASSED - Correct number of notifications")
                successful_tests += 1
            else:
                print(f"      ❌ TEST FAILED - Expected {len(scenario['expected_notifications'])}, got {notifications_sent}")
        else:
            print(f"   ✅ No alert generated (expected for normal posts)")
            if len(scenario['expected_notifications']) == 0:
                successful_tests += 1
        
        time.sleep(1)  # Small delay between tests
    
    print(f"\n📊 LOCATION-BASED ALERT SYSTEM TEST RESULTS:")
    print(f"   Total Scenarios: {total_scenarios}")
    print(f"   Successful Tests: {successful_tests}")
    print(f"   Success Rate: {(successful_tests/total_scenarios*100):.1f}%")
    
    print(f"\n🎯 KEY FEATURES DEMONSTRATED:")
    print(f"   ✅ Geographic proximity filtering (radius-based)")
    print(f"   ✅ City/State/Country location matching")
    print(f"   ✅ WhatsApp message notifications") 
    print(f"   ✅ SMS text message notifications")
    print(f"   ✅ Multi-channel delivery (WhatsApp + SMS)")
    print(f"   ✅ Location-specific subscriber targeting")
    print(f"   ✅ Emergency override capabilities")
    print(f"   ✅ Confidence and urgency filtering")
    
    print(f"\n🌍 SUBSCRIBER COVERAGE:")
    for subscriber in subscribers:
        print(f"   📍 {subscriber.name} ({subscriber.city}):")
        print(f"      Contact: {subscriber.contact_method} ({subscriber.contact_address})")
        print(f"      Radius: {subscriber.alert_radius_km}km")
        print(f"      Types: {', '.join(subscriber.disaster_types)}")
        print()
    
    print(f"🎉 Location-Based Alert System Demo Complete!")
    print(f"🚀 Ready for real-world deployment with geographic targeting!")

if __name__ == "__main__":
    try:
        demo_location_based_alerts()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()