"""
Definitions for common custom type aliases
"""
from typing import (
    Any,
    Dict,
    List,
    Union,
)

__all__ = (
    'Introspection',
)


# NOTE: The Introspection type alias is intended to represent a JSON
#       serializable dictionary. However, as of August 2020, MyPy still does
#       not support recursive types. As a result, the type alias is not
#       currently strict enough to properly validate that a value is actually
#       JSON serializable.
_IntrospectionValue = Union[
    int, float, bool, str, None,
    List[Any],
    Dict[str, Any],
]

Introspection = Dict[str, _IntrospectionValue]
