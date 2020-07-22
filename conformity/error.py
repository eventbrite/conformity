from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import cast
import warnings

import six

# NOTE: The following have been moved to different modules, but are imported
#       here for backwards compatibility. These aliases will be removed in
#       Conformity 2.0.
from conformity.constants import (
    ERROR_CODE_INVALID,
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)
from conformity.types import Error

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
#       will be removed in Conformity 2.0.
def update_error_pointer(error, pointer_or_prefix):
    # type: (Error, six.text_type) -> Error
    warnings.warn(
        'update_error_pointer has been deprecated and will be removed in Conformity 2.0.',
        DeprecationWarning,
        stacklevel=2,
    )

    from conformity.fields.utils import update_pointer
    return cast(Error, update_pointer(error, pointer_or_prefix))
