from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer responsável por validar e estruturar os dados dos clientes B2B.
    Garante a integridade do CNPJ/CPF e associa o registro ao usuário autenticado.
    """

    class Meta:
        model = Client
        fields = [
            "id",
            "user",
            "name",
            "email",
            "phone",
            "cnpj_cpf",
            "company_name",
            "created_at",
            "updated_at",
        ]
        # Garante que o usuário logado não precise enviar o seu próprio ID no payload JSON, pois ele será automaticamente associado ao cliente criado.
        read_only_fields = ["id", "user", "created_at", "updated_at"]
