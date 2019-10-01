from __future__ import (
    absolute_import,
    unicode_literals,
)

import decimal
from typing import (
    ItemsView,
    KeysView,
    ValuesView,
)

import pytest
import six

from conformity import fields
from conformity.settings import (
    Settings,
    SettingsData,
    SettingsSchema,
)


class NonSettingsMixinHasNoImpact(object):
    def do_something(self):
        pass


class SettingsOne(Settings):
    schema = {
        'foo': fields.UnicodeString(),
        'bar': fields.Boolean(),
    }  # type: SettingsSchema

    defaults = {
        'bar': False,
    }  # type: SettingsData


class SettingsTwo(Settings):
    schema = {
        'bar': fields.Integer(),
        'baz': fields.Dictionary(
            {
                'inner_foo': fields.UnicodeString(),
                'inner_bar': fields.Boolean(),
                'inner_baz': fields.List(fields.Integer()),
                'inner_qux': fields.Dictionary(
                    {
                        'most_inner_foo': fields.Boolean(),
                        'most_inner_bar': fields.UnicodeString(),
                    },
                ),
            },
        ),
    }  # type: SettingsSchema

    defaults = {
        'bar': 1,
        'baz': {
            'inner_foo': 'Default inner',
            'inner_qux': {
                'most_inner_bar': 'Default most inner'
            }
        },
    }  # type: SettingsData


class SettingsThree(Settings):
    schema = {
        'baz': fields.List(fields.Float()),
        'qux': fields.Float(),
    }  # type: SettingsSchema

    defaults = {
        'qux': 1.234,
    }  # type: SettingsData


class SettingsFour(SettingsThree):
    schema = {
        'qux': fields.Decimal(),
        'new': fields.ByteString(),
        'old': fields.UnicodeString(),
    }  # type: SettingsSchema

    defaults = {
        'qux': decimal.Decimal('1.234'),
        'old': 'Default old',
    }  # type: SettingsData


class SettingsOneTwo(SettingsOne, SettingsTwo):
    pass


class SettingsTwoOne(SettingsTwo, NonSettingsMixinHasNoImpact, SettingsOne):
    pass


class SettingsTwoOneWithOverrides(SettingsTwo, SettingsOne):
    schema = {
        'baz': fields.ByteString(),
    }  # type: SettingsSchema

    defaults = {
        'baz': b'This is the default',
    }  # type: SettingsData


class SettingsOneThree(SettingsOne, SettingsThree):
    pass


class SettingsOneFour(SettingsOne, SettingsFour):
    pass


class SettingsTwoFour(SettingsTwo, SettingsFour):
    pass


class SettingsTwoFourWithOverrides(SettingsTwo, SettingsFour):
    schema = {
        'baz': fields.ByteString(),
    }  # type: SettingsSchema

    defaults = {
        'baz': b'This is the default',
    }  # type: SettingsData


class SettingsOneTwoThree(SettingsOne, SettingsTwo, NonSettingsMixinHasNoImpact, SettingsThree):
    pass


class SettingsThreeTwoOne(SettingsThree, SettingsTwo, NonSettingsMixinHasNoImpact, SettingsOne):
    pass


class SettingsOneTwoThreeWithOverrides(SettingsOne, SettingsTwo, SettingsThree):
    schema = {
        'baz': fields.ByteString(),
    }  # type: SettingsSchema

    defaults = {
        'baz': b'This is the default',
    }  # type: SettingsData


class SettingsOneTwoThreeWithOverridesExtended(SettingsOneTwoThreeWithOverrides):
    schema = {
        'qux': fields.Decimal(),
        'new': fields.ByteString(),
        'old': fields.UnicodeString(),
    }  # type: SettingsSchema

    defaults = {
        'qux': decimal.Decimal('1.234'),
        'old': 'Default old',
    }  # type: SettingsData


# noinspection PyUnusedLocal,PyProtectedMember
def test_meta_prohibits_non_settings_subclass():
    from conformity.settings import _SettingsMetaclass

    with pytest.raises(TypeError):
        @six.add_metaclass(_SettingsMetaclass)
        class NotASettings(object):
            schema = {
                'foo': fields.UnicodeString(),
                'bar': fields.Boolean(),
            }  # type: SettingsSchema

            defaults = {
                'bar': False,
            }  # type: SettingsData


