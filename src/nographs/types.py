from collections.abc import Sequence, Callable, Iterator, Iterable, Hashable
from typing import Any

Vertex = Any  # Correct typing would exclude None, but a TypeAlias cannot express this
VertexIterator = Iterator[
    Vertex
]  # Due to a sphinx autodocs error, see note in conf.py.
NextVertices = Callable[[Vertex, "Traversal"], Iterable[Vertex]]  # api.rst: manually
NextEdges = Callable[[Vertex, "Traversal"], Iterable[Sequence]]  # api.rst: manually
VertexToID = Callable[[Vertex], Hashable]  # api.rst: manually
