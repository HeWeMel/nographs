import itertools
from collections.abc import Iterator, Iterable

from ._types import T


# --- Solve 3.9 compatibility issue


def _pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
    """Returns an iterator of paired items, overlapping, from the original.
    On Python 3.10 and above, this is replaced by an alias for
    :func:`itertools.pairwise`.

    >>> list(_pairwise("abc"))
    [('a', 'b'), ('b', 'c')]
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    yield from zip(a, b)


try:
    from itertools import pairwise as itertools_pairwise  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover  # not executed under Python >=3.10
    pairwise = _pairwise
else:  # pragma: no cover  # not executed under Python <3.10

    def pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
        yield from itertools_pairwise(iterable)

    pairwise.__doc__ = _pairwise.__doc__
