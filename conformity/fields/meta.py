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

    introspect_type = "nullable"
    conformity_type = introspect_type
    field = attr.ib()

    def errors(self, value):
        if value is None:
            return []

        return self.field.errors(value)

    def introspect(self, include_conformity_type=False):
        result = {
            "type": self.introspect_type,
            "nullable": self.field.introspect(include_conformity_type),
        }
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result


@attr.s
class Polymorph(Base):
    """
    A field which has one of a set of possible contents based on a field
    within it (which must be accessible via dictionary lookups)
    """

    introspect_type = "polymorph"
    conformity_type = introspect_type
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

    def introspect(self, include_conformity_type=False):
        result = strip_none({
            "type": self.introspect_type,
            "description": self.description,
            "switch_field": self.switch_field,
            "contents_map": {
                key: value.introspect(include_conformity_type)
                for key, value in self.contents_map.items()
            },
        })
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result


@attr.s
class ObjectInstance(Base):
    """
    Accepts only instances of a given class or type
    """

    introspect_type = "object_instance"
    conformity_type = introspect_type
    valid_type = attr.ib()
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return [
                Error("Not an instance of %s" % self.valid_type.__name__),
            ]
        else:
            return []

    def introspect(self, include_conformity_type=False):
        result = strip_none({
            "type": self.introspect_type,
            "description": self.description,
            # Unfortunately, this is the one sort of thing we can't represent
            # super well. Maybe add some dotted path stuff in here.
            "valid_type": repr(self.valid_type),
        })
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result


class Any(Base):
    """
    Accepts any one of the types passed as positional arguments.
    Intended to be used for constants but could be used with others.
    """

    introspect_type = "any"
    conformity_type = introspect_type
    description = None

    def __init__(self, *args, **kwargs):
        self.options = args
        # We can't put a keyword argument after *args in Python 2, so we need this
        if "description" in kwargs:
            self.description = kwargs["description"]
            del kwargs["description"]
        if "conformity_type" in kwargs:
            self.conformity_type = kwargs["conformity_type"]
            del kwargs["conformity_type"]
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

    def introspect(self, include_conformity_type=False):
        result = strip_none({
            "type": self.introspect_type,
            "description": self.description,
            "options": [option.introspect(include_conformity_type) for option in self.options],
        })
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result


class All(Base):
    """
    The value must pass all of the types passed as positional arguments.
    Intended to be used for adding extra validation.
    """

    introspect_type = "all"
    conformity_type = introspect_type
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

    def introspect(self, include_conformity_type=False):
        result = strip_none({
            "type": self.introspect_type,
            "description": self.description,
            "requirements": [requirement.introspect(include_conformity_type) for requirement in self.requirements],
        })
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result


@attr.s
class BooleanValidator(Base):
    """
    Uses a boolean callable (probably lambda) passed in to validate the value
    based on if it returns True (valid) or False (invalid).
    """

    introspect_type = "boolean_validator"
    conformity_type = introspect_type
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

    def introspect(self, include_conformity_type=False):
        result = strip_none({
            "type": self.introspect_type,
            "description": self.description,
            "validator": self.validator_description,
        })
        if include_conformity_type:
            result["conformity_type"] = self.conformity_type
        return result
