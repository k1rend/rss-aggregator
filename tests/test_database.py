"""Checks that the SQLite schema required by the task is in place."""

import sqlite3

import pytest


@pytest.fixture(scope="module")
def tables(server):
    conn = sqlite3.connect(server.db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


@pytest.fixture(scope="module")
def columns(server):
    conn = sqlite3.connect(server.db_path)
    try:
        result = {}
        for table in ("Feeds", "Articles", "Users"):
            result[table] = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        return result
    finally:
        conn.close()


def test_required_tables_exist(tables):
    assert {"Feeds", "Articles", "Users"}.issubset(tables)


def test_feeds_columns(columns):
    assert columns["Feeds"] == ["id", "url", "title", "type"]


def test_articles_columns(columns):
    assert columns["Articles"] == ["id", "feed_id", "title", "link", "pub_date", "content"]


def test_users_columns(columns):
    assert columns["Users"] == ["id", "login", "password_hash"]


def test_feed_type_is_constrained(server):
    conn = sqlite3.connect(server.db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO Feeds (url, title, type) VALUES ('https://example.com/bad.xml', 'Bad', 'galaxy')"
            )
    finally:
        conn.close()


def test_article_feed_id_is_a_foreign_key(server):
    conn = sqlite3.connect(server.db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO Articles (feed_id, title, link, pub_date, content) "
                "VALUES (424242, 'orphan', 'https://example.com/orphan', '2026-11-11T00:00:00.000Z', '')"
            )
    finally:
        conn.close()


def test_passwords_are_hashed_not_plaintext(server, user):
    conn = sqlite3.connect(server.db_path)
    try:
        row = conn.execute("SELECT password_hash FROM Users WHERE id = ?", (user.id,)).fetchone()
    finally:
        conn.close()

    assert row is not None
    stored = row[0]
    assert stored != user.password
    assert stored.startswith("$2"), "expected a bcrypt hash"
