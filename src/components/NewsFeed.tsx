import { useState } from 'react';
import PostCard from './PostCard';
import type { Post, SortOption } from '../types';

interface NewsFeedProps {
  posts: Post[];
  sortOption: SortOption;
  onSortChange: (sortOption: SortOption) => void;
  onPostAction: (postId: string, action: 'upvote' | 'downvote' | 'report') => void;
}

export default function NewsFeed({ posts, sortOption, onSortChange, onPostAction }: NewsFeedProps) {
  const [visiblePosts, setVisiblePosts] = useState(10);

  const loadMorePosts = () => {
    setVisiblePosts(prev => Math.min(prev + 10, posts.length));
  };

  const displayedPosts = posts.slice(0, visiblePosts);

  return (
    <div className="news-feed-container">
      {/* Sort Options */}
      <div className="news-feed-header">
        <h2 className="news-feed-title">News Feed</h2>
        <div className="sort-controls">
          <span className="sort-label">Sort by:</span>
          <div className="sort-buttons">
            <button
              onClick={() => onSortChange({ type: 'latest' })}
              className={`sort-btn ${sortOption.type === 'latest' ? 'sort-btn-active' : ''}`}
            >
              🕐 Latest
            </button>
            <button
              onClick={() => onSortChange({ type: 'nearby' })}
              className={`sort-btn ${sortOption.type === 'nearby' ? 'sort-btn-active' : ''}`}
            >
              📍 Nearby
            </button>
          </div>
        </div>
      </div>

      {/* Posts List */}
      <div className="posts-list">
        {displayedPosts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📱</div>
            <h3 className="empty-title">No posts found</h3>
            <p className="empty-description">Try adjusting your search or filters</p>
          </div>
        ) : (
          <>
            {displayedPosts.map((post, index) => (
              <div key={post.id} style={{ '--animation-index': index } as React.CSSProperties}>
                <PostCard
                  post={post}
                  onAction={onPostAction}
                />
              </div>
            ))}
            
            {/* Load More Button */}
            {visiblePosts < posts.length && (
              <div className="load-more-container">
                <button
                  onClick={loadMorePosts}
                  className="load-more-btn"
                >
                  Load More Posts
                </button>
              </div>
            )}
            
            {/* End of Feed */}
            {visiblePosts >= posts.length && posts.length > 0 && (
              <div className="end-of-feed">
                <div className="end-icon">🎉</div>
                <p>You've reached the end of the feed!</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
