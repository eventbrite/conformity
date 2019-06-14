from __future__ import (
    absolute_import,
    unicode_literals,
)

import importlib
from types import ModuleType  # noqa: F401 TODO Python 3
from typing import (  # noqa: F401 TODO Python 3
    Any as AnyType,
    Callable,
    Dict,
    Hashable as HashableType,
    List as ListType,
    Mapping,
    MutableMapping,
    Optional,
    Tuple as TupleType,
    Type,
    Union,
)

import attr
import six

from conformity.error import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
    Error,
    ValidationError,
    update_error_pointer,
)
from conformity.fields.basic import (
    Base,
    attr_is_conformity_field,
)
from conformity.fields.structures import Dictionary
from conformity.utils import (
    attr_is_bool,
    attr_is_instance,
    attr_is_instance_or_instance_tuple,
    attr_is_optional,
    attr_is_string,
    strip_none,
)


@attr.s
class Nullable(Base):
    """
    Accepts the field type passed as the first positional argument or a value of null/None. Introspection is a
    dictionary with "type" set to "nullable" and key "nullable" set to the introspection of the first positional
    argument.
    """

    introspect_type = 'nullable'

    field = attr.ib(validator=attr_is_conformity_field())  # type: Base

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
    """
    Useful as a return type, to indicate that a function returns nothing, for example.
    """

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

    switch_field = attr.ib(validator=attr_is_string())  # type: six.text_type
    contents_map = attr.ib(validator=attr_is_instance(dict))  # type: Mapping[HashableType, Base]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

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
                return [Error("Invalid switch value '{}'".format(switch_value), code=ERROR_CODE_UNKNOWN)]
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

    valid_type = attr.ib(validator=attr_is_instance_or_instance_tuple(type))  # type: Union[Type, TupleType[Type, ...]]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return [Error('Not an instance of {}'.format(self.valid_type.__name__))]
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
class PythonPath(Base):
    """
    Accepts only a unicode path to an importable Python type, function, or variable, including the full path to the
    enclosing module. Both '.' and ':' are recognized as valid separators between module name and item name, but if
    the item is not a top-level member of the module, it can only be accessed by using ':' as the separator.

    All of the following are valid type name formats:

    foo.bar.MyClass
    foo.bar:MyClass
    foo.bar.my_function
    foo.bar.MY_CONSTANT
    foo.bar:MyClass.MY_CONSTANT
    baz.qux:ParentClass.SubClass

    This field performs two validations: First that the path is a unicode string, and second that the item is
    importable (exists). If you later need to actually access that item, you can use the `resolve_python_path` static
    method. Imported items are cached for faster future lookup.

    You can optionally specify a `value_schema` argument to this field, itself a Conformity field, which will perform
    further validation on the value of the imported item.
    """
    introspect_type = 'python_path'

    value_schema = attr.ib(default=None, validator=attr_is_optional(attr_is_conformity_field()))  # type: Optional[Base]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    _module_cache = {}  # type: Dict[six.text_type, ModuleType]
    _import_cache = {}  # type: Dict[TupleType[six.text_type, six.text_type], AnyType]

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, six.text_type):
            return [Error('Not a unicode string')]

        try:
            thing = self.resolve_python_path(value)
        except ValueError:
            return [Error('Value "{}" is not a valid Python import path'.format(value))]
        except ImportError as e:
            return [Error(six.text_type(e.args[0]))]
        except AttributeError as e:
            return [Error(six.text_type(e.args[0]))]

        if self.value_schema:
            return self.value_schema.errors(thing)

        return []

    def introspect(self):  # type: () -> Dict[six.text_type, AnyType]
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'value_schema': self.value_schema.introspect() if self.value_schema else None,
        })

    @classmethod
    def resolve_python_path(cls, type_path):  # type: (six.text_type) -> AnyType
        if ':' in type_path:
            module_name, local_path = type_path.split(':', 1)
        else:
            module_name, local_path = type_path.rsplit('.', 1)

        cache_key = (module_name, local_path)
        if cache_key in cls._import_cache:
            return cls._import_cache[cache_key]

        if module_name not in cls._module_cache:
            cls._module_cache[module_name] = importlib.import_module(module_name)

        thing = cls._module_cache[module_name]  # type: AnyType
        for bit in local_path.split('.'):
            thing = getattr(thing, bit)

        cls._import_cache[cache_key] = thing

        return thing


@attr.s
class TypeReference(Base):
    """
    Accepts only type references, optionally types that must be a subclass of a given type or types.
    """
    introspect_type = 'type_reference'

    base_classes = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance_or_instance_tuple(type)),
    )  # type: Optional[Union[Type, TupleType[Type, ...]]]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

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


