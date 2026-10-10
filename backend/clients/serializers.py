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

    def validate_cnpj_cpf(self, value):
        user = self.context["request"].user
        duplicates = Client.objects.filter(user=user, cnpj_cpf=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                "You already have a client with this document."
            )
        return value
