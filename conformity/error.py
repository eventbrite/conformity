__all__ = (
    'KeywordError',
    'PositionalError',
    'ValidationError',
)


class ValidationError(ValueError):
    """
    Error raised when a value fails to validate.
    """


class PositionalError(TypeError):
    """
    Error raised when you pass positional arguments into a validated function
    that doesn't support them.
    """


class KeywordError(TypeError):
    """
    Error raised when you pass keyword arguments into a validated function that
    doesn't support them.
    """
