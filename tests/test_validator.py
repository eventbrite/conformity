from __future__ import absolute_import, unicode_literals

import unittest

from conformity.fields import (
    Dictionary,
    UnicodeString,
)
from conformity.validator import (
    PositionalError,
    validate,
    validate_call,
    validate_method,
    ValidationError,
)


class ValidatorTests(unittest.TestCase):
    """
    Tests validation functions
    """

    def test_validate(self):

        schema = Dictionary({
            "name": UnicodeString(max_length=20),
            "greeting": UnicodeString(),
        }, optional_keys=["greeting"])

        validate(schema, {"name": "Andrew"})
        validate(schema, {"name": "Andrew", "greeting": "Ahoy-hoy"})

        with self.assertRaises(ValidationError):
            validate(schema, {"name": "Andrewverylongnameperson"})

        with self.assertRaises(ValidationError):
            validate(schema, {"name": "Andrew", "greeeeeeting": "Ahoy-hoy"})

    def test_validate_call(self):

        schema = Dictionary({
            "name": UnicodeString(max_length=20),
            "greeting": UnicodeString(),
        }, optional_keys=["greeting"])

        @validate_call(schema, UnicodeString())
        def greeter(name, greeting="Hello"):
            # Special case to check return value stuff
            if name == "error":
                return 5
            return "%s, %s!" % (greeting, name)

        self.assertEqual(greeter(name="Andrew"), "Hello, Andrew!")
        self.assertEqual(greeter(name="Andrew", greeting="Ahoy"), "Ahoy, Andrew!")

        with self.assertRaises(ValidationError):
            greeter(name="Andrewverylongnameperson")

        with self.assertRaises(ValidationError):
            greeter(name="Andrew", greeeeeeting="Boo")

        with self.assertRaises(ValidationError):
            greeter(name="error")

        with self.assertRaises(PositionalError):
            greeter("Andrew")

    def test_validate_method(self):

        schema = Dictionary({
            "name": UnicodeString(max_length=20),
            "greeting": UnicodeString(),
        }, optional_keys=["greeting"])

        class Greeter(object):
            @classmethod
            @validate_method(schema, UnicodeString())
            def greeter(cls, name, greeting="Hello"):
                # Special case to check return value stuff
                if name == "error":
                    return 5
                return "%s, %s!" % (greeting, name)

        self.assertEqual(Greeter.greeter(name="Andrew"), "Hello, Andrew!")
        self.assertEqual(Greeter.greeter(name="Andrew", greeting="Ahoy"), "Ahoy, Andrew!")

        with self.assertRaises(ValidationError):
            Greeter.greeter(name="Andrewverylongnameperson")

        with self.assertRaises(ValidationError):
            Greeter.greeter(name="Andrew", greeeeeeting="Boo")

        with self.assertRaises(ValidationError):
            Greeter.greeter(name="error")

        with self.assertRaises(PositionalError):
            Greeter.greeter("Andrew")
