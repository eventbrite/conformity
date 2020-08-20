import abc
from typing import (
    Any,
    Dict as DictType,
    Hashable as HashableType,
    Iterable,
    List as ListType,
    Optional as OptionalType,
    Tuple as TupleType,
    Union,
)

from conformity.constants import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)

from conformity.fields.base import (
    BaseField,
    BaseTypeField,
)
from conformity.fields.protocols import (
    Collection,
    Hashable,
    Sized,
)
from conformity.fields.meta import Anything
from conformity.fields.modifiers import Optional
from conformity.fields.utils import strip_none
from conformity.types import (
    Error,
    Validation,
    Warning,
)
from conformity.typing import Introspection

__all__ = (
    'Dictionary',
    'List',
    'Tuple',
)

# Type aliases
_DictContents = DictType[HashableType, BaseField]
_TupleContents = TupleType[Union[HashableType, BaseField], BaseField]
_Contents = Union[_DictContents, _TupleContents, 'Dictionary']


class List(Collection):
    """
    Validates that the value is a list
    """

    valid_type = list


class Dictionary(BaseTypeField):
    """
    Validates that the value is a dictionary with a specific set of keys and
    value that validate with the Conformity fields associated with those keys
    (`contents`). Keys are required unless they are listed in the
    `optional_keys` argument. No extra keys are allowed unless the
    `allow_extra_keys` argument is set to `True`.
    """

    valid_type = dict
    valid_noun = 'a dictionary'
    introspect_type = 'dictionary'

    def __init__(
        self,
        *contents: _Contents,
        optional_keys: Iterable[HashableType] = None,
        allow_extra_keys: bool = False,
        **kwargs: Any
    ) -> None:
        super.__init__(**kwargs)

        self.contents = []  # type: ListType[TupleType[BaseField, BaseField]]
        self._constant_fields = {}  # type: Dict[HashableType, Dict[str, BaseField]]
        self._variable_fields = []  # type: ListType[TupleType[BaseField, BaseField]]

        if not contents:
            # If there are still no contents, raise an error
            raise ValueError("'contents' is a required argument")

        # Build complete key/value field list
        temp_contents = []  # type: ListType[TupleType[Any, Any]]
        for fields in contents:
            if isinstance(fields, Dictionary):
                # fields is a Dictionary instance, which is already valid
                self.contents.extend(fields.contents)
                self._constant_fields.update(fields._constant_fields)
                self._variable_fields.extend(fields._variable_fields)
            elif isinstance(fields, dict):
                temp_contents.extend(fields.items())
            elif isinstance(fields, tuple) and len(fields) == 2:
                temp_contents.append(fields)
            else:
                raise TypeError(
                    'Positional arguments must be either a Dictionary instance, '
                    'a dict instance, or a 2-tuple'
                )

        # Validate optional keys
        if optional_keys is None:
            optional_keys = ()
        elif not isinstance(optional_keys, abc.Iterable):
            raise ValueError("'optional_keys' must be an iterable")
        optional_keys = frozenset(optional_keys)

        # Validate and process each key/value field pair
        for key_field, value_field in temp_contents:
            # Validate fields
            if not isinstance(key_field, BaseField):
                if isinstance(key_field, Hashable):
                    # Convert immutable, hashable types to Constant fields
                    if key_field in optional_keys:
                        key_field = Optional(key_field)
                    else:
                        key_field = Constant(key_field)
                else:
                    raise TypeError(
                        'Key field must be a Conformity field or hashable'
                    )
            if not isinstance(value_field, BaseField):
                raise TypeError('Value fields must be Conformity fields')

            # Sort fields
            if isinstance(key_field, Constant):
                self._constant_fields[key_field.value] = value_field
            else:
                self._variable_fields.append((key_field, value_field))

        self.contents = temp_contents

        # Validate allow_extra_keys
        # TODO: add __class__.allow_extra_keys handling
        if not isinstance(allow_extra_keys, bool):
            raise TypeError("'allow_extra_keys' must be a boolean")
        if allow_extra_keys:
            # Add a variable field that accepts anything
            self._variable_fields.append((Optional(Hashable()), Anything()))

    def validate(self, value: Any) -> Validation:
        v = super().validate(d_value)
        if v.errors:
            # Not a dict
            return v

        # Validate items
        # NOTE: INCOMPLETE
        # TODO: finish this. Particularly, figure out what to do if a dictionary
        #       item matches multiple required content field pairs.
        #
        # This is effectively Any(Chain(key_field, value_field), ...) for each
        # key/value pair. Should it behave identically?
        for key_field, value_field in self.contents:
            if isinstance(key_field, Constant):
                # See if a constant value is in the dictionary
                di_key = None
                di_value = None
                for c_value in key_field.values:
                    if c_value in value:
                        # Found a valid key
                        di_key = c_value
                        di_value = value[di_key]
                        break

                if di_key is not None:
                    v.extend(key_field.validate(di_key), pointer=di_key)
                    v.extend(value_field.validate(di_value), pointer=di_key)
                else:
                    # Key not found
                    if not getattr(key_field, 'optional', False):
                        # TODO: handle missing required key
                        pass
            else:
                # Variable field
                # TODO: Record "unknown" key error if key matches no key field
                #       If only key valid, merge all value validations
                #       If key/value pair valid, break and merge key and value
                #           validations for the pair
                key_found = False
                for di_key, di_value in value.items():
                    key_v = key_field.validate(di_key)
                    if not key_v.errors:
                        key_found = True
                        # v.extend(key_v, pointer=di_key)
                        value_v = value_field.validate(di_value)
                        if not value_v.errors:
                            # Found a valid pair
                            break

        return v

    def extend(
        self,
        *contents: _Contents,
        optional_keys: Iterable[HashableType] = None,
        allow_extra_keys: bool = None,
        description: str = None,
    ) -> 'Dictionary':
        """
        Creates a new Dictionary instance that "extends" from this one.

        NOTE: This method has been deprecated and will be removed in a future
              release. Use Dictionary(<original instance>, <extended fields>)
              syntax instead.
        """
        return Dictionary(
            self,
            *contents,
            optional_keys=optional_keys,
            allow_extra_keys=(
                self.allow_extra_keys
                if allow_extra_keys is None
                else allow_extra_keys
            ),
            description=description or self.description
        )

    def introspect(self) -> Introspection:
        return strip_none({
            'contents': [
                {
                    'key': key_field.introspect(),
                    'value': value_field.introspect(),
                }
                for key_field, value_field in self.contents.items()
            ],
        }).update(super().introspect())


class Tuple(BaseTypeField):
    """
    Validates that the value is a tuple with the same number of arguments as the
    number of positional arguments passed to this field, and that each argument
    passes validation with the corresponding Conformity field provided to the
    positional arguments.
    """

    valid_type = tuple

    def __init__(self, *contents: BaseField, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.contents = contents

        # Validate contents fields
        for i, c in enumerate(self.contents):
            if not isinstance(c, BaseField):
                raise TypeError((
                    'Argument {} must be a Conformity '
                    'field instance, is actually: {!r}'
                ).format(i, c))

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        # Validate that value length matches expected length
        len_value = len(value)
        len_contents = len(self.contents)
        if len_value != len_contents:
            v.errors.append(
                Error((
                    'Number of elements {} does '
                    'not match expected {}'
                ).format(len_value, len_contents))
            )

        # Validate each element against each field
        for i, (c_elem, v_elem) in enumerate(zip(self.contents, value)):
            v.extend(
                c_elem.validate(v_elem),
                pointer=i,
            )

        return v

    def introspect(self) -> Introspection:
        return strip_none({
            'contents': [field.introspect() for field in self.contents],
        }).update(super().introspect())
