"""Tests for /api/feeds and /api/feeds/{id}."""

import pytest


@pytest.fixture
def feeds(client, user, seed):
    response = client.get("/api/feeds", token=user.token)
    assert response.status_code == 200
    return response.json()


def test_list_feeds_includes_config_feeds_with_counts(feeds, seed):
    by_title = {feed["title"]: feed for feed in feeds}

    for feed, feed_id in zip(seed.feeds, seed.feed_ids):
        item = by_title[feed["title"]]
        assert item["id"] == feed_id
        assert item["url"] == feed["url"]
        assert item["type"] == feed["type"]
        assert item["article_count"] == 2


def test_list_feeds_requires_auth(client):
    assert client.get("/api/feeds").status_code == 401


def test_get_feed_by_id(client, user, seed):
    feed = seed.feeds[1]
    feed_id = seed.feed_ids[1]

    response = client.get(f"/api/feeds/{feed_id}", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == feed_id
    assert body["title"] == feed["title"]
    assert body["url"] == feed["url"]
    assert body["type"] == feed["type"]
    assert body["article_count"] == 2


def test_get_unknown_feed_returns_404(client, user):
    response = client.get("/api/feeds/999999", token=user.token)

    assert response.status_code == 404
    assert response.json()["error"] == "Feed not found"


def test_get_feed_requires_auth(client, seed):
    assert client.get(f"/api/feeds/{seed.feed_ids[0]}").status_code == 401
