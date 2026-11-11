"""Shared pytest fixtures for the RSS aggregator API tests.

The suite boots the real Express server (with a throw-away SQLite file and an
empty feeds config so no network access is needed) and exercises the HTTP API.
The Redis instance pointed to by TEST_REDIS_HOST/TEST_REDIS_PORT must be up.
"""

import json
import os
import shutil
import socket
import sqlite3
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
REDIS_HOST = os.environ.get("TEST_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.environ.get("TEST_REDIS_PORT", "6379"))
PASSWORD = "secret123"

SEED_FEEDS = [
    {"url": "https://example.com/feeds/local.xml", "title": "Test Local Feed", "type": "local"},
    {"url": "https://example.com/feeds/country.xml", "title": "Test Country Feed", "type": "country"},
    {"url": "https://example.com/feeds/world.xml", "title": "Test World Feed", "type": "world"},
]

# (feed index, title, link, pub_date, content)
SEED_ARTICLES = [
    (0, "Local one", "https://example.com/articles/local-1", "2026-11-01T08:00:00.000Z", "Local one body"),
    (0, "Local two", "https://example.com/articles/local-2", "2026-11-02T08:00:00.000Z", "Local two body"),
    (1, "Country one", "https://example.com/articles/country-1", "2026-11-03T08:00:00.000Z", "Country one body"),
    (1, "Country two", "https://example.com/articles/country-2", "2026-11-04T08:00:00.000Z", "Country two body"),
    (2, "World one", "https://example.com/articles/world-1", "2026-11-05T08:00:00.000Z", "World one body"),
    (2, "World two", "https://example.com/articles/world-2", "2026-11-06T08:00:00.000Z", "World two body"),
]


# --------------------------------------------------------------------------- #
# Minimal Redis client (RESP) so tests can assert on the sorted sets directly
# without pulling in an extra dependency.
# --------------------------------------------------------------------------- #
def _read_reply(reader):
    line = reader.readline()
    if not line:
        raise RuntimeError("connection closed by redis")
    prefix, body = line[:1], line[1:].rstrip(b"\r\n")
    if prefix == b"+":
        return body.decode()
    if prefix == b"-":
        raise RuntimeError(body.decode())
    if prefix == b":":
        return int(body)
    if prefix == b"$":
        length = int(body)
        if length == -1:
            return None
        return reader.read(length + 2)[:length].decode()
    if prefix == b"*":
        count = int(body)
        if count == -1:
            return None
        return [_read_reply(reader) for _ in range(count)]
    raise RuntimeError(f"unexpected redis reply: {line!r}")


def redis_command(*args):
    payload = f"*{len(args)}\r\n".encode()
    for arg in args:
        raw = str(arg).encode()
        payload += f"${len(raw)}\r\n".encode() + raw + b"\r\n"
    with socket.create_connection((REDIS_HOST, REDIS_PORT), timeout=5) as sock:
        sock.sendall(payload)
        return _read_reply(sock.makefile("rb"))


def history_key(user_id):
    return f"user:{user_id}:history"



# --------------------------------------------------------------------------- #
# HTTP client wrapper
# --------------------------------------------------------------------------- #
class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def request(self, method, path, token=None, headers=None, **kwargs):
        headers = dict(headers or {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return self.session.request(method, self.base_url + path, headers=headers, timeout=15, **kwargs)

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def close(self):
        self.session.close()


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _seed_database(db_path, feeds, articles):
    """Insert deterministic feeds/articles straight into the server's SQLite file."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        feed_ids = []
        for feed in feeds:
            conn.execute(
                "INSERT OR IGNORE INTO Feeds (url, title, type) VALUES (?, ?, ?)",
                (feed["url"], feed["title"], feed["type"]),
            )
            feed_ids.append(conn.execute("SELECT id FROM Feeds WHERE url = ?", (feed["url"],)).fetchone()[0])
        rows = []
        for feed_index, title, link, pub_date, content in articles:
            conn.execute(
                "INSERT OR IGNORE INTO Articles (feed_id, title, link, pub_date, content) VALUES (?, ?, ?, ?, ?)",
                (feed_ids[feed_index], title, link, pub_date, content),
            )
            article_id = conn.execute("SELECT id FROM Articles WHERE link = ?", (link,)).fetchone()[0]
            rows.append(
                {
                    "id": article_id,
                    "feed_id": feed_ids[feed_index],
                    "title": title,
                    "link": link,
                    "pub_date": pub_date,
                }
            )
        conn.commit()
        return feed_ids, rows
    finally:
        conn.close()


@pytest.fixture(scope="session")
def server():
    node = shutil.which("node")
    if not node:
        pytest.skip("node executable is required to run the API tests")

    tmpdir = Path(tempfile.mkdtemp(prefix="rss-aggregator-tests-"))
    db_path = tmpdir / "test.db"
    feeds_config = tmpdir / "feeds.json"
    feeds_config.write_text(json.dumps([]), encoding="utf-8")
    log_path = tmpdir / "server.log"
    port = _free_port()

    env = os.environ.copy()
    env.update(
        {
            "PORT": str(port),
            "DB_PATH": str(db_path),
            "FEEDS_CONFIG": str(feeds_config),
            "REDIS_URL": f"redis://{REDIS_HOST}:{REDIS_PORT}",
            "FEED_REFRESH_MS": str(24 * 60 * 60 * 1000),
            "HISTORY_TTL_SECONDS": "0",
            "JWT_SECRET": "test-secret",
            "NODE_ENV": "test",
        }
    )

    log_file = open(log_path, "wb")
    proc = subprocess.Popen(
        [node, str(ROOT / "src" / "index.js")],
        cwd=str(ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"

    started = False
    deadline = time.time() + 40
    while time.time() < deadline and proc.poll() is None:
        try:
            if requests.get(base_url + "/health", timeout=1).status_code == 200:
                started = True
                break
        except requests.RequestException:
            pass
        time.sleep(0.2)

    if not started:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()
        log_text = log_path.read_text(encoding="utf-8", errors="replace")
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise RuntimeError(f"API server failed to start.\n--- server log ---\n{log_text}")

    handle = SimpleNamespace(proc=proc, base_url=base_url, db_path=db_path, tmpdir=tmpdir, log_path=log_path)
    try:
        yield handle
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_file.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="session")
def seed(server):
    feed_ids, articles = _seed_database(server.db_path, SEED_FEEDS, SEED_ARTICLES)
    return SimpleNamespace(feed_ids=feed_ids, articles=articles, feeds=SEED_FEEDS)


@pytest.fixture(scope="session")
def client(server):
    api = ApiClient(server.base_url)
    yield api
    api.close()


@pytest.fixture
def create_user(client):
    """Factory creating a unique user per test; its Redis history is removed afterwards."""
    created = []

    def _create(prefix="user"):
        login = f"{prefix}_{uuid.uuid4().hex[:10]}"
        response = client.post("/api/auth/signup", json={"login": login, "password": PASSWORD})
        assert response.status_code == 201, response.text
        payload = response.json()
        user = SimpleNamespace(login=login, password=PASSWORD, token=payload["token"], id=payload["user"]["id"])
        created.append(user)
        return user

    yield _create

    for user in created:
        try:
            redis_command("DEL", history_key(user.id))
        except OSError:
            pass


@pytest.fixture
def user(create_user):
    return create_user()

