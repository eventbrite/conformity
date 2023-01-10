"""isort:skip_file"""
# flake8: noqa
import collections
import inspect
import json
from typing import (
    Any as AnyType,
    AnyStr,
    Callable,
    Dict,
    List,
    Optional,
    cast,
)
# noinspection PyCompatibility
from unittest import mock

import attr
import pytest
import six
from sphinx.application import Sphinx
from sphinx.config import Config

from conformity import (
    fields,
    settings,
    __version__,
)
from conformity.fields.logging import PYTHON_LOGGING_CONFIG_SCHEMA
from conformity.sphinx_ext.autodoc import (
    autodoc_process_docstring,
    autodoc_process_signature,
    config_initialized,
    get_annotations,
    get_unwrapped_arg_spec,
    setup as setup_extension_for_test,  # aliased because PyTest will try to run something called `setup`
)
from conformity.validator import validate_method

from tests.sphinx_ext.utils import decorated


LocalToThisModuleOptionalInt = Optional[int]


class ClassHoldingSigsToTest:
    def sig1(self, one, two=None):  # type: (AnyStr, Optional[bool]) -> None
        pass

    def sig1_35(self, one: AnyStr, two: Optional[bool] = None) -> None:  # noqa: E999
        pass

    def sig2(self, one, two=None, *args):
        # type: (bool, Optional[AnyStr], *int) -> List[int]
        pass

    def sig2_35(self, one: bool, *args: int, two: Optional[AnyStr] = None) -> List[int]:
        pass

    @decorated
    def sig3(
        self,
        one,
        two=None,
        **kwargs
    ):
        # type: (six.text_type, LocalToThisModuleOptionalInt, **bool) -> Dict[six.binary_type, int]
        pass

    @decorated
    @validate_method(fields.SchemalessDictionary(), fields.Anything())
    @decorated
    def sig3_super_wrapped(
        self,
        one,
        two=None,
        **kwargs
    ):
        # type: (six.text_type, LocalToThisModuleOptionalInt, **bool) -> Dict[six.binary_type, int]
        pass

    def sig3_35(
        self,
        one: six.text_type,
        *args: AnyType,
        two: Optional[int] = None,
        **kwargs: bool
    ) -> Dict[six.binary_type, int]:
        pass

    def sig4\
            (

                self,
                one,  # type: AnyStr
                two=None,  # type:  Optional[six.text_type]
                three=lambda x: True,  # type: Callable[[AnyStr], bool]
                *args,  # type: str
                **kwargs  # type: AnyType

            ):
        # type: (...) -> six.binary_type
        pass

    def sig4_35(
        self,
        one: AnyStr,
        two: Optional[six.text_type],
        three: Callable[[AnyStr], bool] = lambda x: True,
        *args: str,
        **kwargs: AnyType
    ) -> bytes:
        pass


@attr.s
class ClassUsingAttrs27HintsToTest:

    one = attr.ib()  # type: str

    two = attr.ib(default=attr.Factory(list), validator=attr.validators.instance_of(list))  # type: List[int]

    three = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(Dict[str, bool])),
    )  # type: Optional[Dict[str, bool]]


# noinspection PyCompatibility
@attr.s
class ClassUsingAttrs35HintsToTest:

    one: bytes = attr.ib()

    two: List[bool] = attr.ib(default=attr.Factory(list), validator=attr.validators.instance_of(list))

    three: Optional[Dict[str, int]] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(Dict[str, int])),
    )


# noinspection PyCompatibility
class SettingsToTest(settings.Settings):
    schema: settings.SettingsSchema = {
        'one': fields.Dictionary({
            'a': fields.ClassConfigurationSchema(base_class=ClassUsingAttrs27HintsToTest, description='Nifty schema.'),
            'b': fields.PythonPath(value_schema=fields.UnicodeString(), description='Must be a path, yo.'),
            'c': fields.TypeReference(base_classes=ClassHoldingSigsToTest, description='Refer to that thing!'),
        }),
        'two': fields.SchemalessDictionary(key_type=fields.UnicodeString(), value_type=fields.Boolean()),
        'three': fields.List(fields.Integer()),
        'four': fields.Nullable(fields.Set(fields.ByteString())),
        'five': fields.Any(fields.Integer(), fields.Float()),
        'six': fields.ObjectInstance(valid_type=ClassUsingAttrs27HintsToTest, description='Y u no instance?'),
        'seven': fields.Polymorph(
            'thing',
            {
                'thing1': fields.Dictionary({'z': fields.Boolean()}, allow_extra_keys=True),
                'thing2': fields.Dictionary({'y': fields.Boolean()}, allow_extra_keys=True, optional_keys=('y', )),
            },
        ),
    }

    defaults: settings.SettingsData = {
        'one': {
            'b': 'foo.bar:Class',
        },
        'three': [1, 5, 7],
    }


