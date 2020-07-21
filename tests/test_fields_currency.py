from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest
import warnings

from currint import (
    Amount,
    Currency,
    currencies,
)
import pytest
import six

from conformity.constants import (
    ERROR_CODE_INVALID,
    ERROR_CODE_UNKNOWN,
)
from conformity.fields import currency as currency_fields


class TestAmount(unittest.TestCase):
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

    def test_constructor(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies=1234)  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies=['1', '2', '3'])  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.Amount(valid_currencies={1, 2, 3})  # type: ignore

    def test_valid(self):  # type: () -> None
        self.assertEqual(self.field.errors(self.value), [])

    def test_invalid_not_amount_instance(self):  # type: () -> None
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

    def test_invalid_bad_currency(self):  # type: () -> None
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

    def test_operator_greater_than(self):  # type: () -> None
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

    def test_operator_greater_than_or_equal_to(self):  # type: () -> None
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

    def test_operator_less_than(self):  # type: () -> None
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

    def test_operator_less_than_or_equal_to(self):  # type: () -> None
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

    def test_introspect(self):  # type: () -> None
        self.field.valid_currencies = frozenset({'USD'})
        self.assertEqual(
            self.field.introspect(),
            {
                'type': 'currint.Amount',
                'description': 'An amount',
                'valid_currencies': ['USD'],
            },
        )


class TestAmountRequestDictionaryField(unittest.TestCase):
    """
    Tests the AmountDictionary field
    """

    def setUp(self):
        self.value = {
            'currency': 'USD',
            'value': 100,
        }
        self.field = currency_fields.AmountRequestDictionary(
            description='An amount',
            valid_currencies=['JPY', 'USD'],
        )

    def test_constructor(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(valid_currencies=1234)  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(valid_currencies=[1, 2, 3, 4])  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(gt='not an int')  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(gte='not an int')  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(lt='not an int')  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            currency_fields.AmountRequestDictionary(lte='not an int')  # type: ignore

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)

            currency_fields.AmountRequestDictionary(
                description='An amount',
                valid_currencies=['JPY', 'USD'],
                allow_extra_keys=True,
            )

        assert w
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert (
            '*args and **kwargs are deprecated in AmountRequestDictionary and will be removed in Conformity 2.0.'
        ) in str(w[-1].message)

    def test_valid(self):  # type: () -> None
        self.assertEqual(self.field.errors(self.value), [])

    def test_invalid_bad_currency(self):  # type: () -> None
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

    def test_operator_greater_than(self):  # type: () -> None
        field = currency_fields.AmountRequestDictionary(gt=99)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountRequestDictionary(gt=100)
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

    def test_operator_greater_than_or_equal_to(self):  # type: () -> None
        field = currency_fields.AmountRequestDictionary(gte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountRequestDictionary(gte=101)
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

    def test_operator_less_than(self):  # type: () -> None
        field = currency_fields.AmountRequestDictionary(lt=101)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountRequestDictionary(lt=100)
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

    def test_operator_less_than_or_equal_to(self):  # type: () -> None
        field = currency_fields.AmountRequestDictionary(lte=100)
        self.assertEqual(field.errors(self.value), [])

        field = currency_fields.AmountRequestDictionary(lte=99)
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


class TestAmountDictionariesAndStrings(object):
    def test_amount_response_dict(self):
        field = currency_fields.AmountResponseDictionary(
            description='This is a test, yo',
            major_value_required=False,
            display_required=False,
        )

        amount = Amount(currencies['USD'], 1839)

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
        }) == []

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'major_value': amount.currency.format_decimal(amount.value),
            'display': six.text_type(amount),
        }) == []

        amount = Amount(currencies['JPY'], 8183728)

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
        }) == []

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'major_value': amount.currency.format_decimal(amount.value),
            'display': six.text_type(amount),
        }) == []

        assert field.errors({})
        assert field.errors({'value': amount.value})
        assert field.errors({'currency': amount.currency.code})
        assert field.errors({'value': amount.value, 'currency': amount.currency.code, 'extra': 'Not allowed'})

        field = currency_fields.AmountResponseDictionary(description='Woof', display_required=False)

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'major_value': amount.currency.format_decimal(amount.value),
        }) == []
        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'display': six.text_type(amount),
        })

        field = currency_fields.AmountResponseDictionary(description='Woof', major_value_required=False)

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'display': six.text_type(amount),
        }) == []
        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'major_value': amount.currency.format_decimal(amount.value),
        })

        field = currency_fields.AmountResponseDictionary(description='Woof')

        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'display': six.text_type(amount),
        })
        assert field.errors({
            'value': amount.value,
            'currency': amount.currency.code,
            'major_value': amount.currency.format_decimal(amount.value),
        })

    def test_amount_string(self):
        field = currency_fields.AmountString(description='Yup yup yup')

        assert field.errors('USD,3819') == []
        assert field.errors('USD:87173') == []
        assert field.errors('JPY,6716') == []
        assert field.errors('JPY:83613') == []

        amount = Amount(currencies['USD'], 1839)
        assert field.errors('{},{}'.format(amount.currency.code, amount.value)) == []

        assert field.introspect() == {
            'type': 'currency_amount_string',
            'description': 'Yup yup yup',
            'valid_currencies': '(all currencies)',
        }

        field = currency_fields.AmountString(
            valid_currencies={'USD'},
            gte=100,
            lt=100000,
            description='US only dude',
        )

        assert field.errors('USD,3819') == []
        assert field.errors('USD:87173') == []
        assert field.errors('USD:99')
        assert field.errors('USD:100000')
        assert field.errors('JPF,3819')

        amount = Amount(currencies['JPY'], 1839)
        assert field.errors('{},{}'.format(amount.currency.code, amount.value))

        assert field.errors(b'USD,3819')
        assert field.errors('USD.3819')
        assert field.errors('USD,3819.15')

        assert field.introspect() == {
            'type': 'currency_amount_string',
            'description': 'US only dude',
            'valid_currencies': ['USD'],
            'gte': 100,
            'lt': 100000,
        }

    def test_deprecated_amount_dictionary_constructor_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)

            # noinspection PyDeprecation
            currency_fields.AmountDictionary(
                description='An amount',
                valid_currencies=['JPY', 'USD'],
            )

        assert w
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert (
            'AmountDictionary is deprecated and will be removed in Conformity 2.0. '
            'Use AmountRequestDictionary, instead.'
        ) in str(w[-1].message)


class CurrencyCodeTest(unittest.TestCase):
    """
    Tests the CurrencyCodeField field
    """

    def setUp(self):
        self.currency = 'USD'
        self.field = currency_fields.CurrencyCodeField()

    def test_valid(self):
        self.assertEqual(self.field.errors(self.currency), [])

    def test_invalid_currency_code(self):
        currency = 'US'
        errors = self.field.errors(currency)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.code,
            ERROR_CODE_UNKNOWN,
        )

    def test_not_unicode_string(self):
        currency = b'USD'
        errors = self.field.errors(currency)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(
            error.message,
            'Not a unicode string',
        )

    def test_introspect(self):
        introspection = self.field.introspect()
        self.assertEqual('currency_code_field', introspection['type'])
