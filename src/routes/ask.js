const express = require('express');
const geminiService = require('../services/gemini');
const { authenticateToken } = require('../middleware/auth');
const { db } = require('../services/firebase');

const router = express.Router();

// Handle text/code/image prompts
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { prompt, type = 'text', imageData } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    let response;
    
    switch (type) {
      case 'image':
        if (!imageData) {
          return res.status(400).json({ error: 'Image data required for image analysis' });
        }
        response = await geminiService.generateFromImage(prompt, imageData);
        break;
      case 'code':
        response = await geminiService.generateCode(prompt);
        break;
      default:
        response = await geminiService.generateText(prompt);
    }

    // Save to history
    await db.collection('chat_history').add({
      userId: req.user.uid,
      prompt,
      response,
      type,
      timestamp: new Date()
    });

    res.json({ response });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;