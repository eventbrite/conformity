from __future__ import (
    absolute_import,
    unicode_literals,
)

import abc
from collections import OrderedDict
import sys
from typing import (
    AbstractSet,
    Any as AnyType,
    Callable,
    Container,
    Dict,
    FrozenSet,
    Generic,
    Hashable as HashableType,
    List as ListType,
    Mapping,
    Optional,
    Sequence as SequenceType,
    Sized,
    Tuple as TupleType,
    Type,
    TypeVar,
    Union,
    cast,
)

import attr
import six

from conformity.constants import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)
from conformity.fields.basic import (
    Anything,
    Base,
    Hashable,
    Introspection,
)
from conformity.fields.utils import (
    strip_none,
    update_pointer,
)
from conformity.types import (
    Error,
    Warning,
)
from conformity.utils import (
    attr_is_instance,
    attr_is_int,
    attr_is_iterable,
    attr_is_optional,
    attr_is_string,
)


VT = TypeVar('VT', bound=Container)


if sys.version_info < (3, 7):
    # We can't just decorate this with @six.add_metaclass. In Python < 3.7, that results in this error:
    #    TypeError: Cannot inherit from plain Generic
    # But we can't leave that off, because in Python 3.7+, the abstract method is not enforced without this (it is
    # enforced in < 3.7 since GenericMeta extends ABCMeta).
    # So we do it this way:
    _ACVT = TypeVar('_ACVT')

    def _acv_decorator(_metaclass):  # type: (Type) -> Callable[[Type[_ACVT]], Type[_ACVT]]
        def wrapper(cls):  # type: (Type[_ACVT]) -> Type[_ACVT]
            return cls
        return wrapper
else:
    _acv_decorator = six.add_metaclass


@_acv_decorator(abc.ABCMeta)
class AdditionalCollectionValidator(Generic[VT]):
    """
    Conformity fields validating collections can have an additional custom validator that can perform extra checks
    across the entire collection, such as ensuring that values that need to refer to other values in the same
    collection properly match. This is especially helpful to be able to avoid duplicating the existing collection
    validation in Conformity's structure fields.
    """

    @abc.abstractmethod
    def errors(self, value):  # type: (VT) -> ListType[Error]
        """
        Called after the collection has otherwise passed validation, and not called if the collection has not passed
        its normal validation.

        :param value: The value to be validated.

        :return: A list of errors encountered with this value.
        """


@attr.s
class _BaseSequenceOrSet(Base):
    """
    Conformity field that ensures that the value is a list of items that all pass validation with the Conformity field
    passed to the `contents` argument and optionally establishes boundaries for that list with the `max_length` and
    `min_length` arguments.
    """

    contents = attr.ib()
    max_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    min_length = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[AnyType]]

    valid_types = None  # type: Union[Type[Sized], TupleType[Type[Sized], ...]]
    type_noun = None  # deprecated, will be removed in Conformity 2.0
    introspect_type = None  # type: six.text_type
    type_error = None  # type: six.text_type

    def __attrs_post_init__(self):  # type: () -> None
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot be greater than max_length in UnicodeString')

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
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
                update_pointer(error, lazy_pointer.get())
                for error in (self.contents.errors(element) or [])
            )

        if not result and self.additional_validator:
            return self.additional_validator.errors(value)

        return result

    def warnings(self, value):
        warnings = super(_BaseSequenceOrSet, self).warnings(value)
        for lazy_pointer, element in self._enumerate(value):
            warnings.extend(
                update_pointer(warning, lazy_pointer.get())
                for warning in self.contents.warnings(element)
            )
        return warnings

    @classmethod
    def _enumerate(cls, values):
        # We use a lazy pointer here so that we don't evaluate the pointer for every item that doesn't generate an
        # error. We only evaluate the pointer for each item that does generate an error. This is critical in sets,
        # where the pointer is the value converted to a string instead of an index.
        return ((cls.LazyPointer(i, value), value) for i, value in enumerate(values))

    def introspect(self):  # type: () -> Introspection
        introspection = {
            'type': self.introspect_type,
            'contents': self.contents.introspect(),
            'max_length': self.max_length,
            'min_length': self.min_length,
            'description': self.description,
            'additional_validation': (
                self.additional_validator.__class__.__name__ if self.additional_validator else None
            ),
        }

        return strip_none(introspection)

    class LazyPointer(object):
        def __init__(self, index, _):
            self.get = lambda: index


@attr.s
class List(_BaseSequenceOrSet):
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[list]]

    valid_types = list
    introspect_type = 'list'
    type_error = 'Not a list'


@attr.s
class Sequence(_BaseSequenceOrSet):
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[SequenceType]]

    valid_types = SequenceType
    introspect_type = 'sequence'
    type_error = 'Not a sequence'


