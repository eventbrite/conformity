from collections import abc
from typing import (
    Any as AnyType,
    Callable,
    Hashable,
    Mapping,
    Tuple,
    Type as TypeType,
    Union,
)

from conformity.constants import (
    ERROR_CODE_UNKNOWN,
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
    'All',
    'Any',
    'Anything',
    'Chain',
    'Constant',
    'Instance',
    'Polymorph',
    'Type',
    'Validator',
)


class Anything(BaseField):
    """
    Validates that the value can be anything
    """

    introspect_type = 'anything'

    def validate(self, value: AnyType) -> Validation:
        return Validation()


class Constant(BaseField):
    """
    Validates that the value exactly matches the constant parameter supplied or,
    if multiple constant parameters are supplied, exactly matches one of those
    values.
    """

    introspect_type = 'constant'

    def __init__(self, *values: Hashable, **kwargs: AnyType) -> None:
        super().__init__(**kwargs)

        # Validate arguments
        if not values:
            raise ValueError('You must provide at least one constant value')
        for i, value in enumerate(values):
            if not isinstance(value, abc.Hashable):
                raise TypeError((
                    'Constant value provided at index '
                    '{} is not hashable'
                ).format(i))

        self.values = frozenset(values)

        # Build error message
        def _repr(cv):
            return '"{}"'.format(cv) if isinstance(cv, str) else '{}'.format(cv)
        if len(self.values) == 1:
            self._error_message = 'Value is not {}'.format(_repr(values[0]))
        else:
            self._error_message = 'Value is not one of: {}'.format(
                ', '.join(sorted(_repr(v) for v in self.values)),
            )

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)

        try:
            is_valid = value in self.values
        except TypeError:
            # Unhashable values can't be used for membership checks.
            is_valid = False

        if not is_valid:
            v.errors.append(Error(self._error_message, code=ERROR_CODE_UNKNOWN))

        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'values': [
                s
                if isinstance(s, (str, bool, int, float, type(None)))
                else str(s)
                for s in sorted(self.values, key=str)
            ],
        })


class Polymorph(BaseTypeField):
    """
    A special-case Dictionary field which has one of a set of possible contents
    based on a field within it (which must be accessible via `Mapping` key
    lookups).
    """

    valid_type = dict
    valid_noun = 'a polymorphic dictionary'
    introspect_type = 'polymorph'

    def __init__(
        self,
        *,
        switch_field: str,
        contents_map: Mapping[Hashable, BaseField],
        **kwargs: AnyType
    ):
        super().__init__(**kwargs)

        # Validate arguments
        if not isinstance(switch_field, str):
            raise TypeError('switch_field must be a string')
        if not isinstance(contents_map, dict):
            raise TypeError('contents_map must be a dictionary')
        for key, field in contents_map.items():
            if not isinstance(field, BaseField):
                raise TypeError(
                    'contents_map[{}] must be a Conformity field'.format(key),
                )

        self.switch_field = switch_field
        self.contents_map = contents_map

    def _get_switch_value(self, value: AnyType) -> Tuple[str, bool]:
        # Get switch field value
        bits = self.switch_field.split('.')
        switch_value = value
        valid = True
        for bit in bits:
            switch_value = switch_value[bit]

        if switch_value not in self.contents_map:
            if '__default__' in self.contents_map:
                switch_value = '__default__'
            else:
                valid = False

        return switch_value, valid

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        switch_value, valid = self._get_switch_value(value)
        if not valid:
            v.errors.append(Error(
                'Invalid switch value "{}"'.format(switch_value),
                code=ERROR_CODE_UNKNOWN,
            ))
            return v

        # Perform field validation
        field = self.contents_map[switch_value]
        return field.validate(value)

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'switch_field': self.switch_field,
            'contents_map': {
                key: value.introspect()
                for key, value in self.contents_map.items()
            },
        })


class Instance(BaseField):
    """
    Validates that the value is an instance of the given `valid_type`
    """

    introspect_type = 'instance'

    def __init__(
        self,
        valid_type: Union[TypeType, Tuple[TypeType, ...]],
        **kwargs: AnyType
    ) -> None:
        super().__init__(**kwargs)
        if not isinstance(valid_type, type):
            raise TypeError('`valid_type` must be a type')
        self.valid_type = valid_type

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        if not isinstance(value, self.valid_type):
            v.errors.append(Error(
                'Value is not an instance of {}'.format(getattr(
                    self.valid_type, '__name__', repr(self.valid_type)
                ))
            ))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'valid_type': repr(self.valid_type),
        })


