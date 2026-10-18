from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .dashboard_views import (
    DashboardSummaryView,
    SalesByCategoryView,
    SalesByMonthView,
    TopClientsView,
)
from .views import CSVUploadStatusView, CSVUploadView, OrderViewSet

# O router cuida dos ViewSets (CRUD)
router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")

# urlpatterns combina as rotas do router com as rotas customizadas
urlpatterns = [
    # inclui todas as rotas geradas pelo router (/orders/, /orders/<id>/)
    path("", include(router.urls)),
    # rota manual e explícita para o upload (pois é uma APIView)
    path("upload-csv/", CSVUploadView.as_view(), name="upload-csv"),
    # rota que consulta o status do upload pelo id utilizando uuid
    path(
        "upload-csv/<uuid:pk>/status/",
        CSVUploadStatusView.as_view(),
        name="upload-csv-status",
    ),
    path(
        "dashboard/summary/",
        DashboardSummaryView.as_view(),
        name="dashboard-summary",
    ),
    path(
        "dashboard/sales-by-month/",
        SalesByMonthView.as_view(),
        name="dashboard-sales-by-month",
    ),
    path(
        "dashboard/sales-by-category/",
        SalesByCategoryView.as_view(),
        name="dashboard-sales-by-category",
    ),
    path(
        "dashboard/top-clients/",
        TopClientsView.as_view(),
        name="dashboard-top-clients",
    ),
]
