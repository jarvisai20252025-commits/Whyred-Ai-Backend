const express = require('express');
const searchService = require('../services/search');
const geminiService = require('../services/gemini');
const { authenticateToken } = require('../middleware/auth');
const { db } = require('../services/firebase');

const router = express.Router();

// Google Custom Search integration
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { query } = req.body;
    
    if (!query) {
      return res.status(400).json({ error: 'Search query is required' });
    }

    // Get search results
    const searchData = await searchService.searchWithAI(query);
    
    // Generate AI response based on search results
    const aiPrompt = `Based on the following search results, provide a comprehensive answer to: "${query}"\n\nSearch Results:\n${searchData.context}`;
    const aiResponse = await geminiService.generateText(aiPrompt);
    
    // Save to history
    await db.collection('chat_history').add({
      userId: req.user.uid,
      prompt: query,
      response: aiResponse,
      searchResults: searchData.results,
      type: 'search',
      timestamp: new Date()
    });

    res.json({ 
      response: aiResponse,
      sources: searchData.results
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;