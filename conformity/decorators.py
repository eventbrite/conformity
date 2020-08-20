from functools import wraps
import typing

from conformity.fields.base import BaseField


T = typing.TypeVar('T', bound=typing.Callable[..., typing.Any])


def validate(func: T) -> T:
    type_hints = typing.get_type_hints(func)

    # Collect Conformity fields from annotations
    fields = {}
    for arg, hint in type_hints.items():
        if issubclass(hint, BaseField):
            fields[arg] = hint

    @wraps(func)
    def wrapped(**kwargs):
        # TODO: Add support for positional arguments
        for key, value in kwargs.items():
            field = fields.get(key)
            if field is not None:
                field.errors(value)
        return func(**kwargs)

    return typing.cast(T, wrapped)
