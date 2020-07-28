from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (
    Any as AnyType,
    Dict,
    Hashable as HashableType,
    Mapping,
)
import unittest

import pytest
import six

from conformity.constants import WARNING_CODE_FIELD_DEPRECATED
from conformity.error import ValidationError
from conformity.fields import (
    All,
    Any,
    Boolean,
    BooleanValidator,
    ClassConfigurationSchema,
    Constant,
    Deprecated,
    Dictionary,
    Integer,
    Null,
    Nullable,
    ObjectInstance,
    Polymorph,
    PythonPath,
    SchemalessDictionary,
    TypePath,
    TypeReference,
    UnicodeString,
)
from conformity.types import Error


class MetaFieldTests(unittest.TestCase):
    """
    Tests meta fields
    """

    def test_nullable(self):  # type: () -> None
        constant = Constant('one', 'two')
        schema = Nullable(constant)
        self.assertEqual([], schema.errors(None))
        self.assertEqual([], schema.errors('one'))
        self.assertEqual([], schema.errors('two'))
        self.assertEqual(1, len(schema.errors('three')))
        self.assertEqual({'type': 'nullable', 'nullable': constant.introspect()}, schema.introspect())

        boolean = Boolean(description='This is a test description')
        schema = Nullable(boolean)
        self.assertEqual([], schema.errors(None))
        self.assertEqual([], schema.errors(True))
        self.assertEqual([], schema.errors(False))
        self.assertEqual(1, len(schema.errors('true')))
        self.assertEqual(1, len(schema.errors(1)))
        self.assertEqual({'type': 'nullable', 'nullable': boolean.introspect()}, schema.introspect())

        string = UnicodeString()
        schema = Nullable(string)
        self.assertEqual([], schema.errors(None))
        self.assertEqual([], schema.errors('hello, world'))
        self.assertEqual(1, len(schema.errors(b'hello, world')))
        self.assertEqual({'type': 'nullable', 'nullable': string.introspect()}, schema.introspect())

    def test_null(self):  # type: () -> None
        null = Null()
        assert null.errors(None) == []
        assert null.errors('something') == [Error('Value is not null')]
        assert null.introspect() == {'type': 'null'}

    def test_any(self):  # type: () -> None
        schema = Any(Constant('one'), Constant('two'))
        self.assertEqual(
            schema.errors('one'),
            [],
        )
        self.assertEqual(
            schema.errors('two'),
            [],
        )
        self.assertEqual(
            len(schema.errors('three')),
            2,
        )

        assert schema.introspect() == {
            'type': 'any',
            'options': [
                {'type': 'constant', 'values': ['one']},
                {'type': 'constant', 'values': ['two']},
            ]
        }

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            Any('not a field')  # type: ignore

        with pytest.raises(TypeError):
            Any(Constant('one'), Constant('two'), description=b'Not unicode')

        with pytest.raises(TypeError):
            Any(Constant('one'), Constant('two'), unsupported='argument')

    def test_all(self):  # type: () -> None
        schema = All(Constant('one'), UnicodeString())
        self.assertEqual(
            schema.errors('one'),
            [],
        )
        self.assertEqual(
            len(schema.errors('two')),
            1,
        )

        assert schema.introspect() == {
            'type': 'all',
            'requirements': [
                {'type': 'constant', 'values': ['one']},
                {'type': 'unicode'},
            ]
        }

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            All('not a field')  # type: ignore

        with pytest.raises(TypeError):
            All(Constant('one'), UnicodeString(), description=b'Not unicode')

        with pytest.raises(TypeError):
            All(Constant('one'), UnicodeString(), unsupported='argument')

    def test_object_instance(self):  # type: () -> None
        class Thing(object):
            pass

        class Thingy(Thing):
            pass

        class SomethingElse(object):
            pass

        schema = ObjectInstance(Thing, description='Yessiree')

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
            [Error('Not an instance of Thing')]
        )

        assert schema.introspect() == {
            'type': 'object_instance',
            'description': 'Yessiree',
            'valid_type': repr(Thing),
        }

        schema = ObjectInstance((Thing, SomethingElse))
        assert schema.errors(Thing()) == []
        assert schema.errors(Thingy()) == []
        assert schema.errors(SomethingElse()) == []

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            ObjectInstance('not a type')  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            ObjectInstance((Thing, SomethingElse, 'also not a type'))  # type: ignore

    def test_polymorph(self):  # type: () -> None

        card = Dictionary({
            'payment_type': Constant('card', 'credit'),
            'number': UnicodeString(),
            'cvc': UnicodeString(description='Card Verification Code'),
        })

        bankacc = Dictionary({
            'payment_type': Constant('bankacc'),
            'routing': UnicodeString(description='US RTN or foreign equivalent'),
            'account': UnicodeString(),
        })

        schema = Polymorph(
            'payment_type',
            {
                'card': card,
                'bankacc': bankacc,
            },
        )

        self.assertEqual(
            schema.errors({
                'payment_type': 'card',
                'number': '1234567890123456',
                'cvc': '000',
            }),
            [],
        )

        self.assertEqual(
            schema.errors({
                'payment_type': 'bankacc',
                'routing': '13456790',
                'account': '13910399',
            }),
            [],
        )

        assert schema.errors(
            {
                'payment_type': 'credit',
                'number': '1234567890123456',
                'cvc': '000',
            }
        ) == [Error("Invalid switch value 'credit'", code='UNKNOWN')]

        self.maxDiff = 2000
        self.assertEqual(
            schema.introspect(),
            {
                'type': 'polymorph',
                'contents_map': {
                    'bankacc': {
                        'type': 'dictionary',
                        'allow_extra_keys': False,
                        'contents': {
                            'account': {'type': 'unicode'},
                            'payment_type': {
                                'type': 'constant',
                                'values': ['bankacc'],
                            },
                            'routing': {
                                'type': 'unicode',
                                'description': 'US RTN or foreign equivalent',
                            },
                        },
                        'optional_keys': [],
                    },
                    'card': {
                        'type': 'dictionary',
                        'allow_extra_keys': False,
                        'contents': {
                            'cvc': {
                                'type': 'unicode',
                                'description': 'Card Verification Code',
                            },
                            'number': {'type': 'unicode'},
                            'payment_type': {
                                'type': 'constant',
                                'values': ['card', 'credit'],
                            },
                        },
                        'optional_keys': [],
                    },
                },
                'switch_field': 'payment_type',
            },
        )

        schema = Polymorph(
            'payment_type',
            {
                'card': card,
                'bankacc': bankacc,
                '__default__': card,
            },
        )
        assert schema.errors(
            {
                'payment_type': 'credit',
                'number': '1234567890123456',
                'cvc': '000',
            }
        ) == []

    def test_boolean_validator(self):  # type: () -> None
        schema = BooleanValidator(
            lambda x: x.isdigit(),
            'str.isdigit()',
            'Not all digits',
        )
        # Test valid unicode and byte strings
        self.assertEqual(
            schema.errors('123'),
            [],
        )
        self.assertEqual(
            schema.errors(b'123'),
            [],
        )
        # Test invalid unicode and byte strings
        self.assertEqual(
            len(schema.errors('123a')),
            1,
        )
        self.assertEqual(
            len(schema.errors(b'123a')),
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
                'type': 'boolean_validator',
                'validator': 'str.isdigit()',
            },
        )

    def test_type_reference(self):  # type: () -> None
        schema = TypeReference(description='This is a test')
        assert schema.errors(Foo) == []
        assert schema.errors(Bar) == []
        assert schema.errors(Baz) == []
        assert schema.errors(Qux) == []
        assert schema.errors(Foo()) == [Error('Not a type')]
        assert schema.introspect() == {'type': 'type_reference', 'description': 'This is a test'}

        schema = TypeReference(base_classes=Foo)
        assert schema.errors(Foo) == []
        assert schema.errors(Bar) == []
        assert schema.errors(Baz) == [Error('Type {} is not one of or a subclass of one of: {}'.format(Baz, Foo))]
        assert schema.errors(Qux) == [Error('Type {} is not one of or a subclass of one of: {}'.format(Qux, Foo))]
        assert schema.introspect() == {'type': 'type_reference', 'base_classes': [six.text_type(Foo)]}

        schema = TypeReference(base_classes=(Foo, Baz))
        assert schema.errors(Foo) == []
        assert schema.errors(Bar) == []
        assert schema.errors(Baz) == []
        assert schema.errors(Qux) == [
            Error('Type {} is not one of or a subclass of one of: ({}, {})'.format(Qux, Foo, Baz)),
        ]
        assert schema.introspect() == {
            'type': 'type_reference',
            'base_classes': [six.text_type(Foo), six.text_type(Baz)],
        }

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            TypeReference(base_classes='not a type')  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            TypeReference(base_classes=(Foo, Baz, 'not a type'))  # type: ignore

    def test_type_path(self):  # type: () -> None
        schema = TypePath(description='This is another test')
        assert schema.errors(b'Nope nope nope') == [Error('Not a unicode string')]
        assert schema.errors('Nope nope nope') == [Error('Value "Nope nope nope" is not a valid Python import path')]
        assert schema.errors('foo.bar:Hello') == [
            Error('ImportError: No module named foo.bar' if six.PY2 else "ImportError: No module named 'foo'")
        ]
        assert schema.errors('conformity.fields:NotARealField') == [
            Error(
                "AttributeError: 'module' object has no attribute 'NotARealField'" if six.PY2 else
                "AttributeError: module 'conformity.fields' has no attribute 'NotARealField'"
            )
        ]
        assert schema.errors('conformity.fields:UnicodeString') == []
        assert schema.errors('conformity.fields.UnicodeString') == []
        assert schema.errors('conformity.fields.ByteString') == []
        assert schema.errors('conformity.fields:ByteString') == []
        assert schema.errors('tests.test_fields_meta.Foo') == []
        assert schema.errors('tests.test_fields_meta.Bar') == []
        assert schema.errors('tests.test_fields_meta.Baz') == []
        assert schema.errors('tests.test_fields_meta.Qux') == []
        assert schema.errors('tests.test_fields_meta:Qux.InnerQux') == []

        schema = TypePath(base_classes=Foo)
        assert schema.errors('tests.test_fields_meta.Foo') == []
        assert schema.errors('tests.test_fields_meta.Bar') == []
        assert schema.errors('tests.test_fields_meta.Baz') == [
            Error('Type {} is not one of or a subclass of one of: {}'.format(Baz, Foo)),
        ]
        assert schema.errors('conformity.fields.UnicodeString') == [
            Error('Type {} is not one of or a subclass of one of: {}'.format(
                TypePath.resolve_python_path('conformity.fields.UnicodeString'),
                Foo,
            )),
        ]
        assert schema.introspect() == {
            'type': 'python_path',
            'value_schema': {
                'type': 'type_reference',
                'base_classes': [six.text_type(Foo)],
            }
        }

        assert TypePath.resolve_python_path('tests.test_fields_meta.Qux') == Qux
        assert TypePath.resolve_python_path('tests.test_fields_meta:Qux.InnerQux') == Qux.InnerQux

    def test_python_path(self):  # type: () -> None
        schema = PythonPath()
        assert schema.errors('tests.test_fields_meta.MY_FOO') == []
        assert schema.errors('tests.test_fields_meta.MY_BAR') == []
        assert schema.errors('tests.test_fields_meta:MY_QUX') == []
        assert schema.errors('tests.test_fields_meta.MY_DICT') == []
        assert schema.errors('tests.test_fields_meta:Qux.INNER_CONSTANT') == []

        schema = PythonPath(ObjectInstance(Foo))
        assert schema.errors('tests.test_fields_meta.MY_FOO') == []
        assert schema.errors('tests.test_fields_meta.MY_BAR') == []
        assert schema.errors('tests.test_fields_meta:MY_QUX') == [Error('Not an instance of Foo')]
        assert schema.errors('tests.test_fields_meta.MY_DICT') == [Error('Not an instance of Foo')]
        assert schema.errors('tests.test_fields_meta:Qux.INNER_CONSTANT') == [Error('Not an instance of Foo')]

        schema = PythonPath(SchemalessDictionary())
        assert schema.errors('tests.test_fields_meta.MY_DICT') == []
        assert schema.errors('tests.test_fields_meta:MY_QUX') == [Error('Not a dict')]

        schema = PythonPath(UnicodeString())
        assert schema.errors('tests.test_fields_meta:Qux.INNER_CONSTANT') == []
        assert schema.errors('tests.test_fields_meta.MY_DICT') == [Error('Not a unicode string')]


