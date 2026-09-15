from rest_framework import viewsets, permissions
from .models import Order
from .serializers import OrderSerializer


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
