import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    order_date = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Order
        fields = ["status", "order_date"]
