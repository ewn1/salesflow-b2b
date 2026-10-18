# Backlog

## Next (roadmap, in order)
- [ ] Front end: Vite + React + TypeScript, Redux Toolkit, Styled-Components, Recharts

## Pending
- [ ] Tighten `Client.cnpj_cpf` max_length to 14 (documents are stored as digits only) + migration
- [ ] Move `normalize_document` tests to import from `clients.documents`
- [ ] Refactor old importer tests to use the `import_rows` helper
- [ ] Optional: validate CPF/CNPJ check digits
- [ ] Define rule for negative amounts (refunds)
- [ ] Dockerfile: multi-stage build or build ARG for a production image without dev tools
- [ ] Sweep remaining Portuguese comments/docstrings (e.g. core/celery.py, sales/urls.py) to English
- [ ] Adopt `ruff format` and add `ruff format --check` to CI
- [ ] Docker/CI: map the container user's UID to the host's, so tools can write cache files without `--no-cache` (CI currently runs ruff check --no-cache and pytest -p no:cacheprovider as a workaround)
- [ ] Pin indirect dev dependencies (e.g. pluggy) or use a lock file, so rebuilds are reproducible
- [ ] Move the test helpers (make_client, make_order, api_for, at) to a shared conftest.py
- [ ] The dashboard revenue figure includes all non-cancelled orders, encompassing both PENDING and PROCESSING statuses; a “completed-only” view may become an option in the future.

## Known limitations
- Amount parser accepts odd inputs such as `1..5` (validates characters, not separator positions)
- CSV line numbers in the error report assume one physical line per record
- Whole CSV is read into memory
- Client search on `cnpj_cpf` matches digits only: a punctuated query like `11.111.111/0001-91` finds nothing
- Search uses `LIKE '%term%'` (no index); fine for small volumes, slow at millions of rows