import csv
import logging
import re
from celery import shared_task
from django.db import DatabaseError, transaction
from .models import CSVUpload, Client, Order
import unicodedata

from django.core.exceptions import ValidationError

from datetime import datetime
from django.utils import timezone

from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

STATUS_MAP = {
    "pendente": "PENDING",
    "processando": "PROCESSING",
    "concluido": "COMPLETED",
    "cancelado": "CANCELLED",
}

REQUIRED_COLUMNS = (
    "documento_cliente",
    "nome_cliente",
    "numero_pedido",
    "data_pedido",
    "valor_pedido",
    "status_pedido",
)

DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def normalize_status(raw_status):
    """Translate a CSV status label (e.g. 'Concluído') to the internal value."""
    ascii_text = (
        unicodedata.normalize("NFKD", raw_status or "")
        .encode("ascii", "ignore")
        .decode()
    )
    key = ascii_text.strip().lower()
    if key not in STATUS_MAP:
        raise ValueError(f"Unknown order status: {raw_status!r}")
    return STATUS_MAP[key]


def parse_order_date(raw_date):
    """Parse a CSV date (YYYY-MM-DD or DD/MM/YYYY) into an aware datetime."""
    text = (raw_date or "").strip()
    for date_format in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, date_format)
        except ValueError:
            continue
        return timezone.make_aware(parsed)
    raise ValueError(f"Invalid date {raw_date!r}; use YYYY-MM-DD or DD/MM/YYYY")


def parse_order_amount(raw_amount):
    """Parse a CSV amount ('1500.50', '1500,50', '1.500,50') into a Decimal."""
    text = (raw_amount or "").strip()
    if not re.fullmatch(r"\d[\d.,]*", text):
        raise ValueError(f"Invalid amount {raw_amount!r}")

    last_dot = text.rfind(".")
    last_comma = text.rfind(",")

    decimal_sep = None
    if last_dot != -1 and last_comma != -1:
        # Ambos separadores existem, o último é o separador decimal
        decimal_sep = "." if last_dot > last_comma else ","
    elif last_dot != -1 or last_comma != -1:
        sep = "." if last_dot != -1 else ","
        if text.count(sep) == 1:
            digits_after = len(text) - text.rfind(sep) - 1
            if digits_after == 3:
                raise ValueError(f"Ambiguous amount {raw_amount!r}")
            decimal_sep = sep
        # Se o mesmo separador se repetir ('1.234.567'), trata-se de um separador de milhares.

    if decimal_sep:
        integer_part, _, fraction = text.rpartition(decimal_sep)
        digits = integer_part.replace(".", "").replace(",", "")
        normalized = f"{digits}.{fraction}"
    else:
        normalized = text.replace(".", "").replace(",", "")

    try:
        return Decimal(normalized)
    except InvalidOperation:
        raise ValueError(f"Invalid amount {raw_amount!r}")


@shared_task
def process_csv_upload(upload_id):
    try:
        # Busca o registro do upload e muda o status para PROCESSANDO
        upload = CSVUpload.objects.get(id=upload_id)
        upload.status = "PROCESSING"
        upload.save(update_fields=["status"])

        file_path = upload.file.path
        processed_count = 0
        errors = []

        # utf-8-sig remove o BOM (caractere invisível) caso o arquivo venha do Excel
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Normaliza o nome das colunas para minúsculas e remove espaços em branco extras
            reader = csv.DictReader(f)
            reader.fieldnames = [
                name.strip().lower() for name in (reader.fieldnames or []) if name
            ]

            missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing:
                raise ValueError("Missing required columns: " + ", ".join(missing))

            rows = list(reader)
            upload.total_records = len(rows)
            upload.save(update_fields=["total_records"])

            for line_number, row in enumerate(
                rows, start=2
            ):  # start=2 para considerar o cabeçalho:
                try:
                    with transaction.atomic():

                        # === 1. CLIENTE (CLIENT) ===
                        # Chave de busca (unique_together): user + cnpj_cpf
                        # Assim garantimos o multitenancy: o CNPJ é único apenas para ESTE usuário
                        customer, _ = Client.objects.update_or_create(
                            user=upload.user,
                            cnpj_cpf=row["documento_cliente"].strip(),
                            defaults={
                                "name": row.get("nome_cliente"),
                                "email": row.get("email_cliente"),
                                "phone": row.get("telefone_cliente"),
                                "segment": (row.get("segmento_cliente") or "").strip(),
                                "state": (row.get("estado_cliente") or "")
                                .strip()
                                .upper(),
                            },
                        )

                        # === 2. PEDIDO (ORDER) ===
                        # O modelo Order NÃO possui o campo 'user', ele é vinculado via 'client'
                        # Chave de busca (unique_together): client + order_number
                        Order.objects.update_or_create(
                            client=customer,
                            order_number=row.get("numero_pedido").strip(),
                            defaults={
                                "order_date": parse_order_date(row.get("data_pedido")),
                                "total_amount": parse_order_amount(
                                    row.get("valor_pedido")
                                ),
                                "status": normalize_status(row.get("status_pedido")),
                                "product_category": (
                                    row.get("categoria_produto") or ""
                                ).strip(),
                            },
                        )
                except (ValueError, ValidationError, DatabaseError) as exc:
                    errors.append(f"Line {line_number}: {exc}")
                    continue  # Pula para a próxima linha do CSV, sem interromper o processamento

                processed_count += 1

                # A cada 100 registros, atualiza o progresso no banco de dados
                if processed_count % 100 == 0:
                    upload.processed_records = processed_count
                    upload.save(update_fields=["processed_records"])

        # Finaliza o processamento com sucesso
        upload.processed_records = processed_count
        upload.error_log = "\n".join(errors)
        upload.status = "COMPLETED"
        upload.save()

        return f"Done: {processed_count} linhas processadas, {len(errors)} linhas com erros."

    except Exception as e:
        logger.error(f"Erro no processamento do upload {upload_id}: {str(e)}")
        # Se ocorrer qualquer erro crítico, falha a task inteira e salva o log
        if "upload" in locals():
            upload.status = "FAILED"
            upload.error_log = str(e)
            upload.save()
