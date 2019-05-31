from __future__ import (
    absolute_import,
    unicode_literals,
)

import importlib
from typing import (  # noqa: F401 TODO Python 3
    Dict,
    Tuple,
    Type,
    Union,
)

import attr
import six

from conformity.error import (
    ERROR_CODE_UNKNOWN,
    Error,
)
from conformity.fields.basic import Base
from conformity.utils import strip_none


@attr.s
class Nullable(Base):
    """
    Accepts the field type passed as the first positional argument or a value of null/None. Introspection is a
    dictionary with "type" set to "nullable" and key "nullable" set to the introspection of the first positional
    argument.
    """

    introspect_type = 'nullable'
    field = attr.ib()

    def errors(self, value):
        if value is None:
            return []

        return self.field.errors(value)

    def introspect(self):
        return {
            'type': self.introspect_type,
            'nullable': self.field.introspect(),
        }


class Null(Base):
    introspect_type = 'null'

    def errors(self, value):
        if value is not None:
            return [Error('Value is not null')]
        return []

    def introspect(self):
        return {'type': self.introspect_type}


@attr.s
class Polymorph(Base):
    """
    A field which has one of a set of possible contents based on a field
    within it (which must be accessible via dictionary lookups)
    """

    introspect_type = 'polymorph'
    switch_field = attr.ib()
    contents_map = attr.ib()
    description = attr.ib(default=None)

    def errors(self, value):
        # Get switch field value
        bits = self.switch_field.split('.')
        switch_value = value
        for bit in bits:
            switch_value = switch_value[bit]
        # Get field
        if switch_value not in self.contents_map:
            if '__default__' in self.contents_map:
                switch_value = '__default__'
            else:
                return [
                    Error('Invalid switch value {}'.format(switch_value), code=ERROR_CODE_UNKNOWN),
                ]
        field = self.contents_map[switch_value]
        # Run field errors
        return field.errors(value)

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'switch_field': self.switch_field,
            'contents_map': {
                key: value.introspect()
                for key, value in self.contents_map.items()
            },
        })


@attr.s
class ObjectInstance(Base):
    """
    Accepts only instances of a given class or type
    """

    introspect_type = 'object_instance'
    valid_type = attr.ib()
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return [
                Error('Not an instance of %s' % self.valid_type.__name__),
            ]
        else:
            return []

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            # Unfortunately, this is the one sort of thing we can't represent
            # super well. Maybe add some dotted path stuff in here.
            'valid_type': repr(self.valid_type),
        })


@attr.s
class TypeReference(Base):
    """
    Accepts only type references, optionally types that must be a subclass of a given type or types.
    """
    introspect_type = 'type_reference'
    base_classes = attr.ib(default=None)  # type: Union[Type, Tuple[Type, ...]]
    description = attr.ib(default=None)  # type: six.text_type

    def errors(self, value):
        if not isinstance(value, type):
            return [Error('Not a type')]

        if self.base_classes and not issubclass(value, self.base_classes):
            return [Error('Type {} is not one of or a subclass of one of: {}'.format(value, self.base_classes))]

        return []

    def introspect(self):
        base_classes = None
        if self.base_classes:
            if isinstance(self.base_classes, type):
                base_classes = [six.text_type(self.base_classes)]
            else:
                base_classes = [six.text_type(c) for c in self.base_classes]

        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'base_classes': base_classes,
        })


@attr.s
class TypePath(TypeReference):
    """
    Accepts only a unicode path to an importable Python type, including the full path to the enclosing module. Both '.'
    and ':' are recognized as a valid separator between module name and type name.

    All of the following are valid type name formats:

    foo.bar.MyClass
    foo.bar:MyClass
    baz.qux:ParentClass.SubClass

    This field actually validates that the type is importable and exists (and includes a static resolve_python_path to
    help you convert the value into a type), and so it also includes a long-lived import cache to maximize performance.
    """
    introspect_type = 'type_path'

    import_cache = {}  # type: Dict[Tuple[six.text_type, six.text_type], Type]

    def errors(self, value):
        if not isinstance(value, six.text_type):
            return [Error('Not a unicode string')]

        try:
            thing = self.resolve_python_path(value)
        except ValueError:
            return [Error('Value "{}" is not a valid Python import path'.format(value))]
        except ImportError as e:
            return [Error(e.args[0])]
        except AttributeError as e:
            return [Error(e.args[0])]

        return super(TypePath, self).errors(thing)

    @classmethod
    def resolve_python_path(cls, type_path):  # type: (six.text_type) -> Type
        if ':' in type_path:
            module_name, local_path = type_path.split(':', 1)
        else:
            module_name, local_path = type_path.rsplit('.', 1)

        cache_key = (module_name, local_path)
        if cache_key in cls.import_cache:
            return cls.import_cache[cache_key]

        thing = importlib.import_module(module_name)
        for bit in local_path.split('.'):
            thing = getattr(thing, bit)

        cls.import_cache[cache_key] = thing

        return thing


class Any(Base):
    """
    Accepts any one of the types passed as positional arguments.
    Intended to be used for constants but could be used with others.
    """

    introspect_type = 'any'
    description = None

    def __init__(self, *args, **kwargs):
        self.options = args
        # We can't put a keyword argument after *args in Python 2, so we need this
        if 'description' in kwargs:
            self.description = kwargs['description']
            del kwargs['description']
        if kwargs:
            raise TypeError('Unknown keyword arguments: %s' % ', '.join(kwargs.keys()))

    def errors(self, value):
        result = []
        for option in self.options:
            sub_errors = option.errors(value)
            # If there's no errors from a sub-field, then it's all OK!
            if not sub_errors:
                return []
            # Otherwise, add the errors to the overall results
            result.extend(sub_errors)
        return result

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'options': [option.introspect() for option in self.options],
        })


class All(Base):
    """
    The value must pass all of the types passed as positional arguments.
    Intended to be used for adding extra validation.
    """

    introspect_type = 'all'
    description = None

    def __init__(self, *args, **kwargs):
        self.requirements = args
        # We can't put a keyword argument after *args in Python 2, so we need this
        if 'description' in kwargs:
            self.description = kwargs['description']
            del kwargs['description']
        if kwargs:
            raise TypeError('Unknown keyword arguments: %s' % ', '.join(kwargs.keys()))

    def errors(self, value):
        result = []
        for requirement in self.requirements:
            result.extend(requirement.errors(value) or [])
        return result

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'requirements': [requirement.introspect() for requirement in self.requirements],
        })


@attr.s
class BooleanValidator(Base):
    """
    Uses a boolean callable (probably lambda) passed in to validate the value
    based on if it returns True (valid) or False (invalid).
    """

    introspect_type = 'boolean_validator'
    validator = attr.ib()
    validator_description = attr.ib(validator=attr.validators.instance_of(six.text_type))
    error = attr.ib(validator=attr.validators.instance_of(six.text_type))
    description = attr.ib(default=None)

    def errors(self, value):
        # Run the validator, but catch any errors and return them as an error
        # as this is maybe in an All next to a type-checker.
        try:
            ok = self.validator(value)
        except Exception:
            return [
                Error('Validator encountered an error (invalid type?)'),
            ]
        if ok:
            return []
        else:
            return [
                Error(self.error),
            ]

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'validator': self.validator_description,
        })
