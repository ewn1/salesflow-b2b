import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from sales.models import CSVUpload, Order
from sales.tasks import process_csv_upload
from sales.tasks import normalize_status

HEADER = (
    "documento_cliente,nome_cliente,email_cliente,telefone_cliente,"
    "segmento_cliente,estado_cliente,numero_pedido,data_pedido,"
    "valor_pedido,categoria_produto,status_pedido\n"
)


@pytest.mark.django_db
def test_import_maps_portuguese_status_to_internal_value(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path  # arquivo de teste vai para pasta temporária

    user = get_user_model().objects.create_user(username="u1", password="x")
    row = "11111111000191,Acme,a@acme.com,1199999999,Varejo,SP,1001,2026-01-15,1500.50,Papelaria,Concluido\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    assert Order.objects.get().status == "COMPLETED"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Concluido", "COMPLETED"),
        ("  CONCLUÍDO ", "COMPLETED"),
        ("pendente", "PENDING"),
        ("Cancelado", "CANCELLED"),
    ],
)
def test_normalize_status_accepts_variations(raw, expected):
    assert normalize_status(raw) == expected


def test_normalize_status_rejects_unknown_value():
    with pytest.raises(ValueError):
        normalize_status("Atrasado")
