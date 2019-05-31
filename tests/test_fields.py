from __future__ import (
    absolute_import,
    unicode_literals,
)

from collections import OrderedDict
import datetime
import decimal
import unittest

import freezegun
import pytz

from conformity.error import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
    Error,
)
from conformity.fields import (
    Boolean,
    ByteString,
    Constant,
    Date,
    DateTime,
    Decimal,
    Dictionary,
    Float,
    Integer,
    List,
    SchemalessDictionary,
    Set,
    TimeDelta,
    Tuple,
    TZInfo,
    UnicodeDecimal,
    UnicodeString,
)


class FieldTests(unittest.TestCase):
    """
    Tests fields
    """
    def test_integers(self):
        schema = Integer(gt=0, lt=10)
        self.assertEqual(None, schema.errors(1))
        self.assertEqual([Error('Not an integer')], schema.errors('one'))
        self.assertEqual([Error('Not an integer')], schema.errors(True))
        self.assertEqual([Error('Value not > 0')], schema.errors(0))
        self.assertEqual([Error('Value not < 10')], schema.errors(10))

        schema = Integer(gte=0, lte=10)
        self.assertEqual([Error('Value not >= 0')], schema.errors(-1))
        self.assertEqual([Error('Value not <= 10')], schema.errors(11))

    def test_strings(self):
        schema = UnicodeString()
        self.assertEqual(None, schema.errors(''))
        self.assertEqual(None, schema.errors('Foo bar baz qux foo bar baz qux foo bar baz qux foo bar baz qux foo bar'))
        self.assertEqual([Error('Not a unicode string')], schema.errors(b'Test'))

        schema = UnicodeString(min_length=5, max_length=10)
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(''))
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors('1234'))
        self.assertEqual(None, schema.errors('12345'))
        self.assertEqual(None, schema.errors('1234567890'))
        self.assertEqual([Error('String must have a length no more than 10')], schema.errors('12345678901'))

        schema = UnicodeString(allow_blank=False)
        self.assertEqual([Error('String cannot be blank')], schema.errors(''))
        self.assertEqual([Error('String cannot be blank')], schema.errors(' '))
        self.assertEqual([Error('String cannot be blank')], schema.errors(' \n '))
        self.assertEqual(None, schema.errors('foo'))

        schema = ByteString()
        self.assertEqual(None, schema.errors(b''))
        self.assertEqual(None, schema.errors(b'Foo bar baz qux foo bar baz qux foo bar baz qux foo bar baz qux foo'))
        self.assertEqual([Error('Not a byte string')], schema.errors('Test'))

        schema = ByteString(min_length=5, max_length=10)
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(b''))
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(b'1234'))
        self.assertEqual(None, schema.errors(b'12345'))
        self.assertEqual(None, schema.errors(b'1234567890'))
        self.assertEqual([Error('String must have a length no more than 10')], schema.errors(b'12345678901'))

    def test_complex(self):

        schema = Dictionary({
            'child_ids': List(Integer(gt=0)),
            'address': Dictionary(
                {
                    'line1': UnicodeString(),
                    'line2': UnicodeString(),
                    'city': UnicodeString(),
                    'postcode': UnicodeString(),
                    'state': UnicodeString(),
                    'country': UnicodeString(),
                },
                optional_keys=['line2', 'state'],
            ),
            'unique_things': Set(UnicodeString()),
        })

        self.assertEqual(
            schema.errors(None),
            [Error('Not a dict')],
        )

        self.assertEqual(
            sorted(schema.errors(
                {
                    'child_ids': [1, 2, 'ten'],
                    'unsolicited_item': 'Should not be here',
                    'another_bad': 'Also extra',
                    'unique_things': ['hello', 'world'],
                },
            )),
            sorted([
                Error('Not an integer', pointer='child_ids.2'),
                Error('Missing key: address', code=ERROR_CODE_MISSING, pointer='address'),
                Error('Extra keys present: another_bad, unsolicited_item', code=ERROR_CODE_UNKNOWN),
                Error('Not a set or frozenset', pointer='unique_things'),
            ]),
        )

        self.assertEqual(
            schema.errors({
                'child_ids': [1, 2, 3, 4],
                'address': {
                    'line1': '115 5th Street',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'country': 'USA',
                    'postcode': '94103',
                },
                'unique_things': {'hello', b'world'},
            }),
            [Error('Not a unicode string', pointer='unique_things.[{}]'.format(str(b'world')))],
        )

        self.assertEqual(
            schema.errors({
                'child_ids': [1, 2, 3, 4],
                'address': {
                    'line1': '115 5th Street',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'country': 'USA',
                    'postcode': '94103',
                },
                'unique_things': {'hello', 'world'},
            }),
            [],
        )

        introspection = schema.introspect()
        self.assertEqual('dictionary', introspection['type'])
        self.assertFalse(introspection['allow_extra_keys'])
        self.assertEqual([], introspection['optional_keys'])
        self.assertEqual(3, len(introspection['contents']))
        self.assertIn('child_ids', introspection['contents'])
        self.assertEqual(
            {
                'type': 'list',
                'contents': {'gt': 0, 'type': 'integer'},
            },
            introspection['contents']['child_ids'],
        )
        self.assertIn('address', introspection['contents'])
        self.assertEqual('dictionary', introspection['contents']['address']['type'])
        self.assertFalse(introspection['contents']['address']['allow_extra_keys'])
        self.assertEqual({'line2', 'state'}, set(introspection['contents']['address']['optional_keys']))
        self.assertEqual(
            {
                'city': {'type': 'unicode'},
                'country': {'type': 'unicode'},
                'line1': {'type': 'unicode'},
                'line2': {'type': 'unicode'},
                'postcode': {'type': 'unicode'},
                'state': {'type': 'unicode'},
            },
            introspection['contents']['address']['contents'],
        )
        self.assertEqual(
            {
                'type': 'set',
                'contents': {'type': 'unicode'},
            },
            introspection['contents']['unique_things'],
        )

    def test_dictionary_extension(self):
        schema1 = Dictionary(
            {
                'foo': UnicodeString(),
                'bar': Boolean(),
            },
            optional_keys=('foo', ),
            description='Hello, world',
        )

        schema2 = schema1.extend(
            {
                'bar': Integer(),
                'baz': List(Integer()),
            },
            optional_keys=('baz', ),
        )

        schema3 = schema1.extend(
            {
                'bar': Integer(),
                'baz': List(Integer()),
            },
            optional_keys=('baz',),
            allow_extra_keys=True,
            description='Goodbye, universe',
            replace_optional_keys=True,
        )

        self.assertEqual(
            Dictionary(
                {
                    'foo': UnicodeString(),
                    'bar': Integer(),
                    'baz': List(Integer()),
                },
                optional_keys=('foo', 'baz', ),
                allow_extra_keys=False,
                description='Hello, world',
            ).introspect(),
            schema2.introspect(),
        )

        self.assertEqual(
            Dictionary(
                {
                    'foo': UnicodeString(),
                    'bar': Integer(),
                    'baz': List(Integer()),
                },
                optional_keys=('baz',),
                allow_extra_keys=True,
                description='Goodbye, universe',
            ).introspect(),
            schema3.introspect(),
        )

        assert 'display_order' not in schema1.introspect()
        assert 'display_order' not in schema2.introspect()
        assert 'display_order' not in schema3.introspect()

    def test_dictionary_ordering(self):
        schema1 = Dictionary(
            OrderedDict((
                ('foo', UnicodeString()),
                ('bar', Boolean()),
                ('baz', List(Integer())),
            )),
            optional_keys=('foo',),
            description='Hello, world',
        )

        assert schema1.introspect()['contents'] == {
            'baz': List(Integer()).introspect(),
            'foo': UnicodeString().introspect(),
            'bar': Boolean().introspect(),
        }

        assert schema1.introspect()['display_order'] == ['foo', 'bar', 'baz']

        schema2 = schema1.extend(OrderedDict((
            ('bar', Integer()),
            ('qux', Set(UnicodeString())),
            ('moon', Tuple(Decimal(), UnicodeString())),
        )))

        assert schema2.introspect()['contents'] == {
            'baz': List(Integer()).introspect(),
            'foo': UnicodeString().introspect(),
            'moon': Tuple(Decimal(), UnicodeString()).introspect(),
            'bar': Integer().introspect(),
            'qux': Set(UnicodeString()).introspect(),
        }

        assert schema2.introspect()['display_order'] == ['foo', 'bar', 'baz', 'qux', 'moon']

        assert not schema1.errors({'bar': True, 'foo': 'Hello', 'baz': [15]})

        errors = schema1.errors({'baz': 'Nope', 'foo': False, 'bar': ['Heck nope']})

        assert errors == [
            Error(code='INVALID', pointer='foo', message='Not a unicode string'),
            Error(code='INVALID', pointer='bar', message='Not a boolean'),
            Error(code='INVALID', pointer='baz', message='Not a list'),
        ]

        assert not schema2.errors(
            {'bar': 91, 'foo': 'Hello', 'qux': {'Yes'}, 'baz': [15], 'moon': (decimal.Decimal('15.25'), 'USD')},
        )

        errors = schema2.errors({'baz': 'Nope', 'foo': False, 'bar': ['Heck nope'], 'qux': 'Denied', 'moon': 72})

        assert errors == [
            Error(code='INVALID', pointer='foo', message='Not a unicode string'),
            Error(code='INVALID', pointer='bar', message='Not an integer'),
            Error(code='INVALID', pointer='baz', message='Not a list'),
            Error(code='INVALID', pointer='qux', message='Not a set or frozenset'),
            Error(code='INVALID', pointer='moon', message='Not a tuple'),
        ]

    def test_temporal(self):
        past1985 = datetime.datetime(1985, 10, 26, 1, 21, 0)
        past1955 = datetime.datetime(1955, 11, 12, 22, 4, 0)

        datetime_schema = DateTime(gt=past1985)
        date_schema = Date(gt=past1985.date())
        delta_schema = TimeDelta(gt=datetime.timedelta(0))
        negative_delta_schema = TimeDelta(lt=datetime.timedelta(0))
        time_zone_schema = TZInfo()

        self.assertEqual(
            datetime_schema.errors(datetime.datetime.now()),
            None,
        )

        with freezegun.freeze_time():
            self.assertEqual(None, datetime_schema.errors(datetime.datetime.now()))

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
            datetime_schema.introspect(),
            {
                'type': 'datetime',
                'gt': past1985,
            },
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

        with freezegun.freeze_time():
            self.assertEqual(None, date_schema.errors(datetime.date.today()))

            # fake datetime is not a valid date
            self.assertEqual(
                [Error('Not a datetime.date instance')],
                date_schema.errors(datetime.datetime.now()),
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

        self.assertEqual(
            [Error('Not a datetime.tzinfo instance')],
            time_zone_schema.errors(datetime.datetime.now()),
        )

        self.assertEqual(None, time_zone_schema.errors(pytz.timezone('America/Chicago')))

    def test_schemaless_dict_empty(self):
        """
        Tests the schemaless dict without any schema at all
        (so the default Hashable: Anything)
        """
        schema = SchemalessDictionary()

        self.assertEqual(
            schema.errors({'key': 'value'}),
            []
        )

        self.assertEqual(
            schema.errors('a thing'),
            [Error('Not a dict')]
        )

        self.assertEqual(
            schema.introspect(),
            {
                'type': 'schemaless_dictionary',
            }
        )

    def test_schemaless_dict(self):
        """
        Tests the schemaless dict with some schema
        """
        schema = SchemalessDictionary(Integer(), UnicodeString(), min_length=1, max_length=5)

        self.assertEqual(
            schema.errors({1: 'value'}),
            []
        )

        assert schema.errors({}) == [Error('Dict contains fewer than 1 value(s)')]

        self.assertEqual(
            schema.errors({'x': 123, 2: 'foo', 3: 'bar', 4: 'baz', 5: 'qux', 6: 'too many'}),
            [
                Error('Dict contains more than 5 value(s)'),
                Error('Not an integer', pointer='x'),
                Error('Not a unicode string', pointer='x'),
            ],
        )

        self.assertEqual(
            schema.introspect(),
            {
                'type': 'schemaless_dictionary',
                'key_type': {'type': 'integer'},
                'value_type': {'type': 'unicode'},
                'max_length': 5,
                'min_length': 1,
            }
        )

    def test_tuple(self):
        schema = Tuple(Integer(gt=0), UnicodeString(), Constant('I love tuples'))

        self.assertEqual(
            schema.errors((1, 'test', 'I love tuples')),
            []
        )

        # too short
        self.assertEqual(
            schema.errors((1, 'test')),
            [Error('Number of elements 2 does not match expected 3')]
        )

        # too long
        self.assertEqual(
            schema.errors((1, 'test', 'I love tuples', '... and coffee')),
            [Error('Number of elements 4 does not match expected 3')]
        )

        self.assertEqual(
            schema.errors((-1, None, 'I hate tuples',)),
            [
                Error('Value not > 0', pointer='0'),
                Error('Not a unicode string', pointer='1'),
                Error(
                    'Value is not "I love tuples"',
                    code=ERROR_CODE_UNKNOWN,
                    pointer='2',
                ),
            ]
        )

        self.assertEqual(
            schema.introspect(),
            {
                'type': 'tuple',
                'contents': [
                    {'type': 'integer', 'gt': 0},
                    {'type': 'unicode'},
                    {'type': 'constant', 'values': ['I love tuples']},
                ]
            }
        )

    def test_dictionary_subclass(self):
        """
        Tests that subclassing a Dictionary allows you to provide the
        same options as instantiating it.
        """
        class Coordinate(Dictionary):
            contents = {
                'x': Float(),
                'y': Float(),
                'z': Float(),
            }
            optional_keys = ['z']
        schema = Coordinate(description='Where the treasure is')

        # Test the options work right
        self.assertEqual(
            schema.errors({'x': 4.4, 'y': 65.21}),
            [],
        )
        self.assertEqual(
            schema.errors({'x': 4.4, 'y': 65.21, 'z': 5542}),
            [],
        )
        self.assertEqual(
            len(schema.errors({'x': 'HERRING', 'z': 5542})),
            2,
        )

        # Test you can't make a dict without contents
        with self.assertRaises(ValueError):
            Dictionary()

        # Test not overriding one field
        class TwoDeeCoordinate(Dictionary):
            contents = {
                'x': Float(),
                'y': Float(),
            }
        schema2d = TwoDeeCoordinate(description='Where the treasure is')
        self.assertEqual(
            len(schema2d.errors({'x': 3.14, 'z': 5542})),
            2,
        )

    def test_decimal(self):
        """
        Tests decimal.Decimal object validation
        """
        self.assertEqual(None, Decimal().errors(decimal.Decimal('1')))
        self.assertEqual(None, Decimal().errors(decimal.Decimal('1.4')))
        self.assertEqual(None, Decimal().errors(decimal.Decimal('-3.14159')))
        self.assertEqual(
            [Error('Not a decimal')],
            Decimal().errors('-3.14159')
        )
        self.assertEqual(
            [Error('Not a decimal')],
            Decimal().errors(-3.14159)
        )
        self.assertEqual(
            [Error('Not a decimal')],
            Decimal().errors(15)
        )
        self.assertEqual(
            [Error('Value not > 6')],
            Decimal(lt=12, gt=6).errors(decimal.Decimal('6')),
        )
        self.assertEqual(
            [Error('Value not < 12')],
            Decimal(lt=12, gt=6).errors(decimal.Decimal('12')),
        )
        self.assertEqual(None, Decimal(lt=12, gt=6).errors(decimal.Decimal('6.1')))
        self.assertEqual(None, Decimal(lt=12, gt=6).errors(decimal.Decimal('11.9')))
        self.assertEqual(
            [Error('Value not >= 6')],
            Decimal(lte=12, gte=6).errors(decimal.Decimal('5.9')),
        )
        self.assertEqual(
            [Error('Value not <= 12')],
            Decimal(lte=12, gte=6).errors(decimal.Decimal('12.1')),
        )
        self.assertEqual(None, Decimal(lte=12, gte=6).errors(decimal.Decimal('6')))
        self.assertEqual(None, Decimal(lte=12, gte=6).errors(decimal.Decimal('12')))

    def test_unicode_decimal(self):
        """
        Tests unicode decimal parsing
        """
        schema = UnicodeDecimal()
        self.assertEqual(
            schema.errors('1.4'),
            [],
        )
        self.assertEqual(
            schema.errors('-3.14159'),
            [],
        )
        self.assertEqual(
            schema.errors(b'-3.14159'),
            [Error('Invalid decimal value (not unicode string)')],
        )
        self.assertEqual(
            schema.errors(b'-3.abc'),
            [Error('Invalid decimal value (not unicode string)')],
        )
        self.assertEqual(
            schema.errors('-3.abc'),
            [Error('Invalid decimal value (parse error)')],
        )
        self.assertEqual(
            schema.errors(-3.14159),
            [Error('Invalid decimal value (not unicode string)')],
        )

    def test_multi_constant(self):
        """
        Tests constants with multiple options
        """
        schema = Constant(42, 36, 81, 9231)
        self.assertEqual(
            schema.errors(9231),
            [],
        )
        self.assertEqual(
            schema.errors(81),
            [],
        )
        self.assertEqual(
            schema.errors(360000),
            [Error('Value is not one of: 36, 42, 81, 9231', code=ERROR_CODE_UNKNOWN)],
        )
