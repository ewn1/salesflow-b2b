from django.db import models
from clients.models import Client


class Order(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendente"),
        ("PROCESSING", "Em Processamento"),
        ("COMPLETED", "Concluído"),
        ("CANCELLED", "Cancelado"),
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    order_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"Pedido #{self.id} - {self.client.name} - R$ {self.total_amount}"