@fields.ClassConfigurationSchema.provider(fields.Dictionary(
    collections.OrderedDict((
        ('one', fields.UnicodeString()),
        ('two', fields.Boolean()),
        ('three', fields.Decimal()),
    )),
    description='This is the neatest documentation for a class',
))
class ClassConfigurationToTest:
    pass


@pytest.mark.parametrize(
    ('obj', 'annotations'),
    (
        (ClassHoldingSigsToTest.sig1, {'one': AnyStr, 'two': Optional[bool], 'return': None}),
        (ClassHoldingSigsToTest.sig1_35, {'one': AnyStr, 'two': Optional[bool], 'return': None}),
        (ClassHoldingSigsToTest.sig2, {'one': bool, 'two': Optional[AnyStr], 'args': int, 'return': List[int]}),
        (ClassHoldingSigsToTest.sig2_35, {'one': bool, 'two': Optional[AnyStr], 'args': int, 'return': List[int]}),
        (ClassHoldingSigsToTest.sig3, {
            'one': str,
            'two': Optional[int],
            'kwargs': bool,
            'return': Dict[bytes, int],
        }),
        (ClassHoldingSigsToTest.sig3_super_wrapped, {
            'one': str,
            'two': Optional[int],
            'kwargs': bool,
            'return': Dict[bytes, int],
        }),
        (ClassHoldingSigsToTest.sig3_35, {
            'one': str,
            'two': Optional[int],
            'args': AnyType,
            'kwargs': bool,
            'return': Dict[bytes, int],
        }),
        (ClassHoldingSigsToTest.sig4, {
            'one': AnyStr,
            'two': Optional[str],
            'three': Callable[[AnyStr], bool],
            'args': str,
            'kwargs': AnyType,
            'return': bytes,
        }),
        (ClassHoldingSigsToTest.sig4_35, {
            'one': AnyStr,
            'two': Optional[str],
            'three': Callable[[AnyStr], bool],
            'args': str,
            'kwargs': AnyType,
            'return': bytes,
        }),
    ),
)
def test_get_annotations(obj, annotations):
    spec = get_unwrapped_arg_spec(obj)
    assert get_annotations(spec, obj) == annotations


@pytest.mark.skipif(
    attr.__version__.startswith('17.'),  # type: ignore
    reason='Documentation extensions support only Attrs >= 18',
)
@pytest.mark.parametrize(
    ('obj', 'signature', 'return_annotation', 'new_signature', 'new_return_annotation'),
    (
        (ClassHoldingSigsToTest.sig1, '(one, two=None)', None, '(one: ~AnyStr, two: Optional[bool] = None)', 'None'),
        (
            ClassHoldingSigsToTest.sig1,
            '(one: Fake, two: Faker = None) -> None',
            None,
            '(one: Fake, two: Faker = None)',
            'None',
        ),
        (ClassHoldingSigsToTest.sig1_35, '(one, two=None)', None, '(one: ~AnyStr, two: Optional[bool] = None)', 'None'),
        (
            ClassHoldingSigsToTest.sig2,
            '(one, two=None, *args)',
            None,
            '(one: bool, two: Optional[~AnyStr] = None, *args: int)',
            'List[int]',
        ),
        (
            ClassHoldingSigsToTest.sig2_35,
            '(one, *args, two=None)',
            None,
            '(one: bool, *args: int, two: Optional[~AnyStr] = None)',
            'List[int]',
        ),
        (
            ClassHoldingSigsToTest.sig3,
            '(one, two=None, **kwargs)',
            'No matter',
            '(one: str, two: Optional[int] = None, **kwargs: bool)',
            'Dict[bytes, int]',
        ),
        (
            ClassHoldingSigsToTest.sig3_super_wrapped,
            '(one, two=None, **kwargs)',
            'No matter',
            '(one: str, two: Optional[int] = None, **kwargs: bool)',
            'Dict[bytes, int]',
        ),
        (
            ClassHoldingSigsToTest.sig3_35,
            '(one, *args, two=None, **kwargs)',
            'None',
            '(one: str, *args: Any, two: Optional[int] = None, **kwargs: bool)',
            'Dict[bytes, int]',
        ),
        (
            ClassHoldingSigsToTest.sig4,
            '(one, two=None, three=lambda x: True, *args, **kwargs)',
            'No matter',
            '(one: ~AnyStr, two: Optional[str] = None, '
            'three: Callable[[~AnyStr], bool] = <function ClassHoldingSigsToTest.<lambda>>, '
            '*args: str, **kwargs: Any)',
            'bytes',
        ),
        (
            ClassUsingAttrs27HintsToTest,
            '(one, two=None, three=None)',
            None,
            '(one: str, two: List[int] = NOTHING, three: Union[Dict[str, bool], None] = None)',
            None,
        ),
        (
            ClassUsingAttrs27HintsToTest.__init__,
            '(one, two=None, three=None)',
            None,
            '(one: str, two: List[int] = NOTHING, three: Union[Dict[str, bool], None] = None)',
            None,
        ),
        (
            ClassUsingAttrs35HintsToTest,
            '(one, two=None, three=None)',
            None,
            '(one: bytes, two: List[bool] = NOTHING, three: Union[Dict[str, int], None] = None)',
            None,
        ),
        (
            ClassUsingAttrs35HintsToTest.__init__,
            '(one, two=None, three=None)',
            None,
            '(one: bytes, two: List[bool] = NOTHING, three: Union[Dict[str, int], None] = None)',
            'None',
        ),
    )
)
def test_autodoc_process_signature(obj, signature, return_annotation, new_signature, new_return_annotation):
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    assert autodoc_process_signature(
        sphinx, 'method', 'does not matter', obj, options, signature, return_annotation,
    ) == (new_signature, new_return_annotation)


