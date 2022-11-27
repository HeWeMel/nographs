from __future__ import annotations

from collections.abc import Sequence, Iterator, MutableMapping
from typing import Optional, Any, Generic, cast, Union
from abc import ABC

import nographs
from nographs import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
    vertex_as_id,
    LabeledOutEdge,
    UnweightedUnlabeledFullEdge,
    UnweightedLabeledFullEdge,
    VertexIdToVertexMapping,
    VertexIdToPathEdgeDataMapping,
    GettableSettableForGearProto,
    VertexSequenceWrapperForMappingProto,
    access_to_vertex_mapping_expect_none,
)


class Paths(ABC, Generic[T_vertex, T_vertex_id, T_labels]):
    """
    Bases: ABC, Generic[`T_vertex`, `T_vertex_id`, `T_labels`]

    A Paths object is a container that stores the paths ("ways" through a graph)
    that have been generated by one of the traversal algorithms.

    *Paths* provides methods to access and iterate a path.

    A path is identified by its end vertex. The vertices that come before the
    end vertex are themselves stored as a path. The container will never
    store two paths that lead to the same vertex. An empty path with just one
    vertex can be stored, and the start of each path needs to be an empty path.
    A self loop can not be stored as path (since internally, a self loop is used
    to mark an empty path).

    A path can be iterated in forward direction, i.e., from a start vertex to
    the given vertex, or in the backward direction. The forward iteration is
    implemented based on the backward iteration by creating a copy of the
    path. Thus, it is slower and needs additional memory.

    Class Paths and its subclasses are not intended to be instantiated by application
    code. On demand, the `traversal strategies <traversal_api>` of the library
    will create Paths objects.

    :param predecessor: The predecessor information of the paths will be
        stored in the given mapping.

    :param vertex_to_id: See `VertexToID` function.
    """

    def __init__(
        self,
        predecessor: VertexIdToVertexMapping[T_vertex_id, T_vertex],
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    ):
        self._predecessor = predecessor
        self._predecessor_collection: GettableSettableForGearProto[
            T_vertex_id, T_vertex, Optional[T_vertex]
        ]
        self._predecessor_wrapper: Optional[
            VertexSequenceWrapperForMappingProto[
                T_vertex_id, T_vertex, Optional[T_vertex]
            ]
        ]
        (
            _,
            self._predecessor_collection,
            self._predecessor_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessor)
        self._vertex_to_id = None if vertex_to_id is vertex_as_id else vertex_to_id

    def __contains__(self, vertex: T_vertex) -> bool:
        """Return whether a path to *vertex* exists in the *Paths*
        container. This allows for expressions like *vertex in paths*.

        :param vertex: The vertex to look for.
        """
        if vertex is None:
            raise RuntimeError("Paths: None instead of vertex given.")
        vertex_to_id = self._vertex_to_id
        # If vertex_to_id is None, self._vertex_to_id has been None.
        # Then, parameter vertex_to_id of __init__ has been vertex_as_id.
        # Then, T_vertex is a subtype of T_vertex_id. Then, the cast is correct.
        vertex_id = vertex_to_id(vertex) if vertex_to_id else cast(T_vertex_id, vertex)
        return vertex_id in self._predecessor

    def _check_vertex(self, vertex: T_vertex) -> T_vertex_id:
        """Ensure that a path for *vertex* can be given, else raise RuntimeError.

        :param vertex: The vertex to look for.
        """
        if vertex is None:
            raise RuntimeError("Paths: None instead of vertex given.")
        vertex_to_id = self._vertex_to_id
        vertex_id = (
            vertex_to_id(vertex) if vertex_to_id else cast(T_vertex_id, vertex)
        )  # See docs above for cast
        if vertex_id not in self._predecessor:
            raise RuntimeError("Paths: No path for given vertex.")
        return vertex_id

    def iter_vertices_to_start(self, vertex: T_vertex) -> Iterator[T_vertex]:
        """Iterate the vertices on the path to *vertex* from the last to the
        first.

        :param vertex: The path ending at this vertex will be iterated.
        """
        vertex_id = self._check_vertex(vertex)
        predecessor_collection = self._predecessor_collection
        vertex_to_id = self._vertex_to_id

        while True:
            yield vertex
            from_vertex = predecessor_collection[vertex_id]
            if vertex == from_vertex:
                break  # self loop denotes empty path / end of the path
            assert from_vertex is not None  # prefixes of paths are always paths
            vertex = from_vertex
            vertex_id = (
                vertex_to_id(vertex) if vertex_to_id else cast(T_vertex_id, vertex)
            )  # See comment about the cast in __contains__

    def iter_vertices_from_start(self, vertex: T_vertex) -> Iterator[T_vertex]:
        """Iterate the vertices on the path to *vertex* from the first to the
        last. Internally, a list of all the vertices is created and then
        reversed and iterated.

        :param vertex: The path ending at this vertex will be iterated.
        """
        return reversed(tuple(self.iter_vertices_to_start(vertex)))

    def _iter_raw_edges_to_start(
        self, vertex: T_vertex
    ) -> Iterator[tuple[T_vertex, T_vertex, T_vertex_id]]:
        """Iterate the edges of the path to *vertex* from the last to the
        first and yield the raw data of each edge as tuple
        (from_vertex, to_vertex, to_vertex_id).

        Guarantees that to_vertex_id is contained in self._predecessor.

        :param vertex: The path ending at this vertex will be iterated.
        """
        vertex_id = self._check_vertex(vertex)
        predecessor_collection = self._predecessor_collection
        vertex_to_id = self._vertex_to_id

        while True:
            from_vertex = predecessor_collection[vertex_id]
            # self loop denotes empty path / end of the path
            # (None is included in type specification in order to allow for a
            #  sequence-based collection with integer vertices to mark that
            #  the collection does not contain vertex_id. Can never occur here,
            #  but need to be excluded for correct typing for calling code.)
            if from_vertex == vertex or from_vertex is None:
                break
            yield from_vertex, vertex, vertex_id
            vertex = from_vertex
            vertex_id = (
                vertex_to_id(vertex) if vertex_to_id else cast(T_vertex_id, vertex)
            )  # See comment about the cast in __contains__

    def iter_edges_to_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedUnlabeledFullEdge[T_vertex]]:
        """Iterate the edges of the path to *vertex* from the last to the
        first.

        :param vertex: The path ending at this vertex will be iterated.
        """
        for from_vertex, vertex, vertex_id in self._iter_raw_edges_to_start(vertex):
            yield (from_vertex, vertex)

    def iter_edges_from_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedUnlabeledFullEdge[T_vertex]]:
        """Iterate the edges of the path to *vertex* from the first to the
        last. Internally, a list of all the edges is created and then
        reversed and iterated.

        :param vertex: The path ending at this vertex will be iterated.
        """
        return reversed(tuple(self.iter_edges_to_start(vertex)))

    def iter_labeled_edges_to_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Iterate the edges of the path to *vertex* from the last to the
        first. Raise RuntimeError if the stored edges are not labeled.

        To be overridden in subclasses that support labeled edges.

        :param vertex: The path ending at this vertex will be iterated.
        """
        raise RuntimeError(
            "Edges with labels needed, and Traversal needs to know about them"
        )

    def iter_labeled_edges_from_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Iterate the edges of the path to *vertex* from the first to the
        last. Internally, a list of all the edges is created and then
        reversed and iterated.  Raise RuntimeError if the stored edges are
        not labeled.

        To be overridden in subclasses that support labeled edges.

        :param vertex: The path ending at this vertex will be iterated.
        """
        raise RuntimeError(
            "Edges with labels needed, and Traversal needs to know about them"
        )

    def __getitem__(
        self, vertex: T_vertex
    ) -> Union[
        Sequence[T_vertex],
        Sequence[UnweightedLabeledFullEdge[T_vertex, T_labels]],
    ]:
        """Return the path that ends at *vertex* as a sequence. The orientation
        of the path is from first to last vertex / edge. In case of a labeled
        path, the edges are returned, for an unlabeled path the vertices.

        The method allows for expressions like *paths[vertex]*.

        In fully typed code, you can use an equivalent and fully typed alternative
        for paths without resp. with labels:

        .. code-block:: python

           # If the paths are not labeled, the following is equivalent to paths[vertex]:
           tuple(paths.iter_vertices_from_start(vertex))

           # If the paths are labeled, the following is equivalent to paths[vertex]:
           tuple(paths.iter_labeled_edges_from_start(vertex))

        Internally, the path from the given vertex back to the first vertex
        in the path is computed, and then reversed and stored as sequence.

        :param vertex: The path ending at this vertex will be returned.
        """


