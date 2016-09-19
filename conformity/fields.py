from __future__ import unicode_literals
import six


class Base(object):
    """
    Base field type.
    """

    def errors(self, value):
        """
        Returns a list of errors with the value. An empty/None return means
        that it's valid.
        """
        return ["Validation not implemented on base type"]


class Constant(object):
    """
    Value that must match exactly.
    """

    def __init__(self, value):
        self.value = value

    def errors(self, value):
        """
        Returns a list of errors with the value. An empty/None return means
        that it's valid.
        """
        if value != self.value:
            return ["Value is not %r" % self.value]


class Anything(object):
    """
    Accepts any value.
    """

    def errors(self, value):
        pass


class Boolean(Base):
    """
    Accepts boolean values only
    """

    def errors(self, value):
        if not isinstance(value, bool):
            return ["Not a boolean"]


class Integer(Base):
    """
    Accepts valid integers, with optional range limits.
    """

    def __init__(self, gt=None, lt=None, gte=None, lte=None):
        self.gt = gt
        self.lt = lt
        self.gte = gte
        self.lte = lte

    def errors(self, value):
        if not isinstance(value, int):
            return ["Not an integer"]
        elif self.gt is not None and value <= self.gt:
            return ["Value not > %s" % self.gt]
        elif self.lt is not None and value >= self.ly:
            return ["Value not < %s" % self.lt]
        elif self.gte is not None and value < self.gte:
            return ["Value not >= %s" % self.gte]
        elif self.lte is not None and value > self.lye:
            return ["Value not <= %s" % self.lte]


class UnicodeString(Base):
    """
    Accepts only unicode strings
    """

    instance_type = six.text_type

    def __init__(self, max_length=None):
        self.max_length = max_length

    def errors(self, value):
        if not isinstance(value, six.text_type):
            return ["Not a unicode string"]
        elif self.max_length is not None and len(value) > self.max_length:
            return ["String longer than %s" % self.max_length]


class ByteString(UnicodeString):
    """
    Accepts only byte strings
    """

    instance_type = six.binary_type


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
            return ["Not a list"]
        result = []
        if self.max_length is not None and len(value) > self.max_length:
            result.append("List longer than %s" % self.max_length)
        elif self.min_length is not None and len(value) < self.min_length:
            result.append("List is shorter than %s" % self.min_length)
        for i, element in enumerate(value):
            result.extend(
                "Element %i: %s" % (i, error)
                for error in (self.contents.errors(element) or [])
            )
        return result


class Dictionary(Base):
    """
    A dictionary with types per key (and requirements per key)
    """

    def __init__(self, contents, optional_keys=None, ignore_extra_keys=False):
        self.contents = contents
        self.optional_keys = optional_keys or []
        self.ignore_extra_keys = ignore_extra_keys

    def errors(self, value):
        if not isinstance(value, dict):
            return ["Not a dict"]
        result = []
        seen_keys = set()
        for key, field in self.contents.items():
            # Check key is present
            if key not in value:
                if key not in self.optional_keys:
                    result.append("Key %s missing" % key)
            else:
                seen_keys.add(key)
                # Check key type
                result.extend(
                    "Key %s: %s" % (key, error)
                    for error in (field.errors(value[key]) or [])
                )
        # Check for extra keys
        extra_keys = set(value.keys()) - set(self.contents.keys())
        if extra_keys and not self.ignore_extra_keys:
            result.append("Extra keys %s present" % (", ".join(six.text_type(key) for key in extra_keys)))
        return result


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
