from typing import (
    Any,
    AnyStr,
    Callable,
)

import pycountry

from conformity.fields.meta import Constant
from conformity.fields.simple import String


_countries_a2 = sorted(c.alpha_2 for c in pycountry.countries)


__all__ = (
    'CountryCodeField',
)


class CountryCodeField(Constant, String):
    """
    Validates that the value is a valid ISO 3166 country code. It permits only
    current countries according to the installed version of PyCountry and uses
    the ISO 3166 alpha-2 codes. This field requires PyCountry to be installed.
    """

    introspect_type = 'country_code_field'

    def __init__(
        self,
        code_filter: Callable[[AnyStr], bool] = lambda x: True,
        **kwargs: Any
    ) -> None:
        """
        :param code_filter: If specified, will be called to further filter the
            available country codes
        """
        if not callable(code_filter):
            raise TypeError(
                'Argument code_filter must be a callable that accepts a '
                'country code and returns a bool'
            )
        valid_country_codes = (
            code
            for code in _countries_a2
            if code_filter(code)
        )
        super().__init__(*valid_country_codes, **kwargs)
        self._error_message = 'Not a valid country code'
