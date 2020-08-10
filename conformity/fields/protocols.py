from collections import abc
import numbers
from typing import (
    Any,
    Hashable as HashableType,
    Iterable as IterableType,
    Tuple,
    TypeVar,
)

from conformity.fields.base import (
    BaseField,
    BaseTypeField,
)
from conformity.fields.utils import strip_none
from conformity.types import (
    Error,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'Callable',
    'Collection',
    'Container',
    'Hashable',
    'Iterable',
    'Mapping',
    'Number',
    'Sequence',
    'Set',
    'Sized',
)


T = TypeVar('T')


class Callable(BaseField):
    """
    Validates that the value is callable
    """

    introspect_type = 'callable'

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if not v.errors and not callable(value):
            v.errors.append(Error('Value is not a callable'))
        return v


class Container(BaseTypeField):
    """
    Validates that the value implements the Container protocol (i.e., implements
    the __conatins__ method)
    """

    valid_type = abc.Container


class Hashable(BaseTypeField):
    """
    Validates that the value is hashable (i.e., `hash(...)` can be called on the
    value without error).
    """

    valid_type = abc.Hashable
    valid_noun = 'hashable'


class Iterable(BaseTypeField):
    """
    Validates that the value is iterable
    """

    valid_type = abc.Iterable
    valid_noun = 'iterable'


class Mapping(BaseTypeField):
    """
    Validates that the value implements the Mapping protocol (e.g. a dictionary)
    """

    valid_type = abc.Mapping


class Number(BaseTypeField):
    """
    Validates that the value is a Number and, optionally, enforces boundaries
    for that number with the `gt`, `gte`, `lt`, and `lte` arguments.
    """

    valid_type = numbers.Number

    def __init__(
        self,
        *,
        allow_boolean: bool = False,
        gt: int = None,
        gte: int = None,
        lt: int = None,
        lte: int = None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.allow_boolean = allow_boolean
        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if not self.allow_boolean and isinstance(value, bool):
            v.errors.append(Error(
                'Value is not {}'.format(self.valid_noun),
            ))

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
            **super().introspect(),
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


class Sized(BaseTypeField):
    """
    Validates that the value implements the Sized protocol (i.e., implements
    __len__). Optionally, enforces minimum and maximum lengths on sized values.
    """

    valid_type = abc.Sized
    valid_noun = 'sized'

    def __init__(
        self,
        *,
        min_length: int = None,
        max_length: int = None,
        **kwargs: Any
    ):
        super().__init__(**kwargs)

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
        if not v.errors:
            value_len = len(value)
            if self.min_length is not None and value_len < self.min_length:
                v.errors.append(Error(
                    'Value must have a length of at least {}'.format(
                        self.min_length,
                    ),
                ))
            elif self.max_length is not None and value_len > self.max_length:
                v.errors.append(Error(
                    'Value must have a length of no more than {}'.format(
                        self.max_length,
                    ),
                ))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'min_length': self.min_length,
            'max_length': self.max_length,
        })


class Collection(Sized):
    """
    Validates that the value is a collection of items that all pass validation
    with the Conformity field passed to the `contents` argument and optionally
    establishes boundaries for that list with the `max_length` and `min_length`
    arguments.
    """

    valid_type = abc.Collection

    def __init__(
        self,
        contents: BaseField,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.contents = contents

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)

        if not v.errors:
            for p, element in self._enumerate(value):
                v.extend(
                    self.contents.validate(element),
                    pointer=p,
                )

        return v

    @classmethod
    def _enumerate(
        cls,
        values: IterableType[T],
    ) -> IterableType[Tuple[HashableType, T]]:
        # Overridable value pointer enumeration method
        return enumerate(values)

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'contents': self.contents.introspect(),
        })


class Sequence(Collection):
    valid_type = abc.Sequence


class Set(Collection):
    """
    Validates that the value is an abstract set of items that all pass
    validation with the Conformity field passed to the `contents` argument and
    optionally establishes boundaries for that list with the `max_length` and
    `min_length` arguments.
    """

    valid_type = abc.Set
    introspect_type = 'set'

    @classmethod
    def _enumerate(
        cls,
        values: IterableType[T],
    ) -> IterableType[Tuple[HashableType, T]]:
        return (
            (str(value), value)
            for value in values
        )
