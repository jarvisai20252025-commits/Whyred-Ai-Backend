const express = require('express');
const { db } = require('../services/firebase');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

// Create/Update user profile
router.post('/', authenticateToken, async (req, res) => {
  try {
    const { displayName, preferences } = req.body;
    const userId = req.user.uid;

    await db.collection('users').doc(userId).set({
      uid: userId,
      email: req.user.email,
      displayName: displayName || req.user.name,
      preferences: preferences || {},
      createdAt: new Date(),
      lastActive: new Date()
    }, { merge: true });

    res.json({ message: 'User data saved successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get user data
router.get('/', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.uid;
    const userDoc = await db.collection('users').doc(userId).get();
    
    if (!userDoc.exists) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json(userDoc.data());
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;