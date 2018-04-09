# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import unittest

from conformity.error import Error
from conformity.fields import EmailAddress


class EmailFieldTests(unittest.TestCase):
    """
    Tests emailaddress fields
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
    ]

    def test_valid_email_address(self):
        schema = EmailAddress()
        for one_email in self.valid_emails:
            self.assertEqual(
                schema.errors(one_email),
                [],
            )

    def test_invalid_email_address(self):
        schema = EmailAddress()
        self.assertEqual(
            schema.errors('Abc.example.com'),
            [Error('Not a valid email address (missing @ sign)')],
        )

        self.assertEqual(
            schema.errors('A@b@c@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'A@b@c')],
        )
        self.assertEqual(
            schema.errors('a"b(c)d,e:f;g<h>i[j\k]l@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'a"b(c)d,e:f;g<h>i[j\\k]l')],
        )
        self.assertEqual(
            schema.errors('just"not"right@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'just"not"right')],
        )
        self.assertEqual(
            schema.errors('this is"not\allowed@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'this is"not\x07llowed')],
        )
        self.assertEqual(
            schema.errors('this\ still\"not\\allowed@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'this\\ still"not\\allowed')],
        )
        # self.assertEqual(
        #     schema.errors('1234567890123456789012345678901234567890123456789012345678901234+x@example.com'),
        #     [Error('Not a valid email address (invalid local user field)')],
        # )
        self.assertEqual(
            schema.errors('john..doe@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'john..doe')]
        )
        self.assertEqual(
            schema.errors('john.doe@example..com'),
            [Error('Not a valid email address (invalid domain field)', 'example..com')],
        )
        self.assertEqual(
            schema.errors('" "@example.org'),
            [Error('Not a valid email address (invalid local user field)', '" "')],
        )
        # Internationalization, currently not supported
        self.assertEqual(
            schema.errors('Pelé@example.com'),
            [Error('Not a valid email address (invalid local user field)', 'Pelé')],
        )
        self.assertEqual(
            schema.errors('δοκιμή@παράδειγμα.δοκιμή'),
            [Error('Not a valid email address (invalid local user field)', 'δοκιμή')],
        )
        self.assertEqual(
            schema.errors('我買@屋企.香港'),
            [Error('Not a valid email address (invalid local user field)', '我買')],
        )
        self.assertEqual(
            schema.errors('甲斐@黒川.日本'),
            [Error('Not a valid email address (invalid local user field)', '甲斐')],
        )
        self.assertEqual(
            schema.errors('чебурашка@ящик-с-апельсинами.рф'),
            [Error('Not a valid email address (invalid local user field)', 'чебурашка')],
        )
        self.assertEqual(
            schema.errors('संपर्क@डाटामेल.भारत'),
            [Error('Not a valid email address (invalid local user field)', 'संपर्क')],
        )
