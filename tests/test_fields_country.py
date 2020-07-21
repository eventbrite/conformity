from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

import pytest

from conformity.constants import (
    ERROR_CODE_INVALID,
    ERROR_CODE_UNKNOWN,
)
from conformity.fields.country import CountryCodeField


class CountryCodeTest(unittest.TestCase):
    """
    Tests the Country Code field.
    """

    def setUp(self):
        self.country = 'US'
        self.field = CountryCodeField()

    def test_constructor(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            CountryCodeField(code_filter='not a callable')  # type: ignore

    def test_valid(self):  # type: () -> None
        self.assertEqual(self.field.errors(self.country), [])

    def test_invalid_country_code(self):  # type: () -> None
        country = 'USD'
        errors = self.field.errors(country)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, ERROR_CODE_UNKNOWN)
        self.assertEqual(errors[0].message, 'Not a valid country code')

    def test_not_unicode_string(self):  # type: () -> None
        country = b'US'
        errors = self.field.errors(country)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, ERROR_CODE_INVALID)
        self.assertEqual(errors[0].message, 'Not a unicode string')

    def test_introspect(self):  # type: () -> None
        introspection = self.field.introspect()
        self.assertEqual('country_code_field', introspection['type'])
