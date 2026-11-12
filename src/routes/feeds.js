const express = require('express');
const { feedStmt, articleStmt } = require('../db');
const { requireAuth } = require('../middleware/auth');

const router = express.Router();

// GET /api/feeds list all feeds with article counts
router.get('/', requireAuth, (req, res) => {
  const feeds = feedStmt.all();
  const countStmt = require('../db').db.prepare('SELECT feed_id, COUNT(*) AS n FROM Articles GROUP BY feed_id');
  const counts = new Map(countStmt.all().map((r) => [r.feed_id, r.n]));
  res.json(feeds.map((f) => ({ ...f, article_count: counts.get(f.id) || 0 })));
});

// GET /api/feeds/:id feed details
router.get('/:id', requireAuth, (req, res) => {
  const feed = feedStmt.byId.get(req.params.id);
  if (!feed) return res.status(404).json({ error: 'Feed not found' });
  const n = articleStmt.count({ feedId: feed.id });
  res.json({ ...feed, article_count: n });
});

module.exports = router;