def test_autodoc_process_signature_conformity_schema_data():
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    assert autodoc_process_signature(
        sphinx, 'data', 'path.to.module.DATA_ATTRIBUTE', PYTHON_LOGGING_CONFIG_SCHEMA, options, None, None,
    ) == (' = pre-defined Conformity schema path.to.module.DATA_ATTRIBUTE', None)


def test_autodoc_process_docstring_backticks():
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    lines = [
        'This is the first line of `documentation` which should be ``modified`` but `only` if the ',
        'contents ```warrant``` modification. We especially do not `want` to mess ``with`` ',
        '`links to other titles`_ or `links to other pages <hello>`_ because that would be `bad`.',
        "Conformity field that ensures that the value is a dictionary containing at least "
        "fields `'currency'` and `'value'`",
        "and optionally fields `'major_value'` and `'display'`. This field requires that Currint be installed.",
        'We also do `not` want :class:`classes`, :method:`methods`, :function:`functions`, and :ref:`references`, '
        'etc. to be `changed`, including ending :decorator:`ones`',
        'isort:skip_file',
    ]

    autodoc_process_docstring(sphinx, 'class', 'does not matter', ClassHoldingSigsToTest, options, lines)

    assert lines == [
        'This is the first line of ``documentation`` which should be ``modified`` but ``only`` if the ',
        'contents ```warrant``` modification. We especially do not ``want`` to mess ``with`` ',
        '`links to other titles`_ or `links to other pages <hello>`_ because that would be ``bad``.',
        "Conformity field that ensures that the value is a dictionary containing at least "
        "fields ``'currency'`` and ``'value'``",
        "and optionally fields ``'major_value'`` and ``'display'``. This field requires that Currint be installed.",
        'We also do ``not`` want :class:`classes`, :method:`methods`, :function:`functions`, and :ref:`references`, '
        'etc. to be ``changed``, including ending :decorator:`ones`',
        '',
    ]


def test_autodoc_process_dostring_conformity_schema_data():
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    lines = ['']

    autodoc_process_docstring(sphinx, 'data', 'does not matter', PYTHON_LOGGING_CONFIG_SCHEMA, options, lines)

    assert lines[0] == ''
    assert lines[1] == ''
    assert lines[2] == ''
    assert lines[3].startswith(
        'strict ``dict``: Settings to enforce the standard Python logging dictionary-based configuration',
    )


