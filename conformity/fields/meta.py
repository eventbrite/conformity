from __future__ import absolute_import, unicode_literals

import attr
import six

from conformity.error import (
    Error,
    ERROR_CODE_UNKNOWN,
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

    field = attr.ib()

    def errors(self, value):
        if value is None:
            return []

        return self.field.errors(value)

    def introspect(self):
        return {"type": "nullable", "nullable": self.field.introspect()}


@attr.s
class Polymorph(Base):
    """
    A field which has one of a set of possible contents based on a field
    within it (which must be accessible via dictionary lookups)
    """

    switch_field = attr.ib()
    contents_map = attr.ib()
    description = attr.ib(default=None)

    def errors(self, value):
        # Get switch field value
        bits = self.switch_field.split(".")
        switch_value = value
        for bit in bits:
            switch_value = switch_value[bit]
        # Get field
        if switch_value not in self.contents_map:
            if "__default__" in self.contents_map:
                switch_value = "__default__"
            else:
                return [
                    Error("Invalid switch value {}".format(switch_value), code=ERROR_CODE_UNKNOWN),
                ]
        field = self.contents_map[switch_value]
        # Run field errors
        return field.errors(value)

    def introspect(self):
        return strip_none({
            "type": "polymorph",
            "description": self.description,
            "switch_field": self.switch_field,
            "contents_map": {
                key: value.introspect()
                for key, value in self.contents_map.items()
            }
        })


@attr.s
class ObjectInstance(Base):
    """
    Accepts only instances of a given class or type
    """

    valid_type = attr.ib()
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return [
                Error("Not an instance of %s" % self.valid_type.__name__),
            ]
        else:
            return []

    def introspect(self):
        return strip_none({
            "type": "object_instance",
            "description": self.description,
            # Unfortunately, this is the one sort of thing we can't represent
            # super well. Maybe add some dotted path stuff in here.
            "valid_type": repr(self.valid_type),
        })


class Any(Base):
    """
    Accepts any one of the types passed as positional arguments.
    Intended to be used for constants but could be used with others.
    """

    description = None

    def __init__(self, *args, **kwargs):
        self.options = args
        # We can't put a keyword argument after *args in Python 2, so we need this
        if "description" in kwargs:
            self.description = kwargs["description"]
            del kwargs["description"]
        if kwargs:
            raise TypeError("Unknown keyword arguments: %s" % ", ".join(kwargs.keys()))

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
            "type": "any",
            "description": self.description,
            "options": [option.introspect() for option in self.options],
        })


class All(Base):
    """
    The value must pass all of the types passed as positional arguments.
    Intended to be used for adding extra validation.
    """

    description = None

    def __init__(self, *args, **kwargs):
        self.requirements = args
        # We can't put a keyword argument after *args in Python 2, so we need this
        if "description" in kwargs:
            self.description = kwargs["description"]
            del kwargs["description"]
        if kwargs:
            raise TypeError("Unknown keyword arguments: %s" % ", ".join(kwargs.keys()))

    def errors(self, value):
        result = []
        for requirement in self.requirements:
            result.extend(requirement.errors(value) or [])
        return result

    def introspect(self):
        return strip_none({
            "type": "all",
            "description": self.description,
            "requirements": [requirement.introspect() for requirement in self.requirements],
        })


@attr.s
class BooleanValidator(Base):
    """
    Uses a boolean callable (probably lambda) passed in to validate the value
    based on if it returns True (valid) or False (invalid).
    """

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
                Error("Validator encountered an error (invalid type?)"),
            ]
        if ok:
            return []
        else:
            return [
                Error(self.error),
            ]

    def introspect(self):
        return strip_none({
            "type": "boolean_validator",
            "description": self.description,
            "validator": self.validator_description,
        })
