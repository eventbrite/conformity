from __future__ import unicode_literals

import unittest

from ..fields import (
    Constant,
    Dictionary,
    UnicodeString,
    Polymorph,
    ObjectInstance,
    All,
    Any,
    BooleanValidator,
)
from ..error import Error


class MetaFieldTests(unittest.TestCase):
    """
    Tests meta fields
    """

    def test_any(self):
        schema = Any(Constant("one"), Constant("two"))
        self.assertEqual(
            schema.errors("one"),
            [],
        )
        self.assertEqual(
            schema.errors("two"),
            [],
        )
        self.assertEqual(
            len(schema.errors("three")),
            2,
        )

    def test_all(self):
        schema = All(Constant("one"), UnicodeString())
        self.assertEqual(
            schema.errors("one"),
            [],
        )
        self.assertEqual(
            len(schema.errors("two")),
            1,
        )

    def test_objectinstance(self):
        class Thing(object):
            pass

        class Thingy(Thing):
            pass

        class SomethingElse(object):
            pass

        schema = ObjectInstance(Thing)

        self.assertEqual(
            schema.errors(Thing()),
            []
        )

        # subclasses are valid
        self.assertEqual(
            schema.errors(Thingy()),
            []
        )

        self.assertEqual(
            schema.errors(SomethingElse()),
            [Error("Not an instance of Thing")]
        )

    def test_polymorph(self):

        card = Dictionary({
            "payment_type": Constant("card"),
            "number": UnicodeString(),
            "cvc": UnicodeString(description="Card Verification Code"),
        })

        bankacc = Dictionary({
            "payment_type": Constant("bankacc"),
            "routing": UnicodeString(description="US RTN or foreign equivalent"),
            "account": UnicodeString(),
        })

        schema = Polymorph(
            "payment_type",
            {
                "card": card,
                "bankacc": bankacc,
            },
        )

        self.assertEqual(
            schema.errors({
                "payment_type": "card",
                "number": "1234567890123456",
                "cvc": "000",
            }),
            [],
        )

        self.assertEqual(
            schema.errors({
                "payment_type": "bankacc",
                "routing": "13456790",
                "account": "13910399",
            }),
            [],
        )

        self.assertEqual(
            schema.introspect(),
            {
                "type": "polymorph",
                "contents_map": {
                    "bankacc": {
                        "type": "dictionary",
                        "allow_extra_keys": False,
                        "contents": {
                            "account": {"type": "unicode"},
                            "payment_type": {
                                "type": "constant",
                                "value": "bankacc",
                            },
                            "routing": {
                                "type": "unicode",
                                "description": "US RTN or foreign equivalent",
                            },
                        },
                        "optional_keys": [],
                    },
                    "card": {
                        "type": "dictionary",
                        "allow_extra_keys": False,
                        "contents": {
                            "cvc": {
                                "type": "unicode",
                                "description": "Card Verification Code",
                            },
                            "number": {"type": "unicode"},
                            "payment_type": {
                                "type": "constant",
                                "value": "card",
                            },
                        },
                        "optional_keys": [],
                    },
                },
                "switch_field": "payment_type",
            },
        )

    def test_boolean_validator(self):
        schema = BooleanValidator(
            lambda x: x.isdigit(),
            "str.isdigit()",
            "Not all digits",
        )
        # Test valid unicode and byte strings
        self.assertEqual(
            schema.errors("123"),
            [],
        )
        self.assertEqual(
            schema.errors(b"123"),
            [],
        )
        # Test invalid unicode and byte strings
        self.assertEqual(
            len(schema.errors("123a")),
            1,
        )
        self.assertEqual(
            len(schema.errors(b"123a")),
            1,
        )
        # Test bad-type errors are swallowed well
        self.assertEqual(
            len(schema.errors(344532)),
            1,
        )
        # Test introspection looks OK
        self.assertEqual(
            schema.introspect(),
            {
                "type": "boolean_validator",
                "validator": "str.isdigit()",
            },
        )
