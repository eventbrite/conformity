import decimal
from typing import Any

from conformity.fields.utils import strip_none
from conformity.fields.base import BaseField
from conformity.types import (
    Error,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'Boolean',
    'Bytes',
    'Decimal',
    'Float',
    'Integer',
    'String',
)


#
# Numeric types
#
class Boolean(BaseField):
    """
    Validates that the value is a boolean
    """

    valid_type = bool
    valid_noun = 'a boolean'
    introspect_type = 'boolean'


class Integer(Number):
    """
    Validates that the value is an integer
    """

    valid_type = int
    valid_noun = 'an integer'
    introspect_type = 'integer'


class Float(Number):
    """
    Validates that the value is a float
    """

    valid_type = float


class Decimal(Number):
    """
    Validates that the value is a `decimal.Decimal`
    """

    valid_type = decimal.Decimal

#
# String types
#
class String(Sized):
    """
    Validates that the value is a string. Optionally validates that the string
    is not blank.
    """
    valid_type = str
    introspect_type = 'string'

    def __init__(self, *, allow_blank: bool=True, **kwargs):
        super().__init__(**kwargs)
        self.allow_blank = allow_blank

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if not v.errors:
            if not (self.allow_blank or value.strip()):
                v.errors.append(Error('Value cannot be blank'))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            'allow_blank': self.allow_blank,
        }).update(super().introspect())


class Bytes(Sized):
    """
    Validate that the value is a byte string
    """

    valid_type = bytes
    valid_noun = 'a byte string'
    valid_noun = 'byte string'
