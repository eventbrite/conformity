import re
from typing import Any as AnyType

from conformity.fields.simple import String
from conformity.fields.meta import Any
from conformity.types import (
    Error,
    Validation,
)

__all__ = (
    'IPAddress',
    'IPv4Address',
    'IPv6Address',
)


ipv4_regex = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')


class IPv4Address(String):
    """
    Validates that the value is a string that is a valid IPv4 address.
    """

    valid_noun = 'an IPv4 address'
    introspect_type = 'ipv4_address'

    def validate(self, value: AnyType) -> Validation:
        # Get any basic type errors
        v = super().validate(value)
        if (
            v.is_valid() and
            not ipv4_regex.match(value)
        ):
            v.errors.append(Error('Not a valid IPv4 address'))
        return v


class IPv6Address(String):
    """
    Validates that the value is a string that is a valid IPv6 address.
    """

    valid_noun = 'an IPv6 address'
    introspect_type = 'ipv6_address'

    def validate(self, value: AnyType) -> Validation:
        # Get any basic type errors
        v = super().validate(value)
        if v.errors:
            return v

        # Validate formatting
        if ':' not in value:
            # It must have at least one :
            v.errors.append(Error('Not a valid IPv6 address (no colons)'))
        elif value.count('::') > 1:
            # We can only have one '::' shortener.
            v.errors.append(Error('Not a valid IPv6 address (multiple shorteners)'))
        elif ':::' in value:
            # '::' should be encompassed by start, digits or end.
            v.errors.append(Error('Not a valid IPv6 address (shortener not bounded)'))
        elif (
            (value.startswith(':') and not value.startswith('::')) or
            (value.endswith(':') and not value.endswith('::'))
        ):
            # A single colon can neither start nor end an address.
            v.errors.append(Error('Not a valid IPv6 address (colon at start or end)'))
        elif value.count(':') > 7:
            # We can never have more than 7 ':' (1::2:3:4:5:6:7:8 is invalid)
            v.errors.append(Error('Not a valid IPv6 address (too many colons)'))
        elif '::' not in value and value.count(':') != 7:
            # If we have no concatenation, we need to have 8 fields with 7 ':'.
            # We might have an IPv4 mapped address.
            if value.count('.') != 3:
                v.errors.append(Error('Not a valid IPv6 address (v4 section not valid address)'))

        if not v.errors:
            value = self.expand_ipv6_address(value)
            # Check that each of the hextets are between 0x0 and 0xFFFF.
            for hextet in value.split(':'):
                if v.errors:
                    # Fail fast if we have an error
                    break
                if hextet.count('.') == 3:
                    # If we have an IPv4 mapped address, the IPv4 portion has to
                    # be at the end of the IPv6 portion.
                    if not value.split(':')[-1] == hextet:
                        v.errors.append(Error(
                            'Not a valid IPv6 address (v4 section not at end)',
                        ))
                    elif not ipv4_regex.match(hextet):
                        v.errors.append(Error(
                            'Not a valid IPv6 address (v4 section not valid address)',
                        ))
                else:
                    try:
                        # a value error here means that we got a bad hextet,
                        # something like 0xzzzz
                        if int(hextet, 16) < 0x0 or int(hextet, 16) > 0xFFFF:
                            v.errors.append(Error('Not a valid IPv6 address (invalid hextet)'))
                    except ValueError:
                        v.errors.append(Error('Not a valid IPv6 address (invalid hextet)'))
        return v

    @staticmethod
    def expand_ipv6_address(value: str) -> str:
        """
        Expands a potentially-shortened IPv6 address into its full length
        """
        hextet = value.split('::')
        # If there is a ::, we need to expand it with zeroes
        # to get to 8 hextets - unless there is a dot in the last hextet,
        # meaning we're doing v4-mapping
        if '.' in value.split(':')[-1]:
            fill_to = 7
        else:
            fill_to = 8
        if len(hextet) > 1:
            sep = len(hextet[0].split(':')) + len(hextet[1].split(':'))
            new_ip = hextet[0].split(':')
            for _ in range(fill_to - sep):
                new_ip.append('0000')
            new_ip += hextet[1].split(':')
        else:
            new_ip = value.split(':')
        # Now need to make sure every hextet is 4 lower case characters.
        # If a hextet is < 4 characters, we've got missing leading 0's.
        ret_ip = []
        for hextet_str in new_ip:
            ret_ip.append(('0' * (4 - len(hextet_str)) + hextet_str).lower())
        return ':'.join(ret_ip)


class IPAddress(Any):
    """
    Validates that the value is a string that is a valid IPv4 or IPv6 address.
    """
    valid_noun = 'an IP address'
    introspect_type = 'ip_address'

    def __init__(self, **kwargs: AnyType) -> None:
        super().__init__(IPv4Address(), IPv6Address(), **kwargs)
