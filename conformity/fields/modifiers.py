from typing import Any

from conformity.constants import WARNING_CODE_FIELD_DEPRECATED
from conformity.fields.base import BaseField
from conformity.types import (
    Warning,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'Deprecated',
    'Optional',
)


class Deprecated(BaseField):
    """
    Modifier that marks a field as deprecated
    """
    default_message = 'This field has been deprecated'

    def __init__(
        self,
        field: BaseField,
        *,
        message: str = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        # Validate arguments
        if not isinstance(field, BaseField):
            raise TypeError('field argument must be a Conformity field')
        if message is None:
            message = self.default_message
        elif not isinstance(message, str):
            raise TypeError('message argument must be a string')

        self.field = field
        self.message = message

    def validate(self, value: Any) -> Validation:
        # Pass through validation, then add the deprecation warning
        v = self.field.validate(value)
        v.warnings.append(Warning(
            code=WARNING_CODE_FIELD_DEPRECATED,
            message=self.message,
        ))
        return v

    def introspect(self) -> Introspection:
        # Pass through introspection, then add the deprecated field
        field_introspection = self.field.introspect()
        field_introspection['deprecated'] = True
        return field_introspection


class Optional(BaseField):
    """
    Modifier that marks a field as optional
    """
    def __init__(
        self,
        field: BaseField,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        # Validate arguments
        if not isinstance(field, BaseField):
            raise TypeError('field argument must be a Conformity field')

        self.field = field

    def validate(self, value: Any) -> Validation:
        # Pass through validation, then allow None on error
        v = self.field.validate(value)
        if v.errors and value is None:
            v.errors = []

        return v

    def introspect(self) -> Introspection:
        # Pass through introspection, then add the optional field
        field_introspection = self.field.introspect()
        field_introspection['optional'] = True
        return field_introspection
