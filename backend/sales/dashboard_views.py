from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import OrderFilter
from .models import Order

TWO_PLACES = Decimal("0.01")
UNCATEGORIZED = "Uncategorized"


def money(value):
    """Format a Decimal as a string with two places (commercial rounding)."""
    return str(value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP))


class DashboardBaseView(generics.GenericAPIView):
    """Shared rules for every dashboard endpoint.

    Only the logged-in user's orders count, cancelled orders never count as
    revenue, and the same period filters used by the orders list apply.
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def get_queryset(self):
        return Order.objects.filter(client__user=self.request.user).exclude(
            status="CANCELLED"
        )


class DashboardSummaryView(DashboardBaseView):
    def get(self, request):
        orders = self.filter_queryset(self.get_queryset())
        totals = orders.aggregate(
            revenue=Sum("total_amount"),
            orders_count=Count("pk"),
            active_clients=Count("client", distinct=True),
        )

        revenue = totals["revenue"] or Decimal("0")
        orders_count = totals["orders_count"]
        average_ticket = revenue / orders_count if orders_count else Decimal("0")

        return Response(
            {
                "revenue": money(revenue),
                "orders_count": orders_count,
                "average_ticket": money(average_ticket),
                "active_clients": totals["active_clients"],
            }
        )


class SalesByMonthView(DashboardBaseView):
    def get(self, request):
        rows = (
            self.filter_queryset(self.get_queryset())
            .annotate(month=TruncMonth("order_date"))
            .values("month")
            .annotate(revenue=Sum("total_amount"), orders_count=Count("pk"))
            .order_by("month")
        )

        return Response(
            [
                {
                    "month": row["month"].strftime("%Y-%m"),
                    "revenue": money(row["revenue"]),
                    "orders_count": row["orders_count"],
                }
                for row in rows
            ]
        )


class SalesByCategoryView(DashboardBaseView):
    def get(self, request):
        rows = (
            self.filter_queryset(self.get_queryset())
            .values("product_category")
            .annotate(revenue=Sum("total_amount"), orders_count=Count("pk"))
            .order_by("-revenue", "product_category")
        )

        return Response(
            [
                {
                    "category": row["product_category"] or UNCATEGORIZED,
                    "revenue": money(row["revenue"]),
                    "orders_count": row["orders_count"],
                }
                for row in rows
            ]
        )
