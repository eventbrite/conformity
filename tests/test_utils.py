from __future__ import (
    absolute_import,
    unicode_literals,
)

import attr
import pytest
import six

from conformity.utils import attr_is_instance_or_instance_tuple


class TestAttrIsInstanceOrInstanceTuple(object):
    # noinspection PyTypeChecker
    def test_bad_argument(self):  # type: () -> None
        with pytest.raises(TypeError):
            attr_is_instance_or_instance_tuple('not a type')  # type: ignore

        with pytest.raises(TypeError):
            attr_is_instance_or_instance_tuple((int, 'also not a type'))  # type: ignore

    def test_validator(self):  # type: () -> None
        @attr.s
        class ForTest(object):
            foo = attr.ib(default=1, validator=attr_is_instance_or_instance_tuple(int))
            bar = attr.ib(
                default='hello',
                validator=attr_is_instance_or_instance_tuple((six.text_type, six.binary_type)),
            )

        ForTest()
        ForTest(foo=18378)
        ForTest(foo=(17267, 19378))
        ForTest(bar='yep')
        ForTest(bar=b'also yep')
        ForTest(bar=('baz', b'qux'))

        with pytest.raises(TypeError):
            ForTest(foo=3.14)

        with pytest.raises(TypeError):
            ForTest(bar=18378)
