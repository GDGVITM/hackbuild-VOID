import { formatDistanceToNow } from '../utils/dateUtils';
import { getPlatformIcon, getPlatformColor } from '../utils/platformUtils';
import type { Post } from '../types';

interface PostCardProps {
  post: Post;
  onAction: (postId: string, action: 'upvote' | 'downvote' | 'report') => void;
}

export default function PostCard({ post, onAction }: PostCardProps) {
  const platformIcon = getPlatformIcon(post.platform);
  const platformColor = getPlatformColor(post.platform);

  return (
    <div className="post-card">
      {/* Header */}
      <div className="post-header">
        <div className="post-author">
          <div className={`platform-icon ${platformColor.class}`}>
            {platformIcon}
          </div>
          <div className="post-meta">
            <h3 className="user-handle">{post.userHandle}</h3>
            <div className="post-details">
              <span>{formatDistanceToNow(post.timestamp)}</span>
              <span>•</span>
              <span>{post.location.name}</span>
            </div>
          </div>
        </div>
        <div className="platform-badge">
          {post.platform}
        </div>
      </div>

      {/* Content */}
      <div className="post-content">
        <p className="post-text">
          {post.content}
        </p>
      </div>

      {/* Media */}
      {post.imageUrl && (
        <div className="post-media">
          <img
            src={post.imageUrl}
            alt="Post content"
            className="post-image"
            loading="lazy"
          />
        </div>
      )}

      {post.videoUrl && (
        <div className="post-media">
          <video
            src={post.videoUrl}
            controls
            className="post-video"
            preload="metadata"
          />
        </div>
      )}

      {/* Tags */}
      {post.tags.length > 0 && (
        <div className="post-tags">
          <div className="tags-list">
            {post.tags.map((tag, index) => (
              <span
                key={index}
                className="tag"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="post-actions">
        <div className="action-buttons">
          {/* Upvote */}
          <button
            onClick={() => onAction(post.id, 'upvote')}
            className={`action-btn ${post.isUpvoted ? 'action-btn-upvoted' : ''}`}
          >
            <span className="action-icon">👍</span>
            <span>{post.upvotes}</span>
          </button>

          {/* Downvote */}
          <button
            onClick={() => onAction(post.id, 'downvote')}
            className={`action-btn ${post.isDownvoted ? 'action-btn-downvoted' : ''}`}
          >
            <span className="action-icon">👎</span>
            <span>{post.downvotes}</span>
          </button>

          {/* Report */}
          <button
            onClick={() => onAction(post.id, 'report')}
            className={`action-btn ${post.isReported ? 'action-btn-reported' : ''}`}
            disabled={post.isReported}
          >
            <span className="action-icon">🚩</span>
            <span>{post.isReported ? 'Reported' : 'Report'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
