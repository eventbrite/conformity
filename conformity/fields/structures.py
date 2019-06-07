from __future__ import (
    absolute_import,
    unicode_literals,
)

from collections import OrderedDict
from typing import (  # noqa: F401 TODO Python 3
    Any as AnyType,
    FrozenSet,
    Hashable as HashableType,
    Mapping,
    Optional,
    Sized,
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
    update_error_pointer,
)
from conformity.fields.basic import (
    Anything,
    Base,
    Hashable,
)
from conformity.utils import (
    attr_is_instance,
    attr_is_int,
    attr_is_iterable,
    attr_is_optional,
    attr_is_string,
    strip_none,
)


@attr.s
class List(Base):
    """
    A list of things of a single type.
    """

    contents = attr.ib()
    max_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    min_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    valid_types = list  # type: Union[Type[Sized], TupleType[Type[Sized], ...]]
    type_noun = 'list'  # type: six.text_type
    introspect_type = type_noun  # type: six.text_type
    type_error = 'Not a list'  # type: six.text_type

    def __attrs_post_init__(self):
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot be greater than max_length in UnicodeString')

    def errors(self, value):
        if not isinstance(value, self.valid_types):
            return [Error(self.type_error)]

        result = []
        if self.max_length is not None and len(value) > self.max_length:
            result.append(
                Error('List is longer than {}'.format(self.max_length)),
            )
        elif self.min_length is not None and len(value) < self.min_length:
            result.append(
                Error('List is shorter than {}'.format(self.min_length)),
            )
        for lazy_pointer, element in self._enumerate(value):
            result.extend(
                update_error_pointer(error, lazy_pointer.get())
                for error in (self.contents.errors(element) or [])
            )
        return result

    @classmethod
    def _enumerate(cls, values):
        # We use a lazy pointer here so that we don't evaluate the pointer for every item that doesn't generate an
        # error. We only evaluate the pointer for each item that does generate an error. This is critical in sets,
        # where the pointer is the value converted to a string instead of an index.
        return ((cls.LazyPointer(i, value), value) for i, value in enumerate(values))

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'contents': self.contents.introspect(),
            'max_length': self.max_length,
            'min_length': self.min_length,
            'description': self.description,
        })

    class LazyPointer(object):
        def __init__(self, index, _):
            self.get = lambda: index


@attr.s
class Set(List):
    valid_types = (set, frozenset)
    type_noun = 'set'
    introspect_type = type_noun
    type_error = 'Not a set or frozenset'

    class LazyPointer(object):
        def __init__(self, _, value):
            self.get = lambda: '[{}]'.format(str(value))


@attr.s
class Dictionary(Base):
    """
    A dictionary with types per key (and requirements per key). If the `contents` argument is an instance of
    `OrderedDict`, the field introspection will include a `display_order` list of keys matching the order they exist
    in the `OrderedDict`, and errors will be reported in the order the keys exist in the `OrderedDict`. Order will be
    maintained for any calls to `extend` as long as those calls also use `OrderedDict`. Ordering behavior is undefined
    otherwise. This field does NOT enforce that the value it validates presents keys in the same order. `OrderedDict`
    is used strictly for documentation and error-object-ordering purposes only.
    """

    introspect_type = 'dictionary'

    # Makes MyPy allow optional_keys to have this type
    _optional_keys_default = frozenset()  # type: Union[TupleType[HashableType, ...], FrozenSet[HashableType]]

    contents = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(dict)),
    )  # type: Mapping[HashableType, Base]
    optional_keys = attr.ib(
        default=_optional_keys_default,
        validator=attr_is_iterable(attr_is_instance(object)),
    )  # type: Union[TupleType[HashableType, ...], FrozenSet[HashableType]]
    allow_extra_keys = attr.ib(default=None)  # type: bool
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def __attrs_post_init__(self):
        if self.contents is None and getattr(self.__class__, 'contents', None):
            # If no contents were provided but a subclass has hard-coded contents, use those
            self.contents = self.__class__.contents
        if self.contents is None:
            # If there are still no contents, raise an error
            raise ValueError("'contents' is a required argument")

        if self.optional_keys is self._optional_keys_default and getattr(self.__class__, 'optional_keys', None):
            # If the optional_keys argument was defaulted (not specified) but a subclass has it hard-coded, use that
            self.optional_keys = self.__class__.optional_keys
        if not isinstance(self.optional_keys, frozenset):
            self.optional_keys = frozenset(self.optional_keys)

        if self.allow_extra_keys is None and getattr(self.__class__, 'allow_extra_keys', None):
            # If the allow_extra_keys argument was not specified but a subclass has it hard-coded, use that value
            self.allow_extra_keys = self.__class__.allow_extra_keys
        if self.allow_extra_keys is None:
            # If no value is found, default to False
            self.allow_extra_keys = False

        if self.description is None and getattr(self.__class__, 'description', None):
            # If the description was not specified but a subclass has it hard-coded, use that value
            self.description = self.__class__.description

    def errors(self, value):
        if not isinstance(value, dict):
            return [Error('Not a dict')]

        result = []
        for key, field in self.contents.items():
            # Check key is present
            if key not in value:
                if key not in self.optional_keys:
                    result.append(
                        Error('Missing key: {}'.format(key), code=ERROR_CODE_MISSING, pointer=six.text_type(key)),
                    )
            else:
                # Check key type
                result.extend(
                    update_error_pointer(error, key)
                    for error in (field.errors(value[key]) or [])
                )
        # Check for extra keys
        extra_keys = set(value.keys()) - set(self.contents.keys())
        if extra_keys and not self.allow_extra_keys:
            result.append(
                Error(
                    'Extra keys present: {}'.format(', '.join(six.text_type(key) for key in sorted(extra_keys))),
                    code=ERROR_CODE_UNKNOWN,
                ),
            )
        return result

    def extend(
        self,
        contents=None,
        optional_keys=None,
        allow_extra_keys=None,
        description=None,
        replace_optional_keys=False,
    ):
        """
        This method allows you to create a new `Dictionary` that extends the current `Dictionary` with additional
        contents and/or optional keys, and/or replaces the `allow_extra_keys` and/or `description` attributes.

        :param contents: More contents, if any, to extend the current contents
        :type contents: dict
        :param optional_keys: More optional keys, if any, to extend the current optional keys
        :type optional_keys: union[set, list, tuple]
        :param allow_extra_keys: If non-`None`, this overrides the current `allow_extra_keys` attribute
        :type allow_extra_keys: bool
        :param description: If non-`None`, this overrides the current `description` attribute
        :type description: union[str, unicode]
        :param replace_optional_keys: If `True`, then the `optional_keys` argument will completely replace, instead of
                                      extend, the current optional keys
        :type replace_optional_keys: bool

        :return: A new `Dictionary` extended from the current `Dictionary` based on the supplied arguments
        :rtype: Dictionary
        """
        optional_keys = set(optional_keys or [])
        return Dictionary(
            contents=type(self.contents)(
                (k, v) for d in (self.contents, contents) for k, v in six.iteritems(d)
            ) if contents else self.contents,
            optional_keys=optional_keys if replace_optional_keys else self.optional_keys | optional_keys,
            allow_extra_keys=self.allow_extra_keys if allow_extra_keys is None else allow_extra_keys,
            description=self.description if description is None else description,
        )

    def introspect(self):
        display_order = None
        if isinstance(self.contents, OrderedDict):
            display_order = list(self.contents.keys())

        return strip_none({
            'type': self.introspect_type,
            'contents': {
                key: value.introspect()
                for key, value in self.contents.items()
            },
            'optional_keys': sorted(self.optional_keys),
            'allow_extra_keys': self.allow_extra_keys,
            'description': self.description,
            'display_order': display_order,
        })


