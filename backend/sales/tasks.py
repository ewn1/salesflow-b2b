import csv
import logging
from celery import shared_task
from django.db import transaction
from .models import CSVUpload, Client, Order

logger = logging.getLogger(__name__)


@shared_task
def process_csv_upload(upload_id):
    try:
        # Busca o registro do upload e muda o status para PROCESSANDO
        upload = CSVUpload.objects.get(id=upload_id)
        upload.status = "PROCESSING"
        upload.save(update_fields=["status"])

        file_path = upload.file.path
        processed_count = 0

        # utf-8-sig remove o BOM (caractere invisível) caso o arquivo venha do Excel
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            # Normaliza o nome das colunas para minúsculas e remove espaços em branco extras
            reader.fieldnames = [
                name.strip().lower() for name in reader.fieldnames if name
            ]

            for row in reader:
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
                            # Segmento e estado omitidos pois não estão no models.py atualmente.
                        },
                    )

                    # === 2. PEDIDO (ORDER) ===
                    # O modelo Order NÃO possui o campo 'user', ele é vinculado via 'client'
                    # Chave de busca (unique_together): client + order_number
                    Order.objects.update_or_create(
                        client=customer,
                        order_number=row.get("numero_pedido").strip(),
                        defaults={
                            "order_date": row.get("data_pedido"),
                            "total_amount": row.get("valor_pedido"),
                            "status": row.get("status_pedido"),
                        },
                    )

                processed_count += 1

                # A cada 100 registros, atualiza o progresso no banco de dados
                if processed_count % 100 == 0:
                    upload.processed_records = processed_count
                    upload.save(update_fields=["processed_records"])

        # Finaliza o processamento com sucesso
        upload.processed_records = processed_count
        upload.total_records = (
            processed_count  # Atualiza o total também para bater certinho
        )
        upload.status = "COMPLETED"
        upload.save()

        return f"Sucesso! {processed_count} linhas processadas."

    except Exception as e:
        logger.error(f"Erro no processamento do upload {upload_id}: {str(e)}")
        # Se ocorrer qualquer erro crítico, falha a task inteira e salva o log
        if "upload" in locals():
            upload.status = "FAILED"
            upload.error_log = str(e)
            upload.save()
