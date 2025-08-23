#!/usr/bin/env python3
"""
Disaster Alert System - Startup Script
This script starts all components of the disaster alert system
"""

import subprocess
import time
import os
import signal
import sys
from threading import Thread

def start_api_server():
    """Start the Flask API server"""
    print("🚀 Starting API Server...")
    try:
        subprocess.run([sys.executable, "api_server.py"], check=True)
    except KeyboardInterrupt:
        print("📡 API Server stopped")
    except Exception as e:
        print(f"❌ API Server error: {e}")

def start_reddit_monitor():
    """Start the Reddit monitoring bot"""
    print("🤖 Starting Reddit Monitor...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("🤖 Reddit Monitor stopped")
    except Exception as e:
        print(f"❌ Reddit Monitor error: {e}")

def start_react_app():
    """Start the React development server"""
    print("⚛️ Starting React App...")
    try:
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("⚛️ React App stopped")
    except Exception as e:
        print(f"❌ React App error: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down all services...")
    sys.exit(0)

def main():
    print("="*60)
    print("🌍 DISASTER ALERT SYSTEM - STARTUP")
    print("="*60)
    print("Starting all components...")
    print("- Flask API Server (Port 8000)")
    print("- Reddit Monitor Bot")
    print("- React Frontend (Port 5173)")
    print("="*60)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start API server in background
    api_thread = Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait a moment for API server to start
    time.sleep(3)
    
    # Start Reddit monitor in background
    reddit_thread = Thread(target=start_reddit_monitor, daemon=True)
    reddit_thread.start()
    
    # Wait a moment for Reddit monitor to initialize
    time.sleep(2)
    
    print("✅ All background services started!")
    print("📊 API Server: http://localhost:8000")
    print("🌐 Frontend: http://localhost:5173")
    print("🤖 Reddit Monitor: Running")
    print("\nPress Ctrl+C to stop all services")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")

if __name__ == "__main__":
    main()
