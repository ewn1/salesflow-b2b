import pytest
from rest_framework.test import APIClient

ALLOWED = "http://localhost:5173"
BLOCKED = "http://evil.example.com"
LOGIN_URL = "/api/auth/token/"


@pytest.fixture(autouse=True)
def cors_settings(settings):
    # Pin the allowed origins so these tests do not depend on the .env file.
    settings.CORS_ALLOWED_ORIGINS = [ALLOWED]


def preflight(origin):
    """Simulate the OPTIONS request a browser sends before a real request."""
    return APIClient().options(
        LOGIN_URL,
        HTTP_ORIGIN=origin,
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type",
    )


def test_preflight_from_allowed_origin_is_accepted():
    response = preflight(ALLOWED)

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == ALLOWED
    allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
    assert "authorization" in allowed_headers.lower()


def test_preflight_from_unknown_origin_gets_no_cors_headers():
    response = preflight(BLOCKED)

    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") is None


def test_cors_header_is_present_on_error_responses():
    response = APIClient().get("/api/clients/", HTTP_ORIGIN=ALLOWED)

    assert response.status_code == 401
    assert response.headers.get("Access-Control-Allow-Origin") == ALLOWED
