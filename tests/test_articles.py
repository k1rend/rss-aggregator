"""Tests for /api/articles, /api/articles/{id} and /api/articles/{id}/view."""

import datetime


def titles(body):
    return [article["title"] for article in body["articles"]]


def test_list_articles_default_page(client, user, seed):
    response = client.get("/api/articles", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == len(seed.articles)
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert titles(body) == [
        "World two",
        "World one",
        "Country two",
        "Country one",
        "Local two",
        "Local one",
    ]
    first = body["articles"][0]
    assert first["feed_type"] == "world"
    assert first["feed_title"] == "Test World Feed"
    assert first["viewed"] is False
    assert first["content"] == "World two body"


def test_list_articles_ascending(client, user):
    response = client.get("/api/articles?order=asc", token=user.token)

    assert response.status_code == 200
    assert titles(response.json())[0] == "Local one"


def test_list_articles_pagination(client, user):
    response = client.get("/api/articles?limit=2&offset=2", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 6
    assert body["limit"] == 2
    assert body["offset"] == 2
    assert titles(body) == ["Country two", "Country one"]


def test_list_articles_limit_is_clamped(client, user):
    too_big = client.get("/api/articles?limit=1000", token=user.token).json()
    assert too_big["limit"] == 100
    assert len(too_big["articles"]) <= 100

    zero_defaults = client.get("/api/articles?limit=0", token=user.token).json()
    assert zero_defaults["limit"] == 20

    negative_offset = client.get("/api/articles?offset=-10", token=user.token).json()
    assert negative_offset["offset"] == 0


def test_list_articles_filter_by_feed(client, user, seed):
    feed_id = seed.feed_ids[0]

    response = client.get(f"/api/articles?feed_id={feed_id}", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert titles(body) == ["Local two", "Local one"]
    assert all(article["feed_id"] == feed_id for article in body["articles"])


def test_list_articles_filter_by_type(client, user):
    response = client.get("/api/articles?type=world", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert titles(body) == ["World two", "World one"]
    assert all(article["feed_type"] == "world" for article in body["articles"])


def test_list_articles_ignores_unknown_type(client, user):
    response = client.get("/api/articles?type=galaxy", token=user.token)

    assert response.status_code == 200
    assert response.json()["total"] == 6


def test_get_article_by_id(client, user, seed):
    article = seed.articles[3]

    response = client.get(f"/api/articles/{article['id']}", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == article["id"]
    assert body["feed_id"] == article["feed_id"]
    assert body["title"] == article["title"]
    assert body["link"] == article["link"]
    assert body["pub_date"] == article["pub_date"]
    assert body["viewed"] is False
    assert body["feed_title"] == "Test Country Feed"


def test_get_unknown_article_returns_404(client, user):
    response = client.get("/api/articles/999999", token=user.token)

    assert response.status_code == 404
    assert response.json()["error"] == "Article not found"


def test_mark_article_viewed(client, user, seed):
    article = seed.articles[0]

    response = client.post(f"/api/articles/{article['id']}/view", token=user.token)

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["article_id"] == article["id"]
    datetime.datetime.fromisoformat(body["viewed_at"].replace("Z", "+00:00"))

    detail = client.get(f"/api/articles/{article['id']}", token=user.token).json()
    assert detail["viewed"] is True

    listing = client.get("/api/articles", token=user.token).json()
    viewed_flags = {item["id"]: item["viewed"] for item in listing["articles"]}
    assert viewed_flags[article["id"]] is True
    assert sum(1 for flag in viewed_flags.values() if flag) == 1


def test_only_unviewed_excludes_viewed_articles(client, create_user, seed):
    reader = create_user("unviewed")
    seen = seed.articles[:2]

    for article in seen:
        assert client.post(f"/api/articles/{article['id']}/view", token=reader.token).status_code == 200

    filtered = client.get("/api/articles?only_unviewed=true", token=reader.token).json()

    assert filtered["total"] == len(seed.articles) - len(seen)
    returned_ids = {item["id"] for item in filtered["articles"]}
    assert returned_ids.isdisjoint({article["id"] for article in seen})
    assert all(item["viewed"] is False for item in filtered["articles"])

    # pagination applies to the filtered result set as well
    paged = client.get("/api/articles?only_unviewed=true&limit=2&offset=0", token=reader.token).json()
    assert paged["total"] == 4
    assert len(paged["articles"]) == 2

    everything = client.get("/api/articles", token=reader.token).json()
    assert everything["total"] == 6
    assert sum(1 for item in everything["articles"] if item["viewed"]) == 2


def test_mark_unknown_article_viewed_returns_404(client, user):
    response = client.post("/api/articles/999999/view", token=user.token)

    assert response.status_code == 404
    assert response.json()["error"] == "Article not found"


def test_article_endpoints_require_auth(client, seed):
    article_id = seed.articles[0]["id"]

    assert client.get("/api/articles").status_code == 401
    assert client.get(f"/api/articles/{article_id}").status_code == 401
    assert client.post(f"/api/articles/{article_id}/view").status_code == 401

