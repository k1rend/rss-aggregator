const express = require('express');
const { requireAuth } = require('../middleware/auth');
const { getViewedArticleDetails, getViewedIds } = require('../redis');

const router = express.Router();

// GET /api/history list of viewed articles with view timestamps (oldest first)
router.get('/', requireAuth, async (req, res) => {
  const parseIndex = (value, fallback) => {
    const parsed = parseInt(value, 10);
    return Number.isInteger(parsed) ? parsed : fallback;
  };
  const from = Math.max(parseIndex(req.query.from, 0), 0);
  const to = Math.max(parseIndex(req.query.to, -1), -1);
  const withDetails = req.query.details !== 'false';

  if (withDetails) {
    const items = await getViewedArticleDetails(req.user.sub, from, to);
    return res.json({ count: items.length, items });
  }
  const items = await getViewedIds(req.user.sub, from, to);
  res.json({ count: items.length, items });
});

module.exports = router;
