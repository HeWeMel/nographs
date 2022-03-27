from collections.abc import Callable, Hashable, Iterator, Sequence
from typing import Any

Vertex = Any  # Correct typing would exclude None, but a TypeAlias cannot express this
VertexToID = Callable[[Vertex], Hashable]  # api.rst: manually
Edge = Sequence  # Perfect typing not possible

# Needed due to a sphinx autodocs limitation, see note in conf.py
VertexIterator = Iterator[Vertex]
EdgeIterator = Iterator[Edge]
