const express = require('express');
const bcrypt = require('bcryptjs');
const { userStmt } = require('../db');
const { signToken } = require('../middleware/auth');

const router = express.Router();

const LOGIN_RE = /^[a-zA-Z0-9_.-]{3,32}$/;
const MIN_PASSWORD = 6;

// POST /api/auth/signup  { login, password }
router.post('/signup', async (req, res) => {
  const { login, password } = req.body || {};
  if (!login || !password) return res.status(400).json({ error: 'login and password are required' });
  if (!LOGIN_RE.test(login)) {
    return res.status(400).json({ error: 'login must be 3-32 chars: letters, digits, _, ., -' });
  }
  if (typeof password !== 'string' || password.length < MIN_PASSWORD) {
    return res.status(400).json({ error: `password must be at least ${MIN_PASSWORD} characters` });
  }
  if (userStmt.byLogin.get(login)) {
    return res.status(409).json({ error: 'login already taken' });
  }
  const hash = await bcrypt.hash(password, 10);
  const info = userStmt.insert.run(login, hash);
  const user = { id: info.lastInsertRowid, login };
  return res.status(201).json({ token: signToken(user), user });
});

// POST /api/auth/signin  { login, password }
router.post('/signin', async (req, res) => {
  const { login, password } = req.body || {};
  if (!login || !password) return res.status(400).json({ error: 'login and password are required' });
  const user = userStmt.byLogin.get(login);
  if (!user || !(await bcrypt.compare(password, user.password_hash))) {
    return res.status(401).json({ error: 'Invalid login or password' });
  }
  return res.json({ token: signToken({ id: user.id, login: user.login }), user: { id: user.id, login: user.login } });
});

module.exports = router;
