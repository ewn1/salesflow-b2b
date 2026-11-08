import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

URL = "/api/auth/me/"
PASSWORD = "S3cure-pass-phrase!"


def create_user(username="alice", email="alice@example.com"):
    return User.objects.create_user(username=username, email=email, password=PASSWORD)


def client_logged_in_as(user):
    """Return a client carrying a real access token issued by the login route."""
    response = APIClient().post(
        "/api/auth/token/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.mark.django_db
def test_me_requires_authentication():
    response = APIClient().get(URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_rejects_an_invalid_token():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

    response = client.get(URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_only_the_public_profile_of_the_user():
    user = create_user()

    response = client_logged_in_as(user).get(URL)

    assert response.status_code == 200
    assert response.data == {
        "id": user.id,
        "username": "alice",
        "email": "alice@example.com",
    }


@pytest.mark.django_db
def test_me_returns_the_user_that_owns_the_token():
    create_user("alice", "alice@example.com")
    bob = create_user("bob", "bob@example.com")

    response = client_logged_in_as(bob).get(URL)

    assert response.status_code == 200
    assert response.data["username"] == "bob"


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_me_is_read_only(method):
    client = client_logged_in_as(create_user())

    response = getattr(client, method)(URL, {}, format="json")

    assert response.status_code == 405
