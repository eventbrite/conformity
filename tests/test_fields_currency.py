from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

from currint import (
    Amount,
    Currency,
)
import pytest

from conformity.error import (
    ERROR_CODE_INVALID,
    ERROR_CODE_UNKNOWN,
)
from conformity.fields import currency as currency_fields


class AmountFieldTests(unittest.TestCase):
    """
    Tests the Conformity Amount field
    """

    def setUp(self):
        self.value = Amount.from_code_and_minor(
            'USD',
            100,
        )
        self.field = currency_fields.Amount(
            description='An amount',
        )

    def test_constructor(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies=1234)  # not iterable

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies=['1', '2', '3'])  # not a set

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies={1, 2, 3})  # not strings

    def test_valid(self):
        self.assertEqual(self.field.errors(self.value), [])

    def test_invalid_not_amount_instance(self):
        errors = self.field.errors(100)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Not a currint.Amount instance',
        )

    def test_invalid_bad_currency(self):
        self.value.currency = Currency('XYZ', 12345)
        errors = self.field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Not a valid currency code',
        )

    def test_operator_greater_than(self):
        field = currency_fields.Amount(gt=99)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.Amount(gt=100)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not > 100',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_greater_than_or_equal_to(self):
        field = currency_fields.Amount(gte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.Amount(gte=101)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not >= 101',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_less_than(self):
        field = currency_fields.Amount(lt=101)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.Amount(lt=100)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not < 100',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_less_than_or_equal_to(self):
        field = currency_fields.Amount(lte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.Amount(lte=99)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not <= 99',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_introspect(self):
        self.field.valid_currencies = ['USD']
        self.assertEqual(
            self.field.introspect(),
            {
                'type': 'currint.Amount',
                'description': 'An amount',
                'valid_currencies': ['USD'],
            },
        )


class AmountDictionaryFieldTests(unittest.TestCase):
    """
    Tests the AmountDictionary field
    """

    def setUp(self):
        self.value = {
            'currency': 'USD',
            'value': 100,
        }
        self.field = currency_fields.AmountDictionary(
            description='An amount',
            valid_currencies=['JPY', 'USD'],
        )

    def test_constructor(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(valid_currencies=1234)

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(valid_currencies=[1, 2, 3, 4])

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(gt='not an int')

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(gte='not an int')

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(lt='not an int')

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountDictionary(lte='not an int')

    def test_valid(self):
        self.assertEqual(self.field.errors(self.value), [])

    def test_invalid_bad_currency(self):
        self.value['currency'] = 'XYZ'
        errors = self.field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_UNKNOWN,
        )
        self.assertEqual(
            error.message,
            'Value is not one of: "JPY", "USD"',
        )

    def test_operator_greater_than(self):
        field = currency_fields.AmountDictionary(gt=99)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountDictionary(gt=100)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not > 100',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_greater_than_or_equal_to(self):
        field = currency_fields.AmountDictionary(gte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountDictionary(gte=101)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not >= 101',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_less_than(self):
        field = currency_fields.AmountDictionary(lt=101)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountDictionary(lt=100)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not < 100',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )

    def test_operator_less_than_or_equal_to(self):
        field = currency_fields.AmountDictionary(lte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountDictionary(lte=99)
        errors = field.errors(self.value)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_INVALID,
        )
        self.assertEqual(
            error.message,
            'Value not <= 99',
        )
        self.assertEqual(
            error.pointer,
            'value',
        )
