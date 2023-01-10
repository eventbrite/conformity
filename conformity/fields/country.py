from __future__ import (
    absolute_import,
    unicode_literals,
)

from typing import (
    Any as AnyType,
    AnyStr,
    Callable,
    List as ListType,
)

import pycountry
import six

from conformity.types import Error
from conformity.fields.basic import Constant


_countries_a2 = sorted(c.alpha_2 for c in pycountry.countries)


__all__ = (
    'CountryCodeField',
)


class CountryCodeField(Constant):
    """
    Conformity field that ensures that the value is a valid ISO 3166 country codes. It permits only current countries
    according to the installed version of PyCountry and uses the ISO 3166 alpha-2 codes. This field requires that
    PyCountry be installed.
    """

    introspect_type = 'country_code_field'

    def __init__(
        self,
        code_filter=lambda x: True,  # type: Callable[[AnyStr], bool]
        **kwargs  # type: AnyType
    ):
        # type: (...) -> None
        """
        :param code_filter: If specified, will be called to further filter the available country codes
        """
        if not callable(code_filter):
            raise TypeError('Argument code_filter must be a callable that accepts a country code and returns a bool')
        valid_country_codes = (code for code in _countries_a2 if code_filter(code))
        super(CountryCodeField, self).__init__(*valid_country_codes, **kwargs)
        self._error_message = 'Not a valid country code'

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, six.text_type):
            return [Error('Not a unicode string')]
        return super(CountryCodeField, self).errors(value)
