// Service to handle Python map generation and display
export class MapService {
  private static readonly API_BASE_URL = 'http://localhost:8000';
  private static readonly MAP_GENERATION_ENDPOINT = '/api/generate-map';
  
  /**
   * Triggers Python map generation and returns the HTML file path
   */
  static async generateMap(): Promise<string> {
    try {
      const response = await fetch(`${this.API_BASE_URL}${this.MAP_GENERATION_ENDPOINT}`, {
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
        return result.mapFilePath;
      } else {
        throw new Error(result.error || 'Map generation failed');
      }
    } catch (error) {
      console.error('❌ Map generation error:', error);
      throw error;
    }
  }

  /**
   * Checks if the map service is available
   */
  static async isMapServiceAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Gets the latest map statistics
   */
  static async getMapStatistics() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch map statistics');
      }
      return await response.json();
    } catch (error) {
      console.error('❌ Error fetching map statistics:', error);
      return null;
    }
  }
}
