const express = require('express');
const geminiService = require('../services/gemini');
const { authenticateToken } = require('../middleware/auth');
const { db } = require('../services/firebase');

const router = express.Router();

// Health check endpoint
router.get('/health', async (req, res) => {
  try {
    const isHealthy = await geminiService.healthCheck();
    const modelInfo = geminiService.getModelInfo();
    
    res.json({
      status: isHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
      ...modelInfo
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Test endpoint without authentication
router.post('/test', async (req, res) => {
  try {
    const { prompt = 'Hello, this is a test message.' } = req.body;
    
    console.log('Test endpoint called with prompt:', prompt);
    
    const response = await geminiService.generateText(prompt);
    
    res.json({
      response,
      timestamp: new Date().toISOString(),
      model: 'test-mode',
      success: true
    });
  } catch (error) {
    console.error('Test endpoint error:', error);
    res.json({
      response: `Test response for: "${prompt}". The AI service is currently being optimized.`,
      timestamp: new Date().toISOString(),
      model: 'fallback',
      success: false,
      error: error.message
    });
  }
});

// Main ask endpoint with authentication
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { prompt, type = 'text', imageData } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ 
        error: 'Prompt is required',
        timestamp: new Date().toISOString()
      });
    }

    console.log(`Processing ${type} request for user: ${req.user.uid}`);
    console.log(`Prompt: ${prompt.substring(0, 100)}...`);

    let response;
    let processingTime = Date.now();
    
    switch (type) {
      case 'image':
        if (!imageData) {
          return res.status(400).json({ 
            error: 'Image data required for image analysis',
            timestamp: new Date().toISOString()
          });
        }
        response = await geminiService.generateFromImage(prompt, imageData);
        break;
        
      case 'code':
        response = await geminiService.generateCode(prompt);
        break;
        
      case 'search':
        response = await geminiService.generateSearch(prompt);
        break;
        
      default:
        response = await geminiService.generateText(prompt);
    }

    processingTime = Date.now() - processingTime;
    console.log(`Response generated in ${processingTime}ms`);

    // Save to history with enhanced metadata
    try {
      await db.collection('chat_history').add({
        userId: req.user.uid,
        prompt,
        response,
        type,
        timestamp: new Date(),
        processingTime,
        model: 'gemini-2.0-flash-exp',
        success: true
      });
    } catch (dbError) {
      console.error('Failed to save to history:', dbError.message);
      // Don't fail the request if history save fails
    }

    res.json({ 
      response,
      timestamp: new Date().toISOString(),
      processingTime,
      type,
      success: true
    });

  } catch (error) {
    console.error('Ask endpoint error:', error);
    
    const errorResponse = {
      error: error.message,
      timestamp: new Date().toISOString(),
      type: req.body.type || 'text',
      success: false
    };

    // Try to save error to history
    try {
      if (req.user) {
        await db.collection('chat_history').add({
          userId: req.user.uid,
          prompt: req.body.prompt,
          response: `Error: ${error.message}`,
          type: req.body.type || 'text',
          timestamp: new Date(),
          success: false,
          error: error.message
        });
      }
    } catch (dbError) {
      console.error('Failed to save error to history:', dbError.message);
    }

    // Return appropriate status code based on error type
    if (error.message.includes('API key') || error.message.includes('authentication')) {
      res.status(401).json(errorResponse);
    } else if (error.message.includes('quota') || error.message.includes('limit')) {
      res.status(429).json(errorResponse);
    } else if (error.message.includes('model') || error.message.includes('not found')) {
      res.status(503).json(errorResponse);
    } else {
      res.status(500).json(errorResponse);
    }
  }
});

// Streaming endpoint for real-time responses
router.post('/stream', authenticateToken, async (req, res) => {
  try {
    const { prompt, type = 'text' } = req.body;
    
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Cache-Control'
    });

    // Send initial event
    res.write(`data: ${JSON.stringify({ type: 'start', timestamp: new Date().toISOString() })}\n\n`);

    try {
      const response = await geminiService.generateText(prompt);
      
      // Simulate streaming by sending chunks
      const words = response.split(' ');
      let currentText = '';
      
      for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i];
        
        res.write(`data: ${JSON.stringify({ 
          type: 'chunk', 
          content: currentText,
          progress: (i + 1) / words.length
        })}\n\n`);
        
        // Small delay to simulate real streaming
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      // Send completion event
      res.write(`data: ${JSON.stringify({ 
        type: 'complete', 
        content: response,
        timestamp: new Date().toISOString()
      })}\n\n`);
      
    } catch (error) {
      res.write(`data: ${JSON.stringify({ 
        type: 'error', 
        error: error.message,
        timestamp: new Date().toISOString()
      })}\n\n`);
    }
    
    res.end();
    
  } catch (error) {
    console.error('Stream endpoint error:', error);
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;