class _PathsDummy(Paths[T_vertex, T_vertex_id, Any]):
    """Empty and non-functional default Paths container. Raises RuntimeError
    for all methods returning or iterating a Path, and __contains__ returns False.
    """

    class MappingOfNothing(MutableMapping[T_vertex_id, T_vertex]):
        def __getitem__(self, key: T_vertex_id) -> T_vertex:
            raise KeyError

        def __delitem__(self, key: T_vertex_id) -> None:
            raise KeyError

        def __iter__(self) -> Iterator[T_vertex_id]:
            return iter(())

        def __len__(self) -> int:
            return 0

        def __contains__(self, key: object) -> bool:
            return False

        def __setitem__(self, key: T_vertex_id, value: T_vertex):
            raise RuntimeError(
                "Cannot add a path, " + "traversal not started or no paths requested."
            )

    def __init__(self):
        super().__init__(_PathsDummy.MappingOfNothing(), nographs.vertex_as_id)

    def _check_vertex(self, vertex: T_vertex) -> T_vertex_id:
        """Raise RuntimeError with helpful explanation. This method
        is called by each method of Paths that returns a path as first step.
        So, they all raise the exception."""
        raise RuntimeError(
            "No paths available: " + "Traversal not started or no paths requested."
        )


class PathsOfUnlabeledEdges(Paths[T_vertex, T_vertex_id, Any]):
    """
    Path of edges that are not labeled, i.e., for some starting vertex, an
    edge leading to a specific end vertex is represented only by this end
    vertex.

    This class is not part of the public interface of the library. Its
    signature, methods and implementation can be subject to breaking
    changes even in minor releases. It is not intended to be used by
    application code.

    :param predecessor: The predecessor information of the paths will be
        stored in the given mapping.

    :param vertex_to_id: See `VertexToID` function.
    """

    def __init__(
        self,
        predecessor: VertexIdToVertexMapping[T_vertex_id, T_vertex],
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    ):
        super().__init__(predecessor, vertex_to_id)

    def append_edge(
        self, from_vertex: T_vertex, to_vertex_id: T_vertex_id, to_edge: Any
    ):
        """Create a new path that starts with the existing path to
        from_vertex and ends with the given vertex (resp. id).

        :param from_vertex: The resulting path will start with the path to this vertex.
        :param to_vertex_id: The resulting path will end with an edge to this
           vertex (resp. vertex id).
        :param to_edge: The current class ignores this parameter.
        """
        # This method is used nowhere. Its call is inlined in all algorithms.
        try:
            self._predecessor_collection[to_vertex_id] = from_vertex
        except IndexError:
            # See access_to_vertex_mapping_expect_none for the following:
            assert self._predecessor_wrapper is not None
            self._predecessor_wrapper.extend_and_set(to_vertex_id, from_vertex)

    def __getitem__(self, vertex: T_vertex) -> Sequence[T_vertex]:
        """Sequence of the vertices in the path from the first to the given
        vertex. Internally, a sequence of the vertices in backward order is
        created and then reversed.

        :param vertex: The path ending at this vertex will be returned.
        """
        return tuple(self.iter_vertices_from_start(vertex))


