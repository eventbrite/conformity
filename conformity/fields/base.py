from abc import (
    ABCMeta,
    abstractmethod,
)
from typing import (
    Any,
    List,
    Optional,
)

from conformity.types import (
    Error,
    Warning,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'BaseField',
)


class _BaseMeta(ABCMeta):
    def __init__(self, name, bases, attrs):
        # Validate field definition
        try:
            valid_type = attrs['valid_type']
        except KeyError:
            raise ValueError(
                'All concrete BaseField subclasses must '
                'specify a valid_type class attribute!'
            )
        if 'valid_noun' not in attrs:
            # Naively set the type "noun" from the type name
            attrs['valid_noun'] = 'a {}'.format(valid_type.__name__)
            raise ValueError(
                'All concrete BaseField subclasses must '
                'specify a valid_noun class attribute!'
            )
        if 'introspect_type' not in attrs:
            if isinstance(valid_type, tuple):
                raise ValueError(
                    'introspect_type must be defined for field {} '
                    'when valid_type is a tuple'
                )
            # If unset, infer the introspection type from the type name
            attrs['introspect_type'] = valid_type.__name__

        super().__init__(name, bases, attrs)


class BaseField(metaclass=_BaseMeta):
    """
    The abstract base class from which all other Conformity fields inherit. It
    defines the common `validate()` and `introspect()` interfaces that must be
    implemented by BaseField subclasses.
    """

    def __init__(self, *, description: str=None) -> None:
        self.description = description

    def errors(self, value: Any) -> List[Error]:
        return self.validate(value).errors

    def warnings(self, value: Any) -> List[Warning]:
        return self.validate(value).warnings

    def validate(self, value: Any) -> Validation:
        """
        Interface for field validation.

        Returns a Validation instance containing errors (if any) and,
        optionally, a list of warnings and extracted values.
        """
        errors = []
        if not isinstance(value, self.valid_type):
            errors.append(Error('Value is not {}'.format(self.valid_noun)))
        return Validation(errors=errors)


    def introspect(self) -> Introspection:
        """
        Returns a JSON-serializable dictionary containing introspection data
        that can be used to document the schema.
        """
        return strip_none({
            'introspect_type': self.introspect_type,
            'description': self.description,
        })
