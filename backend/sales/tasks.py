import csv
import io
import logging
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

from celery import shared_task
from django.core.exceptions import ValidationError
from django.db import DatabaseError, transaction
from django.utils import timezone

from clients.documents import normalize_document

from .models import Client, CSVUpload, Order

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
    """Translate a CSV status label (e.g. 'Concluído') into the internal value."""
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
    """Parse a CSV date (YYYY-MM-DD or DD/MM/YYYY) into a timezone-aware datetime."""
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
        # Both separators present: the last one is the decimal separator.
        decimal_sep = "." if last_dot > last_comma else ","
    elif last_dot != -1 or last_comma != -1:
        sep = "." if last_dot != -1 else ","
        if text.count(sep) == 1:
            digits_after = len(text) - text.rfind(sep) - 1
            if digits_after == 3:
                raise ValueError(f"Ambiguous amount {raw_amount!r}")
            decimal_sep = sep
        # A repeated separator ('1.234.567') is a thousands separator.

    if decimal_sep:
        integer_part, _, fraction = text.rpartition(decimal_sep)
        digits = integer_part.replace(".", "").replace(",", "")
        normalized = f"{digits}.{fraction}"
    else:
        normalized = text.replace(".", "").replace(",", "")

    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount {raw_amount!r}") from exc


def get_required(row, column):
    """Return the stripped value of a required column or raise ValueError."""
    value = (row.get(column) or "").strip()
    if not value:
        raise ValueError(f"Missing value for '{column}'")
    return value


def read_csv_text(file_path):
    """Read a CSV file as text (UTF-8, with or without BOM, or Windows-1252)."""
    with open(file_path, "rb") as f:
        raw = f.read()
    try:
        # utf-8-sig also strips the BOM (invisible character) that Excel may add
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1252")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Unsupported file encoding; save the file as UTF-8 or Windows-1252"
        ) from exc


def detect_delimiter(text):
    """Pick ';' (Excel in pt-BR) or ',' by looking at the header line."""
    header_line = text.split("\n", 1)[0]
    return ";" if header_line.count(";") > header_line.count(",") else ","


@shared_task
def process_csv_upload(upload_id):
    try:
        # Fetch the upload record and mark it as PROCESSING
        upload = CSVUpload.objects.get(id=upload_id)
        upload.status = "PROCESSING"
        upload.save(update_fields=["status"])

        file_path = upload.file.path
        processed_count = 0
        errors = []

        text = read_csv_text(file_path)

        with io.StringIO(text) as f:

            # Normalize column names: lowercase and strip extra whitespace
            reader = csv.DictReader(f, delimiter=detect_delimiter(text))
            reader.fieldnames = [
                name.strip().lower() for name in (reader.fieldnames or []) if name
            ]

            missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
            if missing:
                raise ValueError("Missing required columns: " + ", ".join(missing))

            rows = list(reader)
            upload.total_records = len(rows)
            upload.save(update_fields=["total_records"])

            # start=2: line 1 of the file is the header, so data begins on line 2
            for line_number, row in enumerate(rows, start=2):
                try:
                    with transaction.atomic():

                        # === 1. CLIENT ===
                        # Lookup key (unique_together): user + cnpj_cpf
                        # Per-user isolation: the same CNPJ/CPF may exist in
                        # different accounts, but only once within this user's clients
                        customer, _ = Client.objects.update_or_create(
                            user=upload.user,
                            cnpj_cpf=normalize_document(
                                get_required(row, "documento_cliente")
                            ),
                            defaults={
                                "name": get_required(row, "nome_cliente"),
                                "email": (row.get("email_cliente") or "").strip(),
                                "phone": (row.get("telefone_cliente") or "").strip(),
                                "segment": (row.get("segmento_cliente") or "").strip(),
                                "state": (row.get("estado_cliente") or "")
                                .strip()
                                .upper(),
                            },
                        )

                        # === 2. ORDER ===
                        # Order has no 'user'; it belongs to a user via its client
                        # Lookup key (unique_together): client + order_number
                        Order.objects.update_or_create(
                            client=customer,
                            order_number=get_required(row, "numero_pedido"),
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
                    continue  # Skip to the next CSV line without aborting the import

                processed_count += 1

                # Every 100 records, persist progress to the database
                if processed_count % 100 == 0:
                    upload.processed_records = processed_count
                    upload.save(update_fields=["processed_records"])

        # Finish: persist the final count and the per-row error report
        upload.processed_records = processed_count
        upload.error_log = "\n".join(errors)
        upload.status = "COMPLETED"
        upload.save()

        return (
            f"Done: {processed_count} rows processed, {len(errors)} rows with errors."
        )

    except Exception as e:
        logger.error(f"Error processing upload {upload_id}: {str(e)}")
        # File-level failure (unreadable file, missing columns, bug):
        # fail the whole task and store the message in the error log
        if "upload" in locals():
            upload.status = "FAILED"
            upload.error_log = str(e)
            upload.save()
