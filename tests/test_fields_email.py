# -*- coding: utf-8 -*-
from __future__ import (
    absolute_import,
    unicode_literals,
)

import unittest
import warnings

import pytest

from conformity.types import Error
from conformity.fields import EmailAddress


class EmailFieldTests(unittest.TestCase):
    """
    Tests email address field
    """
    # Common valid and invalid patterns excerpted from
    # https://en.wikipedia.org/wiki/Email_address
    valid_emails = [
        'simple@example.com',
        'very.common@example.com',
        'disposable.style.email.with+symbol@example.com',
        'other.email-with-dash@example.com',
        'fully-qualified-domain@example.com',
        'user.name+tag+sorting@example.com',
        'x@example.com',
        # '"very.(),:;<>[]\".VERY.\"very@\\ \"very\".unusual"@strange.example.com',
        'example-indeed@strange-example.com',
        # 'admin@mailserver1',
        "#!$%&'*+-/=?^_`{}|~@example.org",
        # '''"()<>[]:,;@\\\"!#$%&'-/=?^_`{}| ~.a"@example.org''',
        'example@s.solutions',
        # 'user@localserver',
        'user@[2001:DB8::1]',
        'customized@192.168.33.195',
        'nick@alliancefrançaise.nu',  # IDNA
    ]

    def test_constructor(self):  # type: () -> None
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            EmailAddress(whitelist=1234)  # type: ignore

        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            EmailAddress(whitelist=[1, 2, 3, 4])  # type: ignore

        assert EmailAddress(description='This is a test').introspect() == {
            'type': 'email_address',
            'description': 'This is a test',
        }

        assert EmailAddress(whitelist=['green.org']).introspect() == {
            'type': 'email_address',
            'domain_whitelist': ['green.org'],
        }

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)

            # noinspection PyTypeChecker
            EmailAddress(message='hello')  # type: ignore

        assert w
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert (
            'Arguments `message` and `code` are deprecated in EmailAddress and will be removed in Conformity 2.0.'
        ) in str(w[-1].message)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always', DeprecationWarning)

            # noinspection PyTypeChecker
            EmailAddress(code='')  # type: ignore

        assert w
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert (
            'Arguments `message` and `code` are deprecated in EmailAddress and will be removed in Conformity 2.0.'
        ) in str(w[-1].message)

    def test_not_unicode(self):  # type: () -> None
        schema = EmailAddress()
        assert schema.errors(self.valid_emails[0].encode('utf-8')) == [Error('Not a unicode string')]

    def test_valid_email_address(self):  # type: () -> None
        schema = EmailAddress()
        for one_email in self.valid_emails:
            self.assertEqual(
                schema.errors(one_email),
                [],
            )

    def test_invalid_email_address(self):  # type: () -> None
        schema = EmailAddress()
        self.assertEqual(
            schema.errors('Abc.example.com'),
            [Error('Not a valid email address (missing @ sign)')],
        )

        self.assertEqual(
            schema.errors('A@b@c@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='A@b@c')],
        )
        self.assertEqual(
            schema.errors('a"b(c)d,e:f;g<h>i[j\\k]l@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='a"b(c)d,e:f;g<h>i[j\\k]l')],
        )
        self.assertEqual(
            schema.errors('just"not"right@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='just"not"right')],
        )
        self.assertEqual(
            schema.errors('this is"not\allowed@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='this is"not\x07llowed')],
        )
        self.assertEqual(
            schema.errors('this\\ still\"not\\allowed@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='this\\ still"not\\allowed')],
        )
        # self.assertEqual(
        #     schema.errors('1234567890123456789012345678901234567890123456789012345678901234+x@example.com'),
        #     [Error('Not a valid email address (invalid local user field)')],
        # )
        self.assertEqual(
            schema.errors('john..doe@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='john..doe')]
        )
        self.assertEqual(
            schema.errors('john.doe@example..com'),
            [Error('Not a valid email address (invalid domain field)', pointer='example..com')],
        )
        self.assertEqual(
            schema.errors('" "@example.org'),
            [Error('Not a valid email address (invalid local user field)', pointer='" "')],
        )
        # Internationalization, currently not supported
        self.assertEqual(
            schema.errors('Pelé@example.com'),
            [Error('Not a valid email address (invalid local user field)', pointer='Pelé')],
        )
        self.assertEqual(
            schema.errors('δοκιμή@παράδειγμα.δοκιμή'),
            [Error('Not a valid email address (invalid local user field)', pointer='δοκιμή')],
        )
        self.assertEqual(
            schema.errors('我買@屋企.香港'),
            [Error('Not a valid email address (invalid local user field)', pointer='我買')],
        )
        self.assertEqual(
            schema.errors('甲斐@黒川.日本'),
            [Error('Not a valid email address (invalid local user field)', pointer='甲斐')],
        )
        self.assertEqual(
            schema.errors('чебурашка@ящик-с-апельсинами.рф'),
            [Error('Not a valid email address (invalid local user field)', pointer='чебурашка')],
        )
        self.assertEqual(
            schema.errors('संपर्क@डाटामेल.भारत'),
            [Error('Not a valid email address (invalid local user field)', pointer='संपर्क')],
        )
        self.assertEqual(
            schema.errors('nick@[1.2.3.4:56]'),
            [Error('Not a valid email address (invalid domain field)', pointer='[1.2.3.4:56]')]
        )

    def test_non_whitelisted_address(self):  # type: () -> None
        whitelisted_domains = ['a-whitelisted-domain']
        schema = EmailAddress(whitelist=whitelisted_domains)
        self.assertEqual(
            schema.errors('a-name@non-whitelisted-domain'),
            [Error('Not a valid email address (invalid domain field)', pointer='non-whitelisted-domain')],
        )

    def test_valid_non_whitelisted_address(self):  # type: () -> None
        schema = EmailAddress()
        self.assertEqual(
            schema.errors('a-name@a-valid-domain.test'),
            [],
        )

    def test_whitelisted_address_via_constructor(self):  # type: () -> None
        whitelisted_domains = ['a-whitelisted-domain']
        schema = EmailAddress(whitelist=whitelisted_domains)
        self.assertEqual(
            schema.errors('a-name@a-whitelisted-domain'),
            [],
        )

    def test_whitelist_removes_duplicates(self):  # type: () -> None
        whitelisted_domains = ['a-repeated-whitelisted-domain', 'a-repeated-whitelisted-domain']
        schema = EmailAddress(whitelist=whitelisted_domains)
        self.assertEqual(1, len(schema.domain_whitelist))
