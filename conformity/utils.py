def strip_none(value):
    """
    Takes a dict and removes all keys that have None values, used mainly for
    tidying up introspection responses. Take care not to use this on something
    that might legitimately contain a None.
    """
    return {k: v for k, v in value.items() if v is not None}
