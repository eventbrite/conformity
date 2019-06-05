from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import Optional  # noqa: F401 TODO Python 3

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
