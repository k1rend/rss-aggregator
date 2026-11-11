"""Tests for the service endpoints: /health, /openapi.json, /docs and 404 handling."""

EXPECTED_PATHS = [
    "/health",
    "/openapi.json",
    "/api/auth/signup",
    "/api/auth/signin",
    "/api/feeds",
    "/api/feeds/{id}",
    "/api/articles",
    "/api/articles/{id}",
    "/api/articles/{id}/view",
    "/api/history",
]


def test_health_reports_redis_up(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["redis"] == "up"


def test_openapi_json_document(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "RSS Aggregator API"
    assert sorted(spec["paths"]) == sorted(EXPECTED_PATHS)


def test_openapi_document_declares_bearer_auth(client):
    spec = client.get("/openapi.json").json()

    assert "bearerAuth" in spec["components"]["securitySchemes"]
    protected = [
        "/api/feeds",
        "/api/feeds/{id}",
        "/api/articles",
        "/api/articles/{id}",
        "/api/articles/{id}/view",
        "/api/history",
    ]
    for path in protected:
        for operation in spec["paths"][path].values():
            assert {"bearerAuth": []} in operation["security"], path


def test_swagger_ui_is_served(client):
    response = client.get("/docs/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger" in response.text.lower()


def test_unknown_route_returns_404_json(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"error": "Not found"}
