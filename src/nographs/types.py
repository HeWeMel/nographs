from collections.abc import Sequence, Callable, Iterator, Iterable, Hashable
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:  # Not possible at runtime, leads to circular import
    # The following is necessary for MyPy,
    # but error for flake8 and unreachable for coverage
    from nographs import Traversal  # pragma: no cover # noqa: F401

Vertex = Any  # Correct typing would exclude None, but a TypeAlias cannot express this
VertexIterator = Iterator[
    Vertex
]  # Needed due to a sphinx autodocs limitation, see note in conf.py
NextVertices = Callable[[Vertex, "Traversal"], Iterable[Vertex]]  # api.rst: manually
NextEdges = Callable[[Vertex, "Traversal"], Iterable[Sequence]]  # api.rst: manually
VertexToID = Callable[[Vertex], Hashable]  # api.rst: manually
