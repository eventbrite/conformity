from __future__ import (
    absolute_import,
    unicode_literals,
)

import re
from typing import (
    AbstractSet,
    Any as AnyType,
    Iterable,
    List as ListType,
    Optional,
    Tuple as TupleType,
)
import warnings

import attr
import currint
import six

from conformity.constants import ERROR_CODE_INVALID
from conformity.fields.basic import (
    Base,
    Constant,
    Integer,
    Introspection,
    UnicodeString,
)
from conformity.fields.structures import Dictionary
from conformity.fields.utils import strip_none
from conformity.types import Error
from conformity.utils import (
    attr_is_int,
    attr_is_iterable,
    attr_is_optional,
    attr_is_set,
    attr_is_string,
)


__all__ = (
    'Amount',
    'AmountRequestDictionary',
    'AmountResponseDictionary',
    'AmountString',
)


DEFAULT_CURRENCY_CODES = frozenset(currint.currencies.keys())


def _get_errors_for_currency_amount(
    currency_code,  # type: six.text_type
    value,  # type: int
    valid_currencies,  # type: AbstractSet[six.text_type]
    gt,  # type: Optional[int]
    gte,  # type: Optional[int]
    lt,  # type: Optional[int]
    lte,  # type: Optional[int]
):
    errors = []

    if currency_code not in valid_currencies:
        errors.append(Error('Not a valid currency code', code=ERROR_CODE_INVALID))
    if gt is not None and value <= gt:
        errors.append(Error('Value not > {}'.format(gt), code=ERROR_CODE_INVALID))
    if lt is not None and value >= lt:
        errors.append(Error('Value not < {}'.format(lt), code=ERROR_CODE_INVALID))
    if gte is not None and value < gte:
        errors.append(Error('Value not >= {}'.format(gte), code=ERROR_CODE_INVALID))
    if lte is not None and value > lte:
        errors.append(Error('Value not <= {}'.format(lte), code=ERROR_CODE_INVALID))

    return errors


@attr.s
class Amount(Base):
    """
    Conformity field that ensures that the value is an instance of `currint.Amount` and optionally enforces boundaries
    for that amount with the `valid_currencies`, `gt`, `gte`, `lt`, and `lte` arguments. This field requires that
    Currint be installed.
    """

    introspect_type = 'currint.Amount'

    valid_currencies = attr.ib(
        default=frozenset(),
        validator=attr_is_iterable(attr_is_string(), attr_is_set()),
    )  # type: AbstractSet[six.text_type]
    gt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    gte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def __attrs_post_init__(self):  # type: () -> None
        if not self.valid_currencies:
            self.valid_currencies = DEFAULT_CURRENCY_CODES

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, currint.Amount):
            return [Error(
                'Not a currint.Amount instance',
                code=ERROR_CODE_INVALID,
            )]

        return _get_errors_for_currency_amount(
            value.currency.code,
            value.value,
            self.valid_currencies,
            self.gt,
            self.gte,
            self.lt,
            self.lte,
        )

    def introspect(self):  # type: () -> Introspection
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'valid_currencies': (
                '(all currencies)' if self.valid_currencies is DEFAULT_CURRENCY_CODES else sorted(self.valid_currencies)
            ),
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


class AmountRequestDictionary(Dictionary):
    """
    Conformity field that ensures that the value is a dictionary containing exactly fields `'currency'` and `'value'`
    and optionally enforces boundaries for those values with the `valid_currencies`, `gt`, `gte`, `lt`, and `lte`
    arguments. This field requires that Currint be installed. No other arguments are supported; `*args` and `**kwargs`
    are deprecated and will be removed in Conformity 2.0.0.
    """

    def __init__(
        self,
        valid_currencies=None,  # type: Iterable[six.text_type]
        gt=None,  # type: Optional[int]
        gte=None,  # type: Optional[int]
        lt=None,  # type: Optional[int]
        lte=None,  # type: Optional[int]
        description=None,  # type: Optional[six.text_type]
        *args,  # type: AnyType
        **kwargs  # type: AnyType
    ):
        # type: (...) -> None
        """
        Construct the field.

        :param valid_currencies: An iterable of valid currencies (if not specified, all valid currencies will be used)
        :param gt: If specified, the value must be greater than this
        :param gte: If specified, the value must be greater than or equal to this
        :param lt: If specified, the value must be less than this
        :param lte: If specified, the value must be less than or equal to this
        :param description: The description for documentation
        :param args: Deprecated, unused, and will be removed in version 2.0.0
        :param kwargs: Deprecated, unused, and will be removed in version 2.0.0
        """
        if valid_currencies is not None and (
            not hasattr(valid_currencies, '__iter__') or
            not all(isinstance(c, six.text_type) for c in valid_currencies)
        ):
            raise TypeError("'valid_currencies' must be an iterable of unicode strings")

        if gt is not None and not isinstance(gt, int):
            raise TypeError("'gt' must be an int")
        if gte is not None and not isinstance(gte, int):
            raise TypeError("'gte' must be an int")
        if lt is not None and not isinstance(lt, int):
            raise TypeError("'lt' must be an int")
        if lte is not None and not isinstance(lte, int):
            raise TypeError("'lte' must be an int")

        if args or kwargs:
            warnings.warn(
                '*args and **kwargs are deprecated in AmountRequestDictionary and will be removed in Conformity 2.0.',
                DeprecationWarning,
            )

        super(AmountRequestDictionary, self).__init__(
            {
                'currency': Constant(*(valid_currencies or DEFAULT_CURRENCY_CODES)),
                'value': Integer(gt=gt, gte=gte, lt=lt, lte=lte),
            },
            optional_keys=(),
            allow_extra_keys=False,
            description=description,
        )


