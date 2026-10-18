from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from clients.models import Client
from sales.models import Order

User = get_user_model()

URL = "/api/dashboard/summary/"


def make_client(user, name, document):
    return Client.objects.create(user=user, name=name, cnpj_cpf=document)


def make_order(client, number, amount, status="COMPLETED", when=None, category=""):
    return Order.objects.create(
        client=client,
        order_number=number,
        total_amount=Decimal(amount),
        status=status,
        order_date=when or timezone.now(),
        product_category=category,
    )


def at(year, month, day):
    """Aware datetime at noon, in the project time zone."""
    return timezone.make_aware(datetime(year, month, day, 12, 0))


def api_for(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.mark.django_db
def test_summary_requires_authentication():
    response = APIClient().get(URL)

    assert response.status_code == 401


@pytest.mark.django_db
def test_summary_totals_and_distinct_active_clients():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    bob = make_client(owner, "Bob", "22222222222")
    make_order(alice, "A-1", "100.00")
    make_order(alice, "A-2", "20.00")
    make_order(bob, "B-1", "30.50")

    response = api_for(owner).get(URL)

    assert response.status_code == 200
    assert response.json() == {
        "revenue": "150.50",
        "orders_count": 3,
        "average_ticket": "50.17",
        "active_clients": 2,
    }


@pytest.mark.django_db
def test_summary_ignores_cancelled_orders():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    bob = make_client(owner, "Bob", "22222222222")
    make_order(alice, "A-1", "100.00")
    make_order(alice, "A-2", "999.00", status="CANCELLED")
    make_order(bob, "B-1", "500.00", status="CANCELLED")

    response = api_for(owner).get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["revenue"] == "100.00"
    assert body["orders_count"] == 1
    assert body["active_clients"] == 1


@pytest.mark.django_db
def test_summary_never_counts_another_users_orders():
    owner = User.objects.create_user(username="owner", password="x")
    stranger = User.objects.create_user(username="stranger", password="x")
    make_order(make_client(owner, "Alice", "11111111111"), "A-1", "100.00")
    make_order(make_client(stranger, "Eve", "33333333333"), "E-1", "500.00")

    response = api_for(owner).get(URL)

    assert response.status_code == 200
    body = response.json()
    assert body["revenue"] == "100.00"
    assert body["orders_count"] == 1
    assert body["active_clients"] == 1


@pytest.mark.django_db
def test_summary_is_zeroed_when_there_are_no_orders():
    owner = User.objects.create_user(username="owner", password="x")

    response = api_for(owner).get(URL)

    assert response.status_code == 200
    assert response.json() == {
        "revenue": "0.00",
        "orders_count": 0,
        "average_ticket": "0.00",
        "active_clients": 0,
    }


@pytest.mark.django_db
def test_summary_can_be_limited_to_a_period():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    make_order(alice, "A-1", "100.00", when=at(2026, 1, 10))
    make_order(alice, "A-2", "200.00", when=at(2026, 2, 10))
    make_order(alice, "A-3", "400.00", when=at(2026, 3, 10))

    response = api_for(owner).get(
        URL,
        {"order_date_after": "2026-02-01", "order_date_before": "2026-02-28"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["revenue"] == "200.00"
    assert body["orders_count"] == 1


@pytest.mark.django_db
def test_summary_rejects_an_invalid_date():
    owner = User.objects.create_user(username="owner", password="x")

    response = api_for(owner).get(URL, {"order_date_after": "not-a-date"})

    assert response.status_code == 400


MONTH_URL = "/api/dashboard/sales-by-month/"
CATEGORY_URL = "/api/dashboard/sales-by-category/"
GROUPED_URLS = [MONTH_URL, CATEGORY_URL]


@pytest.mark.parametrize("url", GROUPED_URLS)
@pytest.mark.django_db
def test_grouped_endpoints_require_authentication(url):
    response = APIClient().get(url)

    assert response.status_code == 401


@pytest.mark.parametrize("url", GROUPED_URLS)
@pytest.mark.django_db
def test_grouped_endpoints_return_an_empty_list_without_orders(url):
    owner = User.objects.create_user(username="owner", password="x")

    response = api_for(owner).get(url)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("url", GROUPED_URLS)
@pytest.mark.django_db
def test_grouped_endpoints_ignore_cancelled_and_foreign_orders(url):
    owner = User.objects.create_user(username="owner", password="x")
    stranger = User.objects.create_user(username="stranger", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    make_order(alice, "A-1", "100.00")
    make_order(alice, "A-2", "999.00", status="CANCELLED")
    make_order(make_client(stranger, "Eve", "33333333333"), "E-1", "500.00")

    response = api_for(owner).get(url)

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["revenue"] == "100.00"
    assert rows[0]["orders_count"] == 1


@pytest.mark.parametrize("url", GROUPED_URLS)
@pytest.mark.django_db
def test_grouped_endpoints_can_be_limited_to_a_period(url):
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    make_order(alice, "A-1", "100.00", when=at(2026, 1, 10))
    make_order(alice, "A-2", "200.00", when=at(2026, 2, 10))

    response = api_for(owner).get(
        url,
        {"order_date_after": "2026-02-01", "order_date_before": "2026-02-28"},
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["revenue"] == "200.00"


@pytest.mark.django_db
def test_sales_by_month_groups_and_sorts_chronologically():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    # February is created first so insertion order cannot fake the sorting.
    make_order(alice, "A-1", "200.00", when=at(2026, 2, 10))
    make_order(alice, "A-2", "100.00", when=at(2026, 1, 10))
    make_order(alice, "A-3", "50.00", when=at(2026, 1, 20))

    response = api_for(owner).get(MONTH_URL)

    assert response.status_code == 200
    assert response.json() == [
        {"month": "2026-01", "revenue": "150.00", "orders_count": 2},
        {"month": "2026-02", "revenue": "200.00", "orders_count": 1},
    ]


@pytest.mark.django_db
def test_sales_by_month_uses_the_project_time_zone():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    # 23:30 on Jan 31 in Sao Paulo is already Feb 1 in UTC.
    late_january = timezone.make_aware(datetime(2026, 1, 31, 23, 30))
    early_february = timezone.make_aware(datetime(2026, 2, 1, 0, 30))
    make_order(alice, "A-1", "10.00", when=late_january)
    make_order(alice, "A-2", "20.00", when=early_february)

    response = api_for(owner).get(MONTH_URL)

    assert response.status_code == 200
    assert [row["month"] for row in response.json()] == ["2026-01", "2026-02"]


@pytest.mark.django_db
def test_sales_by_category_groups_and_sorts_by_revenue():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    make_order(alice, "A-1", "100.00", category="Software")
    make_order(alice, "A-2", "50.00", category="Software")
    make_order(alice, "A-3", "300.00", category="Hardware")

    response = api_for(owner).get(CATEGORY_URL)

    assert response.status_code == 200
    assert response.json() == [
        {"category": "Hardware", "revenue": "300.00", "orders_count": 1},
        {"category": "Software", "revenue": "150.00", "orders_count": 2},
    ]


@pytest.mark.django_db
def test_sales_by_category_labels_orders_without_category():
    owner = User.objects.create_user(username="owner", password="x")
    alice = make_client(owner, "Alice", "11111111111")
    make_order(alice, "A-1", "100.00")

    response = api_for(owner).get(CATEGORY_URL)

    assert response.status_code == 200
    assert response.json() == [
        {"category": "Uncategorized", "revenue": "100.00", "orders_count": 1},
    ]
