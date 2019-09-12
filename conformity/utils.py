from __future__ import (
    absolute_import,
    unicode_literals,
)

import decimal
from typing import (  # noqa: F401 TODO Python 3
    Any as AnyType,
    Callable,
    Dict,
    Optional,
    Tuple as TupleType,
    Type,
    TypeVar,
    Union,
)

import attr
import six


KT = TypeVar('KT')
VT = TypeVar('VT')
AttrsValidator = Callable[[AnyType, AnyType, AnyType], None]


def strip_none(value):  # type: (Dict[KT, VT]) -> Dict[KT, VT]
    """
    Takes a dict and removes all keys that have `None` values, used mainly for tidying up introspection responses. Take
    care not to use this on something that might legitimately contain a `None`.
    """
    return {k: v for k, v in value.items() if v is not None}


attr_is_instance = attr.validators.instance_of  # type: Callable[[Union[Type, TupleType[Type, ...]]], AttrsValidator]
attr_is_optional = attr.validators.optional  # type: Callable[[AttrsValidator], AttrsValidator]


def attr_is_bool():  # type: () -> AttrsValidator
    """Creates an Attrs validator that ensures the argument is a bool."""
    return attr_is_instance(bool)


def attr_is_int():  # type: () -> AttrsValidator
    """Creates an Attrs validator that ensures the argument is an integer."""
    return attr_is_instance(int)


def attr_is_number():  # type: () -> AttrsValidator
    """Creates an Attrs validator that ensures the argument is a number."""
    return attr_is_instance((int, float, decimal.Decimal))


def attr_is_set():  # type: () -> AttrsValidator
    """Creates an Attrs validator that ensures the argument is an abstract set."""
    return attr_is_instance((set, frozenset))


def attr_is_string():  # type: () -> AttrsValidator
    """Creates an Attrs validator that ensures the argument is a unicode string."""
    return attr_is_instance(six.text_type)


# In Attrs 19.1.0 we can use attr.validators.deep_iterable, but we want to support older versions for a while longer,
# so we use this custom validator for now
def attr_is_iterable(
    member_validator,  # type: AttrsValidator
    iterable_validator=None  # type: Optional[AttrsValidator]
):
    # type: (...) -> AttrsValidator
    """
    The equivalent of `attr.validators.deep_iterable` added in Attrs 19.1.0, but we still support older versions.
    """

    # noinspection PyShadowingNames
    def validator(inst, attr, value):
        if not hasattr(value, '__iter__'):
            raise TypeError(
                "'{name}' must be iterable (got {value!r} that is a {actual!r}).".format(
                    name=attr.name,
                    actual=value.__class__,
                    value=value,
                ),
                attr,
                value,
            )

        if iterable_validator:
            iterable_validator(inst, attr, value)

        class A(object):
            def __init__(self, num):
                self.num = num

            @property
            def name(self):
                return '{}.{}'.format(attr.name, self.num)

        for i, item in enumerate(value):
            member_validator(inst, A(i), item)

    return validator


def attr_is_instance_or_instance_tuple(
    check_type,  # type: Union[Type, TupleType[Type, ...]]
):
    # type: (...) -> AttrsValidator
    """
    Creates an Attrs validator that ensures the argument is a instance of or tuple of instances of the given type.
    """

    # first, some meta META validation
    if not isinstance(check_type, type):
        if not isinstance(check_type, tuple):
            raise TypeError("'check_type' must be a type or tuple of types")
        for i, t in enumerate(check_type):
            if not isinstance(t, type):
                raise TypeError("'check_type[{i}] must be a type or tuple of types".format(i=i))

    def validator(_instance, attribute, value):
        if isinstance(value, check_type):
            return

        if not isinstance(value, tuple):
            raise TypeError(
                "'{name}' must be a {t!r} or a tuple of {t!r} (got {value!r} that is a {actual!r}).".format(
                    name=attribute.name,
                    actual=type(value),
                    value=value,
                    t=check_type,
                ),
                attribute,
                value,
            )

        for i, item in enumerate(value):
            if not isinstance(item, check_type):
                raise TypeError(
                    "'{name}[{i}]' must be a {t!r} (got {value!r} that is a {actual!r}).".format(
                        i=i,
                        name=attribute.name,
                        actual=type(item),
                        value=item,
                        t=check_type,
                    ),
                    attribute,
                    item,
                )

    return validator
