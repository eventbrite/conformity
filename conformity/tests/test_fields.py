from __future__ import unicode_literals

import unittest
import datetime

from ..fields import (
    UnicodeString,
    Dictionary,
    List,
    Integer,
    Polymorph,
    Constant,
    DateTime,
    Date,
    TimeDelta,
    SchemalessDictionary
)


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

    def test_temporal(self):
        past1985 = datetime.datetime(1985, 10, 26, 1, 21, 00)
        past1955 = datetime.datetime(1955, 11, 12, 22, 04, 00)

        datetime_schema = DateTime(gt=past1985)
        date_schema = Date(gt=past1985.date())
        delta_schema = TimeDelta(gt=datetime.timedelta(0))
        negative_delta_schema = TimeDelta(lt=datetime.timedelta(0))

        self.assertEqual(
            datetime_schema.errors(datetime.datetime.now()),
            None,
        )

        # date is not a valid datetime
        self.assertEqual(
            datetime_schema.errors(datetime.date.today()),
            ['Not a datetime.datetime instance'],
        )

        self.assertEqual(
            datetime_schema.errors(past1955),
            ['Value not > 1985-10-26 01:21:00'],
        )

        self.assertEqual(
            date_schema.errors(datetime.date.today()),
            None,
        )

        # datetime is not a valid date
        self.assertEqual(
            date_schema.errors(datetime.datetime.now()),
            ['Not a datetime.date instance'],
        )

        self.assertEqual(
            date_schema.errors(past1955.date()),
            ['Value not > 1985-10-26'],
        )

        self.assertEqual(
            delta_schema.errors(past1985 - past1955),
            None,
        )

        self.assertEqual(
            delta_schema.errors(past1955 - past1985),
            ['Value not > 0:00:00'],
        )

        self.assertEqual(
            negative_delta_schema.errors(past1955 - past1985),
            None,
        )

        self.assertEqual(
            negative_delta_schema.errors(past1985 - past1955),
            ['Value not < 0:00:00'],
        )

    def test_schemaless_dict(self):
        schema = SchemalessDictionary()

        self.assertEqual(
            schema.errors({"key": "value"}),
            []
        )

        self.assertEqual(
            schema.errors("a thing"),
            ['Not a dict']
        )

        schema = SchemalessDictionary(Integer(), UnicodeString())

        self.assertEqual(
            schema.errors({1: u"value"}),
            []
        )

        self.assertEqual(
            schema.errors({"x": 123}),
            ["Key 'x': Not a integer", 'Value 123: Not a unicode string'],
        )
