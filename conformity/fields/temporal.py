from __future__ import unicode_literals
import datetime

from .basic import Base


class TemporalBase(Base):
    def __init__(self, gt=None, lt=None, gte=None, lte=None):
        self.gt = gt
        self.lt = lt
        self.gte = gte
        self.lte = lte

    def errors(self, value):
        if not type(value) == self.valid_type:
            # using stricter type checking, because date is subclass of datetime, but they're not comparable
            return ["Not a %s instance" % self.valid_noun]
        elif self.gt is not None and value <= self.gt:
            return ["Value not > %s" % self.gt]
        elif self.lt is not None and value >= self.lt:
            return ["Value not < %s" % self.lt]
        elif self.gte is not None and value < self.gte:
            return ["Value not >= %s" % self.gte]
        elif self.lte is not None and value > self.lte:
            return ["Value not <= %s" % self.lte]


class DateTime(TemporalBase):
    valid_type = datetime.datetime
    valid_noun = "datetime.datetime"


class Date(TemporalBase):
    valid_type = datetime.date
    valid_noun = "datetime.date"


class TimeDelta(TemporalBase):
    valid_type = datetime.timedelta
    valid_noun = "datetime.timedelta"


class Time(TemporalBase):
    valid_type = datetime.time
    valid_noun = "datetime.time"


class TZInfo(TemporalBase):
    valid_type = datetime.tzinfo
    valid_noun = "datetime.tzinfo"