class PathsOfLabeledEdges(Paths[T_vertex, T_vertex_id, T_labels]):
    """
    Path of edges that are labeled, i.e., for some starting vertex, an
    edge leading to a specific end vertex is represented by a tuple that
    starts with the end vertex and, optionally, contains additional data.

    This class is not part of the public interface of the library. Its
    signature, methods and implementation can be subject to breaking
    changes even in minor releases. It is not intended to be used by
    application code.

    :param predecessor: The predecessor information of the paths will
        be stored in the given mapping.

    :param attributes: The edge data of the paths will be stored in
        the given mapping.

    :param vertex_to_id: See `VertexToID` function.
    """

    def __init__(
        self,
        predecessor: VertexIdToVertexMapping[T_vertex_id, T_vertex],
        attributes: VertexIdToPathEdgeDataMapping[T_vertex_id, T_labels],
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    ):
        super().__init__(predecessor, vertex_to_id)
        self._attributes = attributes
        self._attributes_collection: GettableSettableForGearProto[
            T_vertex_id, T_labels, Optional[T_labels]
        ]
        self._attributes_wrapper: Optional[
            VertexSequenceWrapperForMappingProto[
                T_vertex_id, T_labels, Optional[T_labels]
            ]
        ]
        (
            _,
            self._attributes_collection,
            self._attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

    def append_edge(
        self, from_vertex: T_vertex, to_vertex_id: T_vertex_id, to_edge: LabeledOutEdge
    ):
        """Create a new path that starts with the existing path to
        from_vertex and ends with the given vertex (resp. id). The additional
        edge data provided in to_edge after to_vertex is stored in the path,
        too.

        :param from_vertex: The resulting path will start with the path to this vertex.
        :param to_vertex_id: The resulting path will end with an edge to this
           vertex (resp. vertex id).
        :param to_edge: The edge data of this edge will be stored for the ending
           edge of the path.
        """
        # This method is used nowhere. Its call is inlined in all algorithms,
        # for improved speed.
        try:
            self._predecessor_collection[to_vertex_id] = from_vertex
        except IndexError:
            # See access_to_vertex_mapping_expect_none for the following:
            assert self._predecessor_wrapper is not None
            self._predecessor_wrapper.extend_and_set(to_vertex_id, from_vertex)

        data_of_edge = to_edge[-1]
        try:
            self._attributes_collection[to_vertex_id] = data_of_edge
        except IndexError:
            # See access_to_vertex_mapping_expect_none for the following:
            assert self._attributes_wrapper is not None
            self._attributes_wrapper.extend_and_set(to_vertex_id, data_of_edge)

    def _iter_path_edges(
        self, path_edges: Iterator[tuple[T_vertex, T_vertex, T_vertex_id]]
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Iterate given raw edge data tuples und return them as
        UnweightedLabeledFullEdge. Internal support method.

        :param path_edges: tuples (from_vertex, to_vertex, to_vertex_id)
        """
        attributes: Optional[T_labels]
        for from_vertex, vertex, vertex_id in path_edges:
            # to_vertex_id is contained in self._predecessor
            # (see _iter_raw_edges_to_start).
            # So we know: No KeyError or IndexError will occur here, and we will not
            # get None as result.
            path_attributes: Optional[T_labels] = self._attributes_collection[vertex_id]
            assert path_attributes is not None
            # noinspection PyTypeChecker
            res: UnweightedLabeledFullEdge[T_vertex, T_labels] = (
                from_vertex,
                vertex,
                path_attributes,
            )  # PyCharm cannot check this
            yield res

    def iter_labeled_edges_to_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        return self._iter_path_edges(self._iter_raw_edges_to_start(vertex))

    def iter_labeled_edges_from_start(
        self, vertex: T_vertex
    ) -> Iterator[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        return self._iter_path_edges(
            reversed(tuple(self._iter_raw_edges_to_start(vertex)))
        )

    def __getitem__(
        self, vertex: T_vertex
    ) -> Sequence[UnweightedLabeledFullEdge[T_vertex, T_labels]]:
        """Sequence of the edges in the path from the first to the given
        vertex. Internally, a sequence of all the edges in backward order is
        created and then reversed.

        :param vertex: The path ending at this vertex will be returned.
        """
        return tuple(self.iter_labeled_edges_from_start(vertex))
