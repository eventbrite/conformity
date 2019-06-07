from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (  # noqa: F401 TODO Python 3
    Hashable as HashableType,
    Optional,
)

import attr
import six  # noqa: F401 TODO Python 3

from conformity.utils import (
    attr_is_optional,
    attr_is_string,
)


__all__ = (
    'ERROR_CODE_INVALID',
    'ERROR_CODE_MISSING',
    'ERROR_CODE_UNKNOWN',
    'Error',
    'KeywordError',
    'PositionalError',
    'ValidationError',
    'update_error_pointer',
)


ERROR_CODE_INVALID = 'INVALID'
ERROR_CODE_MISSING = 'MISSING'
ERROR_CODE_UNKNOWN = 'UNKNOWN'


@attr.s
class Error(object):
    """
    Represents an error found validating against the schema.
    """
    message = attr.ib(validator=attr_is_string())  # type: six.text_type
    code = attr.ib(default=ERROR_CODE_INVALID, validator=attr_is_string())  # type: six.text_type
    pointer = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]


class ValidationError(ValueError):
    """
    Error raised when a value fails to validate.
    """


class PositionalError(TypeError):
    """
    Error raised when you pass positional arguments into a validated function that doesn't support them.
    """


class KeywordError(TypeError):
    """
    Error raised when you pass keyword arguments into a validated function that doesn't support them.
    """


def update_error_pointer(error, pointer_or_prefix):  # type: (Error, HashableType) -> Error
    """
    Helper function to update an Error's pointer attribute with a (potentially prefixed) dictionary key or list index.
    """
    if error.pointer:
        error.pointer = '{}.{}'.format(pointer_or_prefix, error.pointer)
    else:
        error.pointer = '{}'.format(pointer_or_prefix)
    return error
