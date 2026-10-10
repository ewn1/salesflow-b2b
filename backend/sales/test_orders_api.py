import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from clients.models import Client
from sales.models import Order

User = get_user_model()


def api_for(user):
    """Return an API client authenticated as the given user."""
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def order_payload(client_id, number="A-1"):
    return {
        "order_number": number,
        "client": client_id,
        "total_amount": "10.00",
        "status": "PENDING",
        "order_date": "2026-06-01T10:00:00Z",
    }


@pytest.mark.django_db
def test_user_cannot_create_order_for_another_users_client():
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    bobs_client = Client.objects.create(
        user=bob, name="Bob Client", cnpj_cpf="22222222000191"
    )

    response = api_for(alice).post(
        "/api/orders/", order_payload(bobs_client.id), format="json"
    )

    assert response.status_code == 400
    assert not Order.objects.exists()


@pytest.mark.django_db
def test_user_cannot_move_own_order_to_another_users_client():
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    own_client = Client.objects.create(
        user=alice, name="Alice Client", cnpj_cpf="33333333000191"
    )
    bobs_client = Client.objects.create(
        user=bob, name="Bob Client", cnpj_cpf="22222222000191"
    )
    api = api_for(alice)
    created = api.post("/api/orders/", order_payload(own_client.id), format="json")
    assert created.status_code == 201

    response = api.patch(
        f"/api/orders/{created.data['id']}/",
        {"client": bobs_client.id},
        format="json",
    )

    assert response.status_code == 400
    assert Order.objects.get().client_id == own_client.id


@pytest.mark.django_db
def test_orders_endpoint_requires_authentication():
    response = APIClient().get("/api/orders/")

    assert response.status_code == 401
