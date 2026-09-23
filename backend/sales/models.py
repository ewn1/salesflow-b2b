from django.db import models
from clients.models import Client

import uuid
from django.conf import settings


class Order(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pendente"),
        ("PROCESSING", "Em Processamento"),
        ("COMPLETED", "Concluído"),
        ("CANCELLED", "Cancelado"),
    )

    order_number = models.CharField(max_length=50)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="orders")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    order_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-order_date"]
        unique_together = ("client", "order_number")

    def __str__(self):
        return f"Pedido #{self.id} - {self.client.name} - R$ {self.total_amount}"


# Modelo de rastreamento do upload de arquivos.CSV
class CSVUpload(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pendente"),
        ("PROCESSING", "Processando"),
        ("COMPLETED", "Concluído"),
        ("FAILED", "Falhou"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="csv_uploads"
    )
    file = models.FileField(upload_to="csv_uploads/%Y/%m/%d/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    task_id = models.CharField(max_length=255, blank=True, null=True)
    total_records = models.IntegerField(default=0)
    processed_records = models.IntegerField(default=0)
    error_log = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Upload {self.id} - {self.user.email} ({self.status})"
