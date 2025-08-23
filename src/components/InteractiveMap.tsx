import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Post, MapFilter } from '../types';

// Fix for default markers in react-leaflet
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface InteractiveMapProps {
  posts: Post[];
  mapPoints?: any[];
  userLocation: { lat: number; lng: number } | null;
  filter: MapFilter;
  onFilterChange: (filter: MapFilter) => void;
  onPostAction: (postId: string, action: 'upvote' | 'downvote' | 'report') => void;
}

// Component to update map center when user location changes
function MapUpdater({ center }: { center: LatLngExpression }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, 11);
  }, [center, map]);
  return null;
}

export default function InteractiveMap({ 
  posts, 
  mapPoints = [],
  userLocation, 
  filter, 
  onFilterChange,
  onPostAction 
}: InteractiveMapProps) {
  const mapRef = useRef<any>(null);

  // Filter posts based on time range
  const filteredPosts = posts.filter(post => {
    const now = new Date();
    const postTime = new Date(post.timestamp);
    const timeDiff = now.getTime() - postTime.getTime();

    switch (filter.timeRange) {
      case 'hour':
        return timeDiff <= 60 * 60 * 1000; // 1 hour
      case '24hours':
        return timeDiff <= 24 * 60 * 60 * 1000; // 24 hours
      case '7days':
        return timeDiff <= 7 * 24 * 60 * 60 * 1000; // 7 days
      default:
        return true;
    }
  });

  // Debug logging
  console.log('📊 InteractiveMap Debug:', {
    totalPosts: posts.length,
    filteredPosts: filteredPosts.length,
    mapPoints: mapPoints.length,
    filter: filter.timeRange,
    postsWithCoords: posts.filter(p => p.location.lat && p.location.lng).length
  });

  const center: LatLngExpression = userLocation 
    ? [userLocation.lat, userLocation.lng] 
    : [20.5937, 78.9629]; // Default to India center (matches database default)

  // Simple reliable icon creation
  const createMarkerIcon = (type: 'disaster' | 'social', platform?: string, urgency?: number) => {
    if (type === 'disaster') {
      const size = urgency === 3 ? 30 : urgency === 2 ? 25 : 20;
      const color = '#ff4444';
      return new Icon({
        iconUrl: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
          <svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
            <circle cx="${size/2}" cy="${size/2}" r="${size/2-2}" fill="${color}" stroke="white" stroke-width="2"/>
            <text x="${size/2}" y="${size/2+3}" text-anchor="middle" fill="white" font-size="10" font-weight="bold">!</text>
          </svg>
        `)}`,
        iconSize: [size, size],
        iconAnchor: [size/2, size/2]
      });
    } else {
      // Social media icon
      const colors: Record<string, string> = {
        twitter: '#1DA1F2',
        reddit: '#FF4500',
        facebook: '#1877F2',
        instagram: '#E4405F',
        tiktok: '#000000'
      };
      const color = colors[platform || 'twitter'] || '#6B7280';
      
      return new Icon({
        iconUrl: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
          <svg width="20" height="20" xmlns="http://www.w3.org/2000/svg">
            <circle cx="10" cy="10" r="8" fill="${color}" stroke="white" stroke-width="2"/>
            <circle cx="10" cy="10" r="4" fill="white"/>
          </svg>
        `)}`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });
    }
  };

  return (
    <div className="map-widget">
      {/* Map Header with Filter */}
      <div className="map-header">
        <div className="map-title-bar">
          <h2 className="map-title">Live Map</h2>
          <span className="map-post-count">
            {filteredPosts.length + mapPoints.length} posts
          </span>
        </div>
        
        <div className="map-filter">
          <span className="filter-icon">🕐</span>
          <select
            value={filter.timeRange}
            onChange={(e) => onFilterChange({ 
              timeRange: e.target.value as 'hour' | '24hours' | '7days' 
            })}
            className="time-filter-select"
          >
            <option value="hour">Last hour</option>
            <option value="24hours">24 hours</option>
            <option value="7days">7 days</option>
          </select>
        </div>
      </div>

      {/* Map Container */}
      <div className="map-content">
        <MapContainer
          ref={mapRef}
          center={center}
          zoom={6}
          style={{ height: '100%', width: '100%' }}
          className="leaflet-map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <MapUpdater center={center} />

          {/* User Location Marker */}
          {userLocation && (
            <Marker
              position={[userLocation.lat, userLocation.lng]}
              icon={new Icon({
                iconUrl: `data:image/svg+xml;base64,${btoa(`
                  <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="10" cy="10" r="8" fill="#3B82F6" stroke="white" stroke-width="2"/>
                    <circle cx="10" cy="10" r="3" fill="white"/>
                  </svg>
                `)}`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
              })}
            >
              <Popup>
                <div className="user-location-popup">
                  <div className="location-name">Your Location</div>
                  <div className="location-details">Mumbai, India</div>
                </div>
              </Popup>
            </Marker>
          )}

          {/* All Posts - Database Disasters + Social Media */}
          {filteredPosts.map((post) => {
            // Check if this is a disaster post (has disaster_info) or social media post
            const isDisasterPost = post.disaster_info && post.disaster_info.type;
            console.log('Rendering post:', post.id, 'isDisaster:', isDisasterPost, 'location:', post.location);
            
            return (
              <Marker
                key={post.id}
                position={[post.location.lat, post.location.lng]}
                icon={isDisasterPost 
                  ? createMarkerIcon('disaster', undefined, post.disaster_info!.urgency_level)
                  : createMarkerIcon('social', post.platform)
                }
              >
                <Popup maxWidth={350} className="custom-popup">
                  {isDisasterPost ? (
                    // Disaster Alert Popup
                    <div className="disaster-post-popup">
                      <div className="popup-header">
                        <h4 className="disaster-title">
                          🚨 {post.disaster_info!.type.toUpperCase()} ALERT
                        </h4>
                        <div className="urgency-badge">
                          Urgency: {post.disaster_info!.urgency_level}/3
                        </div>
                      </div>
                      
                      <div className="popup-content">
                        <p className="post-content">{post.content}</p>
                        
                        <div className="post-meta">
                          <div className="location-info">
                            📍 <strong>{post.location.name}</strong>
                          </div>
                          <div className="author-info">
                            👤 {post.userHandle}
                          </div>
                          <div className="confidence-info">
                            🎯 Confidence: {post.disaster_info!.confidence_level}/10
                          </div>
                          <div className="time-info">
                            🕐 {new Date(post.timestamp).toLocaleString()}
                          </div>
                        </div>

                        {post.tags && post.tags.length > 0 && (
                          <div className="tags-container">
                            {post.tags.map((tag, index) => (
                              <span key={index} className="tag">{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    // Social Media Post Popup
                    <div className="social-post-popup">
                      <div className="popup-header">
                        <h4 className="social-title">
                          📱 {post.platform.toUpperCase()} POST
                        </h4>
                        <div className="platform-badge">
                          {post.userHandle}
                        </div>
                      </div>
                      
                      <div className="popup-content">
                        <p className="post-content">{post.content}</p>
                        
                        {post.imageUrl && (
                          <img 
                            src={post.imageUrl} 
                            alt="Post content" 
                            className="post-image"
                            style={{ maxWidth: '100%', borderRadius: '8px', marginBottom: '8px' }}
                          />
                        )}
                        
                        <div className="post-meta">
                          <div className="location-info">
                            📍 <strong>{post.location.name}</strong>
                          </div>
                          <div className="engagement-info">
                            👍 {post.upvotes} ↑ 👎 {post.downvotes} ↓
                          </div>
                          <div className="time-info">
                            🕐 {new Date(post.timestamp).toLocaleString()}
                          </div>
                        </div>

                        {post.tags && post.tags.length > 0 && (
                          <div className="tags-container">
                            {post.tags.map((tag, index) => (
                              <span key={index} className="tag">{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </Popup>
              </Marker>
            );
          })}

          {/* Additional Map Points (if any) */}
          {mapPoints.length > 0 && mapPoints.map((point) => (
            <Marker
              key={`mappoint-${point.id}`}
              position={[point.lat, point.lng]}
              icon={createMarkerIcon('disaster', undefined, point.urgency)}
            >
              <Popup maxWidth={300}>
                <div className="disaster-popup">
                  <h4>🚨 {point.type?.toUpperCase()} ALERT</h4>
                  <p><strong>Location:</strong> {point.place}</p>
                  <p><strong>Urgency:</strong> {point.urgency}/3</p>
                  <p><strong>Confidence:</strong> {point.confidence}/10</p>
                  <p><strong>Time:</strong> {new Date(point.timestamp).toLocaleString()}</p>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Compact Map Legend */}
      <div className="map-legend-compact">
        <div className="legend-title">Map Markers</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-marker disaster-marker" style={{ backgroundColor: '#ff4444' }}></div>
            <span>Disasters</span>
          </div>
          <div className="legend-item">
            <div className="legend-marker social-marker" style={{ backgroundColor: '#1DA1F2' }}></div>
            <span>Social Posts</span>
          </div>
        </div>
      </div>
    </div>
  );
}
