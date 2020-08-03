from collections import abc
import numbers
from typing import Any

from conformity.fields.base import BaseField
from conformity.types import (
    Error,
    Validation,
)


class Callable(BaseField):
    """
    Validates that the value is callable
    """

    valid_type = abc.Callable
    valid_noun = 'callable'


class Container(BaseField):
    """
    Validates that the value implements the Container protocol (i.e., implements
    the __conatins__ method)
    """

    valid_type = abc.Container


class Hashable(BaseField):
    """
    Validates that the value is hashable (i.e., `hash(...)` can be called on the
    value without error).
    """

    valid_type = abc.Hashable
    valid_noun = 'hashable'


class Iterable(BaseField):
    """
    Validates that the value is iterable
    """

    valid_type = abc.Iterable
    valid_noun = 'iterable'


class Mapping(BaseField):
    """
    Validates that the value implements the Mapping protocol (e.g. a dictionary)
    """

    valid_type = abc.Mapping


class Number(BaseField):
    """
    Validates that the value is a Number and, optionally, enforces boundaries
    for that number with the `gt`, `gte`, `lt`, and `lte` arguments.
    """

    valid_type = numbers.Number

    def __init__(
        self,
        *,
        description: str,
        allow_boolean: bool=False,
        gt: int=None,
        gte: int=None,
        lt: int=None,
        lte: int=None,
    ):
        super().__init__(description)
        self.allow_boolean = allow_boolean
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if not self.allow_boolean and isinstance(value, bool):
            v.errors.append('Value is not {}'.format(self.valid_noun))

        if v.is_valid():
            if self.gt is not None and value <= self.gt:
                v.errors.append(Error('Value not > {}'.format(self.gt)))
            if self.lt is not None and value >= self.lt:
                v.errors.append(Error('Value not < {}'.format(self.lt)))
            if self.gte is not None and value < self.gte:
                v.errors.append(Error('Value not >= {}'.format(self.gte)))
            if self.lte is not None and value > self.lte:
                v.errors.append(Error('Value not <= {}'.format(self.lte)))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        }).update(super().introspect())


class Sized(BaseField):
    """
    Validates that the value implements the Sized protocol (i.e., implements
    __len__). Optionally, enforces minimum and maximum lengths on sized values.
    """

    valid_type = abc.Sized
    valid_noun = 'sized'

    def __init__(
        self,
        *,
        description: str=None,
        min_length: int=None,
        max_length: int=None,
    ):
        super().__init__(description=description)

        # Validate the length constraints
        if min_length is not None:
            if min_length < 0:
                raise ValueError('min_length must be >= 0')
            if max_length is not None and min_length > max_length:
                raise ValueError('min_length cannot be greater than max_length')

        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.is_valid():
            value_len = len(value)
            if self.min_length is not None and value_len < self.min_length:
                v.errors.append(
                    'Value must have a length of at least {}'.format(
                        self.min_length,
                    ),
                )
            elif self.max_length is not None and value_len > self.max_length:
                v.errors.append(
                    'Value must have a length of no more than {}'.format(
                        self.max_length,
                    ),
                )
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            'min_length': self.min_length,
            'max_length': self.max_length,
        }).update(super().introspect())

