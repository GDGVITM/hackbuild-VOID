import { useState } from 'react';
import type { SearchParams, FeedType } from '../types';

interface HeaderProps {
  onSearch: (searchParams: SearchParams) => void;
  feedType: FeedType;
  onFeedTypeChange: (feedType: FeedType) => void;
}

export default function Header({ onSearch, feedType, onFeedTypeChange }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'keyword' | 'hashtag' | 'location'>('keyword');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ query: searchQuery, type: searchType });
  };

  const clearSearch = () => {
    setSearchQuery('');
    onSearch({ query: '', type: searchType });
  };

  return (
    <header className="header">
      <div className="header-container">
        <div className="header-content">
          {/* Logo */}
          <div className="header-logo">
            <h1 className="header-title">SocialNews</h1>
            <span className="live-badge">Live</span>
          </div>

          {/* Search Bar */}
          <div className="search-container">
            <form onSubmit={handleSearch} className="search-form">
              <div className="search-input-group">
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value as 'keyword' | 'hashtag' | 'location')}
                  className="search-type-select"
                >
                  <option value="keyword">Keyword</option>
                  <option value="hashtag">Hashtag</option>
                  <option value="location">Location</option>
                </select>
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={`Search by ${searchType}...`}
                    className="search-input"
                  />
                  {searchQuery && (
                    <button
                      type="button"
                      onClick={clearSearch}
                      className="search-clear-btn"
                    >
                      ×
                    </button>
                  )}
                </div>
                <button
                  type="submit"
                  className="search-submit-btn"
                >
                  🔍
                </button>
              </div>
            </form>
          </div>

          {/* Feed Toggle */}
          <div className="feed-toggle">
            <button
              onClick={() => onFeedTypeChange({ type: 'global' })}
              className={`feed-toggle-btn ${feedType.type === 'global' ? 'feed-toggle-btn-active' : ''}`}
            >
              🌍 Global
            </button>
            <button
              onClick={() => onFeedTypeChange({ type: 'local' })}
              className={`feed-toggle-btn ${feedType.type === 'local' ? 'feed-toggle-btn-active' : ''}`}
            >
              📍 Local
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
