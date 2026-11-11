"""Tests for /api/history and the Redis sorted set behind it."""

import datetime
import time

import pytest

from conftest import history_key, redis_command

VIEW_GAP = 1.05  # history scores have 1 second resolution


def view(client, user, article_id, gap=True):
    response = client.post(f"/api/articles/{article_id}/view", token=user.token)
    assert response.status_code == 200, response.text
    if gap:
        time.sleep(VIEW_GAP)
    return response.json()


@pytest.fixture
def viewer(client, create_user, seed):
    user = create_user("history")
    first, second = seed.articles[2], seed.articles[5]
    first_view = view(client, user, first["id"])
    second_view = view(client, user, second["id"], gap=False)
    return user, first, second, first_view, second_view


def test_history_is_empty_for_new_user(client, user):
    response = client.get("/api/history", token=user.token)

    assert response.status_code == 200
    assert response.json() == {"count": 0, "items": []}
    assert redis_command("EXISTS", history_key(user.id)) == 0


def test_history_lists_viewed_articles_oldest_first(client, viewer):
    user, first, second, first_view, second_view = viewer

    response = client.get("/api/history", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2

    items = body["items"]
    assert [item["id"] for item in items] == [first["id"], second["id"]]
    assert items[0]["title"] == first["title"]
    assert items[0]["articleId"] == first["id"]
    assert items[0]["feed_type"] == "country"
    assert items[1]["feed_title"] == "Test World Feed"

    # details mode adds an ISO timestamp on top of the raw viewedAt millis
    assert items[0]["viewedAt"] <= items[1]["viewedAt"]
    posted = datetime.datetime.fromisoformat(first_view["viewed_at"].replace("Z", "+00:00"))
    stored = datetime.datetime.fromtimestamp(items[0]["viewedAt"] / 1000, tz=datetime.timezone.utc)
    assert abs((posted - stored).total_seconds()) < 2


def test_history_without_details(client, viewer):
    user, first, second, _, _ = viewer

    response = client.get("/api/history?details=false", token=user.token)

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["articleId"] for item in items] == [first["id"], second["id"]]
    for item in items:
        assert set(item) == {"articleId", "viewedAt"}
        assert isinstance(item["viewedAt"], int)


def test_history_pagination(client, viewer):
    user, first, second, _, _ = viewer

    only_second = client.get("/api/history?details=false&from=1&to=1", token=user.token).json()
    assert only_second["count"] == 1
    assert only_second["items"][0]["articleId"] == second["id"]

    only_first = client.get("/api/history?details=false&from=0&to=0", token=user.token).json()
    assert only_first["count"] == 1
    assert only_first["items"][0]["articleId"] == first["id"]


def test_history_is_stored_as_redis_zset_with_timestamp_scores(client, viewer):
    user, first, second, first_view, second_view = viewer
    key = history_key(user.id)

    assert key == f"user:{user.id}:history"
    assert redis_command("TYPE", key) == "zset"
    assert redis_command("ZCARD", key) == 2

    first_score = redis_command("ZSCORE", key, first["id"])
    second_score = redis_command("ZSCORE", key, second["id"])
    assert first_score is not None and second_score is not None
    assert float(first_score) < float(second_score)

    # scores are unix timestamps in seconds taken when the article was viewed
    now = time.time()
    assert now - 120 < float(second_score) <= now + 5
    posted_ms = int(
        datetime.datetime.fromisoformat(second_view["viewed_at"].replace("Z", "+00:00")).timestamp() * 1000
    )
    assert int(float(second_score)) * 1000 == pytest.approx(posted_ms, abs=1000)

    # the millisecond value returned by the API is the redis score in ms
    history = client.get("/api/history?details=false", token=user.token).json()
    assert [item["viewedAt"] for item in history["items"]] == [
        int(float(first_score) * 1000),
        int(float(second_score) * 1000),
    ]


def test_viewing_twice_updates_timestamp_without_duplicating(client, viewer):
    user, _, second, _, _ = viewer
    key = history_key(user.id)
    before = float(redis_command("ZSCORE", key, second["id"]))

    time.sleep(VIEW_GAP)
    view(client, user, second["id"], gap=False)

    after = float(redis_command("ZSCORE", key, second["id"]))
    assert after > before
    assert redis_command("ZCARD", key) == 2  # still two unique articles


def test_history_is_per_user(client, viewer, create_user):
    user, _, _, _, _ = viewer
    other = create_user("other")

    response = client.get("/api/history", token=other.token)

    assert response.status_code == 200
    assert response.json() == {"count": 0, "items": []}
    assert redis_command("ZCARD", history_key(user.id)) == 2


def test_history_requires_auth(client):
    response = client.get("/api/history")

    assert response.status_code == 401
