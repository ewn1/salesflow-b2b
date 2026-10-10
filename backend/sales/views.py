from rest_framework import viewsets, permissions, status
from .models import Order, CSVUpload
from .serializers import OrderSerializer, CSVUploadSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .tasks import process_csv_upload
from django.shortcuts import get_object_or_404
import uuid


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestão de pedidos.
    Garante que o usuário só acesse pedidos atrelados aos SEUS clientes.
    """

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # A mágica da segurança relacional:
        # Filtra os pedidos onde o "dono" do cliente associado é o usuário logado
        return Order.objects.filter(client__user=self.request.user)


class CSVUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = CSVUploadSerializer(data=request.data)

        if serializer.is_valid():
            # Pre-generate the task id so it is saved BEFORE the task is queued
            task_id = str(uuid.uuid4())
            # Per-user isolation: each user can only see their own uploads, so we save the user in the model
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
        # get_object_or_404 já retorna erro 404 automaticamente se não existir
        # ou se não pertencer ao usuário logado
        upload = get_object_or_404(CSVUpload, id=pk, user=request.user)

        # Reutilizamos o serializer
        serializer = CSVUploadSerializer(upload)

        return Response(serializer.data, status=status.HTTP_200_OK)
