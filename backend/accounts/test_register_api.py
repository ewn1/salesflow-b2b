import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

URL = "/api/auth/register/"
PASSWORD = "S3cure-pass-phrase!"


def valid_payload(**overrides):
    payload = {"username": "alice", "email": "alice@example.com", "password": PASSWORD}
    payload.update(overrides)
    return payload


def register(payload):
    return APIClient().post(URL, payload, format="json")


@pytest.mark.django_db
def test_register_creates_a_user_without_authentication():
    response = register(valid_payload())

    assert response.status_code == 201
    assert User.objects.filter(username="alice").exists()


@pytest.mark.django_db
def test_register_never_returns_the_password():
    response = register(valid_payload())

    assert response.status_code == 201
    assert "password" not in response.data


@pytest.mark.django_db
def test_register_stores_a_hashed_password():
    register(valid_payload())

    user = User.objects.get(username="alice")
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


@pytest.mark.django_db
@pytest.mark.parametrize("weak_password", ["123", "password", "12345678"])
def test_register_rejects_weak_passwords(weak_password):
    response = register(valid_payload(password=weak_password))

    assert response.status_code == 400
    assert "password" in response.data
    assert not User.objects.exists()


@pytest.mark.django_db
def test_register_rejects_duplicate_username():
    User.objects.create_user(username="alice", email="other@example.com", password="x")

    response = register(valid_payload())

    assert response.status_code == 400
    assert "username" in response.data


@pytest.mark.django_db
def test_register_rejects_duplicate_email_ignoring_case():
    User.objects.create_user(username="bob", email="Alice@Example.com", password="x")

    response = register(valid_payload())

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_register_requires_an_email():
    response = register(valid_payload(email=""))

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_registered_user_can_log_in():
    register(valid_payload())

    response = APIClient().post(
        "/api/auth/token/",
        {"username": "alice", "password": PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data
