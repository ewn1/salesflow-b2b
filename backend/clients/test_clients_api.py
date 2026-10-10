import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


def api_for(user):
    """Return an API client authenticated as the given user."""
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_duplicate_document_for_same_user_returns_400():
    alice = User.objects.create_user(username="alice", password="x")
    api = api_for(alice)
    payload = {
        "name": "Acme",
        "email": "acme@example.com",
        "cnpj_cpf": "44444444000191",
    }

    first = api.post("/api/clients/", payload, format="json")
    assert first.status_code == 201, first.data

    second = api.post("/api/clients/", payload, format="json")
    assert second.status_code == 400


@pytest.mark.django_db
def test_same_document_is_allowed_for_different_users():
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    payload = {
        "name": "Acme",
        "email": "acme@example.com",
        "cnpj_cpf": "44444444000191",
    }

    assert (
        api_for(alice).post("/api/clients/", payload, format="json").status_code == 201
    )
    assert api_for(bob).post("/api/clients/", payload, format="json").status_code == 201


@pytest.mark.django_db
def test_editing_a_client_does_not_collide_with_itself():
    alice = User.objects.create_user(username="alice", password="x")
    api = api_for(alice)
    created = api.post(
        "/api/clients/",
        {"name": "Acme", "email": "acme@example.com", "cnpj_cpf": "44444444000191"},
        format="json",
    )
    assert created.status_code == 201, created.data

    response = api.patch(
        f"/api/clients/{created.data['id']}/", {"name": "Acme Ltda"}, format="json"
    )

    assert response.status_code == 200, response.data
    assert response.data["name"] == "Acme Ltda"