@attr.s
class Set(_BaseSequenceOrSet):
    """
    Conformity field that ensures that the value is an abstract set of items that all pass validation with the
    Conformity field passed to the `contents` argument and optionally establishes boundaries for that list with the
    `max_length` and `min_length` arguments.
    """
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[AbstractSet]]

    valid_types = AbstractSet
    introspect_type = 'set'
    type_error = 'Not a set or frozenset'

    class LazyPointer(object):
        def __init__(self, _, value):
            self.get = lambda: '[{}]'.format(str(value))


@attr.s
class Dictionary(Base):
    """
    Conformity field that ensures that the value is a dictionary with a specific set of keys and value that validate
    with the Conformity fields associated with those keys (`contents`). Keys are required unless they are listed in
    the `optional_keys` argument. No extra keys are allowed unless the `allow_extra_keys` argument is set to `True`.

    If the `contents` argument is an instance of `OrderedDict`, the field introspection will include a `display_order`
    list of keys matching the order they exist in the `OrderedDict`, and errors will be reported in the order the keys
    exist in the `OrderedDict`. Order will be maintained for any calls to `extend` as long as those calls also use
    `OrderedDict`. Ordering behavior is undefined otherwise. This field does NOT enforce that the value it validates
    presents keys in the same order. `OrderedDict` is used strictly for documentation and error-object-ordering
    purposes only.
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
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[Mapping[HashableType, AnyType]]]

    def __attrs_post_init__(self):  # type: () -> None
        if self.contents is None and getattr(self.__class__, 'contents', None) is not None:
            # If no contents were provided but a subclass has hard-coded contents, use those
            self.contents = self.__class__.contents
        if self.contents is None:
            # If there are still no contents, raise an error
            raise ValueError("'contents' is a required argument")
        if not isinstance(self.contents, dict):
            raise TypeError("'contents' must be a dict")

        if (
            self.optional_keys is self._optional_keys_default and
            getattr(self.__class__, 'optional_keys', None) is not None
        ):
            # If the optional_keys argument was defaulted (not specified) but a subclass has it hard-coded, use that
            self.optional_keys = self.__class__.optional_keys
        if not isinstance(self.optional_keys, frozenset):
            self.optional_keys = frozenset(self.optional_keys)

        if self.allow_extra_keys is None and getattr(self.__class__, 'allow_extra_keys', None) is not None:
            # If the allow_extra_keys argument was not specified but a subclass has it hard-coded, use that value
            self.allow_extra_keys = self.__class__.allow_extra_keys
        if self.allow_extra_keys is None:
            # If no value is found, default to False
            self.allow_extra_keys = False
        if not isinstance(self.allow_extra_keys, bool):
            raise TypeError("'allow_extra_keys' must be a boolean")

        if self.description is None and getattr(self.__class__, 'description', None):
            # If the description was not specified but a subclass has it hard-coded, use that value
            self.description = self.__class__.description
        if self.description is not None and not isinstance(self.description, six.text_type):
            raise TypeError("'description' must be a unicode string")

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
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
                    update_pointer(error, key)
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

        if not result and self.additional_validator:
            return self.additional_validator.errors(value)

        return result

    def warnings(self, value):
        # type: (AnyType) -> ListType[Warning]
        if not isinstance(value, dict):
            return []

        result = []  # type: ListType[Warning]
        for key, field in self.contents.items():
            if key in value:
                result.extend(
                    update_pointer(warning, key)
                    for warning in field.warnings(value[key])
                )

        return result

    def extend(
        self,
        contents=None,  # type: Optional[Mapping[HashableType, Base]]
        optional_keys=None,  # type: Optional[Union[TupleType[HashableType, ...], FrozenSet[HashableType]]]
        allow_extra_keys=None,  # type: Optional[bool]
        description=None,  # type: Optional[six.text_type]
        replace_optional_keys=False,  # type: bool
        additional_validator=None,  # type: Optional[AdditionalCollectionValidator[Mapping[HashableType, AnyType]]]
    ):
        # type: (...) -> Dictionary
        """
        This method allows you to create a new `Dictionary` that extends the current `Dictionary` with additional
        contents and/or optional keys, and/or replaces the `allow_extra_keys` and/or `description` attributes.

        :param contents: More contents, if any, to extend the current contents
        :param optional_keys: More optional keys, if any, to extend the current optional keys
        :param allow_extra_keys: If non-`None`, this overrides the current `allow_extra_keys` attribute
        :param description: If non-`None`, this overrides the current `description` attribute
        :param replace_optional_keys: If `True`, then the `optional_keys` argument will completely replace, instead of
                                      extend, the current optional keys
        :param additional_validator: If non-`None`, this overrides the current `additional_validator` attribute

        :return: A new `Dictionary` extended from the current `Dictionary` based on the supplied arguments
        """
        optional_keys = frozenset(optional_keys or ())
        return Dictionary(
            contents=cast(Type[Union[Dict, OrderedDict]], type(self.contents))(
                (k, v) for d in (self.contents, contents) for k, v in six.iteritems(d)
            ) if contents else self.contents,
            optional_keys=optional_keys if replace_optional_keys else frozenset(self.optional_keys) | optional_keys,
            allow_extra_keys=self.allow_extra_keys if allow_extra_keys is None else allow_extra_keys,
            description=self.description if description is None else description,
            additional_validator=self.additional_validator if additional_validator is None else additional_validator,
        )

    def introspect(self):  # type: () -> Introspection
        display_order = None  # type: Optional[ListType[AnyType]]
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
            'additional_validation': (
                self.additional_validator.__class__.__name__ if self.additional_validator else None
            ),
        })


@attr.s
class SchemalessDictionary(Base):
    """
    Conformity field that ensures that the value is a dictionary of any keys and values, but optionally enforcing that
    the keys pass the Conformity validation specified with the `key_type` argument and/or that the values pass the
    Conformity validation specified with the `value_type` argument. Size of the dictionary can also be constrained with
    the optional `max_length` and `min_length` arguments.
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
    additional_validator = attr.ib(
        default=None,
        validator=attr_is_optional(attr_is_instance(AdditionalCollectionValidator)),
    )  # type: Optional[AdditionalCollectionValidator[Mapping[HashableType, AnyType]]]

    def __attrs_post_init__(self):  # type: () -> None
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot be greater than max_length in UnicodeString')

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, dict):
            return [Error('Not a dict')]

        result = []

        if self.max_length is not None and len(value) > self.max_length:
            result.append(Error('Dict contains more than {} value(s)'.format(self.max_length)))
        elif self.min_length is not None and len(value) < self.min_length:
            result.append(Error('Dict contains fewer than {} value(s)'.format(self.min_length)))

        for key, field in value.items():
            result.extend(
                update_pointer(error, key)
                for error in (self.key_type.errors(key) or [])
            )
            result.extend(
                update_pointer(error, key)
                for error in (self.value_type.errors(field) or [])
            )

        if not result and self.additional_validator:
            return self.additional_validator.errors(value)

        return result

    def warnings(self, value):
        # type: (AnyType) -> ListType[Warning]
        if not isinstance(value, dict):
            return []

        result = []  # type: ListType[Warning]
        for d_key, d_value in value.items():
            result.extend(
                update_pointer(warning, d_key)
                for warning in self.key_type.warnings(d_key)
            )
            result.extend(
                update_pointer(warning, d_key)
                for warning in self.value_type.warnings(d_value)
            )

        return result

    def introspect(self):  # type: () -> Introspection
        result = {
            'type': self.introspect_type,
            'max_length': self.max_length,
            'min_length': self.min_length,
            'description': self.description,
            'additional_validation': (
                self.additional_validator.__class__.__name__ if self.additional_validator else None
            ),
        }  # type: Introspection
        # We avoid using isinstance() here as that would also match subclass instances
        if not self.key_type.__class__ == Hashable:
            result['key_type'] = self.key_type.introspect()
        if not self.value_type.__class__ == Anything:
            result['value_type'] = self.value_type.introspect()

        return strip_none(result)


