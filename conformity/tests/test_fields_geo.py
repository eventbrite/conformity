from __future__ import unicode_literals

import unittest

from ..fields import (
    Latitude,
    Longitude,
)
from ..error import Error


class GeoFieldTests(unittest.TestCase):
    """
    Tests geographic fields
    """

    def test_latitude(self):
        schema = Latitude()
        self.assertEqual(
            schema.errors(89) or [],
            [],
        )
        self.assertEqual(
            schema.errors(-1.3412) or [],
            [],
        )
        self.assertEqual(
            schema.errors(180),
            [Error("Value not <= 90")],
        )
        self.assertEqual(
            schema.errors(-91),
            [Error("Value not >= -90")],
        )

    def test_longitude(self):
        schema = Longitude()
        self.assertEqual(
            schema.errors(129.1) or [],
            [],
        )
        self.assertEqual(
            schema.errors(186) or [],
            [Error("Value not <= 180")],
        )
        self.assertEqual(
            schema.errors(-181.3412) or [],
            [Error("Value not >= -180")],
        )

    def test_limited_longitude(self):
        schema = Longitude(lte=-50)
        self.assertEqual(
            schema.errors(-51.2) or [],
            [],
        )
        self.assertEqual(
            schema.errors(-49.32) or [],
            [Error("Value not <= -50")],
        )
