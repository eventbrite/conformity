from typing import (
    List,
    Optional,
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


class Issue:
    """
    Represents an issue found during validation of a value.
    """
    def __init__(self, message: str, pointer: Optional[str]=None) -> None:
        selef.message = message
        self.pointer = pointer


class Error(Issue):
    """
    Represents an error found during validation of a value.
    """
    def __init__(
        self,
        message: str,
        pointer: Optional[str]=None,
        code: Optional[str]=None,
    ):
        super().__init__(message, pointer)
        self.code = code or ERROR_CODE_INVALID


class Warning(Issue):
    """
    Represents a warning found during validation of a value.
    """
    def __init__(
        self,
        message: str,
        pointer: Optional[str]=None,
        code: Optional[str]=None,
    ):
        super().__init__(message, pointer)
        self.code = code or WARNING_CODE_WARNING


class Validation(object):
    def __init__(
        self,
        *,
        errors: Optional[List[Error]]=None,
        warnings: Optional[List[Error]]=None,
    ):
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self):
        return self.is_valid()

    def is_valid(self):
        return bool(self.errors)
