from datetime import date
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from clients.models import Client
from sales.models import CSVUpload, Order
from sales.tasks import normalize_status, process_csv_upload

HEADER = (
    "documento_cliente,nome_cliente,email_cliente,telefone_cliente,"
    "segmento_cliente,estado_cliente,numero_pedido,data_pedido,"
    "valor_pedido,categoria_produto,status_pedido\n"
)


def import_rows(user, *rows):
    """Upload a CSV made of HEADER + the given rows and run the import."""
    content = HEADER + "".join(rows)
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", content.encode("utf-8")),
    )
    process_csv_upload(upload.id)
    upload.refresh_from_db()
    return upload


@pytest.mark.django_db
def test_import_maps_portuguese_status_to_internal_value(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path  # test files go to a temporary folder

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


@pytest.mark.django_db
def test_order_date_keeps_the_same_calendar_day_in_brazil(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u5", password="x")
    row = "66666666000191,Zeta,z@zeta.com,1144444444,Varejo,SP,6001,15/01/2026,80.00,Papelaria,Concluido\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    order = Order.objects.get()
    sao_paulo = order.order_date.astimezone(ZoneInfo("America/Sao_Paulo"))
    assert sao_paulo.date() == date(2026, 1, 15)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("1500.50", Decimal("1500.50")),
        ("1500,50", Decimal("1500.50")),
        ("1.500,50", Decimal("1500.50")),
        ("1,500.50", Decimal("1500.50")),
        ("1500", Decimal("1500")),
        ("  250.00 ", Decimal("250.00")),
    ],
)
def test_parse_order_amount_accepts_common_formats(raw, expected):
    from sales.tasks import parse_order_amount

    assert parse_order_amount(raw) == expected


@pytest.mark.parametrize("raw", ["1.500", "1,500", "abc", "", "12,3x"])
def test_parse_order_amount_rejects_ambiguous_or_invalid(raw):
    from sales.tasks import parse_order_amount

    with pytest.raises(ValueError):
        parse_order_amount(raw)


