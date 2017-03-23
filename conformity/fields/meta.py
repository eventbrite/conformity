from __future__ import unicode_literals
import attr

from .basic import Base
from ..error import Error
from ..utils import strip_none


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
                    Error("Invalid switch value %r" % switch_value),
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
