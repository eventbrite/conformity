from __future__ import absolute_import, unicode_literals

import attr
import currint

from conformity.error import (
    Error,
    ERROR_CODE_INVALID,
)
from conformity import fields
from conformity.utils import strip_none


@attr.s
class Amount(fields.Base):
    """
    currint.Amount instances
    """
    valid_currencies = attr.ib(default=currint.currencies.keys())
    gt = attr.ib(default=None)
    gte = attr.ib(default=None)
    lt = attr.ib(default=None)
    lte = attr.ib(default=None)
    description = attr.ib(default=None)

    def errors(self, value):
        if not isinstance(value, currint.Amount):
            return [Error(
                "Not a currint.Amount instance",
                code=ERROR_CODE_INVALID,
            )]

        errors = []
        if value.currency.code not in self.valid_currencies:
            errors.append(Error(
                "Not a valid currency code",
                code=ERROR_CODE_INVALID,
                pointer="currency.code",
            ))
        if self.gt is not None and value.value <= self.gt:
            errors.append(Error(
                "Value not > %s" % self.gt,
                code=ERROR_CODE_INVALID,
                pointer="value",
            ))
        if self.lt is not None and value.value >= self.lt:
            errors.append(Error(
                "Value not < %s" % self.lt,
                code=ERROR_CODE_INVALID,
                pointer="value",
            ))
        if self.gte is not None and value.value < self.gte:
            errors.append(Error(
                "Value not >= %s" % self.gte,
                code=ERROR_CODE_INVALID,
                pointer="value",
            ))
        if self.lte is not None and value.value > self.lte:
            errors.append(Error(
                "Value not <= %s" % self.lte,
                code=ERROR_CODE_INVALID,
                pointer="value",
            ))
        return errors

    def introspect(self):
        return strip_none({
            "type": "currint.Amount",
            "description": self.description,
            "valid_currencies": self.valid_currencies,
            "gt": self.gt,
            "gte": self.gte,
            "lt": self.lt,
            "lte": self.lte,
        })


class AmountDictionary(fields.Dictionary):
    """
    Amount dictionaries
    """

    def __init__(self, valid_currencies=None, gt=None, gte=None, lt=None, lte=None, *args, **kwargs):
        super(AmountDictionary, self).__init__({
            "currency": fields.Constant(*(valid_currencies or currint.currencies.keys())),
            "value": fields.Integer(gt=gt, gte=gte, lt=lt, lte=lte),
        }, *args, **kwargs)
