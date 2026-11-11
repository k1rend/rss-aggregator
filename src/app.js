const express = require('express');
const fs = require('fs');
const path = require('path');
const YAML = require('yaml');
const swaggerUi = require('swagger-ui-express');

const authRoutes = require('./routes/auth');
const feedRoutes = require('./routes/feeds');
const articleRoutes = require('./routes/articles');
const historyRoutes = require('./routes/history');

const app = express();
app.use(express.json());

// --- Swagger / OpenAPI docs ---
const openapiPath = path.join(__dirname, '..', 'openapi.yaml');
const openapiDoc = YAML.parse(fs.readFileSync(openapiPath, 'utf8'));
app.use('/docs', swaggerUi.serve, swaggerUi.setup(openapiDoc));
app.get('/openapi.json', (req, res) => res.json(openapiDoc));

// --- Health / readiness ---
app.get('/health', async (req, res) => {
  const { redis } = require('./redis');
  let redisOk = true;
  try { await redis.ping(); } catch { redisOk = false; }
  res.json({ status: 'ok', redis: redisOk ? 'up' : 'down' });
});

// --- API routes ---
app.use('/api/auth', authRoutes);
app.use('/api/feeds', feedRoutes);
app.use('/api/articles', articleRoutes);
app.use('/api/history', historyRoutes);

// 404 + error handler
app.use((req, res) => res.status(404).json({ error: 'Not found' }));
app.use((err, req, res, next) => { // eslint-disable-line no-unused-vars
  console.error('[error]', err.message);
  res.status(500).json({ error: 'Internal server error' });
});

module.exports = app;