@attr.s
class SchemalessDictionary(Base):
    """
    Generic dictionary with requirements about key and value types, but not specific keys
    """

    introspect_type = 'schemaless_dictionary'

    # Makes MyPy allow key_type and value_type have type Base
    _default_key_type = attr.Factory(Hashable)  # type: Base
    _default_value_type = attr.Factory(Anything)  # type: Base

    key_type = attr.ib(default=_default_key_type, validator=attr_is_instance(Base))  # type: Base
    value_type = attr.ib(default=_default_value_type, validator=attr_is_instance(Base))  # type: Base
    max_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    min_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def __attrs_post_init__(self):
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot be greater than max_length in UnicodeString')

    def errors(self, value):
        if not isinstance(value, dict):
            return [Error('Not a dict')]

        result = []

        if self.max_length is not None and len(value) > self.max_length:
            result.append(Error('Dict contains more than {} value(s)'.format(self.max_length)))
        elif self.min_length is not None and len(value) < self.min_length:
            result.append(Error('Dict contains fewer than {} value(s)'.format(self.min_length)))

        for key, field in value.items():
            result.extend(
                update_error_pointer(error, key)
                for error in (self.key_type.errors(key) or [])
            )
            result.extend(
                update_error_pointer(error, key)
                for error in (self.value_type.errors(field) or [])
            )

        return result

    def introspect(self):
        result = {
            'type': self.introspect_type,
            'max_length': self.max_length,
            'min_length': self.min_length,
            'description': self.description,
        }
        # We avoid using isinstance() here as that would also match subclass instances
        if not self.key_type.__class__ == Hashable:
            result['key_type'] = self.key_type.introspect()
        if not self.value_type.__class__ == Anything:
            result['value_type'] = self.value_type.introspect()
        return strip_none(result)


class Tuple(Base):
    """
    A tuple with types per element.
    """

    introspect_type = 'tuple'

    def __init__(self, *contents, **kwargs):  # type: (*Base, **AnyType) -> None
        # We can't use attrs here because we need to capture all positional arguments and support keyword arguments
        self.contents = contents
        for i, c in enumerate(self.contents):
            if not isinstance(c, Base):
                raise TypeError('Argument {} must be a Conformity field instance, is actually: {!r}'.format(i, c))

        # We can't put a keyword argument after *args in Python 2, so we need this
        self.description = kwargs.pop(str('description'), None)  # type: Optional[six.text_type]
        if self.description and not isinstance(self.description, six.text_type):
            raise TypeError("'description' must be a unicode string")
        if kwargs:
            raise TypeError('Unknown keyword arguments: {}'.format(', '.join(kwargs.keys())))

    def errors(self, value):
        if not isinstance(value, tuple):
            return [Error('Not a tuple')]

        result = []
        if len(value) != len(self.contents):
            result.append(
                Error('Number of elements {} does not match expected {}'.format(len(value), len(self.contents)))
            )

        for i, (c_elem, v_elem) in enumerate(zip(self.contents, value)):
            result.extend(
                update_error_pointer(error, i)
                for error in (c_elem.errors(v_elem) or [])
            )

        return result

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'contents': [value.introspect() for value in self.contents],
            'description': self.description,
        })
