from __future__ import (
    absolute_import,
    unicode_literals,
)

import sys


# Skip Sphinx extension tests for Python less than 3.6
collect_ignore = []
if sys.version_info < (3, 6):
    collect_ignore.append('tests/sphinx_ext/test_autodoc.py')
    collect_ignore.append('tests/sphinx_ext/test_linkcode.py')
