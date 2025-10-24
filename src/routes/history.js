const express = require('express');
const { db } = require('../services/firebase');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

// Get chat history for user
router.get('/', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.uid;
    const { limit = 50 } = req.query;

    const snapshot = await db.collection('chat_history')
      .where('userId', '==', userId)
      .orderBy('timestamp', 'desc')
      .limit(parseInt(limit))
      .get();

    const history = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp: doc.data().timestamp.toDate()
    }));

    res.json({ history });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete chat history
router.delete('/', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.uid;
    
    const snapshot = await db.collection('chat_history')
      .where('userId', '==', userId)
      .get();

    const batch = db.batch();
    snapshot.docs.forEach(doc => {
      batch.delete(doc.ref);
    });
    
    await batch.commit();
    res.json({ message: 'Chat history cleared' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;