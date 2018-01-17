from __future__ import absolute_import, unicode_literals

from functools import partial, wraps
import types


class ValidationError(ValueError):
    """
    Error raised when a value fails to validate.
    """
    pass


class PositionalError(TypeError):
    """
    Error raised when you pass positional arguments into a validated function.
    """
    pass


def validate(schema, value, noun="value"):
    """
    Checks the value against the schema, and raises ValidationError if validation
    fails.
    """
    errors = schema.errors(value)
    if errors:
        error_details = ''
        for error in errors:
            if error.pointer:
                error_details += '  - %s: %s\n' % (error.pointer, error.message)
            else:
                error_details += '  - %s\n' % error.message
        raise ValidationError("Invalid %s:\n%s" % (noun, error_details))


def validate_call(kwargs, returns, is_method=False):
    """
    Decorator which runs validation on a callable's arguments and its return
    value. Pass a schema for the kwargs and for the return value. Positional
    arguments are not supported.
    """
    def decorator(func):
        @wraps(func)
        def inner(*passed_args, **passed_kwargs):
            # Enforce no positional args
            # first argument of instance method and class method is always positonal so we need
            # to make expception for them. Static methods are still validated according to standard rules
            # this check happens before methods are bound, so instance method is still a regular function
            max_allowed_passed_args_len = 0
            if is_method and type(func) in (types.FunctionType, classmethod):
                max_allowed_passed_args_len = 1

            if len(passed_args) > max_allowed_passed_args_len:
                raise PositionalError("You cannot call this with positional arguments.")
            # Validate keyword arguments
            validate(kwargs, passed_kwargs, "keyword arguments")
            # Call callable
            return_value = func(*passed_args, **passed_kwargs)
            # Validate return value
            validate(returns, return_value, "return value")
            return return_value
        inner.__wrapped__ = func
        # caveat: checking for f.__validated__ will only work if @validate_call
        # is not masked by other decorators except for @classmethod or @staticmethod
        inner.__validated__ = True
        return inner
    return decorator


# use @validate_method for methods. If it's a class or static method,
# @classdecorator/@staticmethod should be outmost, while @validate_method second outmost
validate_method = partial(validate_call, is_method=True)
