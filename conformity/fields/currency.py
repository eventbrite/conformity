from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (  # noqa: F401 TODO Python 3
    AbstractSet,
    Iterable,
    Optional,
)

import attr
import currint
import six

from conformity.error import (
    ERROR_CODE_INVALID,
    Error,
)
from conformity.fields.basic import (
    Base,
    Constant,
    Integer,
)
from conformity.fields.structures import Dictionary
from conformity.utils import (
    attr_is_int,
    attr_is_iterable,
    attr_is_optional,
    attr_is_set,
    attr_is_string,
    strip_none,
)


@attr.s
class Amount(Base):
    """
    currint.Amount instances
    """

    introspect_type = 'currint.Amount'
    valid_currencies = attr.ib(
        default=frozenset(currint.currencies.keys()),
        validator=attr_is_iterable(attr_is_string(), attr_is_set()),
    )  # type: AbstractSet[six.text_type]
    gt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    gte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def errors(self, value):
        if not isinstance(value, currint.Amount):
            return [Error(
                'Not a currint.Amount instance',
                code=ERROR_CODE_INVALID,
            )]

        errors = []
        if value.currency.code not in self.valid_currencies:
            errors.append(Error(
                'Not a valid currency code',
                code=ERROR_CODE_INVALID,
                pointer='currency.code',
            ))
        if self.gt is not None and value.value <= self.gt:
            errors.append(Error(
                'Value not > {}'.format(self.gt),
                code=ERROR_CODE_INVALID,
                pointer='value',
            ))
        if self.lt is not None and value.value >= self.lt:
            errors.append(Error(
                'Value not < {}'.format(self.lt),
                code=ERROR_CODE_INVALID,
                pointer='value',
            ))
        if self.gte is not None and value.value < self.gte:
            errors.append(Error(
                'Value not >= {}'.format(self.gte),
                code=ERROR_CODE_INVALID,
                pointer='value',
            ))
        if self.lte is not None and value.value > self.lte:
            errors.append(Error(
                'Value not <= {}'.format(self.lte),
                code=ERROR_CODE_INVALID,
                pointer='value',
            ))
        return errors

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'valid_currencies': sorted(self.valid_currencies),
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


class AmountDictionary(Dictionary):
    """
    Amount dictionaries
    """

    def __init__(
        self,
        valid_currencies=None,  # type: Iterable[six.text_type]
        gt=None,  # type: int
        gte=None,  # type: int
        lt=None,  # type: int
        lte=None,  # type: int
        *args,
        **kwargs
    ):
        if valid_currencies is not None and (
            not hasattr(valid_currencies, '__iter__') or
            not all(isinstance(c, six.text_type) for c in valid_currencies)
        ):
            raise TypeError("'valid_currencies' must be an iterable of unicode strings")

        if gt is not None and not isinstance(gt, int):
            raise TypeError("'gt' must be an int")
        if gte is not None and not isinstance(gte, int):
            raise TypeError("'gte' must be an int")
        if lt is not None and not isinstance(lt, int):
            raise TypeError("'lt' must be an int")
        if lte is not None and not isinstance(lte, int):
            raise TypeError("'lte' must be an int")

        super(AmountDictionary, self).__init__({
            'currency': Constant(*(valid_currencies or currint.currencies.keys())),
            'value': Integer(gt=gt, gte=gte, lt=lt, lte=lte),
        }, *args, **kwargs)