class TestSettingsOne(object):
    def test_schema_correct(self):
        assert SettingsOne.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
        }

    def test_defaults_correct(self):
        assert SettingsOne.defaults == {
            'bar': False,
        }

    def test_validation(self):
        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsOne({})

        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsOne({
                'foo': b'Not a unicode string',
                'bar': True,
            })

        SettingsOne({
            'foo': 'Cool',
            'bar': True,
        })

        settings = SettingsOne({'foo': 'Uncool'})
        assert settings['foo'] == 'Uncool'
        assert settings['bar'] is False

        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsOne({
                'foo': 'Cool',
                'bar': True,
                'unknown': 'Not supported',
            })

    def test_standard_mapping_methods(self):
        settings = SettingsOne({
            'foo': 'Cool',
            'bar': True,
        })

        keys = settings.keys()
        assert isinstance(keys, KeysView if not six.PY2 else list)
        keys_list = list(keys)
        assert 'foo' in keys_list
        assert 'bar' in keys_list

        values = settings.values()
        assert isinstance(values, ValuesView if not six.PY2 else list)
        values_list = list(values)
        assert 'Cool' in values_list
        assert True in values_list

        items = settings.items()
        assert isinstance(items, ItemsView if not six.PY2 else list)
        items_list = list(items)
        assert ('foo', 'Cool') in items_list
        assert ('bar', True) in items_list

        assert settings.get('foo') == 'Cool'
        assert settings.get('bar', False) is True
        assert settings.get('baz') is None
        assert settings.get('baz', False) is False
        assert settings.get('baz', 3) == 3

        assert settings['foo'] == 'Cool'
        assert settings['bar'] is True
        with pytest.raises(KeyError):
            _ = settings['baz']  # noqa: F841

        assert len(settings) == 2

        for key in settings:
            assert key in ('foo', 'bar')

        assert 'foo' in settings
        assert 'bar' in settings
        assert 'baz' not in settings

        assert settings == settings
        assert settings == SettingsOne({
            'foo': 'Cool',
            'bar': True,
        })
        assert SettingsOne({
            'foo': 'Cool',
            'bar': True,
        }) == settings
        assert settings != SettingsOne({
            'foo': 'Uncool',
            'bar': True,
        })


class TestSettingsTwo(object):
    def test_schema_correct(self):
        assert SettingsTwo.schema == {
            'bar': fields.Integer(),
            'baz': fields.Dictionary(
                {
                    'inner_foo': fields.UnicodeString(),
                    'inner_bar': fields.Boolean(),
                    'inner_baz': fields.List(fields.Integer()),
                    'inner_qux': fields.Dictionary(
                        {
                            'most_inner_foo': fields.Boolean(),
                            'most_inner_bar': fields.UnicodeString(),
                        },
                    ),
                },
            ),
        }

    def test_defaults_correct(self):
        assert SettingsTwo.defaults == {
            'bar': 1,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
        }

    def test_validation(self):
        with pytest.raises(Settings.ImproperlyConfigured) as error_context:
            SettingsTwo({})

        assert '- inner_bar: Missing key: inner_bar' in error_context.value.args[0]
        assert '- inner_baz: Missing key: inner_baz' in error_context.value.args[0]
        assert '- inner_qux.most_inner_foo: Missing key: most_inner_foo' in error_context.value.args[0]

        settings = SettingsTwo({
            'baz': {
                'inner_bar': True,
                'inner_baz': [3, 7, 4],
                'inner_qux': {
                    'most_inner_foo': False,
                },
            },
        })
        assert settings['bar'] == 1
        assert settings['baz']['inner_foo'] == 'Default inner'
        assert settings['baz']['inner_bar'] is True
        assert settings['baz']['inner_baz'] == [3, 7, 4]
        assert settings['baz']['inner_qux']['most_inner_foo'] is False
        assert settings['baz']['inner_qux']['most_inner_bar'] == 'Default most inner'

        with pytest.raises(Settings.ImproperlyConfigured) as error_context:
            SettingsTwo({
                'baz': {
                    'inner_bar': 'not a bool',
                    'inner_baz': [3, 7, 4],
                    'inner_qux': {
                        'most_inner_foo': False,
                    },
                },
            })

        assert '- inner_bar: Not a boolean' in error_context.value.args[0]

        with pytest.raises(Settings.ImproperlyConfigured) as error_context:
            SettingsTwo({
                'baz': {
                    'inner_bar': True,
                    'inner_baz': [3, 7, 4],
                    'inner_qux': {
                        'most_inner_foo': False,
                        'most_inner_bar': b'not unicode'
                    },
                },
            })

        assert '- inner_qux.most_inner_bar: Not a unicode string' in error_context.value.args[0]

        with pytest.raises(Settings.ImproperlyConfigured) as error_context:
            SettingsTwo({
                'baz': {
                    'inner_bar': True,
                    'inner_baz': [3, 7, 4],
                    'inner_qux': {
                        'most_inner_foo': False,
                        'not_defined': 'Neat',
                    },
                },
            })

        assert '- inner_qux: Extra keys present: not_defined' in error_context.value.args[0]

        with pytest.raises(Settings.ImproperlyConfigured) as error_context:
            SettingsTwo({
                'baz': {
                    'inner_bar': True,
                    'inner_baz': [3, 7, 4],
                    'inner_qux': {
                        'most_inner_foo': False,
                    },
                },
                'not_in_schema': 'Nope nope nope',
                'also_not_part_of_schema': True,
            })

        assert 'Unknown setting(s): ' in error_context.value.args[0]
        assert 'not_in_schema' in error_context.value.args[0]
        assert 'also_not_part_of_schema' in error_context.value.args[0]


