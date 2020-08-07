import importlib
from types import ModuleType
from typing import (
    Any,
    Callable,
    Dict,
    Hashable as HashableType,
    MutableMapping,
    Tuple,
    Type as TypeType,
    Union,
)

from conformity.constants import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)
from conformity.error import ValidationError
from conformity.fields.base import (
    BaseField,
    BaseTypeField,
)
from conformity.fields.meta import Type
from conformity.fields.simple import String
from conformity.fields.structures import Dictionary
from conformity.fields.utils import strip_none
from conformity.types import (
    Error,
    Validation,
)
from conformity.typing import Introspection

__all__ = (
    'PythonPath',
    'TypePath',
    'ClassConfigurationSchema',
)


class PythonPath(String):
    """
    Validates that a value is a string path to an importable Python type,
    function, or variable, including the full path to the enclosing module. Both
    '.' and ':' are recognized as valid separators between module name and item
    name, but if the item is not a top-level member of the module, it can only
    be accessed by using ':' as the separator.

    Examples of valid Python path strings:

    foo.bar.MyClass
    foo.bar:MyClass
    foo.bar.my_function
    foo.bar.MY_CONSTANT
    foo.bar:MyClass.MY_CONSTANT
    baz.qux:ParentClass.SubClass

    This field performs two validations:
    1. That the path is a unicode string, and
    2. That the item is importable (exists)

    If you later need to actually access that item, you can use the
    `resolve_python_path` static method. Imported items are cached for faster
    future lookup.

    You can optionally specify a `value_schema` argument to this field, itself a
    Conformity field, which will perform further validation on the value of the
    imported item.
    """
    introspect_type = 'python_path'

    _module_cache = {}  # type: Dict[str, ModuleType]
    _import_cache = {}  # type: Dict[Tuple[str, str], Any]

    def __init__(
        self,
        *,
        value_schema: BaseField = None,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)

        # Validate arguments
        if value_schema is not None and not isinstance(value_schema, BaseField):
            raise TypeError('value_schema must be a Conformity field')

        self.value_schema = value_schema

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        try:
            thing = self.resolve_python_path(value)
        except ValueError:
            v.errors.append(Error(
                'Value "{}" is not a valid Python import path'.format(value)
            ))
        except ImportError as e:
            v.errors.append(Error(
                'ImportError: {}'.format(str(e.args[0]))
            ))
        except AttributeError as e:
            v.errors.append(Error(
                'AttributeError: {}'.format(str(e.args[0]))
            ))
        else:
            if self.value_schema is not None:
                v.extend(self.value_schema.errors(thing))

        return v

    def introspect(self) -> Introspection:
        return strip_none({
            'value_schema': (
                self.value_schema.introspect()
                if self.value_schema
                else None
            ),
        }).update(super().introspect())

    @classmethod
    def resolve_python_path(cls, type_path: str) -> Any:
        if ':' in type_path:
            module_name, local_path = type_path.split(':', 1)
        else:
            module_name, local_path = type_path.rsplit('.', 1)

        cache_key = (module_name, local_path)
        if cache_key in cls._import_cache:
            return cls._import_cache[cache_key]

        if module_name not in cls._module_cache:
            cls._module_cache[module_name] = importlib.import_module(
                module_name,
            )

        thing = cls._module_cache[module_name]  # type: Any
        for bit in local_path.split('.'):
            thing = getattr(thing, bit)

        cls._import_cache[cache_key] = thing

        return thing


class TypePath(PythonPath):
    """
    A special convenience `PythonPath` extension for expecting the imported
    item to be a type
    """
    def __init__(
        self,
        *,
        base_classes: Union[TypeType, Tuple[TypeType, ...]] = None,
        **kwargs: Any
    ):
        super().__init__(
            value_schema=Type(base_classes=base_classes),
            **kwargs
        )