def test_autodoc_process_docstring_settings_class():
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    lines = ['This is the original documentation.']

    autodoc_process_docstring(sphinx, 'class', 'does not matter', SettingsToTest, options, lines)

    assert lines[0] == 'This is the original documentation.'
    assert lines[1] == ''
    assert lines[2] == ''
    assert lines[3] == '**Settings Schema Definition**'
    assert lines[4] == ''
    assert lines[5] == '- ``five`` - any of the types bulleted below: *(no description)*'
    assert lines[6] == ''
    assert lines[7] == '  - ``integer``: *(no description)*'
    assert lines[8] == '  - ``float``: *(no description)*'
    assert lines[9] == ''
    assert lines[10] == '- ``four`` - ``set`` (nullable): *(no description)*'
    assert lines[11] == ''
    assert lines[12] == '  **values**'
    assert lines[13] == '    ``bytes``: *(no description)*'
    assert lines[14] == ''
    assert lines[15] == '- ``one`` - strict ``dict``: *(no description)*'
    assert lines[16] == ''
    assert lines[17] == '  - ``a`` - dictionary with keys ``path`` and ``kwargs`` whose ``kwargs`` schema switches ' \
                        'based on the value of ``path``, dynamically based on class imported from ``path`` (see the ' \
                        'configuration settings schema documentation for the class named at ``path``). Nifty schema. ' \
                        'The imported item at the specified ``path`` must be a subclass of ' \
                        '``tests.sphinx_ext.test_autodoc.ClassUsingAttrs27HintsToTest``.'
    assert lines[18] == '  - ``b`` - a unicode string importable Python path in the format "foo.bar.MyClass", ' \
                        '"foo.bar:YourClass.CONSTANT", etc. Must be a path, yo. The imported item at the specified ' \
                        'path must match the following schema:'
    assert lines[19] == ''
    assert lines[20] == '    **schema**'
    assert lines[21] == '      ``unicode``: *(no description)*'
    assert lines[22] == ''
    assert lines[23] == '  - ``c`` - a Python ``type`` that is a subclass of the following class or classes: ' \
                        '``tests.sphinx_ext.test_autodoc.ClassHoldingSigsToTest``. Refer to that thing!'
    assert lines[24] == ''
    assert lines[25] == '- ``seven`` - dictionary whose schema switches based on the value of key ``thing``: ' \
                        '*(no description)*'
    assert lines[26] == ''
    assert lines[27] == "  - ``thing == 'thing1'`` - strict ``dict``: *(no description)*"
    assert lines[28] == ''
    assert lines[29] == '    - ``z`` - ``boolean``: *(no description)*'
    assert lines[30] == ''
    assert lines[31] == '    Extra keys of any value are allowed.'
    assert lines[32] == "  - ``thing == 'thing2'`` - strict ``dict``: *(no description)*"
    assert lines[33] == ''
    assert lines[34] == '    - ``y`` - ``boolean``: *(no description)*'
    assert lines[35] == ''
    assert lines[36] == '    Extra keys of any value are allowed. Optional keys: ``y``'
    assert lines[37] == ''
    assert lines[38] == ''
    assert lines[39] == '- ``six`` - a Python object that is an instance of the following class or classes: ' \
                        '``tests.sphinx_ext.test_autodoc.ClassUsingAttrs27HintsToTest``. Y u no instance?'
    assert lines[40] == '- ``three`` - ``list``: *(no description)*'
    assert lines[41] == ''
    assert lines[42] == '  **values**'
    assert lines[43] == '    ``integer``: *(no description)*'
    assert lines[44] == ''
    assert lines[45] == '- ``two`` - flexible ``dict``: *(no description)*'
    assert lines[46] == ''
    assert lines[47] == '  **keys**'
    assert lines[48] == '    ``unicode``: *(no description)*'
    assert lines[49] == ''
    assert lines[50] == '  **values**'
    assert lines[51] == '    ``boolean``: *(no description)*'
    assert lines[52] == ''
    assert lines[53] == ''
    assert lines[54] == '**Default Values**'
    assert lines[55] == ''
    assert lines[56] == 'Keys present in the dict below can be omitted from compliant settings dicts, in which case ' \
                        'the values below will apply as the default values.'
    assert lines[57] == ''
    assert lines[58] == '.. code-block:: json'
    assert lines[59] == ''

    assert json.loads('\n'.join(lines[59:]).strip()) == SettingsToTest.defaults


def test_autodoc_process_docstring_class_configuration():
    sphinx = cast(Sphinx, mock.MagicMock())
    options = mock.MagicMock()

    lines = ['This is the original documentation.']

    autodoc_process_docstring(sphinx, 'class', 'does not matter', ClassConfigurationToTest, options, lines)

    assert lines[0] == 'This is the original documentation.'
    assert lines[1] == ''
    assert lines[2] == ''
    assert lines[3] == '**Class Configuration Schema**'
    assert lines[4] == ''
    assert lines[5] == 'strict ``dict``: This is the neatest documentation for a class'
    assert lines[6] == ''
    assert lines[7] == '- ``one`` - ``unicode``: *(no description)*'
    assert lines[8] == '- ``two`` - ``boolean``: *(no description)*'
    assert lines[9] == '- ``three`` - ``decimal``: *(no description)*'


def test_config_initialized():
    sphinx = mock.MagicMock()
    config = mock.MagicMock()
    config.html_static_path = ['foo/bar/_static']

    config_initialized(cast(Sphinx, sphinx), cast(Config, config))

    assert len(config.html_static_path) == 2
    assert config.html_static_path[-1].endswith('conformity/sphinx_ext/static')

    sphinx.add_js_file.assert_called_once_with('autodoc_auto_toc.js')


def test_setup():
    sphinx = mock.MagicMock()

    assert setup_extension_for_test(cast(Sphinx, sphinx)) == {'version': __version__, 'parallel_read_safe': True}

    sphinx.connect.assert_has_calls(
        [
            mock.call('autodoc-process-docstring', autodoc_process_docstring),
            mock.call('autodoc-process-signature', autodoc_process_signature),
            mock.call('config-inited', config_initialized),
        ],
        any_order=True,
    )
