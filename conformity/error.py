from __future__ import absolute_import, unicode_literals

import attr


ERROR_CODE_INVALID = "INVALID"
ERROR_CODE_MISSING = "MISSING"
ERROR_CODE_UNKNOWN = "UNKNOWN"


@attr.s
class Error(object):
    """
    Represents an error found validating against the schema.
    """
    message = attr.ib()
    code = attr.ib(default=ERROR_CODE_INVALID)
    pointer = attr.ib(default=None)
