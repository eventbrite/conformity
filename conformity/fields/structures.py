import abc
from typing import (
    Any,
    Hashable as HashableType,
    Iterable,
    List as ListType,
    Optional as OptionalType,
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

    If the `contents` argument is an instance of `OrderedDict`, the field
    introspection will include a `display_order` list of keys matching the order
    they exist in the `OrderedDict`, and errors will be reported in the order
    the keys exist in the `OrderedDict`. Order will be maintained for any calls
    to `extend` as long as those calls also use `OrderedDict`. Ordering behavior
    is undefined otherwise. This field does NOT enforce that the value it
    validates presents keys in the same order. `OrderedDict` is used strictly
    for documentation and error-object-ordering purposes only.
    """

    valid_type = dict
    valid_noun = 'a dictionary'
    introspect_type = 'dictionary'

    # Deprecated class var method
    contents = None  # type: OptionalType[BaseField]
    optional_keys = None  # type: OptionalType[bool]
    allow_extra_keys = False  # type: bool
    # TODO: add __class__.description and __init__ processing?

    def __init__(
        self,
        *contents,
        optional_keys: Iterable[HashableType] = None,
        allow_extra_keys: bool = False,
        **kwargs: Any
    ) -> None:
        super.__init__(**kwargs)

        if (
            contents is None and
            getattr(self.__class__, 'contents', None) is not None
        ):
            # If no contents were provided but a subclass has hard-coded
            # contents, use those
            contents = self.__class__.contents
        if contents is None:
            # If there are still no contents, raise an error
            raise ValueError("'contents' is a required argument")

        # Build complete key/value field list
        item_fields = []
        for fields in contents:
            if isinstance(fields, Dictionary):
                fields = fields.contents.items()
            elif isinstance(fields, dict):
                fields = fields.items()
            elif not isinstance(fields, abc.Iterable):
                raise TypeError(
                    'Positional arguments must be either a Dictionary instance, '
                    'a dict instance, or an iterable of (key, value) tuples'
                )
            item_fields.extend(fields)

        # Validate optional keys
        # TODO: handle __class__.optional_keys
        if optional_keys is None:
            optional_keys = ()
        elif not isinstance(optional_keys, abc.Iterable):
            raise ValueError("'optional_keys' must be an iterable")
        optional_keys = frozenset(optional_keys)

        # Validate each key/value field pair
        self._constant_fields = {}
        self._variable_fields = []
        for key_field, value_field in item_fields:
            # Convert hashable builtin type instances to Literals (i.e., constants)
            if isinstance(key_field, LITERAL_TYPES):
                key_field = Literal(key_field)
            if isinstance(value_field, LITERAL_TYPES):
                value_field = Literal(value_field)

            # Validate key/value field types
            if not isinstance(key_field, Hashable):
                raise ValueError(
                    'Dictionary key field must be a Conformity Hashable field'
                )
            if not isinstance(value_field, BaseField):
                raise ValueError(
                    'Dictionary value fields must be a Conformity field'
                )

            if isinstance(key_field, Literal):
                if key_field.value in optional_keys:
                    self._variable_fields.append(Optional(key_field), value_field)
                else:
                    self._constant_fields[key_field.value] = value_field
            else:
                self._variable_fields.append((key_field, value_field))

        # Validate allow_extra_keys
        # TODO: add __class__.allow_extra_keys handling
        if not isinstance(allow_extra_keys, bool):
            raise TypeError("'allow_extra_keys' must be a boolean")
        if allow_extra_keys:
            # Add a variable field that accepts anything
            self._variable_fields.append((Hashable(), Anything()))

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if v.errors:
            return v

        # Validate items
        for d_key, d_value in value.items():
            if d_key in self._constant_fields:
                # Validate constant key field
                value_field = self._constant_fields[d_key]
                value_v = value_field.validate(d_value)
            else:
                # Validate variable key field
                # TODO: extend warnings
                key_valid = False
                key_errors = []
                value_valid = False
                value_errors = []
                for key_field, value_field in self._variable_fields:
                    key_v = key_field.validate(d_key)
                    if key_v.errors:
                        if not key_valid:
                            key_errors = []
                    else:
                        key_valid = True
                        value_v = value_field.validate(d_value)
                        if value_v.errors:
                            if not value_valid:
                                value_errors.extend(value_v.errors)
                        else:
                            value_valid = True

        # result = []
        # for key, field in self.contents.items():
        #     # Check key is present
        #     if key not in value:
        #         if key not in self.optional_keys:
        #             result.append(
        #                 Error('Missing key: {}'.format(key), code=ERROR_CODE_MISSING, pointer=str(key)),
        #             )
        #     else:
        #         # Check key type
        #         result.extend(
        #             #pdate_pointer(error, key)
        #             for error in (field.errors(value[key]) or [])
        #         )
        # # Check for extra keys
        # extra_keys = set(value.keys()) - set(self.contents.keys())
        # if extra_keys and not self.allow_extra_keys:
        #     result.append(
        #         Error(
        #             'Extra keys present: {}'.format(', '.join(str(key) for key in sorted(extra_keys))),
        #             code=ERROR_CODE_UNKNOWN,
        #         ),
        #     )

        return v

    def extend(
        self,
        *contents,
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