class TypePath(PythonPath):
    """
    Accepts only a unicode path to an importable Python type, including the full path to the enclosing module. Both '.'
    and ':' are recognized as a valid separator between module name and type name.

    All of the following are valid type name formats:

    foo.bar.MyClass
    foo.bar:MyClass
    baz.qux:ParentClass.SubClass

    This field actually validates that the type is importable, exists, and is a `type`, possibly one that subclasses
    one or more `base_classes`.

    This is a special convenience `PythonPath` extension for expecting the imported item to be a type.
    """
    def __init__(
        self,
        base_classes=None,  # type: Optional[Union[Type, TupleType[Type, ...]]]
        description=None,  # type: Optional[six.text_type]
    ):
        # type: (...) -> None
        super(TypePath, self).__init__(
            value_schema=TypeReference(base_classes=base_classes),
            description=description,
        )


@attr.s
class ClassConfigurationSchema(Base):
    """
    A special-case dictionary field that accepts exactly two keys: `path` (a `TypePath`-validated string) and `kwargs`
    (a `Dictionary`-or-subclass-validated dict) that can discover initialization schema from classes and validate that
    schema prior to instantiation. By default, the dictionary is mutated to add an `object` key containing the resolved
    class, but this behavior can be disabled by specifying `add_class_object_to_dict=False` to the field arguments. If
    you experience circular dependency errors when using this field, you can mitigate this by specifying
    `eager_default_validation=False` to the field arguments.

    Typical usage would be as follows, in Python pseudocode:

    class BaseThing:
        ...

    @ClassConfigurationSchema.provider(fields.Dictionary({...}, ...))
    class Thing1(BaseThing):
        ...

    @ClassConfigurationSchema.provider(fields.Dictionary({...}, ...))
    class Thing2(BaseThing):
        ...

    settings = get_settings_from_something()
    schema = ClassConfigurationSchema(base_class=BaseThing)
    errors = schema.errors(**settings[kwargs])
    if errors:
        ... handle errors ...

    thing = settings['object'](settings)

    Another approach, using the helper method on the schema, simplifies that last part:

    schema = ClassConfigurationSchema(base_class=BaseThing)
    thing = schema.instantiate_from(get_settings_from_something())  # raises ValidationError

    However, note that, in both cases, instantiation is not nested. If the settings schema Dictionary on some class has
    a key (or further down) whose value is another ClassConfigurationSchema, code that consumes those settings will
    also have to instantiate objects from those settings. Validation, however, will be nested as it all other things
    Conformity.
    """
    introspect_type = 'class_config_dictionary'
    switch_field_schema = TypePath(base_classes=object)
    _init_schema_attribute = '_conformity_initialization_schema'

    base_class = attr.ib(default=None, validator=attr_is_optional(attr_is_instance(type)))  # type: Optional[Type]
    default_path = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]
    eager_default_validation = attr.ib(default=True, validator=attr_is_bool())  # type: bool
    add_class_object_to_dict = attr.ib(default=True, validator=attr_is_bool())  # type: bool

    def __attrs_post_init__(self):
        self._schema_cache = {}  # type: Dict[six.text_type, Dictionary]

        if not self.base_class:
            if getattr(self.__class__, 'base_class', None):
                # If the base class was defaulted but a subclass has hard-coded a base class, use that.
                self.base_class = self.__class__.base_class
            else:
                self.base_class = object
        if self.base_class is not object:
            # If the base class is not the default, create a new schema instance to validate paths.
            self.switch_field_schema = TypePath(base_classes=self.base_class)
        else:
            self.switch_field_schema = self.__class__.switch_field_schema

        if not self.description and getattr(self.__class__, 'description', None):
            # If the description is not specified but a subclass has hard-coded a base class, use that.
            self.description = self.__class__.description

        if not self.default_path and getattr(self.__class__, 'default_path', None):
            # If the default path is not specified but a subclass has hard-coded a default path, use that.
            self.default_path = self.__class__.default_path
        if self.default_path and self.eager_default_validation:
            # If the default path is specified and eager validation is not disabled, validate the default path.
            self.initiate_cache_for(self.default_path)

    def errors(self, value):
        if not isinstance(value, Mapping):
            return [Error('Not a mapping (dictionary)')]

        # check for extra keys (object is allowed in case this gets validated twice)
        extra_keys = [k for k in six.iterkeys(value) if k not in ('path', 'kwargs', 'object')]
        if extra_keys:
            return [Error(
                'Extra keys present: {}'.format(', '.join(six.text_type(k) for k in sorted(extra_keys))),
                code=ERROR_CODE_UNKNOWN,
            )]

        sentinel = object()
        path = value.get('path', sentinel)
        if path is sentinel and not self.default_path:
            return [Error('Missing key (and no default specified): path', code=ERROR_CODE_MISSING, pointer='path')]

        if not path or path is sentinel:
            path = self.default_path

        errors = self._populate_schema_cache_if_necessary(path)
        if errors:
            return [update_error_pointer(e, 'path') for e in errors]

        if isinstance(value, MutableMapping):
            value['path'] = path  # in case it was defaulted
            if self.add_class_object_to_dict:
                value['object'] = PythonPath.resolve_python_path(path)

        return [update_error_pointer(e, 'kwargs') for e in self._schema_cache[path].errors(value.get('kwargs', {}))]

    def initiate_cache_for(self, path):  # type: (six.text_type) -> None
        errors = self._populate_schema_cache_if_necessary(path)
        if errors:
            raise ValidationError(errors)

    def _populate_schema_cache_if_necessary(self, path):  # type: (six.text_type) -> ListType[Error]
        if path in self._schema_cache:
            return []

        errors = self.switch_field_schema.errors(path)
        if errors:
            return errors

        clazz = PythonPath.resolve_python_path(path)
        if not hasattr(clazz, self._init_schema_attribute):
            return [Error(
                "Neither class '{}' nor one of its superclasses was decorated with "
                "@ClassConfigurationSchema.provider".format(path),
            )]

        schema = getattr(clazz, self._init_schema_attribute)
        if not isinstance(schema, Dictionary):
            return [Error(
                "Class '{}' attribute '{}' should be a Dictionary Conformity field or one of its subclasses".format(
                    path,
                    self._init_schema_attribute,
                ),
            )]

        self._schema_cache[path] = schema

        return []

    def instantiate_from(self, configuration):  # type: (MutableMapping[HashableType, AnyType]) -> AnyType
        if not isinstance(configuration, MutableMapping):
            raise ValidationError([Error('Not a mutable mapping (dictionary)')])

        errors = self.errors(configuration)
        if errors:
            raise ValidationError(errors)

        clazz = configuration.get('object')
        if not clazz:
            clazz = PythonPath.resolve_python_path(configuration['path'])

        return clazz(**configuration.get('kwargs', {}))

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'base_class': six.text_type(self.base_class.__name__),
            'default_path': self.default_path,
            'switch_field': 'path',
            'switch_field_schema': self.switch_field_schema.introspect(),
            'kwargs_field': 'kwargs',
            'kwargs_contents_map': {k: v.introspect() for k, v in six.iteritems(self._schema_cache)},
        })

    @staticmethod
    def provider(schema):  # type: (Dictionary) -> Callable[[Type], Type]
        if not isinstance(schema, Dictionary):
            raise TypeError("'schema' must be an instance of the Dictionary Conformity field or one of its subclasses")

        def wrapper(cls):  # type: (Type) -> Type
            if not isinstance(cls, type):
                raise TypeError("ClassConfigurationSchema.provider can only decorate classes")
            setattr(cls, ClassConfigurationSchema._init_schema_attribute, schema)
            return cls

        return wrapper


