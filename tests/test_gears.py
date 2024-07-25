import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)


class ProtocolAndABCNotImplementedErrors:
    """
    Abstract methods of protocols and ABCs.

    If the application calls them and ignores that they are abstract, an assertion
    is to be raised to inform the application about its mistake.
    Check, if this mechanism is correctly implemented.

    Note: The following calls are all illegal w.r.t. typing (only the number of
    parameters is correct): Instance methods are called like a classmethod would,
    the given argument for parameter self has the wrong type, and other arguments may
    be illegal, too, and the generic parameters are missing. But all this does not
    matter here, since the methods are to raise NotImplementedError directly and in
    all cases.


    >>> nog.GearWithoutDistances.vertex_id_set(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.vertex_id_to_vertex_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.vertex_id_to_edge_labels_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.sequence_of_vertices(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.sequence_of_edge_labels(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.vertex_id_to_number_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.zero(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.infinity(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.vertex_id_to_distance_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError
    """


class SpecialFeatures:
    """Tests for features that are not covered by the behaviour tests
    >>> g = nog.GearForHashableVertexIDs[int, int, int, int](0.0, float("infinity"))
    >>> m = g.vertex_id_to_distance_mapping([])  #  Returns a DefaultdictWithNiceStr
    >>> str(m)  # Test __str__ of the DefaultdictWithNiceStr
    '{}'
    """
