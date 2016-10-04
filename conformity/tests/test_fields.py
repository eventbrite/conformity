from __future__ import unicode_literals

import unittest

from ..fields import UnicodeString, Dictionary, List, Integer, Polymorph, Constant


class FieldTests(unittest.TestCase):
    """
    Tests fields
    """

    def test_complex(self):

        schema = Dictionary({
            "child_ids": List(Integer(gt=0)),
            "address": Dictionary(
                {
                    "line1": UnicodeString(),
                    "line2": UnicodeString(),
                    "city": UnicodeString(),
                    "postcode": UnicodeString(),
                    "state": UnicodeString(),
                    "country": UnicodeString(),
                },
                optional_keys=["line2", "state"],
            ),
        })

        self.assertEqual(
            schema.errors(None),
            ["Not a dict"],
        )

        self.assertEqual(
            schema.errors({"child_ids": [1, 2, "ten"]}),
            [
                "Key child_ids: Index 2: Not a integer",
                "Key address missing",
            ],
        )

        self.assertEqual(
            schema.errors({
                "child_ids": [1, 2, 3, 4],
                "address": {
                    "line1": "115 5th Street",
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA",
                    "postcode": "94103",
                }
            }),
            [],
        )

    def test_polymorph(self):

        card = Dictionary({
            "payment_type": Constant("card"),
            "number": UnicodeString(),
            "cvc": UnicodeString(),
        })

        bankacc = Dictionary({
            "payment_type": Constant("bankacc"),
            "routing": UnicodeString(),
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
