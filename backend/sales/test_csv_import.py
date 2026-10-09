import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from sales.models import CSVUpload, Order
from sales.tasks import process_csv_upload
from sales.tasks import normalize_status

from clients.models import Client

from datetime import date
from django.utils import timezone

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


@pytest.mark.django_db
def test_import_saves_segment_state_and_category(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u2", password="x")
    row = "22222222000191,Beta,b@beta.com,1188888888,Varejo,SP,2001,2026-02-10,300.00,Papelaria,Pendente\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    client = Client.objects.get(user=user)
    assert client.segment == "Varejo"
    assert client.state == "SP"
    assert Order.objects.get().product_category == "Papelaria"


@pytest.mark.django_db
def test_import_skips_bad_rows_and_reports_them(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u3", password="x")
    good = "33333333000191,Gama,g@gama.com,1177777777,Varejo,RJ,3001,2026-03-05,100.00,Papelaria,Concluido\n"
    bad = "44444444000191,Delta,d@delta.com,1166666666,Varejo,MG,4001,2026-03-06,200.00,Papelaria,Atrasado\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + good + bad).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    assert upload.total_records == 2
    assert upload.processed_records == 1
    assert "Line 3" in upload.error_log
    assert Order.objects.filter(order_number="3001").exists()
    assert not Order.objects.filter(order_number="4001").exists()


@pytest.mark.django_db
def test_import_parses_brazilian_date_as_aware_datetime(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u4", password="x")
    row = "55555555000191,Epsilon,e@eps.com,1155555555,Varejo,BA,5001,15/01/2026,250.00,Papelaria,Concluido\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.error_log == ""
    order = Order.objects.get()
    assert timezone.is_aware(order.order_date)
    assert timezone.localtime(order.order_date).date() == date(2026, 1, 15)
