# Backlog

## Pending
- [ ] Tighten `Client.cnpj_cpf` max_length to 14 (documents are stored as digits only) + migration
- [ ] Move `normalize_document` tests to import from `clients.documents`
- [ ] Refactor old importer tests to use the `import_rows` helper
- [ ] Optional: validate CPF/CNPJ check digits
- [ ] Define rule for negative amounts (refunds)

## Known limitations
- Amount parser accepts odd inputs such as `1..5` (validates characters, not separator positions)
- CSV line numbers in the error report assume one physical line per record
- Whole CSV is read into memory