import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import type { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import PostPreview from './PostPreview';
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

  const center: LatLngExpression = userLocation 
    ? [userLocation.lat, userLocation.lng] 
    : [19.0760, 72.8777]; // Default to Mumbai

  // Create custom icons for different platforms
  const createCustomIcon = (platform: string) => {
    const colors = {
      twitter: '#1DA1F2',
      reddit: '#FF4500',
      facebook: '#1877F2',
      instagram: '#E4405F',
      tiktok: '#000000'
    };
    
    const color = colors[platform as keyof typeof colors] || '#6B7280';
    
    return new Icon({
      iconUrl: `data:image/svg+xml;base64,${btoa(`
        <svg width="25" height="41" viewBox="0 0 25 41" xmlns="http://www.w3.org/2000/svg">
          <path d="M12.5 0C5.596 0 0 5.596 0 12.5c0 8.5 12.5 28.5 12.5 28.5S25 21 25 12.5C25 5.596 19.404 0 12.5 0z" fill="${color}"/>
          <circle cx="12.5" cy="12.5" r="6" fill="white"/>
        </svg>
      `)}`,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34]
    });
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

          {/* Social Media Posts Markers */}
          {filteredPosts.map((post) => (
            <Marker
              key={post.id}
              position={[post.location.lat, post.location.lng]}
              icon={createCustomIcon(post.platform)}
            >
              <Popup maxWidth={300} className="custom-popup">
                <PostPreview 
                  post={post} 
                  onAction={onPostAction}
                />
              </Popup>
            </Marker>
          ))}

          {/* Disaster Markers */}
          {mapPoints.length > 0 && mapPoints.map((point) => (
            <Marker
              key={`disaster-${point.id}`}
              position={[point.lat, point.lng]}
              icon={new Icon({
                iconUrl: `data:image/svg+xml;base64,${btoa(`
                  <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="15" cy="15" r="12" fill="#ff4444" stroke="white" stroke-width="2"/>
                    <text x="15" y="19" text-anchor="middle" fill="white" font-size="10" font-weight="bold">!</text>
                  </svg>
                `)}`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
              })}
            >
              <Popup maxWidth={300}>
                <div className="disaster-popup">
                  <h4>{point.type?.toUpperCase()} ALERT</h4>
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

      {/* Map Legend */}
      <div className="map-legend">
        <div className="legend-title">Platforms</div>
        <div className="legend-items">
          {['twitter', 'reddit', 'facebook', 'instagram', 'tiktok'].map(platform => {
            const colors = {
              twitter: '#1DA1F2',
              reddit: '#FF4500', 
              facebook: '#1877F2',
              instagram: '#E4405F',
              tiktok: '#000000'
            };
            
            return (
              <div key={platform} className="legend-item">
                <div 
                  className="legend-marker" 
                  style={{ backgroundColor: colors[platform as keyof typeof colors] }}
                ></div>
                <span>{platform}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
