from collections.abc import (
    Callable,
    Hashable,
)
from typing import TypeVar, Protocol, Union
from abc import abstractmethod

"""
Basic types used in NoGraphs.
"""


T_vertex = TypeVar("T_vertex")
T_vertex_id = TypeVar("T_vertex_id", bound=Hashable)
T = TypeVar("T")


# The following class is manually documented in api.rst, keep docs consistent.
class Weight(Protocol[T]):
    @abstractmethod
    def __add__(self: T, value: T) -> T:
        """Return self+value."""
        raise NotImplementedError

    @abstractmethod
    def __sub__(self: T, value: T) -> T:
        """Return self-value."""
        raise NotImplementedError

    @abstractmethod
    def __lt__(self: T, value: T) -> bool:
        # inherited doc string
        raise NotImplementedError

    @abstractmethod
    def __le__(self: T, value: T) -> bool:
        # inherited doc string
        raise NotImplementedError


T_weight = TypeVar("T_weight", bound=Weight)

T_labels = TypeVar("T_labels")

""" Basic type aliases, part 1 """
VertexToID = Callable[[T_vertex], T_vertex_id]


def vertex_as_id(vertex: T_vertex_id) -> T_vertex_id:
    """Return the vertex unchanged as vertex id.

    In practice, this function is used as default `VertexToID` function to
    signal that a vertex can be directly used as its vertex id
    (semantically and w.r.t. `typing <typing>`) in the given use case.

    At runtime, the library skips calling the function and replaces
    the call by a type cast from `T_vertex` to `T_vertex_id`.

    :param vertex: Is returned as vertex id.
    """
    return vertex


# Types of out edges
UnweightedLabeledOutEdge = tuple[T_vertex, T_labels]
WeightedUnlabeledOutEdge = tuple[T_vertex, T_weight]
WeightedLabeledOutEdge = tuple[T_vertex, T_weight, T_labels]

# Combinations of out edge types
WeightedOutEdge = Union[
    WeightedUnlabeledOutEdge[T_vertex, T_weight],
    WeightedLabeledOutEdge[T_vertex, T_weight, T_labels],
]
LabeledOutEdge = Union[
    WeightedLabeledOutEdge[T_vertex, T_weight, T_labels],
    UnweightedLabeledOutEdge[T_vertex, T_labels],
]
OutEdge = Union[
    WeightedUnlabeledOutEdge[T_vertex, T_weight],
    UnweightedLabeledOutEdge[T_vertex, T_labels],
    WeightedLabeledOutEdge[T_vertex, T_weight, T_labels],
]

# Types of full edges
UnweightedUnlabeledFullEdge = tuple[T_vertex, T_vertex]
UnweightedLabeledFullEdge = tuple[T_vertex, T_vertex, T_labels]
WeightedUnlabeledFullEdge = tuple[T_vertex, T_vertex, T_weight]
WeightedLabeledFullEdge = tuple[T_vertex, T_vertex, T_weight, T_labels]

# Combinations of full edge types
WeightedFullEdge = Union[
    WeightedUnlabeledFullEdge[T_vertex, T_weight],
    WeightedLabeledFullEdge[T_vertex, T_weight, T_labels],
]
WeightedOrLabeledFullEdge = Union[
    WeightedUnlabeledFullEdge[T_vertex, T_weight],
    UnweightedLabeledFullEdge[T_vertex, T_labels],
    WeightedLabeledFullEdge[T_vertex, T_weight, T_labels],
]
AnyFullEdge = Union[
    UnweightedUnlabeledFullEdge[T_vertex],
    WeightedUnlabeledFullEdge[T_vertex, T_weight],
    UnweightedLabeledFullEdge[T_vertex, T_labels],
    WeightedLabeledFullEdge[T_vertex, T_weight, T_labels],
]
