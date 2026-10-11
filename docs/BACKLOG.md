# Backlog

## Pending
- [ ] Tighten `Client.cnpj_cpf` max_length to 14 (documents are stored as digits only) + migration
- [ ] Move `normalize_document` tests to import from `clients.documents`
- [ ] Refactor old importer tests to use the `import_rows` helper
- [ ] Optional: validate CPF/CNPJ check digits
- [ ] Define rule for negative amounts (refunds)
- [ ] Dockerfile: multi-stage build or build ARG for a production image without dev tools
- [ ] Sweep remaining Portuguese comments/docstrings (e.g. core/celery.py, sales/urls.py) to English
- [ ] Adopt `ruff format` and add `ruff format --check` to CI
- [ ] Add a CI status badge to the README (when the real README is written)
- [ ] Docker/CI: map the container user's UID to the host's, so tools can write cache files without `--no-cache` (CI currently runs ruff check --no-cache and pytest -p no:cacheprovider as a workaround)

## Known limitations
- Amount parser accepts odd inputs such as `1..5` (validates characters, not separator positions)
- CSV line numbers in the error report assume one physical line per record
- Whole CSV is read into memory