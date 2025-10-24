const axios = require('axios');

class SearchService {
  async googleSearch(query, num = 10) {
    try {
      const response = await axios.get('https://www.googleapis.com/customsearch/v1', {
        params: {
          key: process.env.GOOGLE_API_KEY,
          cx: process.env.SEARCH_ENGINE_ID,
          q: query,
          num: Math.min(num, 10)
        }
      });

      return response.data.items?.map(item => ({
        title: item.title,
        link: item.link,
        snippet: item.snippet,
        displayLink: item.displayLink
      })) || [];
    } catch (error) {
      throw new Error(`Search API error: ${error.message}`);
    }
  }

  async searchWithAI(query) {
    const searchResults = await this.googleSearch(query, 5);
    
    // Format results for AI processing
    const context = searchResults.map(result => 
      `${result.title}: ${result.snippet}`
    ).join('\n\n');

    return {
      results: searchResults,
      context: context
    };
  }
}

module.exports = new SearchService();