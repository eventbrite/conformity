from __future__ import (
    absolute_import,
    unicode_literals,
)

import copy
import itertools
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Optional,
    Tuple,
    TypeVar,
    ValuesView,
    cast,
)

import six

from conformity import fields
from conformity.error import ValidationError
from conformity.validator import validate


__all__ = (
    'Settings',
    'SettingsData',
    'SettingsItemsView',
    'SettingsKeysView',
    'SettingsSchema',
    'SettingsValuesView',
)


try:
    # TODO Always use ABCMeta when Python 3.7-only
    from typing import GenericMeta as BaseMeta  # type: ignore
except ImportError:
    from abc import ABCMeta as BaseMeta  # type: ignore


if six.PY2:
    # TODO Always use KeysView, ValuesView, and ItemsView when Python 3-only
    SettingsKeysView = List[six.text_type]
    SettingsValuesView = List[Any]
    SettingsItemsView = List[Tuple[six.text_type, Any]]
else:
    SettingsKeysView = KeysView[six.text_type]  # type: ignore
    SettingsValuesView = ValuesView[Any]  # type: ignore
    SettingsItemsView = ItemsView[six.text_type, Any]


SettingsSchema = Mapping[six.text_type, fields.Base]
SettingsData = Mapping[six.text_type, Any]

# noinspection PyShadowingBuiltins
_VT = TypeVar('_VT', bound=Any)


class _SettingsMetaclass(BaseMeta):
    """
    Metaclass that gathers fields defined on settings objects into a single variable to access them, and does so at
    the time the class is defined instead of when it is constructed, which makes this perform considerably better.
    """

    ###################################################################################################################
    #
    # Development Notes:
    #
    # _SettingsMetaclass has to extend BaseMeta to prevent this error:
    #
    #    TypeError: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the
    #    metaclasses of all its bases
    #
    # Mapping introduces six classes into the hierarchy: Mapping, Collection, Sized, Iterable, Generic, and Container.
    # In Python 3.7+, all of these have a metaclass of ABCMeta, so we can use that. In Python 2.7-3.6, most have a
    # metaclass of ABCMeta, but Generic has a metaclass of GenericMeta (which does not exist in Python 3.7+), which
    # extends ABCMeta. So we extend from GenericMeta in Python 2.7-3.6 and ABCMeta in Python 3.7+, which gets us a
    # metaclass that is a subclass of the metaclasses of all of the bases of Settings. Observe (abbreviated output
    # from ipython2/ipython3):
    #
    # class Meta(BaseMeta):
    #     def __new__(mcs, name, bases, body):
    #         print('{}: {}'.format(name, bases))
    #         return super(Meta, mcs).__new__(mcs, name, bases, body)
    #
    # @six.add_metaclass(Meta)
    # class Base(Mapping[six.text_type, Any]):
    #     pass
    #
    # class Foo(Base):
    #     pass
    # > Foo: (<class '__main__.Base'>,)
    #
    # class Bar(Base):
    #     pass
    # > Bar: (<class '__main__.Base'>,)
    #
    # class Baz(Base):
    #     pass
    # > Baz: (<class '__main__.Base'>,)
    #
    # class Qux(Foo, Bar):
    #     pass
    # > Qux: (<class '__main__.Foo'>, <class '__main__.Bar'>)
    #
    # class Qux(Foo, Bar, Baz):
    #     pass
    # > Qux: (<class '__main__.Foo'>, <class '__main__.Bar'>, <class '__main__.Baz'>)
    #
    ###################################################################################################################

    def __new__(mcs, name, bases, body):
        cls = super(_SettingsMetaclass, mcs).__new__(mcs, name, bases, body)

        # Merge the schema and defaults objects with their parents
        if cls.__name__ != 'Settings' or cls.__module__ != _SettingsMetaclass.__module__:
            if not issubclass(cls, Settings):
                raise TypeError('The internal _SettingsMetaclass is only valid on Settings')

            applicable_bases = [b for b in bases if issubclass(b, Settings)]

            # We chain all the schemas and defaults from the applicable bases, and then finally end with schema and
            # defaults from the being-defined class if and only if they are not directly inherited from a base. We
            # reverse the bases because we want a left-er base's schema and defaults to take precedence over its
            # right-er bases' schemas and defaults, in the same way left-er bases' method definitions in Python take
            # precedence over their right-er bases' method definitions.
            schema_not_inherited = not any(cls.schema is b.schema for b in applicable_bases)
            defaults_not_inherited = not any(cls.defaults is b.defaults for b in applicable_bases)
            chain_of_schemas = itertools.chain(
                itertools.chain(*(b.schema.items() for b in reversed(applicable_bases))),
                cast(Iterable[Tuple[six.text_type, fields.Base]], cls.schema.items() if schema_not_inherited else ()),
            )
            chain_of_defaults = itertools.chain(
                itertools.chain(*(b.defaults.items() for b in reversed(applicable_bases))),
                cast(Iterable[Tuple[six.text_type, Any]], cls.defaults.items() if defaults_not_inherited else ()),
            )

            # Now we define the schema and defaults for this class to be the merged schemas and defaults from above.
            cls.schema = dict(chain_of_schemas)
            cls.defaults = dict(chain_of_defaults)

        return cls


