from rest_framework import viewsets, permissions, status
from .models import Order, CSVUpload
from .serializers import OrderSerializer, CSVUploadSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from .tasks import process_csv_upload
from django.shortcuts import get_object_or_404


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
            # Salva o arquivo vinculando ao usuário autenticado (multitenancy)
            upload_instance = serializer.save(user=request.user)

            # disparo para o celery, o .delay() joga o trabalho para a fila no Redis e libera o Django imediatamente
            process_csv_upload.delay(upload_instance.id)

            return Response(
                {
                    "message": "Arquivo recebido com sucesso. O processamento foi iniciado em segundo plano.",
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
