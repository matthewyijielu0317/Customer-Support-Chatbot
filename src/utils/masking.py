from __future__ import annotations


def mask_email(email: str | None, query: str | None = None) -> str | None:
    if not email:
        return email
    if query and email.lower() in (query or "").lower():
        return email
    try:
        local, domain = email.split("@", 1)
    except ValueError:
        return "***"

    masked_local = (local[0] + "***") if local else "***"
    masked_domain = "***"
    if "." in domain:
        masked_domain = "***." + domain.split(".")[-1]
    return f"{masked_local}@{masked_domain}"

