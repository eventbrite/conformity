from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from conformity.types import (
    Error,
    Warning,
    Validation,
)

__all__ = (
    'BaseField',
)


# TODO: Not strict enough. Make this JSON serializable type.
# NOTE: removed datetime and decimal types
Introspection = Dict[
    str,
    Union[
        int, float, bool, str, None,
        List[Any],
        Dict[Any, Any],
    ],
]


class _BaseMeta(ABCMeta):
    def __init__(self, name, bases, attrs):
        if 'python_type' not in attrs:
            raise ValueError(
                'All concrete BaseField subclasses must '
                'specify a python_type class attribute!'
            )
        super().__init__(name, bases, attrs)


class BaseField(metaclass=_BaseMeta):
    """
    The abstract base class from which all other Conformity fields inherit. It
    defines the common `validate()` and `introspect()` interfaces that must be
    implemented by BaseField subclasses.
    """

    def __init__(self, description: Optional[str]=None) -> None:
        self.description = description

    def errors(self, value: Any) -> List[Error]:
        return self.validate(value).errors

    def warnings(self, value: Any) -> List[Warning]:
        return self.validate(value).warnings

    @abstractmethod
    def validate(self, value: Any) -> Validation:
        """
        Interface for field validation.

        Returns a Validation instance containing errors (if any) and,
        optionally, a list of warnings and extracted values.
        """

    @abstractmethod
    def introspect(self) -> Introspection:
        """
        Returns a JSON-serializable dictionary containing introspection data
        that can be used to document the schema.
        """
