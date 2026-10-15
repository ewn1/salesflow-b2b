import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from clients.models import Client

User = get_user_model()


def api_for(user):
    """Return an API client authenticated as the given user."""
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def client_payload(document):
    return {"name": "Acme", "email": "acme@example.com", "cnpj_cpf": document}


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


@pytest.mark.django_db
def test_client_can_be_created_without_email():
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/clients/",
        {"name": "No Email Ltda", "cnpj_cpf": "55555555000191"},
        format="json",
    )

    assert response.status_code == 201, response.data


@pytest.mark.django_db
def test_api_stores_document_with_digits_only():
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/clients/", client_payload("44.444.444/0001-91"), format="json"
    )

    assert response.status_code == 201, response.data
    assert response.data["cnpj_cpf"] == "44444444000191"


@pytest.mark.django_db
def test_api_rejects_punctuated_duplicate_of_existing_document():
    alice = User.objects.create_user(username="alice", password="x")
    api = api_for(alice)
    first = api.post("/api/clients/", client_payload("44444444000191"), format="json")
    assert first.status_code == 201, first.data

    second = api.post(
        "/api/clients/", client_payload("44.444.444/0001-91"), format="json"
    )

    assert second.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize("document", ["123", "abc", "1111111100019"])
def test_api_rejects_document_with_invalid_length(document):
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/clients/", client_payload(document), format="json"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_client_list_is_paginated():
    user = User.objects.create_user(username="alice", password="x")
    Client.objects.bulk_create(
        [Client(user=user, name=f"Client {i}", cnpj_cpf=f"{i:011d}") for i in range(25)]
    )
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/clients/")

    assert response.status_code == 200
    assert response.data["count"] == 25
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None


@pytest.mark.django_db
def test_client_list_can_be_searched_by_name():
    user = User.objects.create_user(username="alice", password="x")
    Client.objects.create(user=user, name="Acme Papelaria", cnpj_cpf="11111111000191")
    Client.objects.create(user=user, name="Beta Tintas", cnpj_cpf="22222222000191")
    Client.objects.create(user=user, name="Gama Moveis", cnpj_cpf="33333333000191")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/clients/", {"search": "acme"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Acme Papelaria"


@pytest.mark.django_db
def test_search_never_returns_another_users_clients():
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    Client.objects.create(user=alice, name="Acme Papelaria", cnpj_cpf="11111111000191")
    Client.objects.create(user=bob, name="Acme Bob", cnpj_cpf="44444444000191")
    api = APIClient()
    api.force_authenticate(user=alice)

    response = api.get("/api/clients/", {"search": "acme"})

    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Acme Papelaria"
