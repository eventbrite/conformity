from __future__ import absolute_import, unicode_literals

import unittest

from conformity.fields import (
    IPAddress,
    Longitude
)


class ConformityTypeTests(unittest.TestCase):
    """
    Tests introspection output of conformity_type
    """

    def test_returns_conformity_type_if_asked_upon_introspection(self):
        schema = Longitude()

        detailed_introspect = schema.introspect(include_conformity_type=True)

        self.assertTrue("conformity_type" not in schema.introspect())
        self.assertTrue("conformity_type" in detailed_introspect.keys())
        self.assertEqual(
            detailed_introspect["conformity_type"],
            Longitude.conformity_type
        )
        self.assertEqual(
            detailed_introspect["type"],
            Longitude.introspect_type
        )
        # Note: Specific to some types, others actually do conformity_type = type
        self.assertNotEqual(
            detailed_introspect["type"],
            detailed_introspect["conformity_type"]
        )

    def test_ipaddress_introspect(self):
        schema = IPAddress()
        detailed_introspect = schema.introspect(include_conformity_type=True)

        self.assertEqual(
            detailed_introspect["conformity_type"],
            "ip_address",
        )
        # Partial objects don't have a class so cannot expose attributes
        self.assertEqual(
            detailed_introspect["conformity_type"],
            schema.conformity_type,
        )
