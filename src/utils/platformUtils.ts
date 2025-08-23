// Simple platform utilities without JSX
export const getPlatformIcon = (platform: string) => {
  switch (platform.toLowerCase()) {
    case 'twitter':
      return '🐦';
    case 'reddit':
      return '🤖';
    case 'instagram':
      return '📷';
    default:
      return '📱';
  }
};

// Platform color mapping
export const getPlatformColor = (platform: string) => {
  switch (platform.toLowerCase()) {
    case 'twitter':
      return {
        color: '#1DA1F2',
        class: 'twitter-color'
      };
    case 'reddit':
      return {
        color: '#FF4500',
        class: 'reddit-color'
      };
    case 'instagram':
      return {
        color: '#E4405F',
        class: 'instagram-color'
      };
    default:
      return {
        color: '#3B82F6',
        class: 'default-color'
      };
  }
};

// Platform name mapping
export const getPlatformName = (platform: string): string => {
  switch (platform.toLowerCase()) {
    case 'twitter':
      return 'Twitter';
    case 'reddit':
      return 'Reddit';
    case 'instagram':
      return 'Instagram';
    default:
      return 'Social Media';
  }
};
