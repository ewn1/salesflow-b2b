from rest_framework import serializers
from .models import Order
from .models import CSVUpload


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class CSVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVUpload
        fields = [
            "id",
            "file",
            "status",
            "task_id",
            "total_records",
            "processed_records",
            "error_log",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "task_id",
            "total_records",
            "processed_records",
            "error_log",
            "created_at",
        ]

    def validate_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError(
                "Extensão inválida. Envie apenas arquivos com formato .csv."
            )
        return value
