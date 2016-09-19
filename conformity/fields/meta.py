from __future__ import unicode_literals

from .basic import Base


class Polymorph(Base):
    """
    A field which has one of a set of possible contents based on a field
    within it (which must be accessible via dictionary lookups)
    """

    def __init__(self, switch_field, contents_map):
        self.switch_field = switch_field
        self.contents_map = contents_map

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
                return ["Invalid switch value %r" % switch_value]
        field = self.contents_map[switch_value]
        # Run field errors
        return field.errors(value)
