import { useState, useEffect, useRef } from 'react';
import { MapService } from '../services/mapService';
import type { Post, MapFilter } from '../types';

interface AdvancedMapProps {
  posts: Post[];
  mapPoints?: any[];
  userLocation: { lat: number; lng: number } | null;
  filter: MapFilter;
  onFilterChange: (filter: MapFilter) => void;
  onPostAction: (postId: string, action: 'upvote' | 'downvote' | 'report') => void;
}

export default function AdvancedMap({
  posts,
  filter,
  onFilterChange,
}: AdvancedMapProps) {
  const [mapHtml, setMapHtml] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mapStats, setMapStats] = useState<any>(null);
  const [isServiceAvailable, setIsServiceAvailable] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Check if map service is available
  useEffect(() => {
    checkMapService();
  }, []);

  // Generate map only once on load, not on auto-refresh
  useEffect(() => {
    if (isServiceAvailable) {
      generateMap();
      // Removed auto-refresh interval - only manual refresh now
    }
  }, [isServiceAvailable]);

  const checkMapService = async () => {
    try {
      const available = await MapService.isMapServiceAvailable();
      setIsServiceAvailable(available);
      
      if (!available) {
        setError('Python map service is not running. Please start the map server.');
      }
    } catch (err) {
      console.error('Error checking map service:', err);
      setIsServiceAvailable(false);
      setError('Failed to connect to map service');
    }
  };

  const generateMap = async () => {
    if (!isServiceAvailable) return;
    
    setIsLoading(true);
    setError(null);

    try {
      // Get map statistics
      const stats = await MapService.getMapStatistics();
      setMapStats(stats);

      // Generate the map HTML
      const response = await fetch('http://localhost:8000/api/generate-map', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Map generation failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        // Try to load the HTML content from the public path
        try {
          const mapResponse = await fetch(result.publicMapPath);
          if (mapResponse.ok) {
            const htmlContent = await mapResponse.text();
            setMapHtml(htmlContent);
          } else {
            // Fallback: show embedded link
            setMapHtml(`
              <div style="height: 100%; width: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center;">
                <div style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px);">
                  <h3 style="color: white; margin-bottom: 20px; font-size: 24px;">🗺️ Advanced Disaster Map Generated</h3>
                  <p style="color: rgba(255,255,255,0.9); margin-bottom: 25px; font-size: 16px;">
                    Interactive map with ${stats?.total_disasters || 0} disasters created successfully!
                  </p>
                  <button onclick="window.open('${result.mapFilePath}', '_blank')" 
                          style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: all 0.3s ease;">
                    🖥️ Open Interactive Map
                  </button>
                  <div style="margin-top: 25px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; text-align: center;">
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                      <div style="font-size: 24px; font-weight: bold;">${stats?.total_disasters || 0}</div>
                      <div style="font-size: 12px; opacity: 0.8;">Total Disasters</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                      <div style="font-size: 24px; font-weight: bold;">${stats?.average_confidence || 0}/10</div>
                      <div style="font-size: 12px; opacity: 0.8;">Avg Confidence</div>
                    </div>
                  </div>
                </div>
              </div>
            `);
          }
        } catch (fetchError) {
          console.warn('Failed to fetch map HTML, showing fallback:', fetchError);
          // Enhanced fallback
          setMapHtml(`
            <div style="height: 100%; width: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center;">
              <div style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px);">
                <h3 style="color: white; margin-bottom: 20px; font-size: 24px;">🗺️ Advanced Disaster Map</h3>
                <p style="color: rgba(255,255,255,0.9); margin-bottom: 25px; font-size: 16px;">
                  Interactive map generated successfully with real-time disaster data!
                </p>
                <button onclick="window.open('${result.mapFilePath}', '_blank')" 
                        style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: all 0.3s ease;">
                  🌍 Open Full Map
                </button>
                <div style="margin-top: 20px; color: rgba(255,255,255,0.7); font-size: 12px;">
                  Features: GPS markers, clustering, interactive popups, disaster statistics
                </div>
              </div>
            </div>
          `);
        }
      } else {
        throw new Error(result.error || 'Map generation failed');
      }
    } catch (err) {
      console.error('Map generation failed:', err);
      setError(`Failed to generate map: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshMap = () => {
    generateMap();
  };

  const handleOpenFullscreen = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/generate-map', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Map generation failed: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.success) {
        window.open(result.mapFilePath, '_blank');
      } else {
        throw new Error(result.error || 'Map generation failed');
      }
    } catch (err) {
      console.error('Failed to open fullscreen map:', err);
      alert('Failed to open fullscreen map. Please try again.');
    }
  };

  const handleLocalZoom = async () => {
    setIsLoading(true);
    try {
      // Create a Mumbai-focused map view
      const mumbaiZoomHtml = `
        <div style="height: 100%; width: 100%; display: flex; align-items: center; justify-content: center; flex-direction: column; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center;">
          <div style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; backdrop-filter: blur(10px);">
            <h3 style="color: white; margin-bottom: 20px; font-size: 24px;">📍 Mumbai Local Area Map</h3>
            <p style="color: rgba(255,255,255,0.9); margin-bottom: 25px; font-size: 16px;">
              Zoomed view of Mumbai region with local disasters and demo data
            </p>
            <button onclick="window.open('disaster_map.html', '_blank')" 
                    style="padding: 15px 30px; background: #28a745; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin-bottom: 15px;">
              🗺️ Open Mumbai Detailed Map
            </button>
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; text-align: center;">
              <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                <div style="font-size: 20px; font-weight: bold;">19.0760°N</div>
                <div style="font-size: 12px; opacity: 0.8;">Mumbai Latitude</div>
              </div>
              <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                <div style="font-size: 20px; font-weight: bold;">72.8777°E</div>
                <div style="font-size: 12px; opacity: 0.8;">Mumbai Longitude</div>
              </div>
            </div>
            <div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 8px;">
              <div style="font-size: 14px; margin-bottom: 8px;"><strong>Local Disasters in View:</strong></div>
              <div style="font-size: 12px;">🌊 Andheri East Flooding (High Priority)</div>
              <div style="font-size: 12px;">🔥 Vikhroli Emergency (Database)</div>
              <div style="font-size: 12px;">⚠️ Other Mumbai area incidents</div>
            </div>
          </div>
        </div>
      `;
      
      setMapHtml(mumbaiZoomHtml);
    } catch (err) {
      console.error('Failed to zoom to local area:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter posts based on time range (for stats display)
  const filteredPosts = posts.filter(post => {
    const now = new Date();
    const postTime = new Date(post.timestamp);
    const timeDiff = now.getTime() - postTime.getTime();

    switch (filter.timeRange) {
      case 'hour':
        return timeDiff <= 60 * 60 * 1000;
      case '24hours':
        return timeDiff <= 24 * 60 * 60 * 1000;
      case '7days':
        return timeDiff <= 7 * 24 * 60 * 60 * 1000;
      default:
        return true;
    }
  });

  if (!isServiceAvailable && !isLoading) {
    return (
      <div className="map-widget">
        <div className="map-header">
          <div className="map-title-bar">
            <h2 className="map-title">🗺️ Advanced Map</h2>
            <span className="map-post-count">Service Unavailable</span>
          </div>
        </div>
        
        <div className="map-content" style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          flexDirection: 'column',
          backgroundColor: '#f8f9fa',
          color: '#666',
          textAlign: 'center',
          padding: '40px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>🚫</div>
          <h3 style={{ marginBottom: '16px', color: '#333' }}>Map Service Not Available</h3>
          <p style={{ marginBottom: '20px' }}>
            The Python map service is not running. To use the advanced map features:
          </p>
          <ol style={{ textAlign: 'left', maxWidth: '400px', marginBottom: '20px' }}>
            <li>Open a terminal in the project directory</li>
            <li>Run: <code style={{ background: '#e9ecef', padding: '2px 4px', borderRadius: '3px' }}>python map.py</code></li>
            <li>Or start the API server with map endpoints enabled</li>
          </ol>
          <button
            onClick={checkMapService}
            style={{
              padding: '10px 20px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer'
            }}
          >
            🔄 Check Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="map-widget">
      {/* Map Header with Enhanced Controls */}
      <div className="map-header">
        <div className="map-title-bar">
          <h2 className="map-title">🗺️ Advanced Disaster Map</h2>
          <span className="map-post-count">
            {mapStats?.total_disasters || filteredPosts.length} disasters
          </span>
        </div>
        
        <div className="map-controls">
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
          
          <button
            onClick={handleRefreshMap}
            disabled={isLoading}
            className="map-refresh-btn"
            style={{
              padding: '8px 12px',
              background: isLoading ? '#ccc' : '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              marginLeft: '8px'
            }}
          >
            {isLoading ? '🔄' : '↻'} Refresh
          </button>
          
          <button
            onClick={handleOpenFullscreen}
            className="map-fullscreen-btn"
            style={{
              padding: '8px 12px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginLeft: '8px'
            }}
          >
            🖥️ Fullscreen
          </button>
          
          <button
            onClick={handleLocalZoom}
            className="map-local-zoom-btn"
            style={{
              padding: '8px 12px',
              background: '#6f42c1',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginLeft: '8px'
            }}
          >
            📍 Local
          </button>
        </div>
      </div>

      {/* Map Statistics Bar */}
      {mapStats && (
        <div className="map-stats-bar" style={{
          background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          padding: '8px 16px',
          fontSize: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>📊 Total: {mapStats.total_disasters}</span>
          <span>🎯 Avg Confidence: {mapStats.average_confidence}/10</span>
          <span>🚨 High Priority: {mapStats.by_urgency?.high || 0}</span>
          <span>🌍 Regions: {Object.keys(mapStats.by_region || {}).length}</span>
        </div>
      )}

      {/* Map Content */}
      <div className="map-content" style={{ position: 'relative' }}>
        {isLoading && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            flexDirection: 'column'
          }}>
            <div style={{ fontSize: '24px', marginBottom: '10px' }}>🗺️</div>
            <div>Generating advanced map...</div>
          </div>
        )}
        
        {error && (
          <div style={{
            background: '#ffe6e6',
            color: '#d63031',
            padding: '20px',
            textAlign: 'center',
            borderRadius: '8px',
            margin: '20px'
          }}>
            <div style={{ fontSize: '24px', marginBottom: '10px' }}>⚠️</div>
            <div>{error}</div>
            <button
              onClick={handleRefreshMap}
              style={{
                marginTop: '10px',
                padding: '8px 16px',
                background: '#d63031',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Try Again
            </button>
          </div>
        )}
        
        {mapHtml && !error && (
          <iframe
            ref={iframeRef}
            srcDoc={mapHtml}
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              borderRadius: '8px'
            }}
            title="Advanced Disaster Map"
          />
        )}
      </div>

      {/* Enhanced Map Legend */}
      <div className="map-legend-advanced" style={{
        background: '#f8f9fa',
        padding: '12px 16px',
        borderTop: '1px solid #dee2e6',
        fontSize: '12px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                background: '#e74c3c',
                borderRadius: '50%',
                border: '2px solid white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }}></div>
              <span>High Priority</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                background: '#f39c12',
                borderRadius: '50%',
                border: '2px solid white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }}></div>
              <span>Moderate</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                background: '#27ae60',
                borderRadius: '50%',
                border: '2px solid white',
                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
              }}></div>
              <span>Low Priority</span>
            </div>
          </div>
          <div style={{ color: '#666' }}>
            Powered by Python + Folium | Updates every 30s
          </div>
        </div>
      </div>
    </div>
  );
}
