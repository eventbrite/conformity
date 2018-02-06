from __future__ import absolute_import, unicode_literals

import functools
import re

import attr
import six

from conformity.error import Error
from conformity.fields.basic import UnicodeString
from conformity.fields.meta import Any
from conformity.utils import strip_none


ipv4_regex = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')


@attr.s
class IPv4Address(UnicodeString):

    def errors(self, value):
        # Get any basic type errors
        result = super(IPv4Address, self).errors(value)
        if result:
            return result
        # Check for IPv4-ness
        if ipv4_regex.match(value):
            return []
        else:
            return [Error("Not a valid IPv4 address")]

    def introspect(self):
        return strip_none({
            "type": "ipv4_address",
            "description": self.description,
        })


@attr.s
class IPv6Address(UnicodeString):

    def errors(self, value):
        # Get any basic type errors
        result = super(IPv6Address, self).errors(value)
        if result:
            return result
        # It must have at least one :
        if ':' not in value:
            return [Error("Not a valid IPv6 address (no colons)")]
        # We can only have one '::' shortener.
        if value.count('::') > 1:
            return [Error("Not a valid IPv6 address (multiple shorteners)")]
        # '::' should be encompassed by start, digits or end.
        if ':::' in value:
            return [Error("Not a valid IPv6 address (shortener not bounded)")]
        # A single colon can neither start nor end an address.
        if ((value.startswith(':') and not value.startswith('::')) or
                (value.endswith(':') and not value.endswith('::'))):
            return [Error("Not a valid IPv6 address (colon at start or end)")]
        # We can never have more than 7 ':' (1::2:3:4:5:6:7:8 is invalid)
        if value.count(':') > 7:
            return [Error("Not a valid IPv6 address (too many colons)")]
        # If we have no concatenation, we need to have 8 fields with 7 ':'.
        if '::' not in value and value.count(':') != 7:
            # We might have an IPv4 mapped address.
            if value.count('.') != 3:
                return [Error("Not a valid IPv6 address (v4 section not valid address)")]
        value = self.expand_ipv6_address(value)
        # Check that each of the hextets are between 0x0 and 0xFFFF.
        for hextet in value.split(':'):
            if hextet.count('.') == 3:
                # If we have an IPv4 mapped address, the IPv4 portion has to
                # be at the end of the IPv6 portion.
                if not value.split(':')[-1] == hextet:
                    return [Error("Not a valid IPv6 address (v4 section not at end)")]
                if not ipv4_regex.match(hextet):
                    return [Error("Not a valid IPv6 address (v4 section not valid address)")]
            else:
                try:
                    # a value error here means that we got a bad hextet,
                    # something like 0xzzzz
                    if int(hextet, 16) < 0x0 or int(hextet, 16) > 0xFFFF:
                        return [Error("Not a valid IPv6 address (invalid hextet)")]
                except ValueError:
                    return [Error("Not a valid IPv6 address (invalid hextet)")]
        return []

    @staticmethod
    def expand_ipv6_address(value):
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
            for _ in six.moves.range(fill_to - sep):
                new_ip.append('0000')
            new_ip += hextet[1].split(':')
        else:
            new_ip = value.split(':')
        # Now need to make sure every hextet is 4 lower case characters.
        # If a hextet is < 4 characters, we've got missing leading 0's.
        ret_ip = []
        for hextet in new_ip:
            ret_ip.append(('0' * (4 - len(hextet)) + hextet).lower())
        return ':'.join(ret_ip)

    def introspect(self):
        return strip_none({
            "type": "ipv6_address",
            "description": self.description,
        })


IPAddress = functools.partial(
    Any,
    IPv4Address(),
    IPv6Address(),
)
