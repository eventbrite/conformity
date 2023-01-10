from __future__ import (
    absolute_import,
    unicode_literals,
)

from collections import OrderedDict
import datetime
import decimal
from typing import (
    AbstractSet,
    Any as AnyType,
    Hashable as HashableType,
    Mapping,
    Sequence as SequenceType,
    Tuple as TupleType,
)
import unittest
import warnings

import freezegun
import pytest
import pytz
import six

from conformity.constants import (
    ERROR_CODE_MISSING,
    ERROR_CODE_UNKNOWN,
)
from conformity.fields import (
    AdditionalCollectionValidator,
    Anything,
    Base,
    Boolean,
    ByteString,
    Constant,
    Date,
    DateTime,
    Decimal,
    Dictionary,
    Float,
    Hashable,
    Integer,
    List,
    SchemalessDictionary,
    Sequence,
    Set,
    Time,
    TimeDelta,
    Tuple,
    TZInfo,
    UnicodeDecimal,
    UnicodeString,
)
from conformity.types import Error

try:
    from unittest import mock
except ImportError:
    import mock  # type: ignore


class FieldTests(unittest.TestCase):
    """
    Tests fields
    """
    def test_integers(self):  # type: () -> None
        schema = Integer(gt=0, lt=10)
        self.assertEqual([], schema.errors(1))
        self.assertEqual([Error('Not an integer')], schema.errors('one'))
        self.assertEqual([Error('Not an integer')], schema.errors(True))
        self.assertEqual([Error('Value not > 0')], schema.errors(0))
        self.assertEqual([Error('Value not < 10')], schema.errors(10))

        schema = Integer(gte=0, lte=10)
        self.assertEqual([Error('Value not >= 0')], schema.errors(-1))
        self.assertEqual([Error('Value not <= 10')], schema.errors(11))

    def test_strings(self):  # type: () -> None
        schema = UnicodeString()
        self.assertEqual([], schema.errors(''))
        self.assertEqual([], schema.errors('Foo bar baz qux foo bar baz qux foo bar baz qux foo bar baz qux foo bar'))
        self.assertEqual([Error('Not a unicode string')], schema.errors(b'Test'))

        schema = UnicodeString(min_length=5, max_length=10)
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(''))
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors('1234'))
        self.assertEqual([], schema.errors('12345'))
        self.assertEqual([], schema.errors('1234567890'))
        self.assertEqual([Error('String must have a length no more than 10')], schema.errors('12345678901'))

        schema = UnicodeString(allow_blank=False)
        self.assertEqual([Error('String cannot be blank')], schema.errors(''))
        self.assertEqual([Error('String cannot be blank')], schema.errors(' '))
        self.assertEqual([Error('String cannot be blank')], schema.errors(' \n '))
        self.assertEqual([], schema.errors('foo'))

        schema = ByteString()
        self.assertEqual([], schema.errors(b''))
        self.assertEqual([], schema.errors(b'Foo bar baz qux foo bar baz qux foo bar baz qux foo bar baz qux foo'))
        self.assertEqual([Error('Not a byte string')], schema.errors('Test'))

        schema = ByteString(min_length=5, max_length=10)
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(b''))
        self.assertEqual([Error('String must have a length of at least 5')], schema.errors(b'1234'))
        self.assertEqual([], schema.errors(b'12345'))
        self.assertEqual([], schema.errors(b'1234567890'))
        self.assertEqual([Error('String must have a length no more than 10')], schema.errors(b'12345678901'))

        with pytest.raises(ValueError):
            UnicodeString(min_length=6, max_length=5)

    def test_complex(self):  # type: () -> None

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
                optional_keys=('line2', 'state'),
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
        self.assertEqual(3, len(introspection['contents']))  # type: ignore
        self.assertIn('child_ids', introspection['contents'])  # type: ignore
        self.assertEqual(
            {
                'type': 'list',
                'contents': {'gt': 0, 'type': 'integer'},
            },
            introspection['contents']['child_ids'],  # type: ignore
        )
        self.assertIn('address', introspection['contents'])  # type: ignore
        self.assertEqual('dictionary', introspection['contents']['address']['type'])  # type: ignore
        self.assertFalse(introspection['contents']['address']['allow_extra_keys'])  # type: ignore
        self.assertEqual({'line2', 'state'}, set(introspection['contents']['address']['optional_keys']))  # type: ignore
        self.assertEqual(
            {
                'city': {'type': 'unicode'},
                'country': {'type': 'unicode'},
                'line1': {'type': 'unicode'},
                'line2': {'type': 'unicode'},
                'postcode': {'type': 'unicode'},
                'state': {'type': 'unicode'},
            },
            introspection['contents']['address']['contents'],  # type: ignore
        )
        self.assertEqual(
            {
                'type': 'set',
                'contents': {'type': 'unicode'},
            },
            introspection['contents']['unique_things'],  # type: ignore
        )

    def test_dictionary_extension(self):  # type: () -> None
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

    def test_dictionary_ordering(self):  # type: () -> None
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

    def test_list(self):  # type: () -> None
        schema = List(UnicodeString(), min_length=4, max_length=8)

        assert schema.errors(['foo', 'bar', 'baz', 'qux']) == []
        assert schema.errors(['foo', 'bar', 'baz']) == [Error('List is shorter than 4')]
        assert schema.errors(
            ['foo', 'bar', 'baz', 'qux', 'foo', 'bar', 'baz', 'qux', 'foo'],
        ) == [Error('List is longer than 8')]

        with pytest.raises(ValueError):
            List(UnicodeString(), min_length=21, max_length=20)

    def test_temporal(self):  # type: () -> None
        past1985 = datetime.datetime(1985, 10, 26, 1, 21, 0)
        past1955 = datetime.datetime(1955, 11, 12, 22, 4, 0)

        datetime_schema = DateTime(gt=past1985)
        date_schema = Date(gt=past1985.date())
        time_schema = Time(gte=datetime.time(8, 0, 0), lte=datetime.time(17, 0, 0))  # "business hours"
        delta_schema = TimeDelta(gt=datetime.timedelta(0))
        negative_delta_schema = TimeDelta(lt=datetime.timedelta(0))
        time_zone_schema = TZInfo()

        self.assertEqual(
            datetime_schema.errors(datetime.datetime.now()),
            [],
        )

        with freezegun.freeze_time():
            self.assertEqual([], datetime_schema.errors(datetime.datetime.now()))

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
                'gt': six.text_type(past1985),
            },
        )

        self.assertEqual(
            date_schema.errors(datetime.date.today()),
            [],
        )

        # datetime is not a valid date
        self.assertEqual(
            date_schema.errors(datetime.datetime.now()),
            [Error('Not a datetime.date instance')],
        )

        with freezegun.freeze_time():
            self.assertEqual([], date_schema.errors(datetime.date.today()))

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
            [],
        )

        self.assertEqual(
            delta_schema.errors(past1955 - past1985),
            [Error('Value not > 0:00:00')],
        )

        self.assertEqual(
            negative_delta_schema.errors(past1955 - past1985),
            [],
        )

        self.assertEqual(
            negative_delta_schema.errors(past1985 - past1955),
            [Error('Value not < 0:00:00')],
        )

        self.assertEqual(
            [Error('Not a datetime.tzinfo instance')],
            time_zone_schema.errors(datetime.datetime.now()),
        )

        self.assertEqual([], time_zone_schema.errors(pytz.timezone(str('America/Chicago'))))

        assert time_schema.errors(datetime.time(12, 0, 0)) == []
        assert time_schema.errors(datetime.time(7, 0, 0)) == [Error('Value not >= 08:00:00')]
        assert time_schema.errors(datetime.time(18, 0, 0)) == [Error('Value not <= 17:00:00')]

        with pytest.raises(TypeError):
            Date(gt=datetime.datetime(2019, 1, 12, 12, 15, 0))

        with pytest.raises(TypeError):
            DateTime(lt=datetime.date(2019, 1, 12))

        with pytest.raises(TypeError):
            Time(gte=datetime.datetime(2019, 1, 12, 12, 15, 0))

        with pytest.raises(TypeError):
            Date(lte=datetime.time(12, 15, 0))

    def test_anything(self):  # type: () -> None
        with pytest.raises(TypeError):
            Anything(b'Not unicode')  # type: ignore

        assert Anything('Test description 1').introspect() == {
            'type': 'anything',
            'description': 'Test description 1',
        }

    def test_hashable(self):  # type: () -> None
        assert Hashable('Another description 2').introspect() == {
            'type': 'hashable',
            'description': 'Another description 2',
        }

        assert Hashable().errors('this is hashable') == []
        assert Hashable().errors({'this', 'is', 'not', 'hashable'}) == [Error('Value is not hashable')]

    def test_schemaless_dict_empty(self):  # type: () -> None
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

    def test_schemaless_dict(self):  # type: () -> None
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

        with pytest.raises(ValueError):
            SchemalessDictionary(Integer(), UnicodeString(), min_length=12, max_length=11)

    def test_tuple(self):  # type: () -> None
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

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Tuple('not a field')  # type: ignore

        with pytest.raises(TypeError):
            Tuple(Integer(gt=0), UnicodeString(), Constant('I love tuples'), description=b'Not a unicode string')

        with pytest.raises(TypeError):
            Tuple(Integer(gt=0), UnicodeString(), Constant('I love tuples'), unsupported='argument')

    def test_dictionary_subclass(self):  # type: () -> None
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
            optional_keys = ('z', )
        schema = Coordinate(description='Where the treasure is')  # type: Base

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

        class Another(Dictionary):
            allow_extra_keys = True
            description = 'Yep'

        schema = Another({'foo': UnicodeString()})
        assert schema.introspect() == {
            'type': 'dictionary',
            'contents': {
                'foo': {
                    'type': 'unicode',
                }
            },
            'description': 'Yep',
            'allow_extra_keys': True,
            'optional_keys': [],
        }

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Another({'foo': UnicodeString()}, optional_keys=1234)  # type: ignore

        class BadDict1(Dictionary):
            allow_extra_keys = 'not a bool'  # type: ignore

        with pytest.raises(TypeError):
            BadDict1(contents={})

        class BadDict2(Dictionary):
            description = b'not a unicode'  # type: ignore

        with pytest.raises(TypeError):
            BadDict2(contents={})

        class BadDict3(Dictionary):
            contents = 'not a dict'  # type: ignore

        with pytest.raises(TypeError):
            BadDict3()

        class ExtraDict(Dictionary):
            contents = {}  # type: ignore
            optional_keys = ('one', 'two')  # type: TupleType[HashableType, ...]

        d = ExtraDict()
        assert d.optional_keys == frozenset({'one', 'two'})

        class ExtraExtraDict(ExtraDict):
            optional_keys = ()  # type: TupleType[HashableType, ...]

        d = ExtraExtraDict()
        assert d.optional_keys == frozenset({})

    def test_decimal(self):  # type: () -> None
        """
        Tests decimal.Decimal object validation
        """
        self.assertEqual([], Decimal().errors(decimal.Decimal('1')))
        self.assertEqual([], Decimal().errors(decimal.Decimal('1.4')))
        self.assertEqual([], Decimal().errors(decimal.Decimal('-3.14159')))
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
        self.assertEqual([], Decimal(lt=12, gt=6).errors(decimal.Decimal('6.1')))
        self.assertEqual([], Decimal(lt=12, gt=6).errors(decimal.Decimal('11.9')))
        self.assertEqual(
            [Error('Value not >= 6')],
            Decimal(lte=12, gte=6).errors(decimal.Decimal('5.9')),
        )
        self.assertEqual(
            [Error('Value not <= 12')],
            Decimal(lte=12, gte=6).errors(decimal.Decimal('12.1')),
        )
        self.assertEqual([], Decimal(lte=12, gte=6).errors(decimal.Decimal('6')))
        self.assertEqual([], Decimal(lte=12, gte=6).errors(decimal.Decimal('12')))

    def test_unicode_decimal(self):  # type: () -> None
        """
        Tests unicode decimal parsing
        """
        schema = UnicodeDecimal(description='Foo description')
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

        assert schema.introspect() == {
            'type': 'unicode_decimal',
            'description': 'Foo description',
        }

    def test_multi_constant(self):  # type: () -> None
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
        self.assertEqual(
            schema.errors([42]),
            [Error('Value is not one of: 36, 42, 81, 9231', code=ERROR_CODE_UNKNOWN)],
        )

        with pytest.raises(TypeError):
            Constant(42, 36, 81, 9231, description='foo', unsupported='bar')

        with pytest.raises(ValueError):
            Constant()

        with pytest.raises(TypeError):
            Constant(42, 36, 81, 9231, description=b'not unicode')

    def test_base(self):  # type: () -> None
        schema = Base()
        assert schema.errors('foo') == [Error('Validation not implemented on base type')]
        with pytest.raises(NotImplementedError):
            schema.introspect()

    def test_base_warnings(self):
        # type: () -> None
        schema = Base()
        assert schema.warnings(mock.MagicMock()) == []

    @mock.patch('conformity.fields.Base.warnings')
    @mock.patch('conformity.fields.Base.errors')
    def test_base_validate(self, mock_errors, mock_warnings):
        schema = Base()
        mock_value = mock.MagicMock()
        validation = schema.validate(mock_value)

        mock_errors.assert_called_once_with(mock_value)
        assert validation.errors == mock_errors.return_value
        mock_warnings.assert_called_once_with(mock_value)
        assert validation.warnings == mock_warnings.return_value


