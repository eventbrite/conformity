"""isort:skip_file"""
import subprocess
from typing import cast
# noinspection PyCompatibility
from unittest import mock

import pytest
from sphinx.application import Sphinx

from conformity import __version__
from conformity.sphinx_ext.linkcode import (
    create_linkcode_resolve,
    setup as setup_extension_for_test,  # aliased because PyTest will try to run something called `setup`
)


@pytest.mark.parametrize(
    ('user', 'project', 'module', 'tag', 'commit', 'info', 'link'),
    (
        ('eventbrite', 'conformity', 'conformity', '1.2.3', b'8ot873t',
         {'module': 'conformity.fields.basic', 'fullname': 'UnicodeString'},
         'https://github.com/eventbrite/conformity/blob/8ot873t/conformity/fields/basic.py'),
        ('nick', 'conformity', 'conformity', '1.2.3', subprocess.CalledProcessError(1, 'Hello'),
         {'module': 'conformity.fields.basic', 'fullname': 'ByteString'},
         'https://github.com/nick/conformity/tree/1.2.3/conformity/fields/basic.py'),
        ('eventbrite', 'conformity', 'conformity', '1.2.3', b'8183913',
         {'module': 'conformity.fields.structures', 'fullname': 'List'},
         'https://github.com/eventbrite/conformity/blob/8183913/conformity/fields/structures.py'),
        ('eventbrite', 'conformity', 'conformity', '1.2.3', b'caf2378',
         {'module': 'conformity.fields.structures', 'fullname': 'List.__init__'},
         'https://github.com/eventbrite/conformity/blob/caf2378/conformity/fields/structures.py'),
        ('eventbrite', 'conformity', 'conformity', '1.2.3', b'caf2378',
         {'module': 'conformity.fields.structures', 'fullname': 'List.LazyPointer'},
         'https://github.com/eventbrite/conformity/blob/caf2378/conformity/fields/structures.py'),
        ('eventbrite', 'conformity', 'conformity', '4.5.6', subprocess.CalledProcessError(1, 'Hello'),
         {'module': 'conformity.fields.structures', 'fullname': 'List.LazyPointer.__init__'},
         'https://github.com/eventbrite/conformity/tree/4.5.6/conformity/fields/structures.py'),
    ),
)
def test_create_linkcode_resolve(user, project, module, tag, commit, info, link):
    with mock.patch('conformity.sphinx_ext.linkcode.subprocess.check_output') as mock_check_output:
        mock_check_output.side_effect = [commit]
        linkcode_resolve = create_linkcode_resolve(user, project, module, tag)

    mock_check_output.assert_called_once_with(['git', 'rev-parse', '--short', 'HEAD'])

    result = linkcode_resolve('py', info)

    assert result.startswith(link)
    assert '#L' in result
    assert '#L1-L' not in result


def test_setup():
    sphinx = mock.MagicMock()

    assert setup_extension_for_test(cast(Sphinx, sphinx)) == {'version': __version__, 'parallel_read_safe': True}

    assert sphinx.connect.call_count == 0