class Any(Base):
    """
    Accepts any one of the types passed as positional arguments.
    Intended to be used for constants but could be used with others.
    """

    introspect_type = 'any'

    description = None  # type: Optional[six.text_type]

    def __init__(self, *args, **kwargs):  # type: (*Base, **AnyType) -> None
        # We can't use attrs here because we need to capture all positional arguments and support keyword arguments
        self.options = args
        for i, r in enumerate(self.options):
            if not isinstance(r, Base):
                raise TypeError('Argument {} must be a Conformity field instance, is actually: {!r}'.format(i, r))

        # We can't put a keyword argument after *args in Python 2, so we need this
        self.description = kwargs.pop(str('description'), None)  # type: Optional[six.text_type]
        if self.description and not isinstance(self.description, six.text_type):
            raise TypeError("'description' must be a unicode string")
        if kwargs:
            raise TypeError('Unknown keyword arguments: {}'.format(', '.join(kwargs.keys())))

    def errors(self, value):
        result = []  # type: ListType[Error]
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

    description = None  # type: Optional[six.text_type]

    def __init__(self, *args, **kwargs):  # type: (*Base, **AnyType) -> None
        # We can't use attrs here because we need to capture all positional arguments and support keyword arguments
        self.requirements = args
        for i, r in enumerate(self.requirements):
            if not isinstance(r, Base):
                raise TypeError('Argument {} must be a Conformity field instance, is actually: {!r}'.format(i, r))

        # We can't put a keyword argument after *args in Python 2, so we need this
        self.description = kwargs.pop(str('description'), None)  # type: Optional[six.text_type]
        if self.description and not isinstance(self.description, six.text_type):
            raise TypeError("'description' must be a unicode string")
        if kwargs:
            raise TypeError('Unknown keyword arguments: {}'.format(', '.join(kwargs.keys())))

    def errors(self, value):
        result = []  # type: ListType[Error]
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

    validator = attr.ib()  # type: Callable[[AnyType], bool]
    validator_description = attr.ib(validator=attr_is_string())  # type: six.text_type
    error = attr.ib(validator=attr_is_string())  # type: six.text_type
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        # Run the validator, but catch any errors and return them as an error.
        try:
            ok = self.validator(value)
        except Exception as e:
            return [Error('Validator encountered an error (invalid type?): {!r}'.format(e))]

        if ok:
            return []
        else:
            return [Error(self.error)]

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'validator': self.validator_description,
        })
