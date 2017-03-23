from __future__ import unicode_literals
import attr
import six

from .basic import Base, Hashable, Anything
from ..error import Error
from ..utils import strip_none


def _update_error_pointer(error, pointer_or_prefix):
    """
    Helper function to update an Error's pointer attribute with a (potentially
    prefixed) dictionary key or list index.
    """
    if error.pointer:
        error.pointer = '{}.{}'.format(pointer_or_prefix, error.pointer)
    else:
        error.pointer = '{}'.format(pointer_or_prefix)
    return error


@attr.s
class List(Base):
    """
    A list of things of a single type.
    """

    contents = attr.ib()
    max_length = attr.ib(default=None)
    min_length = attr.ib(default=None)
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, list):
            return [
                Error("Not a list"),
            ]
        result = []
        if self.max_length is not None and len(value) > self.max_length:
            result.append(
                Error("List longer than %s" % self.max_length),
            )
        elif self.min_length is not None and len(value) < self.min_length:
            result.append(
                Error("List is shorter than %s" % self.min_length),
            )
        for i, element in enumerate(value):
            result.extend(
                _update_error_pointer(error, i)
                for error in (self.contents.errors(element) or [])
            )
        return result

    def introspect(self):
        return strip_none({
            "type": "list",
            "contents": self.contents.introspect(),
            "max_length": self.max_length,
            "min_length": self.min_length,
            "description": self.description,
        })


@attr.s
class Dictionary(Base):
    """
    A dictionary with types per key (and requirements per key).
    """

    contents = attr.ib()
    optional_keys = attr.ib(default=attr.Factory(list))
    allow_extra_keys = attr.ib(default=False)
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, dict):
            return [
                Error("Not a dict"),
            ]
        result = []
        for key, field in self.contents.items():
            # Check key is present
            if key not in value:
                if key not in self.optional_keys:
                    result.append(
                        Error("Key %s missing" % key, pointer=key),
                    )
            else:
                # Check key type
                result.extend(
                    _update_error_pointer(error, key)
                    for error in (field.errors(value[key]) or [])
                )
        # Check for extra keys
        extra_keys = set(value.keys()) - set(self.contents.keys())
        if extra_keys and not self.allow_extra_keys:
            result.append(
                Error("Extra keys %s present" % (", ".join(six.text_type(key) for key in extra_keys))),
            )
        return result

    def introspect(self):
        return strip_none({
            "type": "dictionary",
            "contents": {
                key: value.introspect()
                for key, value in self.contents.items()
            },
            "optional_keys": self.optional_keys,
            "allow_extra_keys": self.allow_extra_keys,
            "description": self.description,
        })


@attr.s
class SchemalessDictionary(Base):
    """
    Generic dictionary with requirements about key and value types, but not specific keys
    """

    key_type = attr.ib(default=attr.Factory(Hashable))
    value_type = attr.ib(default=attr.Factory(Anything))
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, dict):
            return [
                Error("Not a dict"),
            ]
        result = []
        for key, field in value.items():
            result.extend(
                _update_error_pointer(error, key)
                for error in (self.key_type.errors(key) or [])
            )
            result.extend(
                _update_error_pointer(error, key)
                for error in (self.value_type.errors(field) or [])
            )
        return result

    def introspect(self):
        result = {
            "type": "schemaless_dictionary",
            "description": self.description,
        }
        # We avoid using isinstance() here as that would also match subclass instances
        if not self.key_type.__class__ == Hashable:
            result["key_type"] = self.key_type.introspect()
        if not self.value_type.__class__ == Anything:
            result["value_type"] = self.value_type.introspect()
        return strip_none(result)


class Tuple(Base):
    """
    A tuple with types per element.
    """

    def __init__(self, *contents, **kwargs):
        # We can't use attrs here because we need to capture all positional
        # arguments, but also extract the description kwarg if provided.
        self.contents = contents
        self.description = kwargs.get("description", None)
        if list(kwargs.keys()) not in ([], ["description"]):
            raise ValueError("Unknown keyword arguments %s" % kwargs.keys())

    def errors(self, value):
        if not isinstance(value, tuple):
            return [
                Error("Not a tuple"),
            ]

        result = []
        if len(value) != len(self.contents):
            result.append(
                Error("Number of elements %d doesn't match expected %d" % (len(value), len(self.contents)))
            )

        for i, (c_elem, v_elem) in enumerate(zip(self.contents, value)):
            result.extend(
                _update_error_pointer(error, i)
                for error in (c_elem.errors(v_elem) or [])
            )

        return result

    def introspect(self):
        return strip_none({
            "type": "tuple",
            "contents": [value.introspect() for value in self.contents],
            "description": self.description,
        })
