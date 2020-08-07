from typing import (
    Dict,
    TypeVar,
)

__all__ = (
    'strip_none',
)

KT = TypeVar('KT')
VT = TypeVar('VT')


def strip_none(value: Dict[KT, VT]) -> Dict[KT, VT]:
    """
    Takes a dict and removes all keys that have `None` values, used mainly for
    tidying up introspection responses. Take care not to use this on something
    that might legitimately contain a `None`.
    """
    return {k: v for k, v in value.items() if v is not None}
