import nographs as nog  # noqa: F401 (used only by doctests)


class ProtocolAndABCNotImplementedErrors:
    """-- Abstract methods of protocols and ABCs.

    If the application calls them and ignores that they are abstract, an assertion
    is to be raised to inform the application about its mistake.
    Check, if this mechanism is correctly implemented.

    Note: The following calls are all illegal w.r.t. typing (only the number of
    parameters is correct): Instance methods are called like a classmethod would,
    the given argument for parameter self has the wrong type, and other arguments may
    be illegal, too, and the generic parameters are missing. But all this does not
    matter here, since the methods are to raise NotImplementedError directly and in
    all cases.

    >>> nog.Weight.__add__(0, 0)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Weight.__sub__(0, 0)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Weight.__lt__(0, 0)
    Traceback (most recent call last):
    NotImplementedError
    >>> nog.Weight.__le__(0, 0)
    Traceback (most recent call last):
    NotImplementedError"""


class Functionality:
    """Test function vertex_as_id. Test needed here, since this
    function is not intended to be really called anywhere in NoGraphs.

    >>> nog.vertex_as_id(0)
    0
    """
