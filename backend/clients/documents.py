import re


def normalize_document(raw_document):
    """Keep only the digits of a CPF/CNPJ and check its length (11 or 14)."""
    digits = re.sub(r"\D", "", raw_document or "")
    if len(digits) not in (11, 14):
        raise ValueError(
            f"Invalid document {raw_document!r}: expected 11 (CPF) or 14 (CNPJ) digits"
        )
    return digits
