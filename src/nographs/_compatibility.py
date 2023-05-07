import itertools
from collections.abc import Iterator, Iterable

from ._types import T


# --- Solve 3.9 compatibility issue


def _pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
    """Returns an iterator of paired items, overlapping, from the original.
    On Python 3.10 and above, this is an alias for :func:`itertools.pairwise`.
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    yield from zip(a, b)


try:
    from itertools import pairwise as itertools_pairwise  # type: ignore[attr-defined]
except ImportError:
    pairwise = _pairwise
else:

    def pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
        yield from itertools_pairwise(iterable)

    pairwise.__doc__ = _pairwise.__doc__
