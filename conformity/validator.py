from __future__ import (
    absolute_import,
    unicode_literals,
)

from functools import wraps
from typing import (  # noqa: F401 TODO Python 3
    Any as AnyType,
    Callable,
    List as ListType,
    Optional,
    Tuple as TupleType,
    Union,
)

import six  # noqa: F401 TODO Python 3

from conformity import fields
from conformity.error import (
    KeywordError,
    PositionalError,
    ValidationError,
)


__all__ = (
    'KeywordError',
    'PositionalError',
    'ValidationError',
    'validate',
    'validate_call',
    'validate_method',
)


def validate(schema, value, noun='value'):
    # type: (fields.Base, AnyType, six.text_type) -> None
    """
    Checks the value against the schema, and raises ValidationError if validation
    fails.
    """
    errors = schema.errors(value)
    if errors:
        error_details = ''
        for error in errors:
            if error.pointer:
                error_details += '  - {}: {}\n'.format(error.pointer, error.message)
            else:
                error_details += '  - {}\n'.format(error.message)
        raise ValidationError('Invalid {}:\n{}'.format(noun, error_details))


def validate_call(
    kwargs,  # type: Optional[Union[fields.Dictionary, fields.SchemalessDictionary]]
    returns,  # type: fields.Base
    is_method=False,  # type: bool
    args=None  # type: Optional[Union[fields.Tuple, fields.List]]
):
    # type: (...) -> Callable[[Callable], Callable]
    """
    Decorator which runs validation on a callable's arguments and its return value. Pass a schema for the kwargs and
    for the return value. Positional arguments are not supported unless `args=fields.List(...)` or
    `args=fields.Tuple(...)` is specified to supply a schema for positional arguments. In almost all cases, you should
    support keyword arguments, but it's possible to support only positional arguments with `kwargs=None`.

    :param args: Validation schema for positional arguments, or `None` if positional arguments are not supported.
    :param kwargs: Validation schema for keyword arguments, or `None` if keyword arguments are not supported.
    :param returns: Validation schema for the return value
    :param is_method: Set this to `True` for instance methods and class methods, but `False` (the default) for all
                      other callables, including static methods.
    """

    if args is not None and not isinstance(args, (fields.Tuple, fields.List)):
        raise ValueError(
            'Invalid use of `validate_call` or `validate_method` decorator: `args` argument must be a `fields.List` '
            'or `None` (the default value).'
        )
    if kwargs is not None and not isinstance(kwargs, (fields.Dictionary, fields.SchemalessDictionary)):
        raise ValueError(
            'Invalid use of `validate_call` or `validate_method` decorator: `kwargs` argument must be a '
            '`fields.Dictionary`, `fields.SchemalessDictionary`, or `None` (there is no default value).'
        )

    def decorator(func):
        @wraps(func)
        def decorated(*passed_args, **passed_kwargs):
            # Validate positional arguments. The first argument of instance and class methods is always a positional
            # argument (`self` ond `cls`, respectively), so we need to make an exception for those if positional
            # arguments are not supported and exclude those if positional arguments are supported.
            if args is not None:
                validate_args = passed_args[(1 if is_method else 0):]  # type: Union[TupleType, ListType]
                if isinstance(args, fields.List):
                    validate_args = list(validate_args)
                validate(args, validate_args, 'positional arguments')
            elif passed_args:
                if not is_method or len(passed_args) > 1:
                    raise PositionalError('{} does not accept positional arguments'.format(func.__name__))

            # Validate keyword arguments.
            if kwargs is not None:
                validate(kwargs, passed_kwargs, 'keyword arguments')
            elif passed_kwargs:
                raise KeywordError('{} does not accept keyword arguments'.format(func.__name__))

            # Call callable
            return_value = func(*passed_args, **passed_kwargs)

            # Validate return value
            validate(returns, return_value, 'return value')

            return return_value

        setattr(decorated, '__wrapped__', func)
        # caveat: checking for f.__validated__ will work only if @validate_call is not masked by other decorators,
        # except for @classmethod or @staticmethod
        setattr(decorated, '__validated__', True)
        setattr(decorated, '__validated_schema_args__', args)
        setattr(decorated, '__validated_schema_kwargs__', kwargs)
        setattr(decorated, '__validated_schema_returns__', returns)
        return decorated

    return decorator


# use @validate_method for methods. If it's a class or static method,
# @classmethod/@staticmethod should be outermost, while @validate_method second-outermost
# used to use a partial, but that masks argument names from intellisense tools.
def validate_method(
    kwargs,  # type: Union[fields.Dictionary, fields.SchemalessDictionary]
    returns,  # type: fields.Base
    args=None,  # type: Union[fields.Tuple, fields.List]
):
    # type: (...) -> Callable[[Callable], Callable]
    """
    Decorator which runs validation on a method's arguments and its return value. Pass a schema for the kwargs and
    for the return value. Positional arguments are not supported unless `args=fields.List(...)` or
    `args=fields.Tuple(...)` is specified to supply a schema for positional arguments. In almost all cases, you should
    support keyword arguments, but it's possible to support only positional arguments with `kwargs=None`.

    :param args: Validation schema for positional arguments, or `None` if positional arguments are not supported.
    :param kwargs: Validation schema for keyword arguments, or `None` if keyword arguments are not supported.
    :param returns: Validation schema for the return value
    """
    return validate_call(args=args, kwargs=kwargs, returns=returns, is_method=True)
