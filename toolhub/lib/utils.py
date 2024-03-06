from typing import TypeVar

T = TypeVar("T")


def not_none(t: T | None, description: str | None = None) -> T:
    assert t is not None, ValueError(
        f"expected {description or 'object'} to be not None"
    )
    return t