@pytest.mark.parametrize(('kwarg', ), (('gt', ), ('lt', ), ('gte', ), ('lte', )))
def test_tzinfo_deprecated_arguments(kwarg):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always', DeprecationWarning)

        TZInfo(**{kwarg: pytz.timezone('America/Chicago')})  # type: ignore

    assert w
    assert len(w) == 1
    assert issubclass(w[-1].category, DeprecationWarning)
    assert (
        'Arguments `gt`, `gte`, `lt`, and `lte` are deprecated in TZInfo and will be removed in Conformity 2.0.'
    ) in str(w[-1].message)


class TestStructures(object):
    def test_additional_collection_validator(self):
        class V(AdditionalCollectionValidator[list]):
            pass

        with pytest.raises(TypeError) as error_context:
            V()  # type: ignore

        assert 'abstract methods' in error_context.value.args[0]

    def test_list(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            List(UnicodeString(), additional_validator='Not a validator')  # type: ignore

        field = List(UnicodeString())

        assert field.errors(('hello', 'goodbye')) == [Error(message='Not a list')]
        assert field.errors({'hello': 'goodbye'}) == [Error(message='Not a list')]
        assert field.errors({'hello', 'goodbye'}) == [Error(message='Not a list')]
        assert field.errors(['hello', 2]) == [Error(message='Not a unicode string', pointer='1')]
        assert field.errors(['hello', 'goodbye']) == []

        class V(AdditionalCollectionValidator[list]):
            def errors(self, value):
                errors = []
                for i, v in enumerate(value):
                    if v > 500:
                        errors.append(Error('Whoop custom error', pointer='{}'.format(i)))
                return errors

        field = List(Integer(), additional_validator=V())

        assert field.errors([501, 'Not a number dude']) == [Error(message='Not an integer', pointer='1')]
        assert field.errors([501, 499]) == [Error(message='Whoop custom error', pointer='0')]
        assert field.errors([500, 499]) == []

    def test_sequence(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Sequence(UnicodeString(), additional_validator='Not a validator')  # type: ignore

        field = Sequence(UnicodeString())

        assert field.errors({'hello': 'goodbye'}) == [Error(message='Not a sequence')]
        assert field.errors({'hello', 'goodbye'}) == [Error(message='Not a sequence')]
        assert field.errors(['hello', 2]) == [Error(message='Not a unicode string', pointer='1')]
        assert field.errors((1, 'world')) == [Error(message='Not a unicode string', pointer='0')]
        assert field.errors(['hello', 'goodbye']) == []
        assert field.errors(('hello', 'goodbye')) == []

        class V(AdditionalCollectionValidator[SequenceType]):
            def errors(self, value):
                errors = []
                for i, v in enumerate(value):
                    if v > 500:
                        errors.append(Error('Whoop another error', pointer='{}'.format(i)))
                return errors

        field = Sequence(Integer(), additional_validator=V())

        assert field.errors([501, 'Not a number dude']) == [Error(message='Not an integer', pointer='1')]
        assert field.errors([501, 499]) == [Error(message='Whoop another error', pointer='0')]
        assert field.errors((501, 499)) == [Error(message='Whoop another error', pointer='0')]
        assert field.errors([500, 499]) == []
        assert field.errors((500, 499)) == []

    def test_set(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Set(UnicodeString(), additional_validator='Not a validator')  # type: ignore

        field = Set(UnicodeString())

        assert field.errors(('hello', 'goodbye')) == [Error(message='Not a set or frozenset')]
        assert field.errors({'hello': 'goodbye'}) == [Error(message='Not a set or frozenset')]
        assert field.errors(['hello', 'goodbye']) == [Error(message='Not a set or frozenset')]
        assert field.errors({'hello', 2}) == [Error(message='Not a unicode string', pointer='[2]')]
        assert field.errors(frozenset(('hello', 2))) == [Error(message='Not a unicode string', pointer='[2]')]
        assert field.errors({'hello', 'goodbye'}) == []
        assert field.errors(frozenset(('hello', 'goodbye'))) == []

        class V(AdditionalCollectionValidator[AbstractSet]):
            def errors(self, value):
                errors = []
                for v in value:
                    if v > 500:
                        errors.append(Error('Whoop custom error', pointer='{}'.format(v)))
                return errors

        field = Set(Integer(), additional_validator=V())

        assert field.errors({501, 'Not a number'}) == [Error(message='Not an integer', pointer='[Not a number]')]
        assert field.errors({501, 499}) == [Error(message='Whoop custom error', pointer='501')]
        assert field.errors(frozenset((501, 499))) == [Error(message='Whoop custom error', pointer='501')]
        assert field.errors({500, 499}) == []
        assert field.errors(frozenset((500, 499))) == []

    def test_dictionary(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Dictionary({'foo': UnicodeString()}, additional_validator='Not a validator')  # type: ignore

        field = Dictionary({
            'foo': UnicodeString(),
            'bar': Integer(),
            'baz': UnicodeString(),
        })

        assert field.errors(['foo', 'bar', 'baz']) == [Error(message='Not a dict')]
        assert field.errors(('foo', 'bar', 'baz')) == [Error(message='Not a dict')]
        assert field.errors({'foo', 'bar', 'baz'}) == [Error(message='Not a dict')]
        assert field.errors({'foo': 'Hello', 'bar': 12, 'baz': True}) == [
            Error(message='Not a unicode string', pointer='baz'),
        ]
        assert field.errors({'foo': 'Hello', 'bar': 12, 'baz': 'Goodbye'}) == []

        class V(AdditionalCollectionValidator[Mapping[HashableType, AnyType]]):
            def errors(self, value):
                if value['foo'] != value['baz']:
                    return [Error('Value foo does not match value baz', pointer='foo')]
                return []

        field = field.extend(additional_validator=V())

        assert field.errors({'foo': 'Hello', 'bar': 12, 'baz': 'Goodbye'}) == [
            Error(message='Value foo does not match value baz', pointer='foo'),
        ]
        assert field.errors({'foo': 'Hello', 'bar': 12, 'baz': 'Hello'}) == []

    def test_schemaless_dictionary(self):
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            SchemalessDictionary(
                key_type=UnicodeString(),
                value_type=Integer(),
                additional_validator='Not a validator',  # type: ignore
            )

        field = SchemalessDictionary(key_type=UnicodeString(), value_type=Integer())

        assert field.errors(['foo', 'bar', 'baz']) == [Error(message='Not a dict')]
        assert field.errors(('foo', 'bar', 'baz')) == [Error(message='Not a dict')]
        assert field.errors({'foo', 'bar', 'baz'}) == [Error(message='Not a dict')]
        assert field.errors({'foo': 42, 'bar': 11, 'baz': 'Goodbye'}) == [
            Error(message='Not an integer', pointer='baz'),
        ]
        assert field.errors({'foo': 42, 'bar': 11, 'baz': 91}) == []

        class V(AdditionalCollectionValidator[Mapping[HashableType, AnyType]]):
            def errors(self, value):
                if value['foo'] != value['baz']:
                    return [Error('Value foo does not match value baz', pointer='foo')]
                return []

        field = SchemalessDictionary(key_type=UnicodeString(), value_type=Integer(), additional_validator=V())

        assert field.errors({'foo': 42, 'bar': 11, 'baz': 91}) == [
            Error(message='Value foo does not match value baz', pointer='foo'),
        ]
        assert field.errors({'foo': 42, 'bar': 11, 'baz': 42}) == []

    def test_tuple(self):
        with pytest.raises(TypeError):
            Tuple(UnicodeString(), Integer(), Boolean(), additional_validator='Not a validator')  # type: ignore

        field = Tuple(UnicodeString(), Integer(), Boolean())

        assert field.errors(['foo', 'bar', 'baz']) == [Error(message='Not a tuple')]
        assert field.errors({'foo': 'bar'}) == [Error(message='Not a tuple')]
        assert field.errors({'foo', 'bar', 'baz'}) == [Error(message='Not a tuple')]
        assert field.errors(('foo', 'bar', True)) == [Error(message='Not an integer', pointer='1')]
        assert field.errors(('foo', 12, False)) == []
        assert field.errors(('foo', 12, True)) == []

        class V(AdditionalCollectionValidator[TupleType[AnyType]]):
            def errors(self, value):
                if value[2] is not True:
                    return [Error('The third value must be True', pointer='2')]
                return []

        field = Tuple(UnicodeString(), Integer(), Boolean(), additional_validator=V())

        assert field.errors(('foo', 12, False)) == [Error(message='The third value must be True', pointer='2')]
        assert field.errors(('foo', 12, True)) == []
