from __future__ import (
    absolute_import,
    unicode_literals,
)

import datetime
from typing import (
    Any as AnyType,
    FrozenSet,
    List as ListType,
    Optional,
    Tuple as TupleType,
    Type,
    Union,
)
import warnings

import attr
import six

from conformity.fields.basic import (
    Base,
    Introspection,
)
from conformity.fields.utils import strip_none
from conformity.types import Error
from conformity.utils import (
    attr_is_optional,
    attr_is_string,
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
    Common base class for all temporal types. Cannot be used on its own without extension.
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

    def __attrs_post_init__(self):  # type: () -> None
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

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
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

    def introspect(self):  # type: () -> Introspection
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'gt': six.text_type(self.gt) if self.gt else None,
            'gte': six.text_type(self.gte) if self.gte else None,
            'lt': six.text_type(self.lt) if self.lt else None,
            'lte': six.text_type(self.lte) if self.lte else None,
        })


@attr.s
class DateTime(TemporalBase):
    """
    Conformity field that ensures that the value is a `datetime.datetime` instance and optionally enforces boundaries
    for that `datetime` with the `gt`, `gte`, `lt`, and `lte` arguments, which must also be `datetime` instances if
    specified.
    """

    valid_types = valid_datetime_types
    valid_noun = 'datetime.datetime'
    introspect_type = 'datetime'


@attr.s
class Date(TemporalBase):
    """
    Conformity field that ensures that the value is a `datetime.date` instance and optionally enforces boundaries
    for that `date` with the `gt`, `gte`, `lt`, and `lte` arguments, which must also be `date` instances if specified.
    """

    valid_types = valid_date_types
    valid_noun = 'datetime.date'
    introspect_type = 'date'


@attr.s
class Time(TemporalBase):
    """
    Conformity field that ensures that the value is a `datetime.time` instance and optionally enforces boundaries
    for that `time` with the `gt`, `gte`, `lt`, and `lte` arguments, which must also be `time` instances if specified.
    """

    valid_types = frozenset({datetime.time})
    valid_noun = 'datetime.time'
    introspect_type = 'time'


@attr.s
class TimeDelta(TemporalBase):
    """
    Conformity field that ensures that the value is a `datetime.timedelta` instance and optionally enforces boundaries
    for that `timedelta` with the `gt`, `gte`, `lt`, and `lte` arguments, which must also be `timedelta` instances if
    specified.
    """

    valid_types = frozenset({datetime.timedelta})
    valid_noun = 'datetime.timedelta'
    introspect_type = 'timedelta'


@attr.s
class TZInfo(TemporalBase):
    """
    Conformity field that ensures that the value is a `datetime.tzinfo` instance. It has `gt`, `gte`, `lt`, and
    `lte` arguments, but they cannot be used, are deprecated, and will be removed in Conformity 2.0.0.
    """

    valid_types = frozenset({datetime.tzinfo})
    valid_isinstance = datetime.tzinfo
    valid_noun = 'datetime.tzinfo'
    introspect_type = 'tzinfo'

    def __attrs_post_init__(self):  # type: () -> None
        if self.gt is not None or self.gte is not None or self.lt is not None or self.lte is not None:
            warnings.warn(
                'Arguments `gt`, `gte`, `lt`, and `lte` are deprecated in TZInfo and will be removed in '
                'Conformity 2.0.',
                DeprecationWarning,
            )

        super(TZInfo, self).__attrs_post_init__()
