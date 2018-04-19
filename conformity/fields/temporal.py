from __future__ import absolute_import, unicode_literals

import datetime

import attr

from conformity.error import Error
from conformity.fields.basic import Base
from conformity.utils import strip_none


try:
    # noinspection PyUnresolvedReferences
    from freezegun import api as _freeze
    valid_datetime_types = frozenset({datetime.datetime, _freeze.FakeDatetime})
    valid_date_types = frozenset({datetime.date, _freeze.FakeDate})
except ImportError:
    valid_datetime_types = frozenset({datetime.datetime})
    valid_date_types = frozenset({datetime.date})


@attr.s
class TemporalBase(Base):
    """
    Common base class for all temporal types.
    """

    gt = attr.ib(default=None)
    gte = attr.ib(default=None)
    lt = attr.ib(default=None)
    lte = attr.ib(default=None)
    description = attr.ib(default=None)

    valid_types = None  # must be overridden
    valid_isinstance = None  # may be overridden

    def __init__(self, gt=None, lt=None, gte=None, lte=None):
        self.gt = gt
        self.lt = lt
        self.gte = gte
        self.lte = lte

    def errors(self, value):
        if type(value) not in self.valid_types and (
            not self.valid_isinstance or not isinstance(value, self.valid_isinstance)
        ):
            # using stricter type checking, because date is subclass of datetime, but they're not comparable
            return [
                Error("Not a %s instance" % self.valid_noun),
            ]
        elif self.gt is not None and value <= self.gt:
            return [
                Error("Value not > %s" % self.gt),
            ]
        elif self.lt is not None and value >= self.lt:
            return [
                Error("Value not < %s" % self.lt),
            ]
        elif self.gte is not None and value < self.gte:
            return [
                Error("Value not >= %s" % self.gte),
            ]
        elif self.lte is not None and value > self.lte:
            return [
                Error("Value not <= %s" % self.lte),
            ]

    def introspect(self):
        return strip_none({
            "type": self.introspect_type,
            "description": self.description,
            "gt": self.gt,
            "gte": self.gte,
            "lt": self.lt,
            "lte": self.lte,
        })


class DateTime(TemporalBase):
    """
    Datetime instances
    """

    valid_types = valid_datetime_types
    valid_noun = "datetime.datetime"
    introspect_type = "datetime"


class Date(TemporalBase):
    """
    Date instances
    """

    valid_types = valid_date_types
    valid_noun = "datetime.date"
    introspect_type = "date"


class Time(TemporalBase):
    """
    Time instances
    """

    valid_types = frozenset({datetime.time})
    valid_noun = "datetime.time"
    introspect_type = "time"


class TimeDelta(TemporalBase):
    """
    Timedelta instances
    """

    valid_types = frozenset({datetime.timedelta})
    valid_noun = "datetime.timedelta"
    introspect_type = "timedelta"


class TZInfo(TemporalBase):
    """
    TZInfo instances
    """

    valid_types = frozenset({datetime.tzinfo})
    valid_isinstance = datetime.tzinfo
    valid_noun = "datetime.tzinfo"
    introspect_type = "tzinfo"
