from abc import abstractmethod

from typing import (
    Any,
    List,
)

from conformity.types import (
    Error,
    Warning,
    Validation,
)
from conformity.fields.base import BaseField


class Base(BaseField):
    """
    The legacy (Conformity 1.x) base field from which all other legacy fields
    inherit. This defines a simple interface for getting a list of validation
    errors and recursively introspecting the schema.
    """
    @abstractmethod
    def errors(self, value: Any) -> List[Error]:
        """
        Returns a list of errors with the value. An empty return means that it's
        valid.
        """

    def warnings(self, value: Any) -> List[Warning]:
        """
        Returns a list of warnings for the field or value.
        """
        return []

    def validate(self, value: Any) -> Validation:
        return Validation(
            errors=self.errors(value),
            warnings=self.warnings(value),
        )