class TestSettingsThree(object):
    def test_schema_correct(self):
        assert SettingsThree.schema == {
            'baz': fields.List(fields.Float()),
            'qux': fields.Float(),
        }

    def test_defaults_correct(self):
        assert SettingsThree.defaults == {
            'qux': 1.234,
        }

    def test_validation(self):
        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsThree({})

        settings = SettingsThree({
            'baz': [8, 3, 56],
        })
        assert settings['baz'] == [8, 3, 56]
        assert settings['qux'] == 1.234

        settings = SettingsThree({
            'baz': [21, 42],
            'qux': 5.678
        })
        assert settings['baz'] == [21, 42]
        assert settings['qux'] == 5.678

        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsThree({
                'baz': ['hello', 3, 56],
            })

        with pytest.raises(Settings.ImproperlyConfigured):
            SettingsThree({
                'baz': [8, 3, 56],
                'not_in_schema': True,
            })


class TestSettingsFour(object):
    def test_schema_correct(self):
        assert SettingsFour.schema == {
            'baz': fields.List(fields.Float()),
            'qux': fields.Decimal(),
            'new': fields.ByteString(),
            'old': fields.UnicodeString(),
        }

    def test_defaults_correct(self):
        assert SettingsFour.defaults == {
            'qux': decimal.Decimal('1.234'),
            'old': 'Default old',
        }


class TestSettingsOneTwo(object):
    def test_schema_correct(self):
        assert SettingsOneTwo.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.Dictionary(
                {
                    'inner_foo': fields.UnicodeString(),
                    'inner_bar': fields.Boolean(),
                    'inner_baz': fields.List(fields.Integer()),
                    'inner_qux': fields.Dictionary(
                        {
                            'most_inner_foo': fields.Boolean(),
                            'most_inner_bar': fields.UnicodeString(),
                        },
                    ),
                },
            ),
        }

    def test_defaults_correct(self):
        assert SettingsOneTwo.defaults == {
            'bar': False,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
        }


class TestSettingsTwoOne(object):
    def test_schema_correct(self):
        assert SettingsTwoOne.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Integer(),
            'baz': fields.Dictionary(
                {
                    'inner_foo': fields.UnicodeString(),
                    'inner_bar': fields.Boolean(),
                    'inner_baz': fields.List(fields.Integer()),
                    'inner_qux': fields.Dictionary(
                        {
                            'most_inner_foo': fields.Boolean(),
                            'most_inner_bar': fields.UnicodeString(),
                        },
                    ),
                },
            ),
        }

    def test_defaults_correct(self):
        assert SettingsTwoOne.defaults == {
            'bar': 1,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
        }


class TestSettingsTwoOneWithOverrides(object):
    def test_schema_correct(self):
        assert SettingsTwoOneWithOverrides.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Integer(),
            'baz': fields.ByteString(),
        }

    def test_defaults_correct(self):
        assert SettingsTwoOneWithOverrides.defaults == {
            'bar': 1,
            'baz': b'This is the default',
        }