class Foo(object):
    pass


class Bar(Foo):
    pass


class Baz(object):
    pass


class Qux(object):
    INNER_CONSTANT = 'hello'

    class InnerQux(object):
        pass


MY_FOO = Foo()
MY_BAR = Bar()
MY_QUX = Qux()
MY_DICT = {'foo': 'bar', 'baz': 'qux'}


class TestClassConfigurationSchema(object):
    def test_provider_decorator(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            ClassConfigurationSchema.provider(Boolean())  # type: ignore

        schema = Dictionary({})

        decorator = ClassConfigurationSchema.provider(schema)

        class IsAClass(object):
            pass

        def is_not_a_class():
            pass

        with pytest.raises(TypeError):
            decorator(is_not_a_class)  # type: ignore

        cls = decorator(IsAClass)
        assert cls is IsAClass
        assert getattr(cls, '_conformity_initialization_schema') is schema

        another_schema = Dictionary({})

        @ClassConfigurationSchema.provider(another_schema)
        class Sample(object):
            pass

        assert getattr(Sample, '_conformity_initialization_schema') is another_schema

    def test_inline_definition_no_default_or_base_class(self):  # type: () -> None
        schema = ClassConfigurationSchema()

        assert schema.errors('Not a dict') == [Error('Not a mapping (dictionary)')]
        assert schema.errors(
            {'foo': 'bar', 'baz': 'qux', 'path': 'unprocessed', 'kwargs': {}, 'object': Foo}
        ) == [Error('Extra keys present: baz, foo', code='UNKNOWN')]
        assert schema.errors({}) == [
            Error('Missing key (and no default specified): path', code='MISSING', pointer='path'),
        ]
        assert schema.errors({'path': 'foo.bar:Hello'}) == [Error(
            'ImportError: No module named foo.bar' if six.PY2 else "ImportError: No module named 'foo'",
            pointer='path',
        )]
        assert schema.errors({'path': 'tests.test_fields_meta.Foo'}) == [Error(
            "Neither class 'tests.test_fields_meta.Foo' nor one of its superclasses was decorated with "
            "@ClassConfigurationSchema.provider",
            pointer='path',
        )]
        assert schema.errors({'path': 'tests.test_fields_meta:InvalidProvider'}) == [Error(
            "Class 'tests.test_fields_meta:InvalidProvider' attribute '_conformity_initialization_schema' should be a "
            "Dictionary or SchemalessDictionary Conformity field or one of their subclasses",
            pointer='path',
        )]

        config = {'path': 'tests.test_fields_meta:BasicProvider'}  # type: Dict[HashableType, AnyType]
        assert sorted(schema.errors(config)) == [
            Error('Missing key: bar', code='MISSING', pointer='kwargs.bar'),
            Error('Missing key: foo', code='MISSING', pointer='kwargs.foo'),
        ]
        assert config['object'] == BasicProvider

        with pytest.raises(ValidationError) as error_context:
            # noinspection PyTypeChecker
            schema.instantiate_from('Not a dict')  # type: ignore
        assert error_context.value.args[0] == [Error('Not a mutable mapping (dictionary)')]

        config = {'path': 'tests.test_fields_meta:BasicProvider'}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert sorted(error_context.value.args[0]) == [
            Error('Missing key: bar', code='MISSING', pointer='kwargs.bar'),
            Error('Missing key: foo', code='MISSING', pointer='kwargs.foo'),
        ]
        assert config['object'] == BasicProvider

        config = {'path': 'tests.test_fields_meta:BasicProvider', 'kwargs': {'foo': 'Fine', 'bar': 'Bad'}}
        assert schema.errors(config) == [Error('Not a boolean', pointer='kwargs.bar')]
        assert config['object'] == BasicProvider

        config = {'path': 'tests.test_fields_meta:BasicProvider', 'kwargs': {'foo': 'Fine', 'bar': 'Bad'}}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [Error('Not a boolean', pointer='kwargs.bar')]
        assert config['object'] == BasicProvider

        config = {'path': 'tests.test_fields_meta:BasicProvider', 'kwargs': {'foo': 'Fine', 'bar': True}}
        assert schema.errors(config) == []
        assert config['object'] == BasicProvider

        config = {'path': 'tests.test_fields_meta:BasicProvider', 'kwargs': {'foo': 'Fine', 'bar': True}}
        value = schema.instantiate_from(config)
        assert isinstance(value, BasicProvider)
        assert value.foo == 'Fine'
        assert value.bar is True
        assert config['object'] == BasicProvider

        schema = ClassConfigurationSchema()
        with pytest.raises(ValidationError):
            schema.initiate_cache_for('foo.bar:Hello')
        schema.initiate_cache_for('tests.test_fields_meta.BasicProvider')
        schema.initiate_cache_for('tests.test_fields_meta:BasicProvider')
        assert schema.introspect() == {
            'type': 'class_config_dictionary',
            'base_class': 'object',
            'switch_field': 'path',
            'switch_field_schema': TypePath(base_classes=object).introspect(),
            'kwargs_field': 'kwargs',
            'kwargs_contents_map': {
                'tests.test_fields_meta.BasicProvider': Dictionary(
                    {'foo': UnicodeString(), 'bar': Boolean()},
                ).introspect(),
                'tests.test_fields_meta:BasicProvider': Dictionary(
                    {'foo': UnicodeString(), 'bar': Boolean()},
                ).introspect(),
            },
        }

        schema = ClassConfigurationSchema(add_class_object_to_dict=False)
        config = {'path': 'tests.test_fields_meta:BasicProvider', 'kwargs': {'foo': 'Fine', 'bar': True}}
        value = schema.instantiate_from(config)
        assert isinstance(value, BasicProvider)
        assert value.foo == 'Fine'
        assert value.bar is True
        assert 'object' not in config

    def test_inline_definition_with_default_and_base_class(self):  # type: () -> None
        schema = ClassConfigurationSchema(
            base_class=BaseSomething,
            default_path='tests.test_fields_meta:SpecificSomething',
        )

        config = {}  # type: dict
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert sorted(error_context.value.args[0]) == [
            Error('Missing key: bar', code='MISSING', pointer='kwargs.bar'),
            Error('Missing key: foo', code='MISSING', pointer='kwargs.foo'),
        ]
        assert config['path'] == 'tests.test_fields_meta:SpecificSomething'
        assert config['object'] == SpecificSomething

        value = schema.instantiate_from({'kwargs': {'foo': True, 'bar': 'walk'}})
        assert isinstance(value, SpecificSomething)
        assert value.foo is True
        assert value.bar == 'walk'

        config = {'path': 'tests.test_fields_meta.AnotherSomething'}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [
            Error('Missing key: baz', code='MISSING', pointer='kwargs.baz'),
        ]
        assert config['object'] == AnotherSomething

        config = {'path': 'tests.test_fields_meta.ExtendedAnotherSomething'}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [
            Error('Missing key: baz', code='MISSING', pointer='kwargs.baz'),
        ]
        assert config['object'] == ExtendedAnotherSomething

        config = {'path': 'tests.test_fields_meta.OverridingAnotherSomething'}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [
            Error('Missing key: no_baz', code='MISSING', pointer='kwargs.no_baz'),
        ]
        assert config['object'] == OverridingAnotherSomething

        config = {'path': 'tests.test_fields_meta.AnotherSomething', 'kwargs': {'baz': None}}
        value = schema.instantiate_from(config)
        assert isinstance(value, AnotherSomething)
        assert value.baz is None
        assert value.qux == 'unset'
        assert config['object'] == AnotherSomething

        config = {'path': 'tests.test_fields_meta.AnotherSomething', 'kwargs': {'baz': 'cool', 'qux': False}}
        value = schema.instantiate_from(config)
        assert isinstance(value, AnotherSomething)
        assert value.baz == 'cool'
        assert value.qux is False
        assert config['object'] == AnotherSomething

        config = {'path': 'tests.test_fields_meta.ExtendedAnotherSomething', 'kwargs': {'baz': 'cool', 'qux': False}}
        value = schema.instantiate_from(config)
        assert isinstance(value, ExtendedAnotherSomething)
        assert value.baz == 'cool'
        assert value.qux is False
        assert config['object'] == ExtendedAnotherSomething

        config = {'path': 'tests.test_fields_meta.OverridingAnotherSomething', 'kwargs': {'no_baz': 'very cool'}}
        value = schema.instantiate_from(config)
        assert isinstance(value, OverridingAnotherSomething)
        assert value.baz == 'very cool'
        assert value.qux == 'no_unset'
        assert config['object'] == OverridingAnotherSomething

    def test_subclass_definition(self):  # type: () -> None
        class ImmutableDict(Mapping):
            def __init__(self, underlying):
                self.underlying = underlying

            def __contains__(self, item):
                return item in self.underlying

            def __getitem__(self, k):
                return self.underlying[k]

            def get(self, k, default=None):
                return self.underlying.get(k, default)

            def __iter__(self):
                return iter(self.underlying)

            def __len__(self):
                return len(self.underlying)

            def keys(self):
                return self.underlying.keys()

            def items(self):
                return self.underlying.items()

            def values(self):
                return self.underlying.values()

        class ExtendedSchema(ClassConfigurationSchema):
            base_class = BaseSomething
            default_path = 'tests.test_fields_meta.AnotherSomething'
            description = 'Neat-o schema thing'

        schema = ExtendedSchema()

        config = {}  # type: dict
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [
            Error('Missing key: baz', code='MISSING', pointer='kwargs.baz'),
        ]
        assert config['object'] == AnotherSomething

        config = {'kwargs': {'baz': None}}
        value = schema.instantiate_from(config)
        assert isinstance(value, AnotherSomething)
        assert value.baz is None
        assert value.qux == 'unset'
        assert config['object'] == AnotherSomething

        config2 = ImmutableDict({'kwargs': {'baz': None}})
        assert schema.errors(config2) == []
        assert 'object' not in config2

        assert schema.introspect() == {
            'type': 'class_config_dictionary',
            'description': 'Neat-o schema thing',
            'default_path': 'tests.test_fields_meta.AnotherSomething',
            'base_class': 'BaseSomething',
            'switch_field': 'path',
            'switch_field_schema': TypePath(base_classes=BaseSomething).introspect(),
            'kwargs_field': 'kwargs',
            'kwargs_contents_map': {
                'tests.test_fields_meta.AnotherSomething': Dictionary(
                    {'baz': Nullable(UnicodeString()), 'qux': Boolean()},
                    optional_keys=('qux', ),
                ).introspect(),
            },
        }

    def test_schemaless(self):  # type: () -> None
        schema = ClassConfigurationSchema(base_class=BaseSomething)

        config = {'path': 'tests.test_fields_meta:SomethingWithJustKwargs'}  # type: dict
        value = schema.instantiate_from(config)
        assert config['object'] == SomethingWithJustKwargs
        assert isinstance(value, SomethingWithJustKwargs)
        assert value.kwargs == {}

        config = {
            'path': 'tests.test_fields_meta:SomethingWithJustKwargs',
            'kwargs': {'dog': 'Bree', 'cute': True, 'cat': b'Pumpkin'},
        }
        value = schema.instantiate_from(config)
        assert config['object'] == SomethingWithJustKwargs
        assert isinstance(value, SomethingWithJustKwargs)
        assert value.kwargs == {'dog': 'Bree', 'cute': True, 'cat': b'Pumpkin'}

        config = {'path': 'tests.test_fields_meta:SomethingWithJustKwargs', 'kwargs': {b'Not unicode': False}}
        with pytest.raises(ValidationError) as error_context:
            schema.instantiate_from(config)
        assert error_context.value.args[0] == [
            Error('Not a unicode string', code='INVALID', pointer='kwargs.Not unicode') if six.PY2 else
            Error('Not a unicode string', code='INVALID', pointer='kwargs.{!r}'.format(b'Not unicode'))
        ]
        assert config['object'] == SomethingWithJustKwargs


class InvalidProvider(object):
    _conformity_initialization_schema = Boolean()


@ClassConfigurationSchema.provider(Dictionary({'foo': UnicodeString(), 'bar': Boolean()}))
class BasicProvider(object):
    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar


class BaseSomething(object):
    pass


@ClassConfigurationSchema.provider(Dictionary({'foo': Boolean(), 'bar': Constant('walk', 'run')}))
class SpecificSomething(BaseSomething):
    def __init__(self, foo, bar):
        self.foo = foo
        self.bar = bar


@ClassConfigurationSchema.provider(
    Dictionary({'baz': Nullable(UnicodeString()), 'qux': Boolean()}, optional_keys=('qux', )),
)
class AnotherSomething(BaseSomething):
    def __init__(self, baz, qux='unset'):
        self.baz = baz
        self.qux = qux


class ExtendedAnotherSomething(AnotherSomething):
    pass


@ClassConfigurationSchema.provider(
    Dictionary({'no_baz': Nullable(UnicodeString()), 'no_qux': Boolean()}, optional_keys=('no_qux', )),
)
class OverridingAnotherSomething(AnotherSomething):
    def __init__(self, no_baz, no_qux='no_unset'):
        super(OverridingAnotherSomething, self).__init__(baz=no_baz, qux=no_qux)


@ClassConfigurationSchema.provider(SchemalessDictionary(key_type=UnicodeString(), value_type=Any()))
class SomethingWithJustKwargs(BaseSomething):
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class TestDeprecatedField(object):
    def test_warnings_returns_field_deprecation_warning(self):
        field = Deprecated(Integer(), 'This field has been deprecated')
        warnings = field.warnings(1)
        assert len(warnings) == 1
        assert warnings[0].code == WARNING_CODE_FIELD_DEPRECATED
        assert warnings[0].message == field.message

    def test_introspect_adds_deprecated_field(self):
        field = Deprecated(Integer(), 'This field has been deprecated')
        introspection = field.introspect()
        assert 'deprecated' in introspection
        assert introspection['deprecated'] is True
