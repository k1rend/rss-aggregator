const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, '..', 'data', 'aggregator.db');

fs.mkdirSync(path.dirname(path.resolve(DB_PATH)), { recursive: true });

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
CREATE TABLE IF NOT EXISTS Feeds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('local', 'country', 'world'))
);

CREATE TABLE IF NOT EXISTS Articles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  link TEXT NOT NULL UNIQUE,
  pub_date TEXT NOT NULL,
  content TEXT,
  FOREIGN KEY (feed_id) REFERENCES Feeds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_articles_feed ON Articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub_date ON Articles(pub_date DESC);

CREATE TABLE IF NOT EXISTS Users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  login TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL
);
`);

const allFeedsStmt = db.prepare('SELECT * FROM Feeds ORDER BY id');

const feedStmt = {
  upsert: db.prepare(`
    INSERT INTO Feeds (url, title, type) VALUES (?, ?, ?)
    ON CONFLICT(url) DO UPDATE SET title = excluded.title, type = excluded.type
  `),
  all: () => allFeedsStmt.all(),
  byId: db.prepare('SELECT * FROM Feeds WHERE id = ?'),
};

const articleStmt = {
  upsert: db.prepare(`
    INSERT INTO Articles (feed_id, title, link, pub_date, content)
    VALUES (@feed_id, @title, @link, @pub_date, @content)
    ON CONFLICT(link) DO UPDATE SET
      title = excluded.title,
      pub_date = excluded.pub_date,
      content = excluded.content
  `),
  byId: db.prepare('SELECT a.*, f.title AS feed_title, f.type AS feed_type FROM Articles a JOIN Feeds f ON f.id = a.feed_id WHERE a.id = ?'),
  list: ({ feedId, type, limit, offset, order, excludeIds = [] }) => {
    let sql = 'SELECT a.*, f.title AS feed_title, f.type AS feed_type FROM Articles a JOIN Feeds f ON f.id = a.feed_id';
    const where = [];
    const params = [];
    if (feedId) { where.push('a.feed_id = ?'); params.push(feedId); }
    if (type) { where.push('f.type = ?'); params.push(type); }
    if (excludeIds.length) {
      where.push(`a.id NOT IN (${excludeIds.map(() => '?').join(', ')})`);
      params.push(...excludeIds);
    }
    if (where.length) sql += ' WHERE ' + where.join(' AND ');
    sql += ` ORDER BY a.pub_date ${order === 'asc' ? 'ASC' : 'DESC'} LIMIT ? OFFSET ?`;
    params.push(limit, offset);
    return db.prepare(sql).all(...params);
  },
  count: ({ feedId, type, excludeIds = [] }) => {
    let sql = 'SELECT COUNT(*) AS n FROM Articles a JOIN Feeds f ON f.id = a.feed_id';
    const where = [];
    const params = [];
    if (feedId) { where.push('a.feed_id = ?'); params.push(feedId); }
    if (type) { where.push('f.type = ?'); params.push(type); }
    if (excludeIds.length) {
      where.push(`a.id NOT IN (${excludeIds.map(() => '?').join(', ')})`);
      params.push(...excludeIds);
    }
    if (where.length) sql += ' WHERE ' + where.join(' AND ');
    return db.prepare(sql).get(...params).n;
  },
};

const userStmt = {
  byLogin: db.prepare('SELECT * FROM Users WHERE login = ?'),
  byId: db.prepare('SELECT id, login FROM Users WHERE id = ?'),
  insert: db.prepare('INSERT INTO Users (login, password_hash) VALUES (?, ?)'),
};

module.exports = { db, feedStmt, articleStmt, userStmt };
