from __future__ import unicode_literals
import six

from .basic import Base, Hashable, Anything
from ..error import Error


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


class List(Base):
    """
    A list of things of a single type.
    """

    def __init__(self, contents, max_length=None, min_length=None):
        self.contents = contents
        self.max_length = max_length
        self.min_length = min_length

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


class Dictionary(Base):
    """
    A dictionary with types per key (and requirements per key).
    """

    def __init__(self, contents, optional_keys=None, allow_extra_keys=False):
        self.contents = contents
        self.optional_keys = optional_keys or []
        self.allow_extra_keys = allow_extra_keys

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


class SchemalessDictionary(Base):
    """
    Generic dictionary with requirements about key and value types, but not specific keys
    """
    def __init__(self, key_type=None, value_type=None):
        self.key_type = key_type or Hashable()
        self.value_type = value_type or Anything()

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


class Tuple(Base):
    """
    A tuple with types per element.
    """

    def __init__(self, *contents):
        self.contents = contents

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
