const Redis = require('ioredis');
const { db } = require('./db');

const REDIS_URL = process.env.REDIS_URL || 'redis://127.0.0.1:6379';
const HISTORY_TTL = Number(process.env.HISTORY_TTL_SECONDS || 0) || null; // 0 = no expiry

const redis = new Redis(REDIS_URL, {
  maxRetriesPerRequest: 2,
  retryStrategy: (times) => Math.min(times * 200, 2000),
  enableOfflineQueue: false,
});

redis.on('error', (err) => console.error('[redis] error:', err.message));
redis.on('connect', () => console.log('[redis] connected to', REDIS_URL));

// ZSET: user:<id>:history -> score: unix timestamp, member: article_id
const historyKey = (userId) => `user:${userId}:history`;

async function addViewed(userId, articleId, when = Date.now()) {
  const key = historyKey(userId);
  const score = Math.floor(when / 1000);
  if (HISTORY_TTL) {
    await redis
      .multi()
      .zadd(key, score, String(articleId))
      .expire(key, HISTORY_TTL)
      .exec();
  } else {
    await redis.zadd(key, score, String(articleId));
  }
}

async function getViewedIds(userId, from = 0, to = -1) {
  // Returns array of { articleId, viewedAt } sorted oldest first.
  const range = await redis.zrange(historyKey(userId), from, to, 'WITHSCORES');
  const out = [];
  for (let i = 0; i < range.length; i += 2) {
    out.push({ articleId: Number(range[i]), viewedAt: Number(range[i + 1]) * 1000 });
  }
  return out;
}

async function getViewedIdSet(userId) {
  return new Set((await redis.zrange(historyKey(userId), 0, -1)).map(Number));
}

async function getViewedArticleDetails(userId, from = 0, to = -1) {
  const viewed = await getViewedIds(userId, from, to);
  if (!viewed.length) return [];
  const ids = viewed.map((v) => v.articleId);
  const rows = db.prepare(
    `SELECT a.*, f.title AS feed_title, f.type AS feed_type
     FROM Articles a JOIN Feeds f ON f.id = a.feed_id
     WHERE a.id IN (${ids.map(() => '?').join(',')})`
  ).all(...ids);
  const byId = new Map(rows.map((r) => [r.id, r]));
  // Articles can disappear (feed cleanup / re-import), so skip unknown ids
  // instead of returning empty objects.
  const out = [];
  for (const v of viewed) {
    const row = byId.get(v.articleId);
    if (!row) continue;
    out.push({
      ...row,
      articleId: v.articleId,
      viewedAt: v.viewedAt,
      viewed_at: new Date(v.viewedAt).toISOString(),
    });
  }
  return out;
}

module.exports = { redis, addViewed, getViewedIds, getViewedIdSet, getViewedArticleDetails };
