class MethodsOfDummyCollectionClasses:
    """-- Methods of dummy collection classes. Objects of these classes are
    used as content of traversal objects as long as the true collections
    that provide state information of the traversal is not initialized yet,
    because the traversal has not been started so far.

    Check, if either a sensible exception raised when called.

    Note: All calls are illegal w.r.t. typing (only the number of parameters
    is correct): Instance methods are called like a classmethod would,
    the given argument for parameter self has the wrong type, and other
    arguments may be illegal, too, and the generic parameters are missing.
    But all this does not matter here, since the methods are to raise
    an Exceptioon or to return a constant value directly and in all cases.

    >>> # noinspection PyProtectedMember
    >>> from nographs._strategies.utils import NoVisitedSet
    >>> NoVisitedSet.__contains__(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoVisitedSet.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoVisitedSet.__len__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoVisitedSet.discard(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoVisitedSet.add(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed


    >>> # noinspection PyProtectedMember
    >>> from nographs._strategies.utils import NoDistancesMapping
    >>> NoDistancesMapping.__getitem__(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoDistancesMapping.__delitem__(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoDistancesMapping.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoDistancesMapping.__len__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoDistancesMapping.__contains__(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> NoDistancesMapping.__setitem__(None, None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed
    """
