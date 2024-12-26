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
    >>> s = NoVisitedSet()
    >>> s.__contains__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> s.__iter__()
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> s.__len__()
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> s.discard(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> s.add(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed


    >>> # noinspection PyProtectedMember
    >>> from nographs._strategies.utils import NoDistancesMapping
    >>> m = NoDistancesMapping()
    >>> m.__getitem__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> m.__delitem__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> m.__iter__()
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> m.__len__()
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> m.__contains__(None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed

    >>> m.__setitem__(None, None)
    Traceback (most recent call last):
    RuntimeError: Traversal not started, no data to be accessed
    """
