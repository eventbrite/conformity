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
        raise ValidationError("Invalid %s:\n  - %s" % (noun, "\n  - ".join(errors)))


def validate_call(kwargs, returns):
    """
    Decorator which runs validation on a callable's arguments and its return
    value. Pass a schema for the kwargs and for the return value. Positional
    arguments are not supported.
    """
    def decorator(func):
        def inner(*passed_args, **passed_kwargs):
            # Enforce no positional args
            if passed_args:
                raise PositionalError("You cannot call this with positional arguments.")
            # Validate keyword arguments
            validate(kwargs, passed_kwargs, "keyword arguments")
            # Call callable
            return_value = func(*passed_args, **passed_kwargs)
            # Validate return value
            validate(returns, return_value, "return value")
            return return_value
        return inner
    return decorator
