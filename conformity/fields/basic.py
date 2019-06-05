from __future__ import (
    absolute_import,
    unicode_literals,
)

import decimal
from typing import (  # noqa: F401 TODO Python 3
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

from conformity.error import (
    ERROR_CODE_UNKNOWN,
    Error,
)
from conformity.utils import (
    attr_is_bool,
    attr_is_instance,
    attr_is_int,
    attr_is_number,
    attr_is_optional,
    attr_is_string,
    strip_none,
)


@attr.s
class Base(object):
    """
    Base field type.
    """

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        """
        Returns a list of errors with the value. An empty return means that it's valid.
        """
        return [Error('Validation not implemented on base type')]

    def introspect(self):  # type: () -> Dict[six.text_type, AnyType]
        """
        Returns a JSON-serializable dictionary containing introspection data that can be used to document the schema.
        """
        raise NotImplementedError('You must override introspect() in a subclass')


def attr_is_conformity_field():
    return attr_is_instance(Base)


class Constant(Base):
    """
    Value that must match exactly. You can pass a series of options and any will be accepted.
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

    def errors(self, value):
        if value not in self.values:
            return [Error(self._error_message, code=ERROR_CODE_UNKNOWN)]
        return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'values': sorted(self.values),
            'description': self.description,
        })


@attr.s
class Anything(Base):
    """
    Accepts any value.
    """

    introspect_type = 'anything'

    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
        })


@attr.s
class Hashable(Anything):
    """
    Accepts any hashable value
    """

    introspect_type = 'hashable'

    def errors(self, value):
        try:
            hash(value)
        except TypeError:
            return [
                Error('Value is not hashable'),
            ]
        return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
        })


@attr.s
class Boolean(Base):
    """
    Accepts boolean values only
    """

    introspect_type = 'boolean'

    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        if not isinstance(value, bool):
            return [
                Error('Not a boolean'),
            ]
        return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
        })


@attr.s
class Integer(Base):
    """
    Accepts valid integers, with optional range limits.
    """

    valid_type = six.integer_types  # type: Union[Type, TupleType[Type, ...]]
    valid_noun = 'an integer'  # type: six.text_type
    introspect_type = 'integer'  # type: six.text_type

    gt = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_number()),
    )  # type: Optional[Union[int, float, decimal.Decimal]]
    gte = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_number()),
    )  # type: Optional[Union[int, float, decimal.Decimal]]
    lt = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_number()),
    )  # type: Optional[Union[int, float, decimal.Decimal]]
    lte = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_number()),
    )  # type: Optional[Union[int, float, decimal.Decimal]]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        if not isinstance(value, self.valid_type) or isinstance(value, bool):
            return [Error('Not {}'.format(self.valid_noun))]

        errors = []
        if self.gt is not None and value <= self.gt:
            errors.append(Error('Value not > {}'.format(self.gt)))
        if self.lt is not None and value >= self.lt:
            errors.append(Error('Value not < {}'.format(self.lt)))
        if self.gte is not None and value < self.gte:
            errors.append(Error('Value not >= {}'.format(self.gte)))
        if self.lte is not None and value > self.lte:
            errors.append(Error('Value not <= {}'.format(self.lte)))
        return errors

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


@attr.s
class Float(Integer):
    """
    Accepts floating point numbers as well as integers.
    """

    valid_type = six.integer_types + (float,)  # type: ignore # see https://github.com/python/mypy/issues/224
    valid_noun = 'a float'
    introspect_type = 'float'


@attr.s
class Decimal(Integer):
    """
    Accepts arbitrary-precision Decimal number objects.
    """

    valid_type = decimal.Decimal
    valid_noun = 'a decimal'
    introspect_type = 'decimal'


@attr.s
class UnicodeString(Base):
    """
    Accepts only unicode strings
    """

    valid_type = six.text_type  # type: Type
    valid_noun = 'unicode string'
    introspect_type = 'unicode'

    min_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    max_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]
    allow_blank = attr.ib(default=True, validator=attr_is_bool())  # type: bool

    def __attrs_post_init__(self):
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot be greater than max_length in UnicodeString')

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return [Error('Not a {}'.format(self.valid_noun))]
        elif self.min_length is not None and len(value) < self.min_length:
            return [Error('String must have a length of at least {}'.format(self.min_length))]
        elif self.max_length is not None and len(value) > self.max_length:
            return [Error('String must have a length no more than {}'.format(self.max_length))]
        elif not (self.allow_blank or value.strip()):
            return [Error('String cannot be blank')]
        return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'allow_blank': self.allow_blank and None,  # if the default True, hide it from introspection
        })


@attr.s
class ByteString(UnicodeString):
    """
    Accepts only byte strings
    """

    valid_type = six.binary_type
    valid_noun = 'byte string'
    introspect_type = 'bytes'


@attr.s
class UnicodeDecimal(Base):
    """
    A decimal value represented as its base-10 unicode string.
    """

    introspect_type = 'unicode_decimal'

    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
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

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
        })
