from __future__ import absolute_import, unicode_literals

import attr
import currint

from conformity.error import (
    Error,
    ERROR_CODE_INVALID,
)
from conformity.fields.basic import Base


@attr.s
class Amount(Base):
    """
    currint.Amount instances
    """

    valid_currencies = attr.ib(default=currint.currencies.keys())
    description = attr.ib(default=None)

    def errors(self, value):
        errors = []
        if not isinstance(value, currint.Amount):
            errors.append(Error(
                "Not an Amount instance",
                code=ERROR_CODE_INVALID,
            ))
        elif value.currency.code not in self.valid_currencies:
            errors.append(Error(
                "Amount does not have a valid currency code",
                code=ERROR_CODE_INVALID,
            ))
        return errors

    def introspect(self):
        return {
            "type": "amount",
            "description": self.description,
            "valid_currency_codes": self.valid_currencies,
        }
