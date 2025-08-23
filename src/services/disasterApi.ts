// API service for disaster data
const API_BASE_URL = 'http://localhost:8000/api';

export interface DisasterPost {
  id: string;
  userHandle: string;
  platform: string;
  content: string;
  imageUrl?: string;
  tags: string[];
  location: {
    lat: number;
    lng: number;
    name: string;
  };
  timestamp: string;
  upvotes: number;
  downvotes: number;
  disaster_info: {
    type: string;
    urgency_level: number;
    confidence_level: number;
    region: string;
    sources: string[];
  };
}

export interface MapPoint {
  id: string;
  lat: number;
  lng: number;
  type: string;
  urgency: number;
  confidence: number;
  place: string;
  title: string;
  timestamp: string;
  author: string;
}

export interface DisasterStats {
  total_posts: number;
  recent_posts_24h: number;
  by_disaster_type: Record<string, number>;
  by_urgency_level: Record<number, number>;
  by_region: Record<string, number>;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp?: string;
}

class DisasterApiService {
  private async fetchWithTimeout(url: string, timeout = 10000): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async getAllPosts(): Promise<ApiResponse<DisasterPost[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/posts`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: data.posts || [],
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error fetching all posts:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        data: []
      };
    }
  }

  async getRecentPosts(): Promise<ApiResponse<DisasterPost[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/posts/recent`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: data.posts || [],
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error fetching recent posts:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        data: []
      };
    }
  }

  async getUrgentPosts(): Promise<ApiResponse<DisasterPost[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/posts/urgent`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: data.posts || [],
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error fetching urgent posts:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        data: []
      };
    }
  }

  async getStats(): Promise<ApiResponse<DisasterStats>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: data.stats,
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error fetching stats:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async getMapData(): Promise<ApiResponse<MapPoint[]>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/map-data`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: data.points || [],
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error fetching map data:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        data: []
      };
    }
  }

  async checkHealth(): Promise<ApiResponse<{ status: string; database: string }>> {
    try {
      const response = await this.fetchWithTimeout(`${API_BASE_URL}/health`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        data: {
          status: data.status,
          database: data.database
        },
        timestamp: data.timestamp
      };
    } catch (error) {
      console.error('Error checking health:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

// Create and export a singleton instance
export const disasterApi = new DisasterApiService();

// Utility function to convert DisasterPost to Post format for existing components
export function convertDisasterPostToPost(disasterPost: DisasterPost): any {
  return {
    id: disasterPost.id,
    userHandle: disasterPost.userHandle,
    platform: disasterPost.platform,
    content: disasterPost.content,
    imageUrl: disasterPost.imageUrl,
    tags: disasterPost.tags,
    location: disasterPost.location,
    timestamp: new Date(disasterPost.timestamp),
    upvotes: disasterPost.upvotes,
    downvotes: disasterPost.downvotes,
    disaster_info: disasterPost.disaster_info
  };
}