class TestSettingsOneThree(object):
    def test_schema_correct(self):
        assert SettingsOneThree.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.List(fields.Float()),
            'qux': fields.Float(),
        }

    def test_defaults_correct(self):
        assert SettingsOneThree.defaults == {
            'bar': False,
            'qux': 1.234,
        }


class TestSettingsOneFour(object):
    def test_schema_correct(self):
        assert SettingsOneFour.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.List(fields.Float()),
            'qux': fields.Decimal(),
            'new': fields.ByteString(),
            'old': fields.UnicodeString(),
        }

    def test_defaults_correct(self):
        assert SettingsOneFour.defaults == {
            'bar': False,
            'qux': decimal.Decimal('1.234'),
            'old': 'Default old',
        }


class TestSettingsTwoFour(object):
    def test_schema_correct(self):
        assert SettingsTwoFour.schema == {
            'bar': fields.Integer(),
            'baz': fields.Dictionary(
                {
                    'inner_foo': fields.UnicodeString(),
                    'inner_bar': fields.Boolean(),
                    'inner_baz': fields.List(fields.Integer()),
                    'inner_qux': fields.Dictionary(
                        {
                            'most_inner_foo': fields.Boolean(),
                            'most_inner_bar': fields.UnicodeString(),
                        },
                    ),
                },
            ),
            'qux': fields.Decimal(),
            'new': fields.ByteString(),
            'old': fields.UnicodeString(),
        }

    def test_defaults_correct(self):
        assert SettingsTwoFour.defaults == {
            'bar': 1,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
            'qux': decimal.Decimal('1.234'),
            'old': 'Default old',
        }


class TestSettingsTwoFourWithOverrides(object):
    def test_schema_correct(self):
        assert SettingsTwoFourWithOverrides.schema == {
            'bar': fields.Integer(),
            'baz': fields.ByteString(),
            'qux': fields.Decimal(),
            'new': fields.ByteString(),
            'old': fields.UnicodeString(),
        }

    def test_defaults_correct(self):
        assert SettingsTwoFourWithOverrides.defaults == {
            'bar': 1,
            'baz': b'This is the default',
            'qux': decimal.Decimal('1.234'),
            'old': 'Default old',
        }


class TestSettingsOneTwoThree(object):
    def test_schema_correct(self):
        assert SettingsOneTwoThree.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.Dictionary(
                {
                    'inner_foo': fields.UnicodeString(),
                    'inner_bar': fields.Boolean(),
                    'inner_baz': fields.List(fields.Integer()),
                    'inner_qux': fields.Dictionary(
                        {
                            'most_inner_foo': fields.Boolean(),
                            'most_inner_bar': fields.UnicodeString(),
                        },
                    ),
                },
            ),
            'qux': fields.Float(),
        }

    def test_defaults_correct(self):
        assert SettingsOneTwoThree.defaults == {
            'bar': False,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
            'qux': 1.234,
        }


class TestSettingsThreeTwoOne(object):
    def test_schema_correct(self):
        assert SettingsThreeTwoOne.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Integer(),
            'baz': fields.List(fields.Float()),
            'qux': fields.Float(),
        }

    def test_defaults_correct(self):
        assert SettingsThreeTwoOne.defaults == {
            'bar': 1,
            'baz': {
                'inner_foo': 'Default inner',
                'inner_qux': {
                    'most_inner_bar': 'Default most inner'
                }
            },
            'qux': 1.234,
        }


class TestSettingsOneTwoThreeWithOverrides(object):
    def test_schema_correct(self):
        assert SettingsOneTwoThreeWithOverrides.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.ByteString(),
            'qux': fields.Float(),
        }

    def test_defaults_correct(self):
        assert SettingsOneTwoThreeWithOverrides.defaults == {
            'bar': False,
            'baz': b'This is the default',
            'qux': 1.234,
        }


class TestSettingsOneTwoThreeWithOverridesExtended(object):
    def test_schema_correct(self):
        assert SettingsOneTwoThreeWithOverridesExtended.schema == {
            'foo': fields.UnicodeString(),
            'bar': fields.Boolean(),
            'baz': fields.ByteString(),
            'qux': fields.Decimal(),
            'new': fields.ByteString(),
            'old': fields.UnicodeString(),
        }

    def test_defaults_correct(self):
        assert SettingsOneTwoThreeWithOverridesExtended.defaults == {
            'bar': False,
            'baz': b'This is the default',
            'qux': decimal.Decimal('1.234'),
            'old': 'Default old',
        }
