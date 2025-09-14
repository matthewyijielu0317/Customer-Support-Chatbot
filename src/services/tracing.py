import contextlib
from typing import Iterator


@contextlib.contextmanager
def traced_span(name: str) -> Iterator[None]:
    # Placeholder for LangSmith/OTel span
    try:
        yield
    finally:
        pass


