from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (
    Dict,
    Hashable,
    TypeVar,
)

from conformity.types import (
    Issue,
    Error,
    Warning,
)


KT = TypeVar('KT')
VT = TypeVar('VT')

IssueVar = TypeVar('IssueVar', Issue, Error, Warning)


def strip_none(value):
    # type: (Dict[KT, VT]) -> Dict[KT, VT]
    """
    Takes a dict and removes all keys that have `None` values, used mainly for
    tidying up introspection responses. Take care not to use this on something
    that might legitimately contain a `None`.
    """
    return {k: v for k, v in value.items() if v is not None}


def update_pointer(issue, pointer_or_prefix):
    # type: (IssueVar, Hashable) -> IssueVar
    """
    Helper function to update a pointer attribute with a (potentially prefixed)
    dictionary key or list index.
    """
    if issue.pointer:
        issue.pointer = '{}.{}'.format(pointer_or_prefix, issue.pointer)
    else:
        issue.pointer = '{}'.format(pointer_or_prefix)
    return issue
