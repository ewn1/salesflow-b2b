from django.conf import settings
from rest_framework import serializers

from clients.models import Client

from .models import CSVUpload, Order


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ["id", "created_at"]

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            fields["client"].queryset = Client.objects.filter(user=user)
        else:
            fields["client"].queryset = Client.objects.none()
        return fields


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
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError(
                "Invalid extension. Upload only .csv files."
            )
        if value.size > settings.CSV_UPLOAD_MAX_BYTES:
            raise serializers.ValidationError(
                "File too large. "
                f"Maximum size is {settings.CSV_UPLOAD_MAX_BYTES} bytes."
            )
        return value