class AmountDictionary(AmountRequestDictionary):
    """
    :deprecated:
    """
    def __init__(
        self,
        valid_currencies=None,  # type: Iterable[six.text_type]
        gt=None,  # type: Optional[int]
        gte=None,  # type: Optional[int]
        lt=None,  # type: Optional[int]
        lte=None,  # type: Optional[int]
        description=None,  # type: Optional[six.text_type]
        *args,  # type: AnyType
        **kwargs  # type: AnyType
    ):
        warnings.warn(
            'AmountDictionary is deprecated and will be removed in Conformity 2.0. '
            'Use AmountRequestDictionary, instead.',
            DeprecationWarning,
        )

        # type ignored due to MyPy bug https://github.com/python/mypy/issues/2582
        super(AmountDictionary, self).__init__(  # type: ignore
            valid_currencies=valid_currencies,
            gt=gt,
            gte=gte,
            lt=lt,
            lte=lte,
            description=description,
            *args,
            **kwargs
        )


@attr.s
class AmountString(Base):
    """
    Conformity field that ensures that the value is a unicode string matching the format CUR,1234 or CUR:1234, where
    the part before the delimiter is a valid currency and the part after the delimiter is an integer. It also optionally
    enforces boundaries for those values with the `valid_currencies`, `gt`, `gte`, `lt`, and `lte` arguments. This
    field requires that Currint be installed.
    """

    _format = re.compile(r'[,:]')

    introspect_type = 'currency_amount_string'

    valid_currencies = attr.ib(
        default=frozenset(),
        validator=attr_is_iterable(attr_is_string(), attr_is_set()),
    )  # type: AbstractSet[six.text_type]
    gt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    gte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lt = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    lte = attr.ib(default=None, validator=attr_is_optional(attr_is_int()))  # type: Optional[int]
    description = attr.ib(default=None, validator=attr_is_optional(attr_is_string()))  # type: Optional[six.text_type]

    def __attrs_post_init__(self):  # type: () -> None
        if not self.valid_currencies:
            self.valid_currencies = DEFAULT_CURRENCY_CODES

    def errors(self, value):  # type: (AnyType) -> ListType[Error]
        if not isinstance(value, six.text_type):
            return [Error('Not a unicode string currency amount')]

        parts = self._format.split(value)
        if len(parts) != 2:
            return [Error('Currency string does not match format CUR,1234 or CUR:1234')]

        currency = parts[0]
        try:
            value = int(parts[1])
        except ValueError:
            return [Error('Currency amount {} cannot be converted to an integer'.format(parts[1]))]

        return _get_errors_for_currency_amount(
            currency,
            value,
            self.valid_currencies,
            self.gt,
            self.gte,
            self.lt,
            self.lte,
        )

    def introspect(self):  # type: () -> Introspection
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'valid_currencies': (
                '(all currencies)' if self.valid_currencies is DEFAULT_CURRENCY_CODES else sorted(self.valid_currencies)
            ),
            'gt': self.gt,
            'gte': self.gte,
            'lt': self.lt,
            'lte': self.lte,
        })


class AmountResponseDictionary(Dictionary):
    """
    Conformity field that ensures that the value is a dictionary containing at least fields `'currency'` and `'value'`
    and optionally fields `'major_value'` and `'display'`. This field requires that Currint be installed.
    """

    def __init__(self, description=None, major_value_required=True, display_required=True):
        # type: (Optional[six.text_type], bool, bool) -> None
        """
        Construct the field.

        :param description: The description for documentation
        :param major_value_required: By default, `'major_value'` is a required field in the response, but setting this
                                     to `False` makes it optional
        :param display_required: By default, `'display'` is a required field in the response, but setting this to
                                 `False` makes it optional
        """
        optional_keys = ()  # type: TupleType[six.text_type, ...]
        if not major_value_required:
            optional_keys += ('major_value', )
        if not display_required:
            optional_keys += ('display', )
        super(AmountResponseDictionary, self).__init__(
            {
                'currency': Constant(*DEFAULT_CURRENCY_CODES),
                'value': Integer(),
                'major_value': UnicodeString(),
                'display': UnicodeString(),
            },
            optional_keys=optional_keys,
            allow_extra_keys=False,
            description=description,
        )


class CurrencyCodeField(Constant):
    """
    An enum field for restricting values to valid currency codes. Permits only current currencies
    and uses currint library.
    """
    introspect_type = 'currency_code_field'

    def __init__(self, code_filter=lambda x: True, **kwargs):
        """
        :param code_filter: If specified, will be called to further filter the available currency codes
        :type code_filter: lambda x: bool
        """

        valid_currency_codes = (code for code in DEFAULT_CURRENCY_CODES if code_filter(code))
        super(CurrencyCodeField, self).__init__(*valid_currency_codes, **kwargs)

    def errors(self, value):
        if not isinstance(value, six.text_type):
            return [Error('Not a unicode string')]

        return super(CurrencyCodeField, self).errors(value)