@pytest.mark.django_db
def test_import_saves_amount_written_in_brazilian_format(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u6", password="x")
    row = '77777777000191,Eta,e@eta.com,1133333333,Varejo,RS,7001,2026-04-01,"1.500,50",Papelaria,Concluido\n'
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.error_log == ""
    assert Order.objects.get().total_amount == Decimal("1500.50")


@pytest.mark.django_db
def test_import_fails_with_clear_message_when_required_columns_are_missing(
    settings, tmp_path
):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u7", password="x")
    content = "documento_cliente,nome_cliente\n11111111000191,Acme\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", content.encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "FAILED"
    assert "Missing required columns" in upload.error_log
    assert "numero_pedido" in upload.error_log


@pytest.mark.django_db
def test_import_rejects_rows_with_missing_required_values(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u8", password="x")
    good = "88888888000191,Ok Ltda,ok@x.com,1100000000,Varejo,SP,8001,2026-05-01,10.00,Papelaria,Concluido\n"
    no_doc = ",Sem Doc,s@x.com,1100000000,Varejo,SP,8002,2026-05-02,10.00,Papelaria,Concluido\n"
    no_number = "77777777000191,Sem Numero,n@x.com,1100000000,Varejo,SP,,2026-05-03,10.00,Papelaria,Concluido\n"
    short = "66666666000191,Curta\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile(
            "t.csv", (HEADER + good + no_doc + no_number + short).encode("utf-8")
        ),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    assert upload.total_records == 4
    assert upload.processed_records == 1
    assert "Line 3" in upload.error_log
    assert "Line 4" in upload.error_log
    assert "Line 5" in upload.error_log
    assert not Client.objects.filter(cnpj_cpf="").exists()


@pytest.mark.django_db
def test_import_accepts_semicolon_delimited_file(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u9", password="x")
    header = HEADER.replace(",", ";")
    row = "99999999000191;Ponto e Virgula;pv@x.com;1100000000;Varejo;SP;9001;15/01/2026;1.500,50;Papelaria;Concluido\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (header + row).encode("utf-8")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    assert upload.error_log == ""
    assert Order.objects.get().total_amount == Decimal("1500.50")


@pytest.mark.django_db
def test_import_accepts_windows_1252_encoded_file(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    user = get_user_model().objects.create_user(username="u10", password="x")
    row = "10101010000191,Açaí Ltda,a@acai.com,1100000000,Varejo,SP,10001,2026-01-15,50.00,Papelaria,Concluido\n"
    upload = CSVUpload.objects.create(
        user=user,
        file=SimpleUploadedFile("t.csv", (HEADER + row).encode("cp1252")),
    )

    process_csv_upload(upload.id)

    upload.refresh_from_db()
    assert upload.status == "COMPLETED", upload.error_log
    assert Client.objects.get(user=user).name == "Açaí Ltda"


@pytest.mark.django_db
def test_importing_the_same_file_twice_does_not_duplicate_data(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = get_user_model().objects.create_user(username="u11", password="x")
    row = "12121212000191,Repetida,r@x.com,1100000000,Varejo,SP,11001,2026-06-01,100.00,Papelaria,Pendente\n"
    changed = "12121212000191,Repetida,r@x.com,1100000000,Varejo,SP,11001,2026-06-01,250.00,Papelaria,Concluido\n"

    import_rows(user, row)
    second = import_rows(user, row)
    assert second.error_log == ""
    assert Client.objects.filter(user=user).count() == 1
    assert Order.objects.filter(client__user=user).count() == 1

    import_rows(user, changed)
    order = Order.objects.get(client__user=user)
    assert order.total_amount == Decimal("250.00")
    assert order.status == "COMPLETED"


@pytest.mark.django_db
def test_same_document_in_two_accounts_stays_isolated(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user_a = get_user_model().objects.create_user(username="ua", password="x")
    user_b = get_user_model().objects.create_user(username="ub", password="x")
    row_a = "13131313000191,Alfa,a@x.com,1100000000,Varejo,SP,12001,2026-06-01,10.00,Papelaria,Pendente\n"
    row_b = "13131313000191,Beta,b@x.com,1100000000,Varejo,RJ,12001,2026-06-01,99.00,Papelaria,Pendente\n"

    import_rows(user_a, row_a)
    import_rows(user_b, row_b)

    assert Client.objects.filter(cnpj_cpf="13131313000191").count() == 2
    assert Client.objects.get(user=user_a).name == "Alfa"
    assert Client.objects.get(user=user_b).name == "Beta"
    assert Order.objects.get(client__user=user_a).total_amount == Decimal("10.00")


@pytest.mark.django_db
def test_document_with_punctuation_matches_the_same_client(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    user = get_user_model().objects.create_user(username="u12", password="x")
    punctuated = "11.111.111/0001-91,Mascarada,m@x.com,1100000000,Varejo,SP,13001,2026-06-01,10.00,Papelaria,Pendente\n"
    plain = "11111111000191,Mascarada,m@x.com,1100000000,Varejo,SP,13002,2026-06-02,20.00,Papelaria,Pendente\n"

    upload = import_rows(user, punctuated, plain)

    assert upload.error_log == ""
    assert Client.objects.filter(user=user).count() == 1
    assert Client.objects.get(user=user).cnpj_cpf == "11111111000191"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("11.111.111/0001-91", "11111111000191"),
        ("111.444.777-35", "11144477735"),
        (" 11111111000191 ", "11111111000191"),
    ],
)
def test_normalize_document_keeps_only_digits(raw, expected):
    from sales.tasks import normalize_document

    assert normalize_document(raw) == expected


@pytest.mark.parametrize("raw", ["123", "abc", "1111111100019"])
def test_normalize_document_rejects_invalid_length(raw):
    from sales.tasks import normalize_document

    with pytest.raises(ValueError):
        normalize_document(raw)
