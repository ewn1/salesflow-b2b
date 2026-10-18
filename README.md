# Sales Flow B2B

[![CI](https://github.com/ewn1/salesflow-b2b/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ewn1/salesflow-b2b/actions/workflows/ci.yml)

A sales dashboard for B2B teams. Users sign up, import their sales from a CSV
file and read aggregated numbers (revenue, sales by month and by category,
top clients). Every user only ever sees their own data.

> **Status:** the backend (REST API) is complete and tested. The front end
> (React + TypeScript) is the next step. Roadmap and known limitations are in
> [`docs/BACKLOG.md`](docs/BACKLOG.md).

## Features

- JWT authentication and public user registration
- Clients and orders with full CRUD, search, filters and pagination
- Per-user data isolation on every endpoint
- Asynchronous CSV import (Celery + Redis) with progress tracking and a
  per-row error report
- Dashboard endpoints: summary, sales by month, sales by category, top clients
- Automated tests (pytest) and lint (ruff) on every push through GitHub Actions

## Tech stack

Python 3.12, Django 6, Django REST Framework, SimpleJWT, PostgreSQL 16,
Celery, Redis, Docker Compose, pytest, ruff, GitHub Actions.

## Getting started

Requirements: Docker with the Compose plugin.

```bash
git clone https://github.com/ewn1/salesflow-b2b.git
cd salesflow-b2b

# Create your local configuration, then edit SECRET_KEY and POSTGRES_PASSWORD
cp .env.example .env

# Build the images and start the API, worker, database and Redis
docker compose up -d --build

# Create the database tables
docker compose exec web python manage.py migrate
```

The API is now available at `http://localhost:8000/api/`.

### Try it

```bash
# 1. Create an account
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "S3cure-pass-phrase!"}'

# 2. Log in (the response contains "access" and "refresh" tokens)
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "S3cure-pass-phrase!"}'

# 3. Call a protected endpoint with the access token
curl http://localhost:8000/api/dashboard/summary/ \
  -H "Authorization: Bearer <access-token>"
```

## Running the tests

```bash
docker compose exec web pytest -q
docker compose exec web ruff check .
```

## API reference

All routes live under `/api/` and require `Authorization: Bearer <access-token>`,
except registration and login.

| Method | Route | Description |
|---|---|---|
| POST | `/auth/register/` | Create an account (public) |
| POST | `/auth/token/` | Log in and get `access` and `refresh` tokens (public) |
| POST | `/auth/token/refresh/` | Get a new access token from a refresh token (public) |
| GET, POST | `/clients/` | List (with `?search=`) or create clients |
| GET, PUT, PATCH, DELETE | `/clients/{id}/` | Read, update or delete a client |
| GET, POST | `/orders/` | List or create orders |
| GET, PUT, PATCH, DELETE | `/orders/{id}/` | Read, update or delete an order |
| POST | `/upload-csv/` | Upload a CSV file (field `file`); returns `202` and the `upload_id` |
| GET | `/upload-csv/{upload_id}/status/` | Import status, progress and error report |
| GET | `/dashboard/summary/` | Revenue, orders count, average ticket, active clients |
| GET | `/dashboard/sales-by-month/` | Revenue and orders count per month, oldest first |
| GET | `/dashboard/sales-by-category/` | Revenue and orders count per category, biggest first |
| GET | `/dashboard/top-clients/` | Clients ranked by revenue (`?limit=`, 1 to 50, default 5) |

List endpoints are paginated (20 per page, `?page=`). The order list also
accepts `?search=` (order number, client name or category), `?status=` and a
period filter, `?order_date_after=YYYY-MM-DD` and `?order_date_before=YYYY-MM-DD`
(the end date is inclusive). The four dashboard endpoints accept the same
period filter. Invalid parameters return `400`.

### Business rules behind the numbers

- **Data isolation:** every query is scoped to the logged-in user; another
  user's data is never returned.
- **Revenue:** cancelled orders are excluded. Pending and processing orders are
  counted.
- **Months** are computed in the `America/Sao_Paulo` time zone.
- **Money** is returned as strings with two decimals (for example `"1500.50"`),
  so no precision is lost in JSON.

## CSV import

Send the file to `POST /api/upload-csv/` as `multipart/form-data`. Processing
runs in the background; poll `GET /api/upload-csv/{upload_id}/status/` to
follow the progress.

| Column | Required | Notes |
|---|---|---|
| `documento_cliente` | yes | CPF or CNPJ, with or without punctuation (stored as digits) |
| `nome_cliente` | yes | |
| `numero_pedido` | yes | Unique per client |
| `data_pedido` | yes | `YYYY-MM-DD` or `DD/MM/YYYY` |
| `valor_pedido` | yes | `1500.50`, `1500,50` or `1.500,50` |
| `status_pedido` | yes | `Pendente`, `Processando`, `Concluido` or `Cancelado` (accents optional) |
| `email_cliente`, `telefone_cliente`, `segmento_cliente`, `estado_cliente`, `categoria_produto` | no | |

- The delimiter (`,` or `;`) and the encoding (UTF-8 with or without BOM, or
  Windows-1252) are detected automatically. Maximum size: 5 MB.
- Rows with problems are skipped and listed in the error report with their line
  number; the other rows are still imported.
- Importing the same file again updates the existing records instead of
  duplicating them.

## Production notes

The provided Docker Compose setup is meant for development (code mounted into
the container, auto-reload, test tooling installed). A production image is on
the backlog.

Before starting the containers on a Linux server, adjust the kernel memory
setting that Redis needs:

```bash
# Enable memory overcommit for the current session
sudo sysctl vm.overcommit_memory=1

# Make the change permanent across reboots
echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf
```