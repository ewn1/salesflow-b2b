from rest_framework import viewsets, permissions
from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint para CRUD completo de clientes.
    Exige autenticação JWT e isola as requisições por usuário.
    """

    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Garante que o usuário veja estritamente os clientes associados à sua conta.
        """
        return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Injeta automaticamente o usuário autenticado na requisição antes de salvar no banco.
        """
        serializer.save(user=self.request.user)
