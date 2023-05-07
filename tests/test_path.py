import nographs as nog  # noqa: F401 (used only by doctests)


class PathHandling:
    # noinspection PyShadowingNames
    """Special cases not covered in regular use

    >>> # noinspection PyProtectedMember
    >>> _path = nog._path

    >>> # noinspection PyProtectedMember
    >>> _take_except_for_last = _path._take_except_for_last
    >>> for iter_content_len in range(4):
    ...     list(_take_except_for_last(iter(range(iter_content_len))))
    []
    []
    [0]
    [0, 1]
    """
