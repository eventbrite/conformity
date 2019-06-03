from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

import pytest
import six

from conformity.error import Error
from conformity.fields import (
    All,
    Any,
    Boolean,
    BooleanValidator,
    Constant,
    Dictionary,
    Null,
    Nullable,
    ObjectInstance,
    Polymorph,
    TypePath,
    TypeReference,
    UnicodeString,
)


class MetaFieldTests(unittest.TestCase):
    """
    Tests meta fields
    """

    def test_nullable(self):
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

    def test_null(self):
        null = Null()
        assert null.errors(None) == []
        assert null.errors('something') == [Error('Value is not null')]
        assert null.introspect() == {'type': 'null'}

    def test_any(self):
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
            Any('not a field')

        with pytest.raises(TypeError):
            Any(Constant('one'), Constant('two'), description=b'Not unicode')

        with pytest.raises(TypeError):
            Any(Constant('one'), Constant('two'), unsupported='argument')

    def test_all(self):
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
            All('not a field')

        with pytest.raises(TypeError):
            All(Constant('one'), UnicodeString(), description=b'Not unicode')

        with pytest.raises(TypeError):
            All(Constant('one'), UnicodeString(), unsupported='argument')

    def test_object_instance(self):
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
            ObjectInstance('not a type')

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            ObjectInstance((Thing, SomethingElse, 'also not a type'))

    def test_polymorph(self):

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

    def test_boolean_validator(self):
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

    def test_type_reference(self):
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
            TypeReference(base_classes='not a type')

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            TypeReference(base_classes=(Foo, Baz, 'not a type'))

    def test_type_path(self):
        schema = TypePath(description='This is another test')
        assert schema.errors(b'Nope nope nope') == [Error('Not a unicode string')]
        assert schema.errors('Nope nope nope') == [Error('Value "Nope nope nope" is not a valid Python import path')]
        assert schema.errors('foo.bar:Hello') == [
            Error('No module named foo.bar' if six.PY2 else "No module named 'foo'")
        ]
        assert schema.errors('conformity.fields:NotARealField') == [
            Error(
                "'module' object has no attribute 'NotARealField'" if six.PY2 else
                "module 'conformity.fields' has no attribute 'NotARealField'"
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
        assert schema.introspect() == {'type': 'type_path', 'base_classes': [six.text_type(Foo)]}

        assert TypePath.resolve_python_path('tests.test_fields_meta.Qux') == Qux
        assert TypePath.resolve_python_path('tests.test_fields_meta:Qux.InnerQux') == Qux.InnerQux


class Foo(object):
    pass


class Bar(Foo):
    pass


class Baz(object):
    pass


class Qux(object):
    class InnerQux(object):
        pass
