import { formatDistanceToNow } from '../utils/dateUtils';
import { getPlatformIcon, getPlatformColor } from '../utils/platformUtils';
import type { Post } from '../types';

interface PostPreviewProps {
  post: Post;
  onAction: (postId: string, action: 'upvote' | 'downvote' | 'report') => void;
  onClose: () => void;
}

export default function PostPreview({ post, onAction, onClose }: PostPreviewProps) {
  const PlatformIcon = getPlatformIcon(post.platform);
  const platformColor = getPlatformColor(post.platform);

  return (
    <div className="post-preview">
      {/* Header */}
      <div className="post-preview-header">
        <div className="preview-author">
          <div className={`preview-platform-icon ${platformColor.class}`}>
            <PlatformIcon />
          </div>
          <div className="preview-meta">
            <div className="preview-user-handle">{post.userHandle}</div>
            <div className="preview-timestamp">{formatDistanceToNow(post.timestamp)}</div>
          </div>
        </div>
        <button
          onClick={onClose}
          className="preview-close-btn"
        >
          ✕
        </button>
      </div>

      {/* Content */}
      <div className="post-preview-content">
        <p className="preview-text">
          {post.content}
        </p>
        
        {/* Image */}
        {post.imageUrl && (
          <div className="preview-media">
            <img
              src={post.imageUrl}
              alt="Post content"
              className="preview-image"
              loading="lazy"
            />
          </div>
        )}

        {/* Tags */}
        {post.tags.length > 0 && (
          <div className="preview-tags">
            <div className="preview-tags-list">
              {post.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className="preview-tag"
                >
                  {tag}
                </span>
              ))}
              {post.tags.length > 2 && (
                <span className="preview-tags-more">
                  +{post.tags.length - 2} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Location */}
        <div className="preview-location">
          📍 {post.location.name}
        </div>
      </div>

      {/* Actions */}
      <div className="post-preview-actions">
        <div className="preview-action-buttons">
          {/* Upvote */}
          <button
            onClick={() => onAction(post.id, 'upvote')}
            className={`preview-action-btn ${post.isUpvoted ? 'preview-action-btn-upvoted' : ''}`}
          >
            <span className="preview-action-icon">👍</span>
            <span>{post.upvotes}</span>
          </button>

          {/* Downvote */}
          <button
            onClick={() => onAction(post.id, 'downvote')}
            className={`preview-action-btn ${post.isDownvoted ? 'preview-action-btn-downvoted' : ''}`}
          >
            <span className="preview-action-icon">👎</span>
            <span>{post.downvotes}</span>
          </button>

          {/* Report */}
          <button
            onClick={() => onAction(post.id, 'report')}
            className={`preview-action-btn ${post.isReported ? 'preview-action-btn-reported' : ''}`}
            disabled={post.isReported}
          >
            <span className="preview-action-icon">🚩</span>
            <span>{post.isReported ? 'Reported' : 'Report'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
