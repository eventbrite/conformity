from abc import abstractmethod

from typing import (
    Any,
    List,
)

from conformity.fields.base import BaseField
from conformity.fields.meta import (
    All,
    Constant,
    Instance,
    Type,
    Validator,
)
from conformity.fields.protocols import Sized
from conformity.fields.simple import (
    Bytes,
    Decimal,
    String,
)
from conformity.fields.structures import Dictionary
from conformity.fields.utils import strip_none
from conformity.types import (
    Error,
    Warning,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'Base',
    'ByteString',
    'Null',
    'Nullable',
    'ObjectInstance',
    'SchemalessDictionary',
    'TypeReference',
    'UnicodeDecimal',
    'UnicodeString',
)


class Base(BaseField):
    """
    The legacy (Conformity 1.x) base field from which all other legacy fields
    inherit. This defines a simple interface for getting a list of validation
    errors and recursively introspecting the schema.
    """
    @abstractmethod
    def errors(self, value: Any) -> List[Error]:
        """
        Returns a list of errors with the value. An empty return means that it's
        valid.
        """

    def warnings(self, value: Any) -> List[Warning]:
        """
        Returns a list of warnings for the field or value.
        """
        return []

    def validate(self, value: Any) -> Validation:
        return Validation(
            errors=self.errors(value),
            warnings=self.warnings(value),
        )


class Null(Constant):
    """
    Legacy field that is shorthand for Constant(None, ...)
    """
    def __init__(self, **kwargs):
        # NOTE: Ignoring typing, since Mypy thinks None isn't hashable (it is)
        super().__init__(None, **kwargs)  # type: ignore


class Nullable(BaseField):
    """
    Field that allows a null / `None` value and delegates validation the field
    type passed as the first positional argument for all non-null values.
    Introspection is a dictionary with "type" set to "nullable" and key
    "nullable" set to the introspection of the first positional argument.
    """

    introspect_type = 'nullable'

    def __init__(self, field: BaseField, **kwargs):
        super().__init__(**kwargs)

        # Validate arguments
        if not isinstance(field, BaseField):
            raise TypeError('field argument must be a Conformity field')

        self.field = field

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)

        if value is None:
            return v

        return self.field.validate(value)

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'nullable': self.field.introspect(),
        })


class SchemalessDictionary(Dictionary, Sized):
    """
    Validates that the value is a dictionary of any keys and values, but
    optionally enforcing that the keys pass the Conformity validation specified
    with the `key_type` argument and/or that the values pass the Conformity
    validation specified with the `value_type` argument. Size of the dictionary
    can also be constrained with the optional `max_length` and `min_length`
    arguments.
    """

    introspect_type = 'schemaless_dictionary'

    def __init__(
        self,
        *,
        key_type: BaseField = None,
        value_type: BaseField = None,
        **kwargs: Any
    ) -> None:
        super().__init__((key_type, value_type), **kwargs)


class UnicodeDecimal(All):
    """
    Validates that the value is a string that is also a valid decimal and can
    successfully be converted to a `decimal.Decimal`.
    """

    introspect_type = 'unicode_decimal'

    def __init__(self, **kwargs):
        super().__init__(String(), Decimal(), **kwargs)


# Deprecated Conformity 1.x aliases
BooleanValidator = Validator
ByteString = Bytes
ObjectInstance = Instance
TypeReference = Type
UnicodeString = String
