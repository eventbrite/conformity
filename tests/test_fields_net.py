from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest

from conformity.fields import (
    IPAddress,
    IPv4Address,
    IPv6Address,
)
from conformity.types import Error


class NetFieldTests(unittest.TestCase):
    """
    Tests net fields
    """

    def test_ipv4address(self):  # type: () -> None
        schema = IPv4Address()
        self.assertEqual(
            schema.errors('127.0.0.1'),
            [],
        )
        self.assertEqual(
            schema.errors('127.300.0.1'),
            [Error('Not a valid IPv4 address')],
        )
        self.assertEqual(
            schema.errors('127.0.0'),
            [Error('Not a valid IPv4 address')],
        )
        self.assertEqual(
            schema.errors('a2.12.55.3'),
            [Error('Not a valid IPv4 address')],
        )

    def test_ipv6address(self):  # type: () -> None
        schema = IPv6Address()
        self.assertEqual(
            schema.errors('::2'),
            [],
        )
        self.assertEqual(
            schema.errors('abdf::4'),
            [],
        )
        self.assertEqual(
            schema.errors('34de:e23d::233e:32'),
            [],
        )
        self.assertEqual(
            schema.errors('::ffff:222.1.41.90'),
            [],
        )
        self.assertEqual(
            schema.errors('1232:d4af:6023:1afc:cfed:0239d:0934:0923d'),
            [],
        )
        self.assertEqual(
            schema.errors('1232:d4af:6023:1afc:cfed:0239d:0934:0923d:3421'),
            [Error('Not a valid IPv6 address (too many colons)')],
        )
        self.assertEqual(
            schema.errors('1:::42'),
            [Error('Not a valid IPv6 address (shortener not bounded)')],
        )
        self.assertEqual(
            schema.errors('1351:z::3'),
            [Error('Not a valid IPv6 address (invalid hextet)')],
        )
        self.assertEqual(
            schema.errors('dead:beef::3422:23::1'),
            [Error('Not a valid IPv6 address (multiple shorteners)')],
        )
        self.assertEqual(
            schema.errors('dead:beef::127.0.0.1:0'),
            [Error('Not a valid IPv6 address (v4 section not at end)')],
        )
        self.assertEqual(
            schema.errors('dead:beef::127.0.0.300'),
            [Error('Not a valid IPv6 address (v4 section not valid address)')],
        )

    def test_ipaddress(self):  # type: () -> None
        schema = IPAddress()
        self.assertEqual(
            schema.errors('127.34.22.11'),
            [],
        )
        self.assertEqual(
            schema.errors('1232:d4af:6023:1afc:cfed:0239d:0934:0923d'),
            [],
        )
        self.assertEqual(
            len(schema.errors('I LOVE FISH')),
            2,
        )
