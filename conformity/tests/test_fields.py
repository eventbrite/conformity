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
    SchemalessDictionary,
    ObjectInstance,
    Tuple,
)
from ..error import Error


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
            [Error("Not a dict")],
        )

        self.assertEqual(
            schema.errors({"child_ids": [1, 2, "ten"]}),
            [
                Error("Not a integer", pointer="child_ids.2"),
                Error("Key address missing", pointer="address"),
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
            [Error('Not a datetime.datetime instance')],
        )

        self.assertEqual(
            datetime_schema.errors(past1955),
            [Error('Value not > 1985-10-26 01:21:00')],
        )

        self.assertEqual(
            date_schema.errors(datetime.date.today()),
            None,
        )

        # datetime is not a valid date
        self.assertEqual(
            date_schema.errors(datetime.datetime.now()),
            [Error('Not a datetime.date instance')],
        )

        self.assertEqual(
            date_schema.errors(past1955.date()),
            [Error('Value not > 1985-10-26')],
        )

        self.assertEqual(
            delta_schema.errors(past1985 - past1955),
            None,
        )

        self.assertEqual(
            delta_schema.errors(past1955 - past1985),
            [Error('Value not > 0:00:00')],
        )

        self.assertEqual(
            negative_delta_schema.errors(past1955 - past1985),
            None,
        )

        self.assertEqual(
            negative_delta_schema.errors(past1985 - past1955),
            [Error('Value not < 0:00:00')],
        )

    def test_schemaless_dict(self):
        schema = SchemalessDictionary()

        self.assertEqual(
            schema.errors({"key": "value"}),
            []
        )

        self.assertEqual(
            schema.errors("a thing"),
            [Error('Not a dict')]
        )

        schema = SchemalessDictionary(Integer(), UnicodeString())

        self.assertEqual(
            schema.errors({1: u"value"}),
            []
        )

        self.assertEqual(
            schema.errors({"x": 123}),
            [
                Error("Not a integer", pointer="x"),
                Error("Not a unicode string", pointer="x"),
            ],
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

    def test_tuple(self):
        schema = Tuple(Integer(gt=0), UnicodeString(), Constant("I love tuples"))

        self.assertEqual(
            schema.errors((1, "test", "I love tuples")),
            []
        )

        # too short
        self.assertEqual(
            schema.errors((1, "test")),
            [Error("Number of elements 2 doesn't match expected 3")]
        )

        # too long
        self.assertEqual(
            schema.errors((1, "test", "I love tuples", "... and coffee")),
            [Error("Number of elements 4 doesn't match expected 3")]
        )

        self.assertEqual(
            schema.errors((-1, None, "I hate tuples",)),
            [
                Error('Value not > 0', pointer='0'),
                Error('Not a unicode string', pointer='1'),
                Error("Value is not u'I love tuples'", pointer='2'),
            ]
        )
