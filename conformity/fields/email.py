from __future__ import (
    absolute_import,
    unicode_literals,
)

import re
from typing import (  # noqa: F401  TODO Python 3
    Any as AnyType,
    Iterable,
)

import six

from conformity.error import Error
from conformity.fields.basic import UnicodeString
from conformity.fields.net import IPAddress
from conformity.utils import strip_none


class EmailAddress(UnicodeString):
    """
    On the shoulder of mighty Django (v2.0.x)
    https://github.com/django/django/blob/stable/2.0.x/django/core/validators.py#L164
    UTF-8 emails are not supported in general.
    """

    introspect_type = 'email_address'
    ip_schema = IPAddress()

    # unused, will be removed in version 2.0.0
    message = None  # type: ignore
    code = None  # type: ignore

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

    def __init__(self, message=None, code=None, whitelist=None, **kwargs):
        # type: (None, None, Iterable[six.text_type], **AnyType) -> None
        """
        Construct a new email address field.

        :param message: Unused, and will be removed in version 2.0.0
        :param code: Unused, and will be removed in version 2.0.0
        :param whitelist: If specified, an invalid domain part will be permitted if it is in this list
        """
        if whitelist is not None and (
            not hasattr(whitelist, '__iter__') or
            not all(isinstance(c, six.text_type) for c in whitelist)
        ):
            raise TypeError("'whitelist' must be an iterable of unicode strings")

        super(EmailAddress, self).__init__(**kwargs)
        if whitelist is not None:
            self.domain_whitelist = whitelist if isinstance(whitelist, frozenset) else frozenset(whitelist)

    def errors(self, value):
        # Get any basic type errors
        result = super(EmailAddress, self).errors(value)
        if result:
            return result
        if not value or '@' not in value:
            return [Error('Not a valid email address (missing @ sign)')]

        user_part, domain_part = value.rsplit('@', 1)
        if not self.user_regex.match(user_part):
            return [Error('Not a valid email address (invalid local user field)', pointer=user_part)]
        if domain_part in self.domain_whitelist or self.is_domain_valid(domain_part):
            return []
        else:
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if self.is_domain_valid(domain_part):
                    return []
            except UnicodeError:
                pass
            return [Error('Not a valid email address (invalid domain field)', pointer=domain_part)]

    @classmethod
    def is_domain_valid(cls, domain_part):
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

    def introspect(self):
        return strip_none({
            'type': self.introspect_type,
            'description': self.description,
            'domain_whitelist': (
                sorted(self.domain_whitelist)
                if self.domain_whitelist and self.domain_whitelist is not self.__class__.domain_whitelist
                else None
            ),
        })
