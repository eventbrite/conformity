from __future__ import (
    absolute_import,
    unicode_literals,
)

import attr

from conformity.fields.basic import Float


@attr.s
class Latitude(Float):
    """
    Latitude coordinate on an ellipsoid or sphere
    """

    def __attrs_post_init__(self):
        # Set end limits if they're not set (and clip any set ones to valid range)
        self.gte = max(-90, self.gte or -100)
        self.lte = min(90, self.lte or 100)


@attr.s
class Longitude(Float):
    """
    Longitude coordinate on an ellipsoid or sphere
    """

    def __attrs_post_init__(self):
        # Set end limits if they're not set (and clip any set ones to valid range)
        self.gte = max(-180, self.gte or -190)
        self.lte = min(180, self.lte or 190)
