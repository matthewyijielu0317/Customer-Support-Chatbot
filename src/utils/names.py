from __future__ import annotations

from typing import Tuple


def derive_name_from_email(email: str | None) -> Tuple[str | None, str | None]:
    """Best-effort first/last name extraction from an email-like user id."""
    if not email:
        return None, None

    local_part = email.split("@", 1)[0].strip()
    if not local_part:
        return None, None

    tokens = [part for part in _split_local_part(local_part) if part]
    if not tokens:
        return None, None

    if len(tokens) == 1:
        return tokens[0].title(), None

    first = tokens[0].title()
    last = tokens[-1].title()
    return first, last


def _split_local_part(local: str) -> list[str]:
    separators = [".", "_", "-", "+"]
    for sep in separators:
        local = local.replace(sep, " ")
    return [chunk for chunk in local.split() if chunk]
