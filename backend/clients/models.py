from django.db import models
from django.contrib.auth.models import User


class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="clients")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    cnpj_cpf = models.CharField(max_length=20)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("user", "cnpj_cpf")

    def __str__(self):
        return f"{self.name} - {self.company_name or 'Pessoa Física'}"
