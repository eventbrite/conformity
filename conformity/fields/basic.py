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


class Constant(Base):
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


class Anything(Base):
    """
    Accepts any value.
    """

    def errors(self, value):
        pass


class Hashable(Anything):
    """
    Accepts any hashable value
    """
    def errors(self, value):
        try:
            hash(value)
        except TypeError:
            return ["Value is not hashable"]


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

    valid_type = (int, long)
    valid_noun = "integer"

    def __init__(self, gt=None, lt=None, gte=None, lte=None):
        self.gt = gt
        self.lt = lt
        self.gte = gte
        self.lte = lte

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return ["Not a %s" % self.valid_noun]
        elif self.gt is not None and value <= self.gt:
            return ["Value not > %s" % self.gt]
        elif self.lt is not None and value >= self.lt:
            return ["Value not < %s" % self.lt]
        elif self.gte is not None and value < self.gte:
            return ["Value not >= %s" % self.gte]
        elif self.lte is not None and value > self.lte:
            return ["Value not <= %s" % self.lte]


class Float(Base):
    """
    Accepts floating point numbers as well as integers.
    """

    valid_type = (int, long, float)
    valid_noun = "float"


class UnicodeString(Base):
    """
    Accepts only unicode strings
    """

    valid_type = six.text_type
    valid_noun = "unicode string"

    def __init__(self, max_length=None):
        self.max_length = max_length

    def errors(self, value):
        if not isinstance(value, self.valid_type):
            return ["Not a %s" % self.valid_noun]
        elif self.max_length is not None and len(value) > self.max_length:
            return ["String longer than %s" % self.max_length]


class ByteString(UnicodeString):
    """
    Accepts only byte strings
    """

    valid_type = six.binary_type
    valid_noun = "byte string"
