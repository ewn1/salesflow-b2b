import uuid

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from sales.filters import OrderFilter

from .models import CSVUpload, Order
from .serializers import CSVUploadSerializer, OrderSerializer
from .tasks import process_csv_upload


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing orders.
    Ensures users can only access orders linked to THEIR clients.
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = OrderFilter
    search_fields = ["order_number", "client__name", "product_category"]

    def get_queryset(self):
        return Order.objects.filter(client__user=self.request.user).order_by(
            "-order_date", "-pk"
        )


class CSVUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)

        if serializer.is_valid():
            # Pre-generate the task id so it is saved BEFORE the task is queued
            task_id = str(uuid.uuid4())
            # Per-user isolation: the upload is saved with its owner
            upload_instance = serializer.save(user=request.user, task_id=task_id)
            process_csv_upload.apply_async(args=[upload_instance.id], task_id=task_id)
            return Response(
                {
                    "message": "File received. Processing started.",
                    "upload_id": upload_instance.id,
                    "status": upload_instance.status,
                },
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CSVUploadStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        # get_object_or_404 already returns a 404 if the object does not exist
        # or does not belong to the logged-in user
        upload = get_object_or_404(CSVUpload, id=pk, user=request.user)

        # We reuse the serializer to return the current state of the upload,
        # including status and progress.
        serializer = CSVUploadSerializer(upload)

        return Response(serializer.data, status=status.HTTP_200_OK)
