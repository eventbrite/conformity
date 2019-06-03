from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

import pytest

from conformity.fields import (
    Dictionary,
    Integer,
    List,
    Null,
    SchemalessDictionary,
    Tuple,
    UnicodeString,
)
from conformity.validator import (
    KeywordError,
    PositionalError,
    ValidationError,
    validate,
    validate_call,
    validate_method,
)


class ValidatorTests(unittest.TestCase):
    """
    Tests validation functions
    """
    def test_validator_arguments_validation(self):
        with pytest.raises(ValueError):
            @validate_call(List(UnicodeString()), UnicodeString())
            def something(_foo):
                pass

        with pytest.raises(ValueError):
            @validate_call(args=SchemalessDictionary(), kwargs=None, returns=UnicodeString())
            def something_else(_foo):
                pass

    def test_validate(self):
        schema = Dictionary({
            'name': UnicodeString(max_length=20),
            'greeting': UnicodeString(),
        }, optional_keys=['greeting'])

        validate(schema, {'name': 'Andrew'})
        validate(schema, {'name': 'Andrew', 'greeting': 'Ahoy-hoy'})

        with self.assertRaises(ValidationError):
            validate(schema, {'name': 'Andrewverylongnameperson'})

        with self.assertRaises(ValidationError):
            validate(schema, {'name': 'Andrew', 'greeeeeeting': 'Ahoy-hoy'})

    def test_validate_call(self):
        schema = Dictionary({
            'name': UnicodeString(max_length=20),
            'greeting': UnicodeString(),
        }, optional_keys=['greeting'])

        @validate_call(schema, UnicodeString())
        def greeter(name, greeting='Hello'):
            # Special case to check return value stuff
            if name == 'error':
                return 5
            return '{}, {}!'.format(greeting, name)

        self.assertEqual(greeter(name='Andrew'), 'Hello, Andrew!')
        self.assertEqual(greeter(name='Andrew', greeting='Ahoy'), 'Ahoy, Andrew!')

        with self.assertRaises(ValidationError):
            greeter(name='Andrewverylongnameperson')

        with self.assertRaises(ValidationError):
            greeter(name='Andrew', greeeeeeting='Boo')

        with self.assertRaises(ValidationError):
            greeter(name='error')

        with self.assertRaises(PositionalError):
            greeter('Andrew')

        @validate_call(
            args=Tuple(Integer(), UnicodeString()),
            kwargs=None,
            returns=Null(),
        )
        def args_function(foo, bar):
            if foo:
                return bar.format(bar)

        assert args_function(0, 'John {}') is None
        with pytest.raises(ValidationError):
            args_function(1, 'Jeff {}')
        with pytest.raises(ValidationError):
            args_function(0, b'Nope {}')
        with pytest.raises(ValidationError):
            args_function(0, bar='John {}')
        with pytest.raises(KeywordError):
            args_function(0, 'John {}', extra='Unsupported')

        @validate_call(
            args=Tuple(Integer(), UnicodeString()),
            kwargs=Dictionary({'extra': UnicodeString()}, optional_keys=('extra', )),
            returns=UnicodeString(),
        )
        def args_and_kwargs_function(foo, bar, extra='baz'):
            return bar.format(foo, extra)

        assert args_and_kwargs_function(0, 'John {}: {}') == 'John 0: baz'
        assert args_and_kwargs_function(1, 'Jeff {}: {}', extra='cool') == 'Jeff 1: cool'
        with pytest.raises(ValidationError):
            args_and_kwargs_function(1, 'Jeff {}: {}', 'cool')
        with pytest.raises(ValidationError):
            args_and_kwargs_function('nope', 'Jeff {}: {}')
        with pytest.raises(ValidationError):
            args_and_kwargs_function(1, b'nope')
        with pytest.raises(ValidationError):
            args_and_kwargs_function(0, bar='John {}: {}')

    def test_validate_method(self):
        schema = Dictionary({
            'name': UnicodeString(max_length=20),
            'greeting': UnicodeString(),
        }, optional_keys=['greeting'])

        class Helper(object):
            @classmethod
            @validate_method(schema, UnicodeString())
            def greeter(cls, name, greeting='Hello'):
                # Special case to check return value stuff
                if name == 'error':
                    return 5
                return '{}, {}!'.format(greeting, name)

            @staticmethod
            @validate_call(args=Tuple(Integer(), Integer()), kwargs=None, returns=Integer())
            def args_method(one, two):
                return one + two

            # noinspection PyMethodMayBeStatic
            @validate_method(
                args=List(UnicodeString()),
                kwargs=SchemalessDictionary(value_type=UnicodeString()),
                returns=List(UnicodeString()),
            )
            def args_and_kwargs_method(self, *args, **kwargs):
                return [s.format(**kwargs) for s in args]

        self.assertEqual(Helper.greeter(name='Andrew'), 'Hello, Andrew!')
        self.assertEqual(Helper.greeter(name='Andrew', greeting='Ahoy'), 'Ahoy, Andrew!')

        with self.assertRaises(ValidationError):
            Helper.greeter(name='Andrewverylongnameperson')

        with self.assertRaises(ValidationError):
            Helper.greeter(name='Andrew', greeeeeeting='Boo')

        with self.assertRaises(ValidationError):
            Helper.greeter(name='error')

        with self.assertRaises(PositionalError):
            Helper.greeter('Andrew')

        assert Helper.args_method(1, 2) == 3
        assert Helper.args_method(75, 23) == 98
        with pytest.raises(ValidationError):
            Helper.args_method(1.0, 2)
        with pytest.raises(ValidationError):
            Helper.args_method(1, 2.0)
        with pytest.raises(KeywordError):
            Helper.args_method(1, 2, extra='Forbidden')

        assert Helper().args_and_kwargs_method('hello', 'cool {planet}', 'hot {star}', planet='Earth', star='Sun') == [
            'hello',
            'cool Earth',
            'hot Sun',
        ]
        with pytest.raises(ValidationError):
            Helper().args_and_kwargs_method(1, 'sweet', planet='Earth', star='Sun')
        with pytest.raises(ValidationError):
            Helper().args_and_kwargs_method('hello', 'cool {planet}', 'hot {star}', planet=1, star=2)
