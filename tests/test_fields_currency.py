from __future__ import absolute_import, unicode_literals

import unittest

from currint import (
    Amount,
    Currency,
)

from conformity.error import (
    Error,
    ERROR_CODE_INVALID,
)
from conformity.fields.currency import Amount as AmountField


class AmountFieldTests(unittest.TestCase):
    """
    Tests the Conformity Amount field
    """

    def setUp(self):
        self.amount = Amount.from_code_and_minor(
            'USD',
            100,
        )
        self.field = AmountField(
            description='An amount',
        )

    def test_valid(self):
        self.assertEqual(
            self.field.errors(self.amount),
            [],
        )

    def test_invalid_not_amount(self):
        errors = self.field.errors(100)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Not an Amount instance',
        )

    def test_invalid_bad_currency(self):
        self.amount.currency = Currency('XYZ', 12345)
        errors = self.field.errors(self.amount)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Amount does not have a valid currency code',
        )

    def test_introspect(self):
        self.field.valid_currencies = ['USD']
        self.assertEqual(
            self.field.introspect(),
            {
                'type': 'amount',
                'description': 'An amount',
                'valid_currency_codes': ['USD'],
            },
        )
