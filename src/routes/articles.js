const express = require('express');
const { articleStmt } = require('../db');
const { requireAuth } = require('../middleware/auth');
const { addViewed, getViewedIdSet } = require('../redis');

const router = express.Router();

// GET /api/articles?feed_id=&type=&limit=&offset=&order=&only_unviewed=true
router.get('/', requireAuth, async (req, res) => {
  const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 20, 1), 100);
  const offset = Math.max(parseInt(req.query.offset, 10) || 0, 0);
  const order = req.query.order === 'asc' ? 'asc' : 'desc';
  const parsedFeedId = parseInt(req.query.feed_id, 10);
  const feedId = Number.isInteger(parsedFeedId) ? parsedFeedId : null;
  const type = ['local', 'country', 'world'].includes(req.query.type) ? req.query.type : null;
  const onlyUnviewed = req.query.only_unviewed === 'true';

  const viewedIds = await getViewedIdSet(req.user.sub);
  const excludeIds = onlyUnviewed ? [...viewedIds] : [];

  const filter = { feedId, type, excludeIds };
  const total = articleStmt.count(filter);
  const articles = articleStmt.list({ ...filter, limit, offset, order });

  res.json({
    total,
    limit,
    offset,
    articles: articles.map((a) => ({
      id: a.id,
      feed_id: a.feed_id,
      feed_title: a.feed_title,
      feed_type: a.feed_type,
      title: a.title,
      link: a.link,
      pub_date: a.pub_date,
      content: a.content,
      viewed: viewedIds.has(a.id),
    })),
  });
});

// GET /api/articles/:id
router.get('/:id', requireAuth, async (req, res) => {
  const article = articleStmt.byId.get(req.params.id);
  if (!article) return res.status(404).json({ error: 'Article not found' });
  const viewedSet = await getViewedIdSet(req.user.sub);
  res.json({ ...article, viewed: viewedSet.has(article.id) });
});

// POST /api/articles/:id/view — mark as viewed
router.post('/:id/view', requireAuth, async (req, res) => {
  const article = articleStmt.byId.get(req.params.id);
  if (!article) return res.status(404).json({ error: 'Article not found' });
  await addViewed(req.user.sub, article.id);
  res.json({ ok: true, article_id: article.id, viewed_at: new Date().toISOString() });
});

module.exports = router;
