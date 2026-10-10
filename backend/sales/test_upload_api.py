import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from sales.models import CSVUpload

User = get_user_model()

CSV_CONTENT = (
    "documento_cliente,nome_cliente,email_cliente,telefone_cliente,"
    "segmento_cliente,estado_cliente,numero_pedido,data_pedido,"
    "valor_pedido,categoria_produto,status_pedido\n"
    "11111111000191,Acme,a@acme.com,1199999999,Varejo,SP,1001,2026-01-15,"
    "1500.50,Papelaria,Concluido\n"
)


def api_for(user):
    """Return an API client authenticated as the given user."""
    api = APIClient()
    api.force_authenticate(user=user)
    return api


def csv_upload(name="sales.csv", content=CSV_CONTENT):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


@pytest.mark.django_db
def test_upload_returns_202_and_stores_task_id(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/upload-csv/", {"file": csv_upload()}, format="multipart"
    )

    assert response.status_code == 202, response.data
    upload = CSVUpload.objects.get(id=response.data["upload_id"])
    assert upload.task_id
    assert upload.status == "COMPLETED"


@pytest.mark.django_db
def test_upload_accepts_uppercase_extension(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/upload-csv/", {"file": csv_upload("SALES.CSV")}, format="multipart"
    )

    assert response.status_code == 202, response.data


@pytest.mark.django_db
def test_upload_rejects_file_over_size_limit(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.CSV_UPLOAD_MAX_BYTES = 100
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/upload-csv/",
        {"file": csv_upload(content="a" * 101)},
        format="multipart",
    )

    assert response.status_code == 400
    assert not CSVUpload.objects.exists()


@pytest.mark.django_db
def test_upload_rejects_non_csv_extension(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    alice = User.objects.create_user(username="alice", password="x")

    response = api_for(alice).post(
        "/api/upload-csv/", {"file": csv_upload("notes.txt")}, format="multipart"
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_requires_authentication():
    response = APIClient().post(
        "/api/upload-csv/", {"file": csv_upload()}, format="multipart"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_upload_status_is_visible_only_to_its_owner(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    alice = User.objects.create_user(username="alice", password="x")
    bob = User.objects.create_user(username="bob", password="x")
    created = api_for(alice).post(
        "/api/upload-csv/", {"file": csv_upload()}, format="multipart"
    )
    url = f"/api/upload-csv/{created.data['upload_id']}/status/"

    assert api_for(alice).get(url).status_code == 200
    assert api_for(bob).get(url).status_code == 404
