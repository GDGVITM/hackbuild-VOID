import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import NewsFeed from './components/NewsFeed';
import AdvancedMap from './components/AdvancedMap';
import type { Post, FeedType, SortOption, MapFilter, SearchParams } from './types';
import { mockPosts } from './data/mockData';
import { disasterApi, convertDisasterPostToPost, type DisasterPost, type MapPoint } from './services/disasterApi';

function App() {
  const [posts, setPosts] = useState<Post[]>(mockPosts); // Start with demo data, then enhance with real data
  const [filteredPosts, setFilteredPosts] = useState<Post[]>(mockPosts);
  const [feedType, setFeedType] = useState<FeedType>({ type: 'global' });
  const [sortOption, setSortOption] = useState<SortOption>({ type: 'latest' });
  const [mapFilter, setMapFilter] = useState<MapFilter>({ timeRange: '24hours' });
  const [searchParams, setSearchParams] = useState<SearchParams>({ query: '', type: 'keyword' });
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [mapPoints, setMapPoints] = useState<MapPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  // Mock user location (Mumbai)
  useEffect(() => {
    setUserLocation({ lat: 19.0760, lng: 72.8777 });
  }, []);

  // Function to fetch disaster data from API
  const fetchDisasterData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Check API health first
      const healthResponse = await disasterApi.checkHealth();
      if (!healthResponse.success) {
        throw new Error('API server is not available');
      }

      // Fetch posts and map data
      const [postsResponse, mapResponse] = await Promise.all([
        disasterApi.getAllPosts(),
        disasterApi.getMapData()
      ]);

      if (postsResponse.success && postsResponse.data) {
        // Convert disaster posts to the format expected by existing components
        const convertedPosts = postsResponse.data.map(convertDisasterPostToPost);
        
        // Combine database posts with demo posts for rich demonstration
        const combinedPosts = [...convertedPosts, ...mockPosts];
        setPosts(combinedPosts);
        setLastUpdate(postsResponse.timestamp || new Date().toISOString());
        console.log('✅ Successfully loaded', convertedPosts.length, 'database posts +', mockPosts.length, 'demo posts');
        console.log('📊 Combined posts sample:', combinedPosts.slice(0, 2));
      } else {
        console.warn('Failed to fetch posts, using demo data:', postsResponse.error);
        setPosts(mockPosts);
        console.log('📊 Using mockPosts:', mockPosts.length, 'posts');
      }

      if (mapResponse.success && mapResponse.data) {
        setMapPoints(mapResponse.data);
        console.log('✅ Successfully loaded', mapResponse.data.length, 'map points from database');
      } else {
        console.warn('Failed to fetch map data:', mapResponse.error);
        setMapPoints([]);
      }

    } catch (err) {
      console.error('Error fetching disaster data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      // Fallback to demo data for better user experience
      setPosts(mockPosts);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchDisasterData();
  }, [fetchDisasterData]);

  // Auto-refresh data every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchDisasterData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [fetchDisasterData]);

  // Filter and sort posts based on current settings
  useEffect(() => {
    let filtered = [...posts];

    // Apply search filter
    if (searchParams.query) {
      filtered = filtered.filter(post => {
        switch (searchParams.type) {
          case 'keyword':
            return post.content.toLowerCase().includes(searchParams.query.toLowerCase());
          case 'hashtag':
            return post.tags.some(tag => 
              tag.toLowerCase().includes(searchParams.query.toLowerCase())
            );
          case 'location':
            return post.location.name.toLowerCase().includes(searchParams.query.toLowerCase());
          default:
            return true;
        }
      });
    }

    // Apply feed type filter
    if (feedType.type === 'local' && userLocation) {
      // Filter posts within 50km radius (simplified)
      filtered = filtered.filter(post => {
        const distance = getDistance(
          userLocation.lat, userLocation.lng,
          post.location.lat, post.location.lng
        );
        return distance <= 50;
      });
    }

    // Apply sort
    if (sortOption.type === 'latest') {
      filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    } else if (sortOption.type === 'nearby' && userLocation) {
      filtered.sort((a, b) => {
        const distanceA = getDistance(
          userLocation.lat, userLocation.lng,
          a.location.lat, a.location.lng
        );
        const distanceB = getDistance(
          userLocation.lat, userLocation.lng,
          b.location.lat, b.location.lng
        );
        return distanceA - distanceB;
      });
    }

    setFilteredPosts(filtered);
  }, [posts, feedType, sortOption, searchParams, userLocation]);

  const getDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat/2) * Math.sin(dLat/2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  };

  const handlePostAction = (postId: string, action: 'upvote' | 'downvote' | 'report') => {
    setPosts(prevPosts => 
      prevPosts.map(post => {
        if (post.id === postId) {
          switch (action) {
            case 'upvote':
              return {
                ...post,
                upvotes: post.isUpvoted ? post.upvotes - 1 : post.upvotes + 1,
                downvotes: post.isDownvoted ? post.downvotes - 1 : post.downvotes,
                isUpvoted: !post.isUpvoted,
                isDownvoted: false
              };
            case 'downvote':
              return {
                ...post,
                downvotes: post.isDownvoted ? post.downvotes - 1 : post.downvotes + 1,
                upvotes: post.isUpvoted ? post.upvotes - 1 : post.upvotes,
                isDownvoted: !post.isDownvoted,
                isUpvoted: false
              };
            case 'report':
              return { ...post, isReported: true };
            default:
              return post;
          }
        }
        return post;
      })
    );
  };

  return (
    <div className="app">
      <Header
        onSearch={setSearchParams}
        feedType={feedType}
        onFeedTypeChange={setFeedType}
      />
      
      <main className="main-content">
        {/* News Feed */}
        <div className="news-feed">
          <NewsFeed
            posts={filteredPosts}
            sortOption={sortOption}
            onSortChange={setSortOption}
            onPostAction={handlePostAction}
          />
        </div>
        
        {/* Advanced Interactive Map */}
        <div className="map-container">
                      <AdvancedMap 
              posts={filteredPosts}
              mapPoints={mapPoints}
              userLocation={userLocation}
              filter={mapFilter}
              onFilterChange={setMapFilter}
              onPostAction={handlePostAction}
            />
        </div>
      </main>
    </div>
  );
}

export default App;
