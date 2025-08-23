export interface Post {
  id: string;
  userHandle: string;
  platform: 'twitter' | 'reddit' | 'facebook' | 'instagram' | 'tiktok';
  content: string;
  imageUrl?: string;
  videoUrl?: string;
  tags: string[];
  location: {
    lat: number;
    lng: number;
    name: string;
  };
  timestamp: Date;
  upvotes: number;
  downvotes: number;
  isUpvoted?: boolean;
  isDownvoted?: boolean;
  isReported?: boolean;
  disaster_info?: {
    type: string;
    urgency_level: number;
    confidence_level: number;
    region: string;
    sources: string[];
  };
}

export interface MapFilter {
  timeRange: 'hour' | '24hours' | '7days';
}

export interface FeedType {
  type: 'global' | 'local';
}

export interface SortOption {
  type: 'latest' | 'nearby';
}

export interface SearchParams {
  query: string;
  type: 'keyword' | 'hashtag' | 'location';
}
