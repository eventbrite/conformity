from __future__ import (
    absolute_import,
    unicode_literals,
)


# NOTE: The following have been moved to different modules, but are imported
#       here for backwards compatibility. These aliases will be removed in a
#       future release.
from conformity.constants import (
    ERROR_CODE_INVALID,
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)
from conformity.types import Error
from conformity.utils.field import update_pointer


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


# NOTE: update_error_pointer has been deprecated. Use utils.field:update_pointer
#       instead. This alias has been added for backwards compatibility, but it
#       will be removed in a future release.
update_error_pointer = update_pointer