class ClassConfigurationSchema(BaseTypeField):
    """
    A special-case dictionary field that accepts exactly two keys:
    * `path` - a `TypePath`-validated string), and
    * `kwargs` - a `Dictionary`-or-subclass-validated dict

    It can discover initialization schema from classes and validate that schema
    prior to instantiation. By default, the dictionary is mutated to add an
    `object` key containing the resolved class, but this behavior can be
    disabled by specifying `add_class_object_to_dict=False` to the field
    arguments. If you experience circular dependency errors when using this
    field, you can mitigate this by specifying `eager_default_validation=False`
    to the field arguments.

    Typical usage would be as follows, in Python pseudocode:

    .. code-block:: python

        class BaseThing:
            ...

        @fields.ClassConfigurationSchema.provider(fields.Dictionary({...}, ...))
        class Thing1(BaseThing):
            ...

        @fields.ClassConfigurationSchema.provider(fields.Dictionary({...}, ...))
        class Thing2(BaseThing):
            ...

        settings = get_settings_from_something()
        schema = fields.ClassConfigurationSchema(base_class=BaseThing)
        errors = schema.errors(**settings[kwargs])
        if errors:
            ... handle errors ...

        thing = settings['object'](settings)

    Another approach, using the helper method on the schema, simplifies that
    last part:

    .. code-block:: python

        schema = fields.ClassConfigurationSchema(base_class=BaseThing)

        # the following raises a ValidationError
        thing = schema.instantiate_from(get_settings_from_something())

    However, note that, in both cases, instantiation is not nested. If the
    settings schema Dictionary on some class has a key (or further down) whose
    value is another `ClassConfigurationSchema`, code that consumes those
    settings will also have to instantiate objects from those settings.
    Validation, however, will be nested as in all other things Conformity.
    """
    valid_type = dict
    valid_noun = 'a class configuration dictionary'
    introspect_type = 'class_config_dictionary'

    _init_schema_attribute = '_conformity_initialization_schema'

    def __init__(
        self,
        *,
        base_class: type = None,
        default_path: str = None,
        eager_default_validation: bool = True,
        add_class_object_to_dict: bool = True,
        **kwargs: Any
    ):
        super().__init__(**kwargs)
        self._schema_cache = {}  # type: Dict[str, Dictionary]

        base_class = base_class or getattr(self.__class__, 'base_class', object)
        if not isinstance(base_class, type):
            raise TypeError('base_class must be a type')
        self.switch_field_schema = TypePath(base_classes=base_class)

        self.default_path = (
            default_path or getattr(self.__class__, 'default_path', None)
        )
        if self.default_path and eager_default_validation:
            self.initiate_cache_for(self.default_path)
        self.default_path = default_path

        self.add_class_object_to_dict = add_class_object_to_dict

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        # Check for extra keys
        # Note: object is allowed in case this gets validated twice
        extra_keys = set(value.keys()) - set(('path', 'kwargs', 'object'))
        if extra_keys:
            v.errors.append(Error(
                'Extra keys present: {}'.format(
                    ', '.join(str(k) for k in extra_keys),
                ),
                code=ERROR_CODE_UNKNOWN,
            ))
            return v

        sentinel = object()
        path = value.get('path', sentinel)
        if path is sentinel and not self.default_path:
            v.errors.append(Error(
                'Missing key (and no default specified): path',
                code=ERROR_CODE_MISSING,
                pointer='path',
            ))
            return v

        if not path or path is sentinel:
            path = self.default_path

        path_v = self._populate_schema_cache_if_necessary(path)
        if path_v.errors:
            v.extend(path_v, pointer='path')
            return v

        if isinstance(value, MutableMapping):
            value['path'] = path
            if self.add_class_object_to_dict:
                value['object'] = PythonPath.resolve_python_path(path)

        kwargs_v = self._schema_cache[path].validate(value.get('kwargs', {}))
        v.extend(kwargs_v, pointer='kwargs')
        return v

    def initiate_cache_for(self, path: str) -> None:
        v = self._populate_schema_cache_if_necessary(path)
        if v.errors:
            raise ValidationError(v.errors)

    def _populate_schema_cache_if_necessary(self, path: str) -> Validation:
        if path in self._schema_cache:
            return Validation()

        v = self.switch_field_schema.validate(path)
        if v.errors:
            return v

        clazz = PythonPath.resolve_python_path(path)
        if not hasattr(clazz, self._init_schema_attribute):
            v.errors.append(Error(
                'Neither class "{}" nor one of its superclasses was decorated '
                'with @ClassConfigurationSchema.provider'.format(path),
            ))
            return v

        schema = getattr(clazz, self._init_schema_attribute)
        if not isinstance(schema, Dictionary):
            v.errors.append(Error(
                'Class "{}" attribute "{}" should be a Dictionary field or one '
                'of its subclasses'.format(path, self._init_schema_attribute),
            ))
            return v

        self._schema_cache[path] = schema
        return v

    def instantiate_from(
        self,
        configuration: MutableMapping[HashableType, Any],
    ) -> Any:
        if not isinstance(configuration, MutableMapping):
            raise ValidationError([Error('Not a mutable mapping (dictionary)')])

        v = self.validate(configuration)
        if v.errors:
            raise ValidationError(v.errors)

        clazz = configuration.get('object')
        if not clazz:
            clazz = PythonPath.resolve_python_path(configuration['path'])

        return clazz(**configuration.get('kwargs', {}))

    def introspect(self) -> Introspection:
        return strip_none({
            'switch_field': 'path',
            'switch_field_schema': self.switch_field_schema.introspect(),
            'kwargs_field': 'kwargs',
            'kwargs_contents_map': {
                k: v.introspect()
                for k, v in self._schema_cache.items()
            },
        }).update(super().introspect())

    @staticmethod
    def provider(schema: Dictionary) -> Callable[[Type], Type]:
        if not isinstance(schema, Dictionary):
            raise TypeError(
                '"schema" must be an instance of a Dictionary field or one of '
                'its subclasses',
            )

        def wrapper(cls: Type) -> Type:
            if not isinstance(cls, type):
                raise TypeError(
                    'ClassConfigurationSchema.provider can only decorate '
                    'classes'
                )
            setattr(cls, ClassConfigurationSchema._init_schema_attribute, schema)
            return cls

        return wrapper
