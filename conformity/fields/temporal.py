from __future__ import (
    absolute_import,
    unicode_literals,
)

import datetime
from typing import (  # noqa: F401 TODO Python 3
    FrozenSet,
    Optional,
    Tuple as TupleType,
    Type,
    Union,
)

import attr
import six  # noqa: F401 TODO Python 3

from conformity.error import Error
from conformity.fields.basic import Base
from conformity.utils import (
    attr_is_optional,
    attr_is_string,
    strip_none,
)


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

    # These four must be overridden
    introspect_type = None  # type: six.text_type
    valid_isinstance = None  # type: Optional[Union[Type, TupleType[Type, ...]]]
    valid_noun = None  # type: six.text_type
    valid_types = None  # type: FrozenSet[Type]

    gt = attr.ib(default=None)  # type: Union[datetime.date, datetime.time, datetime.datetime, datetime.timedelta]
    gte = attr.ib(default=None)  # type: Union[datetime.date, datetime.time, datetime.datetime, datetime.timedelta]
    lt = attr.ib(default=None)  # type: Union[datetime.date, datetime.time, datetime.datetime, datetime.timedelta]
    lte = attr.ib(default=None)  # type: Union[datetime.date, datetime.time, datetime.datetime, datetime.timedelta]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def __attrs_post_init__(self):
        if self.gt is not None and self._invalid(self.gt):
            raise TypeError("'gt' value {!r} cannot be used for comparisons in this type".format(self.gt))
        if self.gte is not None and self._invalid(self.gte):
            raise TypeError("'gte' value {!r} cannot be used for comparisons in this type".format(self.gte))
        if self.lt is not None and self._invalid(self.lt):
            raise TypeError("'lt' value {!r} cannot be used for comparisons in this type".format(self.lt))
        if self.lte is not None and self._invalid(self.lte):
            raise TypeError("'lte' value {!r} cannot be used for comparisons in this type".format(self.lte))

    @classmethod
    def _invalid(cls, value):
        return type(value) not in cls.valid_types and (
            not cls.valid_isinstance or not isinstance(value, cls.valid_isinstance)
        )

    def errors(self, value):
        if self._invalid(value):
            # using stricter type checking, because date is subclass of datetime, but they're not comparable
            return [Error('Not a {} instance'.format(self.valid_noun))]

        errors = []
        if self.gt is not None and value <= self.gt:
            errors.append(Error('Value not > {}'.format(self.gt)))
        if self.lt is not None and value >= self.lt:
            errors.append(Error('Value not < {}'.format(self.lt)))
        if self.gte is not None and value < self.gte:
            errors.append(Error('Value not >= {}'.format(self.gte)))
        elif self.lte is not None and value > self.lte:
            errors.append(Error('Value not <= {}'.format(self.lte)))
        return errors

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


@attr.s
class DateTime(TemporalBase):
    """
    Datetime instances
    """

    valid_types = valid_datetime_types
    valid_noun = 'datetime.datetime'
    introspect_type = 'datetime'


@attr.s
class Date(TemporalBase):
    """
    Date instances
    """

    valid_types = valid_date_types
    valid_noun = 'datetime.date'
    introspect_type = 'date'


@attr.s
class Time(TemporalBase):
    """
    Time instances
    """

    valid_types = frozenset({datetime.time})
    valid_noun = 'datetime.time'
    introspect_type = 'time'


@attr.s
class TimeDelta(TemporalBase):
    """
    Timedelta instances
    """

    valid_types = frozenset({datetime.timedelta})
    valid_noun = 'datetime.timedelta'
    introspect_type = 'timedelta'


@attr.s
class TZInfo(TemporalBase):
    """
    TZInfo instances
    """

    valid_types = frozenset({datetime.tzinfo})
    valid_isinstance = datetime.tzinfo
    valid_noun = 'datetime.tzinfo'
    introspect_type = 'tzinfo'
