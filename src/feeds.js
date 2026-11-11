const fs = require('fs');
const path = require('path');
const Parser = require('rss-parser');
const { feedStmt, articleStmt } = require('./db');

const parser = new Parser({ timeout: 15000 });
const CONFIG_PATH = process.env.FEEDS_CONFIG || path.join(__dirname, '..', 'config', 'feeds.json');
const VALID_TYPES = ['local', 'country', 'world'];

function loadFeedsFromConfig() {
  const raw = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  if (!Array.isArray(raw)) throw new Error('feeds config must be a JSON array');
  const upsert = feedStmt.upsert;
  const tx = (require('./db')).db.transaction((feeds) => {
    for (const f of feeds) {
      if (!f.url || !f.title) throw new Error(`feed entry missing url or title: ${JSON.stringify(f)}`);
      const type = f.type || 'world';
      if (!VALID_TYPES.includes(type)) throw new Error(`invalid feed type "${type}" (must be local/country/world)`);
      upsert.run(f.url, f.title, type);
    }
  });
  tx(raw);
  return feedStmt.all().length;
}

async function fetchFeed(feed) {
  try {
    const parsed = await parser.parseURL(feed.url);
    const tx = (require('./db')).db.transaction((items) => {
      for (const item of items) {
        const link = item.link || item.guid;
        if (!link || !item.title) continue;
        const pubDate = item.isoDate || (item.pubDate ? new Date(item.pubDate).toISOString() : new Date().toISOString());
        const content = item['content:encoded'] || item.content || item.contentSnippet || '';
        articleStmt.upsert.run({ feed_id: feed.id, title: item.title, link, pub_date: pubDate, content });
      }
    });
    tx(parsed.items || []);
    return { feed: feed.id, ok: true, items: (parsed.items || []).length };
  } catch (err) {
    console.error(`[feeds] failed to fetch "${feed.title}" (${feed.url}): ${err.message}`);
    return { feed: feed.id, ok: false, error: err.message };
  }
}

async function refreshAllFeeds() {
  const feeds = feedStmt.all();
  const results = await Promise.all(feeds.map(fetchFeed));
  const ok = results.filter((r) => r.ok).length;
  console.log(`[feeds] refreshed: ${ok}/${feeds.length} feeds ok`);
  return results;
}

let timer = null;
function startFeedRefresh(intervalMs = Number(process.env.FEED_REFRESH_MS || 10 * 60 * 1000)) {
  if (timer) return;
  timer = setInterval(() => refreshAllFeeds().catch((e) => console.error('[feeds] refresh error:', e)), intervalMs);
  timer.unref();
}

module.exports = { loadFeedsFromConfig, refreshAllFeeds, startFeedRefresh };
