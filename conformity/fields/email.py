import re
from typing import (
    Any,
    Iterable,
)

from conformity.fields.builtin import String
from conformity.fields.utils import strip_none
from conformity.fields.net import IPAddress
from conformity.types import Error
from conformity.typing import Introspection

__all__ = (
    'EmailAddress',
)


class EmailAddress(UnicodeString):
    """
    Validates that the value is a string that is a valid email address according
    to RFC 2822 and optionally accepts non-compliant fields listed in the
    `whitelist` argument. Substantially copied from Django (v2.0.x):
    https://github.com/django/django/blob/stable/2.0.x/django/core/validators.py#L164
    """

    valid_noun = 'an email address'
    introspect_type = 'email_address'
    ip_schema = IPAddress()

    user_regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE
    )
    domain_regex = re.compile(
        # max length for domain name labels is 63 characters per RFC 1034
        r'((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))\Z',
        re.IGNORECASE
    )
    literal_regex = re.compile(
        # literal form, ipv4 or ipv6 address (SMTP 4.1.3)
        r'\[([A-f0-9:.]+)\]\Z',
        re.IGNORECASE
    )
    domain_whitelist = frozenset({'localhost'})

    def __init__(self, *, whitelist: Iterable[str]=None, **kwargs) -> None:
        """
        Construct a new email address field.

        :param whitelist: If specified, an invalid domain part will be permitted
            if it is in this list
        """
        kwargs['allow_blank'] = False
        super().__init__(**kwargs)

        if whitelist is not None:
            if (
                not isinstance(whitelist, Iterable) or
                not all(isinstance(c, str) for c in whitelist)
            ):
                raise TypeError("'whitelist' must be an iterable of strings")
            self.domain_whitelist = (
                whitelist if isinstance(whitelist, frozenset)
                else frozenset(whitelist)
            )

    def validate(self, value: Any) -> Validation:
        v = super().validate(value)
        if not v.is_valid():
            return v

        if '@' not in value:
            v.errors.append(Error('Not a valid email address (missing @ symbol)'))
            return v

        errors = []
        user_part, domain_part = value.rsplit('@', 1)
        if not self.user_regex.match(user_part):
            errors.append(Error(
                'Not a valid email address (invalid local user field)',
                pointer=user_part,
            )]
        if (
            domain_part not in self.domain_whitelist and
            not self.is_domain_valid(domain_part)
        ):
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                domain_valid = self.is_domain_valid(domain_part)
            except UnicodeError:
                domain_valid = False
            if not domain_valid:
                errors.append(Error(
                    'Not a valid email address (invalid domain field)',
                    pointer=domain_part,
                )]
        return Validation(errors=errors)

    @classmethod
    def is_domain_valid(cls, domain_part: str) -> bool:
        if cls.domain_regex.match(domain_part):
            return True

        literal_match = cls.literal_regex.match(domain_part)
        if literal_match:
            ip_address = literal_match.group(1)
            if cls.ip_schema.errors(ip_address):
                return False
            else:
                return True
        return False

    def introspect(self) -> Introspection:
        domain_whitelist = None
        if (
            self.domain_whitelist and
            self.domain_whitelist is not self.__class__.domain_whitelist
        ):
            domain_whitelist = sorted(self.domain_whitelist)

        return strip_none({
            'domain_whitelist': domain_whitelist,
        }).update(super().introspect())
