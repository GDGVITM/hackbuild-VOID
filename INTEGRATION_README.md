# 🌍 Disaster Alert System - Real-Time Integration

A comprehensive disaster monitoring and alert system that integrates Reddit monitoring, AI analysis, real-time mapping, and social media news aggregation.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Reddit Bot    │───▶│  Flask API      │───▶│  React Frontend │
│   (Python)      │    │  (Python)       │    │  (TypeScript)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ AI Analysis     │    │ SQLite Database │    │ Interactive Map │
│ (Gemini/Pplx)   │    │ (Disaster Data) │    │ (Leaflet.js)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Email Alerts    │    │ Real-time API   │    │ Live Updates    │
│ (SMTP)          │    │ (30s refresh)   │    │ (Auto-refresh)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Features

### Backend (Python)
- **Reddit Monitoring**: Automatic post moderation and analysis on r/disasterhazards
- **AI Analysis**: Real-time disaster classification using Gemini and Perplexity APIs
- **Database Storage**: SQLite database for persistent disaster data
- **Email Alerts**: Regional email notifications for high-urgency disasters
- **REST API**: Flask server providing real-time data to frontend

### Frontend (React + TypeScript)
- **Real-time Feed**: Auto-refreshing news feed with disaster posts
- **Interactive Map**: Live disaster visualization with different urgency levels
- **Social Media Integration**: Displays posts from Twitter, Reddit, Facebook, etc.
- **Professional UI**: Modern design with animations and responsive layout

## 📊 Data Flow

1. **Reddit Monitoring**: Bot continuously monitors r/disasterhazards for new posts
2. **Content Moderation**: AI analyzes posts for location, promotion, and relevance
3. **Disaster Analysis**: AI extracts disaster type, urgency, confidence, and location
4. **Database Storage**: Approved posts stored with analysis results
5. **API Serving**: Flask API serves real-time data to React frontend
6. **Live Visualization**: Frontend displays posts on map and news feed
7. **Auto-refresh**: Frontend fetches new data every 30 seconds

## 🛠️ Installation & Setup

### 1. Clone and Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your API keys and credentials
```

Required API keys:
- Reddit API credentials (client_id, client_secret, username, password)
- Gemini API key
- Perplexity API key
- Email SMTP credentials (optional)

### 3. Database Setup

```bash
# Create the database
python -c "from database import create_database; create_database()"
```

## 🎯 Running the System

### Option 1: Manual Start (Development)

```bash
# Terminal 1: Start API Server
python api_server.py

# Terminal 2: Start Reddit Monitor
python main.py

# Terminal 3: Start React Frontend
npm run dev
```

### Option 2: Automated Start (Recommended)

```bash
# Start all components automatically
python start_system.py
```

The system will start:
- 📡 Flask API Server on http://localhost:8000
- 🤖 Reddit Monitor (background)
- ⚛️ React Frontend on http://localhost:5173

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/posts` | GET | All approved disaster posts |
| `/api/posts/recent` | GET | Posts from last 24 hours |
| `/api/posts/urgent` | GET | High urgency posts only |
| `/api/stats` | GET | Disaster statistics |
| `/api/map-data` | GET | Map visualization data |

## 🗺️ Map Integration

The interactive map shows:
- **Regular Posts**: Social media posts with platform-colored markers
- **Disaster Alerts**: Real-time disaster markers with urgency-based sizing
- **User Location**: Your current location (Mumbai by default)
- **Time Filters**: Hour, 24 hours, or 7 days
- **Real-time Updates**: Auto-refresh every 30 seconds

### Disaster Marker Legend:
- 🔴 **Red**: Fire disasters
- 🔵 **Blue**: Flood disasters  
- 🟠 **Orange**: Earthquake disasters
- 🟣 **Purple**: Storm disasters
- 🟢 **Green**: Other disasters

### Urgency Levels:
- **Large markers**: High urgency (Level 3)
- **Medium markers**: Moderate urgency (Level 2)
- **Small markers**: Low urgency (Level 1)

## 🎛️ Configuration

### Reddit Bot Settings
- **Subreddit**: r/disasterhazards (configurable)
- **Moderation**: Automatic approval/rejection based on AI analysis
- **Confidence Threshold**: Posts below 4/10 confidence are rejected
- **Update Frequency**: Real-time monitoring

### Frontend Settings
- **Auto-refresh**: 30 seconds
- **Map Center**: Mumbai, India (configurable)
- **Data Sources**: API + Mock data for demonstration
- **Performance**: Optimized for 100+ disaster posts

## 🚨 Email Alert System

Regional email alerts are sent for high-urgency disasters:

```
Asia: vihaan.ovalekar@gmail.com
Europe: electroknight999@gmail.com  
North America: yashpradhan0712@gmail.com
Other regions: global-alerts@disasterwatch.org
```

## 🔧 Development

### Project Structure
```
├── src/                    # React frontend
│   ├── components/         # React components
│   ├── services/          # API service layer
│   └── types/             # TypeScript types
├── api_server.py          # Flask API server
├── main.py               # Reddit bot entry point
├── auto_mod.py           # Reddit moderation logic
├── analysis.py           # AI analysis functions
├── database.py           # Database operations
├── email_notifications.py # Email alert system
└── requirements.txt      # Python dependencies
```

### Adding New Features
1. **Backend**: Add new endpoints in `api_server.py`
2. **Frontend**: Add API calls in `src/services/disasterApi.ts`
3. **Database**: Modify schema in `database.py`
4. **AI Analysis**: Update prompts in `analysis.py`

## 🐛 Troubleshooting

### Common Issues

**API Server not starting:**
```bash
# Check if port 8000 is in use
netstat -an | grep 8000
# Kill process if needed
```

**Reddit bot authentication failed:**
```bash
# Verify Reddit API credentials in .env
# Ensure account has moderator permissions on subreddit
```

**Map not showing data:**
```bash
# Check if API server is running
curl http://localhost:8000/api/health
# Verify database has data
python -c "from database import get_all_analyses; print(len(get_all_analyses()))"
```

**Frontend not updating:**
```bash
# Check browser console for API errors
# Verify API server CORS settings
```

## 🔮 Future Enhancements

- [ ] WebSocket real-time updates
- [ ] Mobile app version
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Machine learning predictions
- [ ] Integration with official weather APIs
- [ ] Push notifications
- [ ] User authentication system

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

For support, email team@disasterwatch.org or create an issue on GitHub.

---

Built with ❤️ for HackBuild Hackathon 2025