class Tuple(Base):
    """
    Conformity field that ensures that the value is a tuple with the same number of arguments as the number of
    positional arguments passed to this field, and that each argument passes validation with the corresponding
    Conformity field provided to the positional arguments.
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

        self.additional_validator = kwargs.pop(
            'additional_validator',
            None,
        )  # type: Optional[AdditionalCollectionValidator[TupleType[AnyType, ...]]]
        if self.additional_validator and not isinstance(self.additional_validator, AdditionalCollectionValidator):
            raise TypeError("'additional_validator' must be an AdditionalCollectionValidator")

        if kwargs:
            raise TypeError('Unknown keyword arguments: {}'.format(', '.join(kwargs.keys())))

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, tuple):
            return [Error('Not a tuple')]

        result = []
        if len(value) != len(self.contents):
            result.append(
                Error('Number of elements {} does not match expected {}'.format(len(value), len(self.contents)))
            )

        for i, (c_elem, v_elem) in enumerate(zip(self.contents, value)):
            result.extend(
                update_pointer(error, i)
                for error in (c_elem.errors(v_elem) or [])
            )

        if not result and self.additional_validator:
            return self.additional_validator.errors(value)

        return result

    def warnings(self, value):
        # type: (AnyType) -> ListType[Warning]
        if (
            not isinstance(value, tuple) or
            len(value) != len(self.contents)
        ):
            return []

        result = []  # type: ListType[Warning]
        for i, (field, item) in enumerate(zip(self.contents, value)):
            result.extend(
                update_pointer(warning, i)
                for warning in field.warnings(item)
            )

        return result

    def introspect(self):  # type: () -> Introspection
        return strip_none({
            'type': self.introspect_type,
            'contents': [value.introspect() for value in self.contents],
            'description': self.description,
            'additional_validation': (
                self.additional_validator.__class__.__name__ if self.additional_validator else None
            ),
        })
