const express = require('express');
const geminiService = require('../services/gemini');
const { authenticateToken } = require('../middleware/auth');
const { db } = require('../services/firebase');

const router = express.Router();

// Image generation/analysis endpoint
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { prompt, imageData, action = 'analyze' } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    let response;

    if (action === 'analyze' && imageData) {
      // Analyze existing image
      response = await geminiService.generateFromImage(prompt, imageData);
    } else {
      // Generate image description or handle image-related text
      const imagePrompt = `Generate a detailed description for creating an image: ${prompt}`;
      response = await geminiService.generateText(imagePrompt);
    }

    // Save to history
    await db.collection('chat_history').add({
      userId: req.user.uid,
      prompt,
      response,
      type: 'image',
      action,
      timestamp: new Date()
    });

    res.json({ response });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;