class Type(BaseTypeField):
    """
    Validates that the value is an instance of `type` and, optionally, that the
    value is a subclass of the type or types specified by `base_classes`
    """

    valid_type = type

    def __init__(
        self,
        *,
        base_classes: Union[TypeType, Tuple[TypeType, ...]] = None,
        **kwargs: AnyType
    ) -> None:
        super().__init__(**kwargs)

        # Clean arguments
        if base_classes is None:
            base_classes = ()
        elif not isinstance(base_classes, tuple):
            base_classes = (base_classes,)

        # Validate bases
        for base in base_classes:
            if not isinstance(base, type):
                raise TypeError('{!r} is not a type'.format(base))
        self.base_classes = base_classes

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        if self.base_classes and not issubclass(value, self.base_classes):
            v.errors.append(Error(
                'Type {} is not one of or a subclass of one of: {}'.format(
                    value,
                    self.base_classes,
                ),
            ))

        return v

    def introspect(self) -> Introspection:
        base_classes = None
        if self.base_classes:
            base_classes = [repr(c) for c in self.base_classes]

        return strip_none({
            **super().introspect(),
            'base_classes': base_classes,
        })


class Any(BaseField):
    """
    Validates that the value passes validation with at least one of the
    Conformity fields passed as positional arguments
    """

    introspect_type = 'any'

    def __init__(self, *options: BaseField, **kwargs: AnyType) -> None:
        super().__init__(**kwargs)

        # Validate fields
        for i, field in enumerate(options):
            if not isinstance(field, BaseField):
                raise TypeError((
                    'Argument {} must be a Conformity field '
                    'instance, is actually: {!r}'
                ).format(i, field))
        self.options = options

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        for field in self.options:
            field_v = field.validate(value)
            # If there's no errors from a sub-field, then it's all OK!
            if not field_v.errors:
                return field_v
            # Otherwise, add the errors to the overall results
            v.extend(field_v)

        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'options': [option.introspect() for option in self.options],
        })


class All(BaseField):
    """
    Validates that the value passes validation with all of the Conformity fields
    passed as positional arguments
    """

    introspect_type = 'all'

    def __init__(self, *requirements: BaseField, **kwargs: AnyType) -> None:
        super().__init__(**kwargs)

        for i, field in enumerate(requirements):
            if not isinstance(field, BaseField):
                raise TypeError((
                    'Argument {} must be a Conformity field '
                    'instance, is actually: {!r}'
                ).format(i, field))

        self.requirements = requirements

    def validate(self, value: AnyType) -> Validation:
        v = Validation()
        for field in self.requirements:
            v.extend(field.validate(value))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'requirements': [field.introspect() for field in self.requirements],
        })


class Chain(BaseField):
    """
    Sequentially validates the value with the Conformity fields passed as
    positional arguments. Importantly, validation only continues to the next
    field if the current field validates the value without errors.
    """

    introspect_type = 'chain'

    def __init__(self, *fields: BaseField, **kwargs: AnyType) -> None:
        super().__init__(**kwargs)

        for i, field in enumerate(fields):
            if not isinstance(field, BaseField):
                raise TypeError((
                    'Argument {} must be a Conformity field '
                    'instance, is actually: {!r}'
                ).format(i, field))

        self.fields = fields

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        for field in self.fields:
            if v.errors:
                return v
            v.extend(field.validate(value))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'fields': [field.introspect() for field in self.fields],
        })


class Validator(BaseField):
    """
    Validates that the value passes validation with the provided
    `typing.Callable[[typing.Any], bool]` `validator` argument
    """

    introspect_type = 'validator'

    def __init__(
        self,
        validator: Callable[[AnyType], bool],
        *,
        validator_description: str,
        error: str,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self.validator = validator
        self.validator_description = validator_description
        self.error = error

        # Validate arguments
        if not callable(self.validator):
            raise TypeError('validator argument must be callable')
        if not isinstance(self.validator_description, str):
            raise TypeError('validator_description must be a string')
        if not isinstance(self.error, str):
            raise TypeError('error must be a string')

    def validate(self, value: AnyType) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        # Run the validator, but catch any errors and return them as an error.
        try:
            ok = self.validator(value)
        except Exception as e:
            v.errors.append(Error(
                'Validator encountered an error (invalid type?): {!r}'.format(e)
            ))
            return v

        if not ok:
            v.errors.append(Error(self.error))
        return v

    def introspect(self) -> Introspection:
        return strip_none({
            **super().introspect(),
            'validator': self.validator_description,
        })
