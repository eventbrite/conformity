import datetime
import decimal
from typing import (
    Any as AnyType,
    Dict,
    List as ListType,
    Optional,
    Tuple as TupleType,
    Type,
    Union,
)

import attr
import six

from conformity.constants import ERROR_CODE_UNKNOWN
from conformity.fields.utils import strip_none
from conformity.fields.base import BaseField
from conformity.types import (
    Error,
    Warning,
    Validation,
)
from conformity.typing import Introspection


# TODO: update
class Constant(BaseField):
    """
    Conformity field that ensures that the value exactly matches the constant
    value supplied or, if multiple constant values are supplied, exactly matches
    one of those values.
    """

    introspect_type = 'constant'

    def __init__(self, *args, **kwargs):  # type: (*AnyType, **AnyType) -> None
        self.values = frozenset(args)
        if not self.values:
            raise ValueError('You must provide at least one constant value')
        self.description = kwargs.pop(str('description'), None)  # type: Optional[six.text_type]
        if self.description and not isinstance(self.description, six.text_type):
            raise TypeError("'description' must be a unicode string")
        # Check they didn't pass any other kwargs
        if kwargs:
            raise TypeError('Invalid keyword arguments for Constant: {}'.format(kwargs.keys()))

        def _repr(cv):
            return '"{}"'.format(cv) if isinstance(cv, six.string_types) else '{}'.format(cv)

        if len(self.values) == 1:
            self._error_message = 'Value is not {}'.format(_repr(tuple(self.values)[0]))
        else:
            self._error_message = 'Value is not one of: {}'.format(', '.join(sorted(_repr(v) for v in self.values)))

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        try:
            is_valid = value in self.values
        except TypeError:
            # Unhashable values can't be used for membership checks.
            is_valid = False

        if not is_valid:
            return [Error(self._error_message, code=ERROR_CODE_UNKNOWN)]
        return []

    def introspect(self) -> Introspection:
        return strip_none({
            'type': self.introspect_type,
            'values': [
                s if isinstance(s, (six.text_type, bool, int, float, type(None))) else six.text_type(s)
                for s in sorted(self.values, key=six.text_type)
            ],
            'description': self.description,
        })


class Anything(BaseField):
    """
    Validates that the value can be anything.
    """

    introspect_type = 'anything'

    def validate(self, value: AnyType) -> Validation:
        return Validation()


class Boolean(BaseField):
    """
    Validates that the value is a boolean.
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
    Conformity field that ensures that the value is a `decimal.Decimal` and optionally enforces boundaries for that
    decimal with the `gt`, `gte`, `lt`, and `lte` arguments.
    """

    valid_type = decimal.Decimal


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

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.is_valid():
            # TODO: implement "should continue" instead of using is_valid()
            #       here and elsewhere.
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


# Deprecated Conformity 1.x aliases
UnicodeString = String
ByteString = Bytes


@attr.s
class UnicodeDecimal(Base):
    """
    Conformity field that ensures that the value is a unicode string that is also a valid decimal and can successfully
    be converted to a `decimal.Decimal`.
    """

    introspect_type = 'unicode_decimal'

    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, six.text_type):
            return [
                Error('Invalid decimal value (not unicode string)'),
            ]
        try:
            decimal.Decimal(value)
        except decimal.InvalidOperation:
            return [
                Error('Invalid decimal value (parse error)'),
            ]
        return []

    def introspect(self):  # type: () -> Introspection
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
        })