@six.add_metaclass(_SettingsMetaclass)
class Settings(Mapping[six.text_type, Any]):
    """
    Represents settings schemas and defaults that can be inherited and merged across the inheritance hierarchy.

    The base classes are designed to be inherited from and have their schema extended, any number of levels deep.
    Multiple inheritance is also supported, with the rightmost `Settings`-extending base class's schema and defaults
    taking precedence over all following `Settings`-extending base classes to the right, and so on. Schema and defaults
    from all base classes will be merged, with left-er base classes overriding conflicting right-er base classes'
    schema or defaults components, and then finally the concrete class's schema and settings (if any) will be merged
    in, overriding conflicting base classes' schema or defaults components. This matches the behavior of Python method
    definition inheritance.

    Examples:

    .. code-block:: python

        class BaseSettings(Settings):
            schema = {
                'foo': fields.Integer(),
                'bar': fields.Dictionary({'baz': fields.Integer(), 'qux': fields.Boolean}),
            }  # type: SettingsSchema

            defaults = {
                'foo': 1,
                'bar': {'baz': 2},
            }  # type: SettingsData

        class MoreBaseSettings(BaseSettings):
            # `schema` will have 'foo' and 'ipsum' from this class, 'bar' from `BaseSettings`
            schema = {
                'foo': fields.Any(fields.Integer(), fields.Float(), fields.Decimal()),
                'ipsum': fields.UnicodeString(),
            }  # type: SettingsSchema

            # `defaults` will have 'ipsum' from this class, 'foo' and 'bar' from `BaseSettings`
            defaults = {
                'ipsum': 'Default more',
            }

        class OtherBaseSettings(Settings):
            schema = {
                'lorem': fields.UnicodeString(),
                'ipsum': fields.ByteString(),
            }  # type: SettingsSchema

            defaults = {
                'lorem': 'Default lorem',
            }  # type: SettingsData

        class FinalSettings1(BaseSettings, OtherBaseSettings):
            # `schema` will have 'foo', 'bar', 'lorem', and 'ipsum'
            # `defaults` will have 'foo', 'bar', and 'lorem'
            pass

        class FinalSettings2(OtherBaseSettings, MoreBaseSettings):
            # `schema` will have 'lorem', 'ipsum' from `OtherBaseSettings`, 'foo' from `MoreBaseSettings`, 'bar'
            # `defaults` will have 'lorem', 'ipsum', 'foo', 'bar'
            pass

        class FinalSettings3(MoreBaseSettings, OtherBaseSettings):
            # `schema` will have 'foo', 'ipsum' from `MoreBaseSettings`, 'lorem' from `OtherBaseSettings`, 'bar'
            # `defaults` will have 'lorem', 'ipsum', 'foo', 'bar'
            pass

    To use `Settings`, instantiate the target/concrete `Settings` subclass with the raw settings value (a `Mapping`,
    usually a dictionary), which will validate that data according to the schema, and then access the data using
    `Mapping` syntax and methods, such as `settings['foo']`, `settings.get('foo')`, `'foo' in settings`, etc. The class
    will merge any passed values into its defaults, with passed values taking precedence over defaults when conflicts
    arise, before performing validation.
    """

    schema = {}  # type: SettingsSchema
    defaults = {}  # type: SettingsData

    class ImproperlyConfigured(Exception):
        """
        Raised when validation fails for the configuration data (contents) passed into the constructor or `set(data)`.
        """

    def __init__(self, data):  # type: (SettingsData) -> None
        """
        Instantiate a new Settings object and validate its contents.

        :param data: A mapping of unicode string keys to any values, which, together with the defined defaults in this
                     class, should match the defined schema for this class, as merged with its parent classes.

        :raises: :class:`conformity.settings.Settings.ImproperlyConfigured`
        """
        self._data = {}  # type: SettingsData
        self.set(data)

    def set(self, data):  # type: (SettingsData) -> None
        """
        Initialize and validate the configuration data (contents) for this settings object.

        :param data: A mapping of unicode string keys to any values, which, together with the defined defaults in this
                     class, should match the defined schema for this class, as merged with its parent classes.

        :raises: :class:`conformity.settings.Settings.ImproperlyConfigured`
        """
        # Merged the class defaults with the supplied data to get the effective settings data
        settings = self._merge_mappings(copy.deepcopy(data), copy.deepcopy(self.defaults))

        # Ensure that all keys required by the schema are present in the settings data
        unpopulated_keys = set(self.schema.keys()) - set(settings.keys())
        if unpopulated_keys:
            raise self.ImproperlyConfigured(
                'No value provided for required setting(s): {}'.format(', '.join(unpopulated_keys))
            )

        # Ensure that all keys in the settings data are present in the schema
        unconsumed_keys = set(settings.keys()) - set(self.schema.keys())
        if unconsumed_keys:
            raise self.ImproperlyConfigured('Unknown setting(s): {}'.format(', '.join(unconsumed_keys)))

        # Ensure that all values in the settings data pass standard Conformity field validation
        for key, value in settings.items():
            try:
                validate(self.schema[key], value, "setting '{}'".format(key))
            except ValidationError as e:
                raise self.ImproperlyConfigured(*e.args)

        # Once all checks have passed, atomically set the internal settings data
        self._data = settings

    @classmethod
    def _merge_mappings(cls, data, defaults):  # type: (SettingsData, SettingsData) -> SettingsData
        new_data = {}  # type: Dict[six.text_type, Any]

        for key in set(itertools.chain(data.keys(), defaults.keys())):
            if key in data and key in defaults:
                if isinstance(data[key], Mapping) and isinstance(defaults[key], Mapping):
                    new_data[key] = cls._merge_mappings(data[key], defaults[key])
                else:
                    new_data[key] = data[key]
            elif key in data:
                new_data[key] = data[key]
            else:
                new_data[key] = defaults[key]

        return new_data

    def keys(self):  # type: () -> SettingsKeysView
        """
        Returns a `KeysView` of the settings data (even in Python 2).

        :return: A view of the unicode string keys in this settings data.
        """
        return cast(SettingsKeysView, self._data.keys())

    def values(self):  # type: () -> SettingsValuesView
        """
        Returns a `ValuesView` of the settings data (even in Python 2).

        :return: A view of the values in this settings data.
        """
        return self._data.values()

    def items(self):  # type: () -> SettingsItemsView
        """
        Returns an `ItemsView` of the settings data (even in Python 2).

        :return: A view of unicode string keys and their values in this settings data.
        """
        return cast(SettingsItemsView, self._data.items())

    def get(self, key, default=None):  # type: (six.text_type, Optional[_VT]) -> Optional[_VT]
        """
        Returns the value associated with the given key, or the default if specified as an argument, or `None` if no
        default is specified.

        :param key: The key to look up
        :param default: The default to return if the key does not exist (which itself defaults to `None`)

        :return: The value associated with the given key, or the appropriate default.
        """
        return self._data.get(key, default)

    def __getitem__(self, key):  # type: (six.text_type) -> Any
        """
        Returns the value associated with the given key, or raises a `KeyError` if it does not exist.

        :param key: The key to look up

        :return: The value associated with the given key.

        :raises: `KeyError`
        """
        return self._data[key]

    def __len__(self):  # type: () -> int
        """
        Returns the number of keys in the root of this settings data.

        :return: The number of keys.
        """
        return len(self._data)

    def __iter__(self):  # type: () -> Iterator[six.text_type]
        """
        Returns an iterator over the keys of this settings data.

        :return: An iterator of unicode strings.
        """
        return iter(self._data)

    def __contains__(self, key):  # type: (Any) -> bool
        """
        Indicates whether the specific key exists in this settings data.

        :param key: The key to check

        :return: `True` if the key exists and `False` if it does not.
        """
        return key in self._data

    def __eq__(self, other):  # type: (Any) -> bool
        """
        Indicates whether the other object provided is an instance of the same Settings subclass as this Settings
        subclass and its settings data matches this settings data.

        :param other: The other object to check

        :return: `True` if the objects are equal, `False` if they are not.
        """
        return isinstance(other, self.__class__) and self._data == other._data

    def __ne__(self, other):  # type: (Any) -> bool
        """
        Indicates the reverse of __eq__.

        :param other: The other object to check

        :return: `False` if the objects are equal, `True` if they are not.
        """
        return not self.__eq__(other)
