from conformity.fields.builtin import Float

__all__ = (
    'Latitude',
    'Longitude',
)


class Latitude(Float):
    """
    Validates that the value is a float within the normal boundaries of a
    geographical latitude on an ellipsoid or sphere.
    """
    def __init__(self, **kwargs) -> None:
        kwargs['gte'] = max(kwargs.get('gte', -100), -90)
        kwargs['lte'] = min(kwargs.get('lte', 100), 90)
        super().__init__(**kwargs)


class Longitude(Float):
    """
    Validates that the value is a float within the normal boundaries of a
    geographical longitude on an ellipsoid or sphere.
    """

    def __init__(self, **kwargs) -> None:
        kwargs['gte'] = max(kwargs.get('gte', -190), -180)
        kwargs['lte'] = min(kwargs.get('lte', 190), 180)
        super().__init__(**kwargs)
