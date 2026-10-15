from rest_framework import permissions, viewsets

from backend.sales.models import Order

from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for full CRUD on clients.
    Requires JWT authentication and isolates requests per user.
    """

    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(client__user=self.request.user).order_by(
            "-order_date", "-pk"
        )

    def perform_create(self, serializer):
        """
        Automatically set the authenticated user as the owner before saving.
        """
        serializer.save(user=self.request.user)
