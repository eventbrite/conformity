"""
This file simply instantiates every field with all possible arguments, so that running `mypy .` at the root of the
project will cause all of our type hints to be validated. This is just a second-line sanity check to make sure all
valid ways of instantiating fields pass MyPy verification.
"""
from __future__ import (
    absolute_import,
    unicode_literals,
)

import datetime
import decimal

from conformity.fields import (
    All,
    Any,
    Anything,
    Boolean,
    BooleanValidator,
    ByteString,
    ClassConfigurationSchema,
    Constant,
    Date,
    DateTime,
    Decimal,
    Dictionary,
    EmailAddress,
    Float,
    Hashable,
    Integer,
    IPAddress,
    IPv4Address,
    IPv6Address,
    Latitude,
    List,
    Longitude,
    Null,
    Nullable,
    ObjectInstance,
    Polymorph,
    SchemalessDictionary,
    Set,
    Time,
    TimeDelta,
    Tuple,
    TypePath,
    TypeReference,
    TZInfo,
    UnicodeDecimal,
    UnicodeString,
)


All(Boolean(), UnicodeString(), description='Hello, world')

Any(Boolean(), UnicodeString(), description='Hello, world')

Anything(description='Hello, world')

Boolean(description='Hello, world')

BooleanValidator(
    validator=lambda x: x == 'run, Forrest, run',
    validator_description='This is the way the validator works',
    error='This is the error message',
    description='Hello, world',
)

ByteString(
    min_length=1,
    max_length=12,
    description='Hello, world',
    allow_blank=True,
)

ClassConfigurationSchema(
    base_class=datetime.datetime,
    default_path='com.foo.Something',
    description='Hello, world',
    eager_default_validation=False,
    add_class_object_to_dict=False,
)

Constant('value1', 'value2', 'value3', description='Hello, world')

Date(
    gt=datetime.date(2018, 12, 31),
    gte=datetime.date(2019, 1, 1),
    lt=datetime.date(2020, 1, 1),
    lte=datetime.date(2019, 12, 31),
    description='Hello, world',
)

DateTime(
    gt=datetime.datetime(2018, 12, 31, 23, 59, 59),
    gte=datetime.datetime(2019, 1, 1, 0, 0, 0),
    lt=datetime.datetime(2020, 1, 1, 0, 0, 0),
    lte=datetime.datetime(2019, 12, 31, 23, 59, 59),
    description='Hello, world',
)

Decimal(
    gt=1,
    gte=2,
    lt=21,
    lte=20,
    description='Hello, world',
)

Dictionary(
    contents={'baz': Nullable(UnicodeString()), 'qux': Boolean()},
    optional_keys=('qux', ),
)
Dictionary(
    contents={'baz': UnicodeString(), 'qux': Boolean()},
    optional_keys=frozenset({'qux'}),
    allow_extra_keys=True,
    description='Hello, world',
)

EmailAddress(
    whitelist=['eventbrite.com'],
    description='Hello, world',
)

Float(
    gt=1.9999999,
    gte=2.0,
    lt=21.0,
    lte=20.999999,
    description='Hello, world',
)

Hashable(description='Hello, world')

Integer(
    gt=decimal.Decimal('1'),
    gte=decimal.Decimal('2'),
    lt=decimal.Decimal('21'),
    lte=decimal.Decimal('22'),
    description='Hello, world',
)

IPAddress(description='Hello, world')

IPv4Address(description='Hello, world', allow_blank=True)

IPv6Address(description='Hello, world', allow_blank=False)

Latitude(
    gt=4.45,
    gte=4.46,
    lt=85.05,
    lte=85.04,
    description='Hello, world',
)

List(
    UnicodeString(),
    min_length=5,
    max_length=100,
    description='Hello, world',
)
List(
    Nullable(Integer()),
    min_length=5,
    max_length=100,
    description='Hello, world',
)

Longitude(
    gt=4.45,
    gte=4.46,
    lt=85.05,
    lte=85.04,
    description='Hello, world',
)

Null()

Nullable(Boolean())
Nullable(Latitude())
Nullable(Tuple(Latitude(), Longitude()))

ObjectInstance(datetime.datetime, description='Hello, world')
ObjectInstance((datetime.date, datetime.datetime, datetime.time), description='Hello world')

Polymorph(
    switch_field='path',
    contents_map={
        'com.foo': Dictionary({'path': UnicodeString(), 'foo': Boolean()}),
        'com.bar': Dictionary({'path': UnicodeString(), 'bar': Integer()}),
    },
    description='Hello, world',
)

SchemalessDictionary(
    key_type=UnicodeString(),
    value_type=Integer(),
    min_length=5,
    max_length=20,
    description='Hello, world',
)

Set(
    UnicodeString(),
    min_length=5,
    max_length=20,
    description='Hello, world',
)

Time(
    gt=datetime.time(23, 59, 59),
    gte=datetime.time(0, 0, 0),
    lt=datetime.time(0, 0, 0),
    lte=datetime.time(23, 59, 59),
    description='Hello, world',
)

TimeDelta(
    gt=datetime.timedelta(seconds=30),
    gte=datetime.timedelta(seconds=31),
    lt=datetime.timedelta(hours=24),
    lte=datetime.timedelta(hours=23, minutes=59, seconds=59),
    description='Hello, world',
)

TypePath(datetime.date, description='Hello, world')
TypePath((datetime.date, datetime.datetime, datetime.time), description='Hello, world')

TypeReference(datetime.date, description='Hello, world')
TypeReference((datetime.date, datetime.datetime, datetime.time), description='Hello, world')

TZInfo(description='Hello, world')

UnicodeDecimal(description='Hello, world')

UnicodeString(
    min_length=1,
    max_length=12,
    description='Hello, world',
    allow_blank=True,
)
