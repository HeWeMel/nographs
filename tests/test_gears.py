import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)


class SpecialFeatures:
    """Tests for features that are not covered by the behaviour tests
    >>> g = nog.GearForHashableVertexIDs[int, int, int, int](0.0, float("infinity"))
    >>> m = g.vertex_id_to_distance_mapping([])  #  Returns a DefaultdictWithNiceStr
    >>> str(m)  # Test __str__ of the DefaultdictWithNiceStr
    '{}'
    """
