from typing import (
    Any,
    Hashable,
    List,
    TypeVar,
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
    def __init__(self, message: str, pointer: str = None) -> None:
        self.message = message
        self.pointer = pointer


class Error(Issue):
    """
    Represents an error found during validation of a value.
    """
    def __init__(
        self,
        *,
        code: str = None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.code = code or ERROR_CODE_INVALID


class Warning(Issue):
    """
    Represents a warning found during validation of a value.
    """
    def __init__(
        self,
        *,
        code: str = None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.code = code or WARNING_CODE_WARNING


class Validation(object):
    def __init__(
        self,
        *,
        errors: List[Error] = None,
        warnings: List[Warning] = None,
    ):
        self.errors = errors or []  # type: List[Error]
        self.warnings = warnings or []  # type: List[Warning]

    def __bool__(self):
        return self.is_valid()

    def is_valid(self):
        return bool(self.errors)

    def extend(
        self,
        other: 'Validation',
        *,
        pointer: Hashable = None,
    ) -> None:
        if pointer is not None:
            self.errors.extend([
                _update_pointer(error, pointer)
                for error in other.errors
            ])
            self.warnings.extend([
                _update_pointer(warning, pointer)
                for warning in other.warnings
            ])
        else:
            self.errors.extend(other.errors)
            self.warnings.extend(other.warnings)


IssueVar = TypeVar('IssueVar', Issue, Error, Warning)


def _update_pointer( issue: IssueVar, pointer_or_prefix: Hashable) -> IssueVar:
    """
    Helper function to update a pointer attribute with a (potentially prefixed)
    dictionary key or list index.
    """
    if issue.pointer:
        issue.pointer = '{}.{}'.format(pointer_or_prefix, issue.pointer)
    else:
        issue.pointer = '{}'.format(pointer_or_prefix)
    return issue
