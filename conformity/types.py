from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (
    List,
    Optional,
)

import attr
import six

from conformity.utils import (
    attr_is_optional,
    attr_is_string,
)
from conformity.constants import (
    ERROR_CODE_INVALID,
    WARNING_CODE_WARNING,
)

__all__ = (
    'Error',
    'Issue',
    'Validation',
    'Warning',
)


@attr.s
class Issue(object):
    """
    Represents an issue found during validation of a value.
    """
    message = attr.ib(validator=attr_is_string())  # type: six.text_type
    pointer = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]


@attr.s
class Error(Issue):
    """
    Represents an error found during validation of a value.
    """
    code = attr.ib(default=ERROR_CODE_INVALID, validator=attr_is_string())  # type: six.text_type


@attr.s
class Warning(Issue):
    """
    Represents a warning found during validation of a value.
    """
    code = attr.ib(default=WARNING_CODE_WARNING, validator=attr_is_string())  # type: six.text_type


@attr.s
class Validation(object):
    errors = attr.ib(factory=list)  # type: List[Error]
    warnings = attr.ib(factory=list)  # type: List[Warning]

    def __bool__(self):
        return bool(self.errors)
