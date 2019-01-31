from __future__ import (
    absolute_import,
    unicode_literals,
)

import pycountry
import six

from conformity.error import Error
from conformity.fields.basic import Constant


_countries_a2 = sorted(c.alpha_2 for c in pycountry.countries)


class CountryCodeField(Constant):
    """
    An enum field for restricting values to valid ISO 3166 country codes.
    Permits only current countries and uses the ISO 3166 alpha-2 codes.
    """

    introspect_type = "country_code_field"

    def __init__(self, code_filter=lambda x: True, **kwargs):
        """
        :param code_filter: If specified, will be called to further filter the available country codes
        :type code_filter: lambda x: bool
        """
        valid_country_codes = (code for code in _countries_a2 if code_filter(code))
        super(CountryCodeField, self).__init__(*valid_country_codes, **kwargs)
        self._error_message = "Not a valid country code"

    def errors(self, value):
        if not isinstance(value, six.text_type):
            return [Error("Not a unicode string")]
        return super(CountryCodeField, self).errors(value)
