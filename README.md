# SocialNews - Real-time Social Media News Aggregator

A modern web application that displays social media posts from real people as news, featuring an interactive map and clean, responsive design.

## Features

### 🏠 Homepage Layout
- **Split Screen Design**: News feed on the left, interactive live map on the right
- **Responsive**: Map repositions above/below feed on mobile devices
- **Clean UI**: Minimal design with Tailwind CSS

### 📰 News Feed
- **Infinite Scroll**: Load more posts as you scroll
- **Post Cards**: Display user handle, platform icon, content, tags, and location
- **Social Actions**: Upvote, downvote, and report functionality
- **Sorting Options**: 
  - 🕒 Latest (most recent posts first)
  - 📍 Nearby (posts from your region)

### 🗺️ Interactive Live Map
- **Location-based**: Auto-detects user location and zooms to their region
- **Post Markers**: Shows posts as markers with platform-specific colors
- **Click Interaction**: Click markers to see post previews
- **Time Filters**: "Last hour", "24 hours", "7 days"
- **Legend**: Shows platform distribution

### 🔍 Search Functionality
- **Multi-type Search**: Search by keyword, hashtag, or location
- **Real-time Filtering**: Instant results as you type
- **Clear Search**: Easy search reset functionality

### 🌍 Feed Toggle
- **Global Feed**: Shows posts worldwide
- **Local Feed**: Shows posts from user's current location (50km radius)

## Installation & Usage

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Tech Stack

- **Frontend**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Heroicons & custom platform icons
- **Maps**: Leaflet.js with React-Leaflet
- **Build Tool**: Vite
- **UI Components**: Headless UI

## Project Structure

```
src/
├── components/         # React components
│   ├── Header.tsx     # Top navigation with search and feed toggle
│   ├── NewsFeed.tsx   # Main news feed component
│   ├── PostCard.tsx   # Individual post card
│   ├── InteractiveMap.tsx  # Map component with markers
│   └── PostPreview.tsx     # Map popup preview
├── data/              # Mock data
│   └── mockData.ts    # Sample posts from various Indian cities
├── types/             # TypeScript type definitions
│   └── index.ts       # All interfaces and types
├── utils/             # Utility functions
│   ├── dateUtils.ts   # Date formatting helpers
│   └── platformUtils.tsx  # Platform icons and colors
└── App.tsx           # Main application component
```

## Backend Integration Ready

The application is designed for easy backend integration:
- All data is managed through React state
- API calls can be easily added to replace mock data
- Consistent data structure with TypeScript interfaces
- Separated concerns with utility functions

## Sample Data

Includes mock posts from major Indian cities:
- Mumbai, Delhi, Bangalore, Chennai, Pune, Kolkata, Hyderabad, Goa, Jaipur
- Various platforms: Twitter, Reddit, Facebook, Instagram, TikTok
- Different post types: text, images, location-based content
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
