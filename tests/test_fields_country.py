from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

from conformity.error import (
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

    def test_valid(self):
        self.assertEqual(self.field.errors(self.country), [])

    def test_invalid_country_code(self):
        country = 'USD'
        errors = self.field.errors(country)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, ERROR_CODE_UNKNOWN)
        self.assertEqual(errors[0].message, "Not a valid country code")

    def test_not_unicode_string(self):
        country = b'US'
        errors = self.field.errors(country)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].code, ERROR_CODE_INVALID)
        self.assertEqual(errors[0].message, "Not a unicode string")

    def test_introspect(self):
        introspection = self.field.introspect()
        self.assertEqual("country_code_field", introspection["type"])
