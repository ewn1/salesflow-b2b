from rest_framework import serializers

from .documents import normalize_document
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """
    Validates and structures B2B client data.
    Normalizes the CNPJ/CPF to digits, rejects duplicates and ties the
    record to the authenticated user.
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
        # 'user' is set from the authenticated request,
        # so clients must not send it in the payload.
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def validate_cnpj_cpf(self, value):
        try:
            value = normalize_document(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

        user = self.context["request"].user
        duplicates = Client.objects.filter(user=user, cnpj_cpf=value)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                "You already have a client with this document."
            )
        return value
