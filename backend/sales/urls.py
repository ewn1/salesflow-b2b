from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CSVUploadView, CSVUploadStatusView

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
]
