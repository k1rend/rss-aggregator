require('dotenv').config();
const app = require('./app');
const { db } = require('./db');
const { redis } = require('./redis');
const { loadFeedsFromConfig, refreshAllFeeds, startFeedRefresh } = require('./feeds');

const PORT = Number(process.env.PORT || 3000);

async function main() {
  const feedCount = loadFeedsFromConfig();
  console.log(`[feeds] loaded ${feedCount} feeds from config`);

  // Initial refresh + periodic refresh
  refreshAllFeeds().catch((e) => console.error('[feeds] initial refresh error:', e));
  startFeedRefresh();

  const server = app.listen(PORT, () => console.log(`[server] listening on http://localhost:${PORT} (docs: /docs)`));

  const shutdown = (signal) => {
    console.log(`[server] ${signal} received, shutting down`);
    server.close(async () => {
      try { await redis.quit(); } catch { /* already closed */ }
      try { db.close(); } catch { /* already closed */ }
      process.exit(0);
    });
    // Do not hang forever if connections are still open
    setTimeout(() => process.exit(0), 5000).unref();
  };

  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

main().catch((e) => {
  console.error('Fatal:', e);
  process.exit(1);
});
