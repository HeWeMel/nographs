import itertools
from collections.abc import Iterator, Iterable

from ._types import T


# --- Solve 3.9 compatibility issue


def _manual_pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
    """Returns an iterator of paired items, overlapping, from the original.
    On Python 3.10 and above, this is replaced by an alias for
    :func:`itertools.pairwise`.

    >>> list(_manual_pairwise("abc"))
    [('a', 'b'), ('b', 'c')]
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    yield from zip(a, b)


# Under Python 3.9, detect that itertools.pairwise is missing, and replace it by a
# manual implementation. Under Python >3.9, use build-in function.
try:
    # Under 3.9, MyPy need to ignore that pairwise is missing. Under >3.9, it needs
    # to ignore, that the ignore statement is not needed.
    from itertools import (  # type: ignore[attr-defined,unused-ignore]
        pairwise as itertools_pairwise,
    )
except ImportError:  # pragma: no cover  # not executed under Python >=3.10
    pairwise = _manual_pairwise
else:  # pragma: no cover  # not executed under Python <3.10

    # We cannot assign itertools_pairwise (type: type[pairwise[Any]] to
    # pairwise (type "Callable[[Iterable[T]], Iterator[tuple[T, T]]]", see above).
    # So, we need to also manually implement a wrapper around itertools_pairwise.
    def pairwise(iterable: Iterable[T]) -> Iterator[tuple[T, T]]:
        yield from itertools_pairwise(iterable)

    # The following would be nice, but with PyPyC, __doc__ is not writable.
    # pairwise.__doc__ = _pairwise.__doc__


# --- MyPyC issues ---

try:
    from mypy_extensions import trait
except (
    ModuleNotFoundError
):  # pragma: no cover  # Not reachable if mypy_extensions are installed

    def trait(cls: T) -> T:
        return cls
