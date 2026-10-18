# Backlog

## Next (roadmap, in order)
- [ ] Front end: Vite + React + TypeScript, Redux Toolkit, Styled-Components, Recharts
- [ ] Final README: front-end instructions, screenshots or GIF, "How this was built" section

## Pending
- [ ] Tighten `Client.cnpj_cpf` max_length to 14 (documents are stored as digits only) + migration
- [ ] Move `normalize_document` tests to import from `clients.documents`
- [ ] Refactor old importer tests to use the `import_rows` helper
- [ ] Optional: validate CPF/CNPJ check digits
- [ ] Define rule for negative amounts (refunds)
- [ ] Dockerfile: multi-stage build or build ARG for a production image without dev tools
- [ ] Adopt `ruff format` and add `ruff format --check` to CI
- [ ] Docker/CI: map the container user's UID to the host's, so tools can write cache files without `--no-cache` (CI currently runs ruff check --no-cache and pytest -p no:cacheprovider as a workaround)
- [ ] Pin indirect dev dependencies (e.g. pluggy) or use a lock file, so rebuilds are reproducible
- [ ] Move the test helpers (make_client, make_order, api_for, at) to a shared conftest.py
- [ ] Translate the remaining Portuguese text in non-Python files (`Dockerfile`, `docker-compose.yml`, `backend/api_tests.http`) and update `api_tests.http` with the registration and dashboard requests
- [ ] Throttling (rate limiting) and e-mail confirmation on registration
- [ ] Decide the fate of `/admin`: register the models and serve static files (e.g. WhiteNoise), or remove the route
- [ ] Decide how API error messages reach pt-BR users: the front maps error codes, or Django translates (`LANGUAGE_CODE = "pt-br"` + `gettext`). Settle this when building the login and sign-up screens
- [ ] Sample CSV generator for the demo and the README

## Known limitations
- Amount parser accepts odd inputs such as `1..5` (validates characters, not separator positions)
- CSV line numbers in the error report assume one physical line per record
- Whole CSV is read into memory
- Client search on `cnpj_cpf` matches digits only: a punctuated query like `11.111.111/0001-91` finds nothing
- Search uses `LIKE '%term%'` (no index); fine for small volumes, slow at millions of rows
- The dashboard revenue figure includes all non-cancelled orders, encompassing both PENDING and PROCESSING statuses; a “completed-only” view may become an option in the future.