import itertools
from collections.abc import Iterator, Callable
from typing import Generic, Any, Union, TypeVar
from abc import ABC, abstractmethod

from ._types import (
    T,
    T_vertex,
    T_vertex_id,
    T_labels,
    UnweightedUnlabeledFullEdge,
    UnweightedLabeledFullEdge,
)

from ._paths import (
    Paths,
)

from ._compatibility import (
    pairwise,
)


def _take_except_for_last(iterator: Iterator[T]) -> Iterator[T]:
    """Yield each element from the iterator except for the last."""
    try:
        v1 = next(iterator)
    except StopIteration:
        return
    for v2 in iterator:
        yield v1
        v1 = v2


def _get_empty_iter() -> Iterator[Any]:
    """Return an exhausted Iterator"""
    return iter(())


def reverse_edges(
    edges: Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]],
) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
    for v, w, l in edges:
        yield w, v, l


SelfPath = TypeVar("SelfPath", bound="Path[Any, Any, Any]")


class Path(ABC, Generic[T_vertex, T_vertex_id, T_labels]):
    """
    Bases: ABC, Generic[`T_vertex`, `T_vertex_id`, `T_labels`]

    A Path object stores a path ("way" through a graph)
    that has been generated by one of the `search algorithms <search_api>`.

    *Path* provides methods to access and iterate the stored path.

    A path can be iterated in forward direction, i.e., from a start vertex to
    the given vertex, or in the backward direction.

    Implementation detail: In fact, Path does not store the path itself, but only
    functions that, when one of the offered kind of iteration of the path is demanded,
    can create the necessary iterator.

    Class Path and its subclasses are not intended to be instantiated by application
    code. On demand, the `search algorithms <search_api>` of the library
    will create Path objects.

    :param get_vertex_forwards_iter: Return an iterator that iterates the vertices
        of the paths in forwards direction.

    :param get_vertex_backwards_iter: Return an iterator that iterates the vertices
        of the paths in backwards direction.

    :param get_edge_forwards_iter: Return an iterator that iterates the labeled edges
        of the paths in forwards direction, or raise RuntimeError if the path does
        not contain labeled edges.

    :param get_edge_backwards_iter: Return an iterator that iterates the labeled edges
        of the paths in backwards direction, or raise RuntimeError if the path does
        not contain labeled edges.
    """

    def __init__(
        self,
        get_vertex_forwards_iter: Callable[[], Iterator[T_vertex]],
        get_vertex_backwards_iter: Callable[[], Iterator[T_vertex]],
        get_edge_forwards_iter: Callable[
            [], Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]
        ],
        get_edge_backwards_iter: Callable[
            [], Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]
        ],
    ):
        self._get_vertex_forwards_iter = get_vertex_forwards_iter
        self._get_vertex_backwards_iter = get_vertex_backwards_iter
        self._get_edge_forwards_iter = get_edge_forwards_iter
        self._get_edge_backwards_iter = get_edge_backwards_iter

    @classmethod
    def from_bidirectional_search(
        cls: type[SelfPath],
        paths_forwards: Paths[T_vertex, T_vertex_id, T_labels],
        paths_backwards: Paths[T_vertex, T_vertex_id, T_labels],
        connecting_vertex: T_vertex,
    ) -> SelfPath:
        """Create path from two parts generated by a bidirectional search,
        the first in forwards direction, the second in backwards direction,
        that meet in the connecting_vertex. The paths forwards need to have
        at least one edge.
        """

        def get_vertex_forwards_iter() -> Iterator[T_vertex]:
            return itertools.chain(
                _take_except_for_last(
                    paths_forwards.iter_vertices_from_start(connecting_vertex)
                ),
                paths_backwards.iter_vertices_to_start(connecting_vertex),
            )

        def get_vertex_backwards_iter() -> Iterator[T_vertex]:
            return itertools.chain(
                paths_backwards.iter_vertices_from_start(connecting_vertex),
                itertools.islice(
                    paths_forwards.iter_vertices_to_start(connecting_vertex), 1, None
                ),
            )

        def get_edge_forwards_iter() -> (
            Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]
        ):
            return itertools.chain(
                paths_forwards.iter_labeled_edges_from_start(connecting_vertex),
                reverse_edges(
                    paths_backwards.iter_labeled_edges_to_start(connecting_vertex)
                ),
            )

        def get_edge_backwards_iter() -> (
            Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]
        ):
            return itertools.chain(
                reverse_edges(
                    paths_backwards.iter_labeled_edges_from_start(connecting_vertex)
                ),
                paths_forwards.iter_labeled_edges_to_start(connecting_vertex),
            )

        return cls(
            get_vertex_forwards_iter,
            get_vertex_backwards_iter,
            get_edge_forwards_iter,
            get_edge_backwards_iter,
        )

    @classmethod
    def of_nothing(cls: type[SelfPath]) -> "Path[T_vertex, T_vertex_id, T_labels]":
        return cls(_get_empty_iter, _get_empty_iter, _get_empty_iter, _get_empty_iter)

    @classmethod
    def from_vertex(cls, vertex: T_vertex) -> "Path[T_vertex, T_vertex_id, T_labels]":
        def get_iter_of_one_vertex() -> Iterator[T_vertex]:
            return iter((vertex,))

        return cls(
            get_iter_of_one_vertex,
            get_iter_of_one_vertex,
            _get_empty_iter,
            _get_empty_iter,
        )

    def iter_vertices_from_start(self) -> Iterator[T_vertex]:
        """Iterate the vertices on the path from the first to the last."""
        return self._get_vertex_forwards_iter()

    def iter_vertices_to_start(self) -> Iterator[T_vertex]:
        """Iterate the vertices on the path from the last to the first."""
        return self._get_vertex_backwards_iter()

    def iter_edges_from_start(self) -> Iterator[UnweightedUnlabeledFullEdge[T_vertex]]:
        """Iterate the edges of the path from the first to the last."""
        return pairwise(self._get_vertex_forwards_iter())

    def iter_edges_to_start(self) -> Iterator[UnweightedUnlabeledFullEdge[T_vertex]]:
        """Iterate the edges of the path from the last to the first."""
        for w, v in pairwise(self._get_vertex_backwards_iter()):
            yield v, w

    def iter_labeled_edges_to_start(
        self,
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Iterate the edges of the path from the last to the first. Raise
        RuntimeError if the stored edges are not labeled.
        """
        return self._get_edge_backwards_iter()

    def iter_labeled_edges_from_start(
        self,
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Iterate the edges of the path from the first to the last. Raise
        RuntimeError if the stored edges are not labeled.
        """
        return self._get_edge_forwards_iter()

    @abstractmethod
    def __iter__(
        self,
    ) -> Union[
        Iterator[T_vertex], Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]
    ]:
        """
        If the path is unlabeled, return an iterator that iterates the vertices of the
        path from the first to the last. If the path is labeled, return an iterator
        that iterate the edges of the path from the first to the last.

        In fully typed code, you can use the following alternative:

        .. code-block:: python

           # If the path is not labeled, the following is equivalent to iter(path):
           path.iter_vertices_from_start()

           # If the path is labeled, the following is equivalent to iter(path):
           path.iter_labeled_edges_from_start()
        """


class PathOfUnlabeledEdges(Path[T_vertex, T_vertex_id, T_labels]):
    """
    Path of edges that are not labeled, i.e., for some starting vertex, an
    edge leading to a specific end vertex is represented only by this end
    vertex.

    This class is not part of the public interface of the library. Its
    signature, methods and implementation can be subject to breaking
    changes even in minor releases. It is not intended to be used by
    application code.
    """

    def __iter__(self) -> Iterator[T_vertex]:
        return self._get_vertex_forwards_iter()


class PathOfLabeledEdges(Path[T_vertex, T_vertex_id, T_labels]):
    """
    Path of edges that are labeled, i.e., for some starting vertex, an
    edge leading to a specific end vertex is represented by a tuple that
    starts with the end vertex and, optionally, contains additional data.

    This class is not part of the public interface of the library. Its
    signature, methods and implementation can be subject to breaking
    changes even in minor releases. It is not intended to be used by
    application code.
    """

    def __iter__(self) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        return self._get_edge_forwards_iter()
