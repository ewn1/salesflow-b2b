from rest_framework import filters, permissions, viewsets

from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for full CRUD on clients.
    Requires JWT authentication and isolates requests per user.
    """

    serializer_class = ClientSerializer

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "company_name", "cnpj_cpf"]

    def get_queryset(self):
        """
        Ensure users only see the clients that belong to their own account.
        """
        return Client.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically set the authenticated user as the owner before saving.
        """
        serializer.save(user=self.request.user)
