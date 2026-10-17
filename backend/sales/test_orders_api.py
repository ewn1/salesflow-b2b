from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
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


def make_order(client, number, category="", status="PENDING", order_date=None):
    return Order.objects.create(
        client=client,
        order_number=number,
        order_date=order_date or timezone.now(),
        total_amount=Decimal("10.00"),
        status=status,
        product_category=category,
    )


def local(year, month, day, hour=12):
    return timezone.make_aware(datetime(year, month, day, hour))


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


@pytest.mark.django_db
def test_order_list_can_be_searched_by_order_number():
    user = User.objects.create_user(username="alice", password="x")
    client = Client.objects.create(user=user, name="Acme", cnpj_cpf="11111111000191")
    make_order(client, "A-1001")
    make_order(client, "B-2002")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/orders/", {"search": "2002"})

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["order_number"] == "B-2002"


@pytest.mark.django_db
def test_order_list_can_be_searched_by_client_name():
    user = User.objects.create_user(username="alice", password="x")
    acme = Client.objects.create(user=user, name="Acme", cnpj_cpf="11111111000191")
    beta = Client.objects.create(user=user, name="Beta", cnpj_cpf="22222222000191")
    make_order(acme, "A-1001")
    make_order(beta, "B-2002")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/orders/", {"search": "acme"})

    assert response.data["count"] == 1
    assert response.data["results"][0]["order_number"] == "A-1001"


@pytest.mark.django_db
def test_order_search_never_returns_another_users_orders():
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    mine = Client.objects.create(user=alice, name="Acme", cnpj_cpf="11111111000191")
    theirs = Client.objects.create(user=bob, name="Acme", cnpj_cpf="11111111000191")
    make_order(mine, "A-1001")
    make_order(theirs, "A-9999")
    api = APIClient()
    api.force_authenticate(user=alice)

    response = api.get("/api/orders/", {"search": "acme"})

    assert response.data["count"] == 1
    assert response.data["results"][0]["order_number"] == "A-1001"


@pytest.mark.django_db
def test_order_list_can_be_filtered_by_status():
    user = User.objects.create_user(username="alice", password="x")
    client = Client.objects.create(user=user, name="Acme", cnpj_cpf="11111111000191")
    make_order(client, "A-1001", status="PENDING")
    make_order(client, "B-2002", status="COMPLETED")
    make_order(client, "C-3003", status="COMPLETED")
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/orders/", {"status": "COMPLETED"})

    assert response.status_code == 200
    assert response.data["count"] == 2
    numbers = {order["order_number"] for order in response.data["results"]}
    assert numbers == {"B-2002", "C-3003"}


@pytest.mark.django_db
def test_order_list_can_be_filtered_by_date_range():
    user = User.objects.create_user(username="alice", password="x")
    client = Client.objects.create(user=user, name="Acme", cnpj_cpf="11111111000191")
    make_order(client, "A-1", order_date=local(2026, 1, 10))
    make_order(client, "B-2", order_date=local(2026, 1, 20))
    make_order(client, "C-3", order_date=local(2026, 2, 5))
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get(
        "/api/orders/",
        {"order_date_after": "2026-01-15", "order_date_before": "2026-01-31"},
    )

    assert response.status_code == 200
    numbers = {order["order_number"] for order in response.data["results"]}
    assert numbers == {"B-2"}


@pytest.mark.django_db
def test_date_range_includes_the_whole_last_day():
    user = User.objects.create_user(username="alice", password="x")
    client = Client.objects.create(user=user, name="Acme", cnpj_cpf="11111111000191")
    make_order(client, "A-1", order_date=local(2026, 1, 31, 23))
    make_order(client, "B-2", order_date=local(2026, 2, 1, 1))
    api = APIClient()
    api.force_authenticate(user=user)

    response = api.get("/api/orders/", {"order_date_before": "2026-01-31"})

    numbers = {order["order_number"] for order in response.data["results"]}
    assert numbers == {"A-1"}
