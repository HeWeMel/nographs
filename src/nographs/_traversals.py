from __future__ import annotations

import array
import copy
import itertools
from abc import ABC, abstractmethod
from collections.abc import (
    Callable,
    Iterator,
    Iterable,
)
from heapq import heapify, heappop, heappush
from numbers import Real
from typing import Optional, Any, Union, cast, overload, Generic, Literal

from ._gear_collections import (
    access_to_vertex_set,
    access_to_vertex_mapping,
    access_to_vertex_mapping_expect_none,
)
from ._gears import (
    GearWithoutDistances,
    Gear,
    GearDefault,
    VertexIdSet,
    VertexIdToVertexMapping,
    VertexIdToDistanceMapping,
    VertexIdToPathEdgeDataMapping,
    MutableSequenceOfVertices,
)
from ._paths import (
    Paths,
    DummyPredecessorOrAttributesMapping,
    PathsDummy,
)
from ._strategies import (
    StrRepr,
    Strategy,
    T_strategy,
    NextVertices,
    NextEdges,
    NextLabeledEdges,
    NextWeightedEdges,
    NextWeightedLabeledEdges,
    NextEdgesOrVertices,
    NextWeightedMaybeLabeledEdges,
    iter_start_ids,
    iter_start_vertices_and_ids,
    define_visited,
    define_distances,
    create_paths,
    NoIterator,
    NoVisitedSet,
    NoDistancesMapping,
)
from ._types import (
    T_vertex,
    T_vertex_id,
    T_weight,
    T_labels,
    VertexToID,
    vertex_as_id,
    WeightedOutEdge,
    WeightedFullEdge,
)


# --------------- internal support functions -------------


def _start_from_needs_traversal_object(obj: Any) -> None:
    if not isinstance(obj, Traversal):
        raise RuntimeError(
            "Method start_from can only be called on a Traversal object."
        )


def _create_unified_next(
    next_vertices: Optional[NextVertices[T_vertex, T_strategy]],
    next_edges: Optional[NextEdges[T_vertex, T_strategy]],
    next_labeled_edges: Optional[NextLabeledEdges[T_vertex, T_strategy, T_labels]],
) -> tuple[NextEdgesOrVertices[T_vertex, T_strategy, T_labels], bool, bool]:
    """Check configuration of given next_vertices, next_edges, and next_labeled_edges
    and calculate unified NextEdgesOrVertices
    and whether we have edges with data (weights and/or labels) and/or labeled_edges.
    """
    next_edges_or_vertices: NextEdgesOrVertices[T_vertex, T_strategy, T_labels]
    if next_vertices is not None:
        if next_edges is not None:
            raise RuntimeError("Both next_vertices and next_edges provided.")
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_vertices and next_labeled_edges provided.")
        next_edges_or_vertices = next_vertices
        edges_with_data = False
        labeled_edges = False
    elif next_edges is not None:
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_edges and next_labeled_edges provided.")
        next_edges_or_vertices = next_edges
        edges_with_data = True
        labeled_edges = False
    else:
        if next_labeled_edges is None:
            raise RuntimeError(
                "Neither next_vertices nor next_edges "
                + "nor next_labeled_edges provided."
            )
        next_edges_or_vertices = next_labeled_edges
        edges_with_data = True
        labeled_edges = True
    return next_edges_or_vertices, edges_with_data, labeled_edges


def _create_unified_next_weighted(
    next_edges: Optional[NextWeightedEdges[T_vertex, T_strategy, T_weight]],
    next_labeled_edges: Optional[
        NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels]
    ],
) -> tuple[
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels], bool
]:
    """Check configuration of given next_edges and next_labeled_edges and calculate
    unified _NextWeightedMaybeLabeledEdges[] and whether we have labeled_edges."""
    next_maybe_labeled_edges: NextWeightedMaybeLabeledEdges[
        T_vertex, T_strategy, T_weight, T_labels
    ]
    if next_edges is not None:
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_edges and next_labeled_edges provided.")
        next_maybe_labeled_edges = next_edges
        labeled_edges = False
    else:
        if next_labeled_edges is None:
            raise RuntimeError("Neither next_edges and next_labeled_edges provided.")
        next_maybe_labeled_edges = next_labeled_edges
        labeled_edges = True
    return next_maybe_labeled_edges, labeled_edges


# -- traversal strategies for unweighted graphs with or without edge labels --


class Traversal(Strategy[T_vertex, T_vertex_id, T_labels]):
    """
    Abstract Class. Its subclasses provide methods to iterate through vertices
    and edges using some specific traversal strategies.
    """

    @abstractmethod
    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    ) -> None:
        # -- attributes of graph adaptation
        self._labeled_edges = labeled_edges
        self._is_tree = is_tree
        self._vertex_to_id = vertex_to_id

        # -- general attributes set and needed by all traversal strategies
        self._generator: Iterator[T_vertex] = NoIterator[T_vertex]()
        self._start_vertices: Iterable[T_vertex] = tuple[T_vertex]()
        self._build_paths: bool = False
        self._calculation_limit: Optional[int] = None

        # -- attributes for path data, needed by all traversal strategies
        self.paths: Paths[T_vertex, T_vertex_id, T_labels] = PathsDummy[
            T_vertex, T_vertex_id, T_labels
        ](vertex_to_id)
        """ The container *paths* holds the created paths, if path creation has been
        demanded. If labeled edges were provided (parameter *next_labeled_edges*), the
        paths contain them instead of just vertices.
        """
        self._predecessors: VertexIdToVertexMapping[
            T_vertex_id, T_vertex
        ] = DummyPredecessorOrAttributesMapping[T_vertex_id, T_vertex]()
        self._attributes: VertexIdToPathEdgeDataMapping[
            T_vertex_id, T_labels
        ] = DummyPredecessorOrAttributesMapping[T_vertex_id, T_labels]()

    def __iter__(
        self,
    ) -> Iterator[T_vertex]:  # Type alias needed do to a sphinx limitation
        """
        Return the iterator of a started traversal. This allows for using a
        `Traversal` in *for* loops or as parameter to a call of function
        *next()*.

        Subsequent calls return the same iterator again. This allows for using
        the same `Traversal` in subsequent *for* loops or *next()* calls, as
        long as the iterator is not exhausted.

        The iterator yields vertices reported by the traversal algorithm.
        When a vertex is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`)."""
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go can only be called on a Traversal object.")
        return self._generator

    def __next__(self) -> T_vertex:
        """Returns the next vertex reported by the (started) traversal. This
        allows for calls like *next(traversal)*.

        Delegates to the iterator of the traversal."""
        return next(self._generator)

    def go_for_vertices_in(
        self, vertices: Iterable[T_vertex], fail_silently: bool = False
    ) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator that fetches vertices
        from the traversal, reports a vertex if it is in *vertices*, and stops when
        all the *vertices* have been found and reported.

        If the iterator has no more vertices to report (graph is exhausted) without
        having found all the *vertices*, KeyError is raised, or the traversal just
        terminates, if a silent fail is demanded.

        If *vertices* does not provide any vertices, an empty iterator is returned.

        If a `VertexToID` function is used, the method searches for vertices
        that have the same id as one of the *vertices*.

        Whenever a vertex is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).

        :param vertices: Vertices to find
        :param fail_silently: Terminate, but do not raise KeyError, when graph
            is exhausted.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_vertices_in can only be called "
                + "on a Traversal object."
            )
        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function

        def my_generator() -> Iterator[T_vertex]:
            vertex_to_id = self._vertex_to_id
            if vertex_to_id == vertex_as_id:
                vertex_set = set(cast(Iterable[T_vertex_id], vertices))
                v_count = len(vertex_set)
                if v_count:
                    for v in self._generator:
                        if v not in vertex_set:
                            continue
                        yield v
                        v_count -= 1
                        if v_count == 0:
                            break
            else:
                vertex_set = set(vertex_to_id(vertex) for vertex in vertices)
                v_count = len(vertex_set)
                if v_count:
                    for v in self._generator:
                        if vertex_to_id(v) not in vertex_set:
                            continue
                        yield v
                        v_count -= 1
                        if v_count == 0:
                            break
            if v_count > 0 and not fail_silently:
                raise KeyError("Not all of the given vertices have been found")

        return my_generator()

    @overload
    def go_to(
        self, vertex: T_vertex, fail_silently: Literal[False] = False
    ) -> T_vertex:
        ...

    @overload
    def go_to(
        self, vertex: T_vertex, fail_silently: Literal[True]
    ) -> Optional[T_vertex]:
        ...

    def go_to(
        self, vertex: T_vertex, fail_silently: bool = False
    ) -> Optional[T_vertex]:
        """
        For a started traversal, walk through the graph, stop at *vertex* and
        return it. If the traversal ends (traversal iterator is exhausted) without
        having found *vertex*, raise KeyError, or return None,
        if a silent fail is demanded.

        If a `VertexToID` function is used, the method searches for a vertex
        that has the same id as the given *vertex*.

        When *vertex* is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).

        :param vertex: Stop search at this vertex.

        :param fail_silently: Terminate and return None, but do not raise KeyError,
            when graph is exhausted.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go_to can only be called on a Traversal object.")

        vertex_to_id = self._vertex_to_id
        if vertex_to_id == vertex_as_id:
            for v in self._generator:
                if v != vertex:
                    continue
                return v
            else:
                if fail_silently:
                    return None
                else:
                    raise KeyError("Vertex not found, graph exhausted.")
        else:
            vertex_id = vertex_to_id(vertex)
            for v in self._generator:
                if vertex_to_id(v) != vertex_id:
                    continue
                return v
            else:
                if fail_silently:
                    return None
                else:
                    raise KeyError("Vertex not found, graph exhausted.")

    def _start_from(
        self,
        start_vertex: Optional[T_vertex],
        start_vertices: Optional[Iterable[T_vertex]],
        build_paths: bool,
        calculation_limit: Optional[int],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    ) -> None:
        # Check start vertices options. Compute multi-vertices form from single vertex.
        if start_vertex is not None:
            if start_vertices is not None:
                raise RuntimeError("Both start_vertex and start_vertices provided.")
            self._start_vertices = (start_vertex,)
        else:
            if start_vertices is None:
                raise RuntimeError("Neither start_vertex nor start_vertices provided.")
            self._start_vertices = start_vertices

        # Create and store path container and path setting
        self._build_paths = build_paths
        self.paths, self._predecessors, self._attributes = create_paths(
            build_paths,
            gear,
            self._labeled_edges,
            self._vertex_to_id,
            self._start_vertices,
        )

        # store calculation limit
        self._calculation_limit = calculation_limit

    def _start(self) -> None:
        self._generator = self._traverse()

    @abstractmethod
    def _traverse(self) -> Iterator[T_vertex]:
        """Has to be implemented in subclass"""

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Convert a Paths object to an object that can be converted to a str.
        # Paths in the paths object are only valid for reported vertices,
        # and these do not need to be hashable. So, we cannot convert them
        # to a dict and from there to a string.
        del state["paths"]
        if vertices is not None:
            state["paths"] = (
                StrRepr.from_iterable(
                    (vertex, self.paths[vertex]) for vertex in vertices
                )
                if self._build_paths
                else dict()
            )
        super()._improve_state(state, vertices)


# -------------- Traversal strategies for unweighted edges -----------------


class _TraversalWithoutWeights(Traversal[T_vertex, T_vertex_id, T_labels], ABC):
    """Internal: A traversal without weight type and distances collection, but
    with attribute visited."""

    def __init__(
        self,
        edges_with_data: bool,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    ) -> None:
        super().__init__(labeled_edges, is_tree, vertex_to_id)
        self._edges_with_data = edges_with_data
        self._gear = gear
        self.visited: VertexIdSet[T_vertex_id] = NoVisitedSet[T_vertex_id]()
        """ A collection that contains the visited vertices (resp. their hashable ids
        from vertex_to_id). After an exhaustive search, it contains
        the vertices (resp. vertex ids) reachable from the start vertices.
        """

    def _start_with_or_without_labels_from(
        self,
        start_vertex: Optional[T_vertex],
        start_vertices: Optional[Iterable[T_vertex]],
        build_paths: bool,
        calculation_limit: Optional[int],
        already_visited: Optional[VertexIdSet[T_vertex_id]],
    ) -> None:
        _start_from_needs_traversal_object(self)
        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            self._gear,
        )
        self.visited = define_visited(
            self._gear,
            already_visited,
            iter_start_ids(self._start_vertices, self._vertex_to_id),
            self._is_tree,
        )
        super()._start()

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Visited, a MutableSet, is typically not ordered. str(self.visited)
        # results in different strings for different interpreters (PyPy) and
        # the keys are not sorted. Here, we create a normalized description.
        del state["visited"]
        state["visited"] = StrRepr.from_set(self.visited)
        super()._improve_state(state, vertices)


class _TraversalWithoutWeightsBasic(
    _TraversalWithoutWeights[T_vertex, T_vertex_id, T_labels], ABC
):
    @abstractmethod
    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> Traversal[T_vertex, T_vertex_id, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The vertices the search should start at. Only
            allowed if start_vertex equals None.

        :param build_paths: If true, build paths from some start vertex to each visited
            vertex. Paths of start vertices are empty paths.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param already_visited: If provided, this set is used instead of an internal
            one to keep vertices (resp. their hashable ids from vertex_to_id),
            that have already been visited. This parameter can be used to get online
            access to the internal bookkeeping of visited vertices, or to preload
            vertices that should never be visited, or to provide your own way for
            storing the information that a vertex has already been visited.

        :return: Traversal, that has been started, e.g., statements like *iter()*,
            *next()*, *for* and the methods "go*" of the Traversal can now be used.
        """


class _TraversalWithoutWeightsDFS(
    _TraversalWithoutWeights[T_vertex, T_vertex_id, T_labels], ABC
):
    @abstractmethod
    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        compute_depth: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> Traversal[T_vertex, T_vertex_id, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The vertices the search should start at. Only
            allowed if start_vertex equals None.

        :param build_paths: If true, build paths from some start vertex to each visited
            vertex.

        :param compute_depth: For each reported vertex, provide the search depth is has
            been found at (Note: Often, this information is not helpful, and the
            computation increases memory consumption and runtime).

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param already_visited: If provided, this set is used instead of an internal
            one to keep vertices (resp. their hashable ids from vertex_to_id),
            that have already been visited. This parameter can be used to get online
            access to the internal bookkeeping of visited vertices, or to preload
            vertices that should never be visited, or to provide your own way for
            storing the information that a vertex has already been visited.

        :return: Traversal, that has been started, e.g., statements like *iter()*,
            *next()*, *for* and the methods "go*" of the Traversal can now be used.
        """


class TraversalBreadthFirstFlex(
    _TraversalWithoutWeightsBasic[T_vertex, T_vertex_id, T_labels]
):

    """
    Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: See `NextVertices` function. If None, provide next_edges
     or next_labeled_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertices equals
      None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
      next_vertices and next_edges equal None. If given, paths will record the given
      labels.

    :param is_tree: bool: If it is certain, that during each traversal run,
     each vertex can be reached only once, is_tree can be set to True. This
     improves performance, but attribute *visited* of the traversal will not be
     updated during and after the traversal.

    **Algorithm:** Breadth First Search, non-recursive, based on FIFO queue,
    vertices are reported when they are first "seen".

    **Properties:** Reports and expands vertices in breadth first order, i.e.,
    with ascending depth (edge count of the path with the fewest edges from a start
    vertex). All computed paths are *shortest paths* , i.e., paths with minimal number
    of edges from a start vertex to their end vertex.
    A vertex is regarded as visited when it has been reported or if it is a start
    vertex.

    **Input:** Directed graph. Unlabeled or labeled edges. One or more start
    vertices. Optional calculation limit.

    **Search state:** When a vertex is
    *expanded* (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        (
            self._next_edge_or_vertex,
            edges_with_data,
            labeled_edges,
        ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        self.depth: int = -1  # value not used, initialized during traversal
        """ At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        For the special case of TraversalBreadthFirst, it equals the
        *depth of the vertex* (minimal number of edges needed to come to it
        from a start vertex).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self._report_depth_increase = False

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
        _report_depth_increase: bool = False,  # hidden parameter for internal use
    ) -> TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]:
        _start_from_needs_traversal_object(self)
        self._start_with_or_without_labels_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
        )
        self._report_depth_increase = _report_depth_increase
        self.depth = 0
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        report_depth_increase = self._report_depth_increase
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Copy _TraversalWithoutWeights attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex
        visited = self.visited

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            index_and_bit_method,
        ) = access_to_vertex_set(visited)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Initialize method specific bookkeeping -----

        # Two lists used as FIFO queue with just two buckets
        # (using a queue and counting down the size of current depth horizon is slower,
        # and creating a new list instead of clear() is also slower)

        to_expand = self._gear.sequence_of_vertices(self._start_vertices)
        next_to_expand = self._gear.sequence_of_vertices(())

        prev_traversal = copy.copy(self)  # copy of self, for keeping previous depth
        self.depth = 1  # used for reporting (prev_traversal starts at 0)

        # Get method references of specific bookkeeping (avoid attribute resolution)
        to_expand_append = to_expand.append
        next_to_expand_append = next_to_expand.append

        # ----- Typing preparation of inner loop -----

        # The following type Any opens no space for typing problems, since
        # the content of next_edge_or_vertex is type checked and iterates
        # objects of type T_vertex for edges_with_data==False and otherwise of
        # one of the following:
        #   WeightedUnlabeledOutEdge[T_vertex, Any],
        #   UnweightedLabeledOutEdge[T_vertex, T_labels],
        #   WeightedLabeledOutEdge[T_vertex, Any, T_labels],
        # And if labeled_edges==True, the first case is excluded.
        # (Any alternative code version of the inner loop without
        #  Any or 'type: ignore' is slower)
        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        edge_data: T_labels  # Re-establish type "after" the "hole"

        # ----- Inner loop -----

        while to_expand:
            for vertex in to_expand:
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    if not is_tree or build_paths:
                        n_id: T_vertex_id = (
                            maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                            if maybe_vertex_to_id
                            else neighbor
                        )

                        # If not is_tree: Ignore neighbor if already seen, and
                        # else include its ID in visited set.
                        # (If-nesting optimized for first case)
                        if not is_tree and not visited_uses_sequence:
                            # Standard implementation for "normal" MutableMapping
                            if n_id in visited:
                                continue
                            visited_add(n_id)
                        elif not is_tree:
                            if visited_uses_bits:
                                # Same as above, but with bits in byte sequence
                                sequence_key, bit_number = index_and_bit_method(n_id, 8)
                                bit_mask = 1 << bit_number
                                try:
                                    value = visited_sequence[sequence_key]
                                    if value & bit_mask:
                                        continue
                                    visited_sequence[sequence_key] = value | bit_mask
                                except IndexError:
                                    visited_wrapper.extend_and_set(
                                        sequence_key, bit_mask
                                    )
                            else:
                                # Same as above, but with booleans in byte sequence
                                try:
                                    if visited_sequence[n_id]:
                                        continue
                                    visited_sequence[n_id] = True
                                except IndexError:
                                    visited_wrapper.extend_and_set(n_id, True)

                        if build_paths:
                            # Store the predecessor (vertex) of the neighbor
                            try:
                                predecessors_sequence[n_id] = vertex
                            except IndexError:
                                predecessors_wrapper.extend_and_set(n_id, vertex)
                            # Store the labels of the edge to the neighbor
                            if labeled_edges:
                                edge_data = edge_or_vertex[-1]
                                try:
                                    attributes_sequence[n_id] = edge_data
                                except IndexError:
                                    attributes_wrapper.extend_and_set(n_id, edge_data)

                    # Vertex has been seen, report it now
                    yield neighbor
                    # Needs to be expanded in the next round
                    next_to_expand_append(neighbor)

            if report_depth_increase and next_to_expand:
                # We are not finished yet, because we found new vertices to expand,
                # and we are about to increase the depth now, and it is demanded
                # to report this situation by reporting the last vertex reported so far
                # again. So we report it again.
                yield next_to_expand[-1]

            # Update external views (reporting/expanding) on depth
            self.depth += 1
            prev_traversal.depth += 1
            # Prepare state for next depth level of vertices
            to_expand, next_to_expand, to_expand_append, next_to_expand_append = (
                next_to_expand,
                to_expand,
                next_to_expand_append,
                to_expand_append,
            )
            del next_to_expand[:]

    def go_for_depth_range(self, start: int, stop: int) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator. During the traversal,
        the iterator skips vertices as long as their depth is lower than *start*.
        From then on, is reports the found vertices. It stops when the reached depth
        is equal to or higher than *stop*.

        Note: The first vertex with a depth equal or higher than *stop* will be
        consumed from the traversal, but will not be reported, so it is lost (compare
        *itertools.takewhile*).

        :param start: Vertices lower than this are skipped.
        :param stop: Reporting stops when reached depth is equal or higher than this.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_depth_range can only be called "
                + "on a Traversal object."
            )

        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function
        def my_generator() -> Iterator[T_vertex]:
            for v in self._generator:
                if self.depth >= start:
                    if self.depth < stop:
                        yield v
                    break
            for v in self._generator:
                if self.depth >= stop:
                    break
                yield v

        return my_generator()


class TraversalBreadthFirst(
    Generic[T_vertex, T_labels], TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]
):
    """
    Eases the use of `TraversalBreadthFirstFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    Uses the following standard arguments for the respective parameters of
    the parent class:

    - vertex_to_id = `vertex_as_id`
    - gear = `GearDefault`
    - `T_vertex_id` = `T_vertex`

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


class TraversalDepthFirstFlex(
    _TraversalWithoutWeightsDFS[T_vertex, T_vertex_id, T_labels]
):
    """
    Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: See `NextVertices` function. If None, provide next_edges
     or next_labeled_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertices equals
     None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
      next_vertices and next_edges equal None. If given, paths will record the given
      labels.

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
        can be reached only once, is_tree can be set to True. This improves
        performance, but attribute *visited* of the traversal will not be updated
        during and after the traversal.

    **Algorithm:** Depth First Search ("BFS"), non-recursive, based on stack,
    vertices are reported when they are about to be expanded (neighbors read from the
    graph).

    **Properties:** Follows edges to new vertices (and reports and expands them) as
    long as possible, and goes back a step and follows further edges that start at some
    visited vertex only if necessary to come to new vertices.
    A vertex is regarded as visited when it has been reported or if it is a start
    vertex.

    **Input:** Directed graph. One or more start vertices. Vertices must be
    hashable, or hashable id can be provided. Unlabeled or labeled edges. Optional
    calculation limit.

    **Search state:** When a vertex is
    *expanded* (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalDepthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalDepthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalDepthFirstFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        (
            self._next_edge_or_vertex,
            edges_with_data,
            labeled_edges,
        ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        self.depth: int = -1  # value not used
        """ If depth computation has been demanded:
        At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self._compute_depth = False  # value not used
        self._allow_reordering = False  # value not used

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        compute_depth: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> TraversalDepthFirstFlex[T_vertex, T_vertex_id, T_labels]:
        _start_from_needs_traversal_object(self)
        self._start_with_or_without_labels_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
        )
        self._compute_depth = compute_depth
        self.depth = 0
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        compute_depth = self._compute_depth
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        paths = self.paths
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1  # Allows for limit check by zero check

        # Copy _TraversalWithoutWeights attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex
        visited = self.visited

        # Create booleans (avoid checks with "is", make decisions clear)
        check_and_set_visited_on_expand = not is_tree
        check_visited_when_seen = paths and not is_tree
        # An alternative is, to choose here: not is_tree.
        # This always checks and avoids taking already visited vertices
        # on top of the stack. It saves space, but costs runtime.
        # For an average of n children per node, it reduces the
        # space needed by the stack by factor 1/(n/2), e.g. for 6
        # children, it reduces memory consumption to 2/3, i.e., by 1/3.
        # But the runtime increase is seen as more important here, so the
        # alternative is not chosen. The application can often just
        # use TraversalNeighborsThenDepthFlex, that brings the advantage
        # without the disadvantage.

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            index_and_bit_method,
        ) = access_to_vertex_set(visited)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Initialize method specific bookkeeping -----

        depth = -1  # The inner loop starts with incrementing, so, we pre-decrement
        if not compute_depth:
            self.depth = depth  # In this case, we leave the -1 the whole time

        # vertices to enter or leave
        to_visit = self._gear.sequence_of_vertices(self._start_vertices)
        to_visit_append = to_visit.append
        to_visit_pop = to_visit.pop

        if compute_depth:
            # Sequence of flag bytes (store in a Q array) marking the vertices to leave
            # by 1 and the vertices to enter by 0.
            # Initially, store a zero flag for each start vertex.
            to_leave_markers = array.array("B", itertools.repeat(False, len(to_visit)))
            to_leave_markers_pop = to_leave_markers.pop
            to_leave_markers_append = to_leave_markers.append
        else:
            # the following is needed to replace the real depth with at least
            # the information whether it is 0 oder higher.
            # This does not work if we have no start vertices, but in this case,
            # we can just stop working because we will not report results anyway
            if len(to_visit) == 0:
                return
            top_start_vertex: Optional[T_vertex] = to_visit[-1]

        # ----- Typing preparation of inner loop (for details see BFS) -----

        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        data_of_edge: T_labels  # Re-establish type "after" the "hole"

        # ----- Inner loop -----

        while to_visit:
            vertex = to_visit_pop()  # Enter first added vertex first
            if compute_depth:
                depth += 1
                # (noinspection necessary due to bug PY-9479, also below...)
                # noinspection PyUnboundLocalVariable
                while to_leave_markers_pop():
                    depth -= 1  # Got marker "leave a vertex", update depth
                # Update external view on depth
                self.depth = depth
                # Store marker True: when reached, we are leaving a vertex
                # noinspection PyUnboundLocalVariable
                to_leave_markers_append(True)
            else:
                # if vertex is top_start_vertex:
                # noinspection PyUnboundLocalVariable
                if vertex is top_start_vertex:  # "is" is used on purpose
                    depth = 0  # is start vertex
                    if to_visit:
                        top_start_vertex = to_visit[-1]  # new top start vertex
                    else:
                        top_start_vertex = None
                else:
                    depth = 1  # is no start vertex

            if depth:  # Vertex is no start vertex, ready to expand: Report it now
                if check_and_set_visited_on_expand:
                    # Ignore neighbor if already visited, and
                    # else include its ID in visited set.
                    v_id: T_vertex_id = (
                        maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else vertex
                    )
                    # (If-nesting optimized for first case)
                    if not visited_uses_sequence:
                        # Standard implementation for "normal" MutableMapping
                        if v_id in visited:
                            continue
                        visited_add(v_id)
                    elif visited_uses_bits:
                        # Same as above, but with bits in byte sequence
                        sequence_key, bit_number = index_and_bit_method(v_id, 8)
                        bit_mask = 1 << bit_number
                        try:
                            value = visited_sequence[sequence_key]
                            if value & bit_mask:
                                continue
                            visited_sequence[sequence_key] = value | bit_mask
                        except IndexError:
                            visited_wrapper.extend_and_set(sequence_key, bit_mask)
                    else:
                        # Same as above, but with booleans in byte sequence
                        try:
                            if visited_sequence[v_id]:
                                continue
                            visited_sequence[v_id] = True
                        except IndexError:
                            visited_wrapper.extend_and_set(v_id, True)

                # (Note: Each seen vertex can enter the stack only once, because later
                # seen identical vertices are blocked. The exception are start vertices,
                # but they are not regarded here. Thus: "Each vertex is reported
                # at most once.")
                yield vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                if check_visited_when_seen or build_paths:
                    n_id: T_vertex_id = (
                        maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else neighbor
                    )
                    # Ignore neighbor if already visited/expanded, i.e., not put it
                    # onto the stack to_visit.
                    # If we do not create paths, this is just a variant of the
                    # algorithms: The results do not change, since visited vertices
                    # will not be visited again.
                    # But in case that we create paths, it is necessary: We like to
                    # store the predecessor of the neighbor directly here, when we first
                    # see the neighbor and have the predecessor still present. And we
                    # need to make sure not to overwrite the real predecessor of a
                    # vertex the has been already expanded. If
                    # the neighbor has not been visited, it is safe (and necessary)
                    # to overwrite a pre-existing predecessor of neighbor because
                    # a later found edge (predecessor, neighbor) will be evaluated
                    # first (to_visit is a stack) and so, this predecessor need to
                    # "win".
                    # (If-nesting optimized for first case)
                    if check_visited_when_seen and not visited_uses_sequence:
                        # Standard implementation for "normal" MutableMapping:
                        if n_id in visited:
                            continue
                    elif check_visited_when_seen and visited_uses_bits:
                        # Same as above, but with bits in byte sequence
                        sequence_key, bit_number = index_and_bit_method(n_id, 8)
                        try:
                            if visited_sequence[sequence_key] & (1 << bit_number):
                                continue
                        except IndexError:
                            pass
                    elif check_visited_when_seen:
                        # Same as above, but with booleans in byte sequence
                        try:
                            if visited_sequence[n_id]:
                                continue
                        except IndexError:
                            pass
                    if build_paths:
                        # Store the predecessor (vertex) of the neighbor
                        try:
                            predecessors_sequence[n_id] = vertex
                        except IndexError:
                            predecessors_wrapper.extend_and_set(n_id, vertex)
                        # Store the labels of the edge to the neighbor
                        if labeled_edges:
                            data_of_edge = edge_or_vertex[-1]
                            try:
                                attributes_sequence[n_id] = data_of_edge
                            except IndexError:
                                attributes_wrapper.extend_and_set(n_id, data_of_edge)

                # Needs to be visited, in stack order
                to_visit_append(neighbor)

                if compute_depth:
                    # Store marker False: when reached, we are entering a vertex
                    to_leave_markers_append(False)


class TraversalDepthFirst(
    Generic[T_vertex, T_labels], TraversalDepthFirstFlex[T_vertex, T_vertex, T_labels]
):
    """
    Eases the use of `TraversalDepthFirstFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    Uses the following standard arguments for the respective parameters of
    the parent class:

    - vertex_to_id = `vertex_as_id`
    - gear = `GearDefault`
    - `T_vertex_id` = `T_vertex`

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalDepthFirstFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[T_vertex, TraversalDepthFirstFlex[T_vertex, T_vertex, T_labels]]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalDepthFirstFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


class TraversalNeighborsThenDepthFlex(
    _TraversalWithoutWeightsDFS[T_vertex, T_vertex_id, T_labels]
):
    """
    Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: See `NextVertices` function. If None, provide next_edges
     or next_labeled_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertices equals
     None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
      next_vertices and next_edges equal None. If given, paths will record the given
      labels.

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
        can be reached only once, is_tree can be set to True. This improves
        performance, but attribute *visited* of the traversal will not be updated
        during and after the traversal.

    **Algorithm:** Variant of Depth First Search ("DFS"), non-recursive, based on stack,
    vertices are reported when they are seen (neighbors read from the graph).

    **Properties:** Like `nographs.TraversalDepthFirst`, but first reports all
    neighbors of the current vertex and then goes deeper.
    A vertex is regarded as visited when it has been reported or if it is a start
    vertex.

    **Input:** Directed graph. One or more start vertices. Vertices must be
    hashable, or hashable id can be provided. Unlabeled or labeled edges. Optional
    calculation limit.

    **Search state:** When a vertex is
    *expanded* (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            NextVertices[
                T_vertex,
                TraversalNeighborsThenDepthFlex[T_vertex, T_vertex_id, T_labels],
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex,
                TraversalNeighborsThenDepthFlex[T_vertex, T_vertex_id, T_labels],
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalNeighborsThenDepthFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        (
            self._next_edge_or_vertex,
            edges_with_data,
            labeled_edges,
        ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        self.depth: int = -1  # value not used
        """ If depth computation has been demanded:
        At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self._compute_depth = False  # value not used

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        compute_depth: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> TraversalNeighborsThenDepthFlex[T_vertex, T_vertex_id, T_labels]:
        _start_from_needs_traversal_object(self)
        self._start_with_or_without_labels_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
        )
        self.depth = 0
        self._compute_depth = compute_depth
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        compute_depth = self._compute_depth
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1  # Allows for limit check by zero check

        # Copy TraversalWithoutWeights attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex
        visited = self.visited

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            visited_index_and_bit_method,
        ) = access_to_vertex_set(visited)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Initialize method specific bookkeeping -----

        depth = -1  # The inner loop starts with incrementing, so, we pre-decrement
        if not compute_depth:
            self.depth = depth  # In this case, we leave the -1 the whole time
        prev_traversal = copy.copy(self)  # copy of self, for keeping previous depth

        # vertices to expand
        to_expand = self._gear.sequence_of_vertices(self._start_vertices)
        to_expand_append = to_expand.append
        to_expand_pop = to_expand.pop

        if compute_depth:
            # Sequence of flag bytes (store in a Q array) marking the vertices to leave
            # by 1 and the vertices to enter (these are in to_expand) by 0.
            # Initially, store a zero flag for each start vertex.
            to_leave_marker = array.array("B", itertools.repeat(False, len(to_expand)))
            to_leave_marker_pop = to_leave_marker.pop
            to_leave_marker_append = to_leave_marker.append

        # ----- Typing preparation of inner loop (for details see BFS) -----

        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        data_of_edge: T_labels  # Re-establish type "after" the "hole"

        # ----- Inner loop -----

        while to_expand:
            vertex = to_expand_pop()  # Enter first added vertex first
            if compute_depth:
                depth += 1
                # noinspection PyUnboundLocalVariable
                while to_leave_marker_pop():
                    depth -= 1  # Got marker "leave a vertex", update depth
                # Update external view on depth
                prev_traversal.depth = depth
                self.depth = depth + 1
                # Store marker True: when reached, we are leaving a vertex
                # noinspection PyUnboundLocalVariable
                to_leave_marker_append(True)

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                if not is_tree or build_paths:
                    n_id: T_vertex_id = (
                        maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else neighbor
                    )
                    # Ignore neighbor if already visited/expanded, i.e., not put it
                    # onto the stack to_expand.
                    # (If-nesting optimized for first case)
                    if not is_tree and not visited_uses_sequence:
                        # Standard implementation for "normal" MutableMapping:
                        if n_id in visited:
                            continue
                        visited_add(n_id)
                    elif not is_tree and visited_uses_bits:
                        # Same as above, but with bits in byte sequence
                        sequence_key, bit_number = visited_index_and_bit_method(n_id, 8)
                        bit_mask = 1 << bit_number
                        try:
                            value = visited_sequence[sequence_key]
                            if value & bit_mask:
                                continue
                            visited_sequence[sequence_key] = value | bit_mask
                        except IndexError:
                            visited_wrapper.extend_and_set(sequence_key, bit_mask)
                    elif not is_tree:
                        # Same as above, but with booleans in byte sequence
                        try:
                            if visited_sequence[n_id]:
                                continue
                            visited_sequence[n_id] = True
                        except IndexError:
                            visited_wrapper.extend_and_set(n_id, True)
                    if build_paths:
                        # Store the predecessor (vertex) of the neighbor
                        try:
                            predecessors_sequence[n_id] = vertex
                        except IndexError:
                            predecessors_wrapper.extend_and_set(n_id, vertex)
                        # Store the labels of the edge to the neighbor
                        if labeled_edges:
                            data_of_edge = edge_or_vertex[-1]
                            try:
                                attributes_sequence[n_id] = data_of_edge
                            except IndexError:
                                attributes_wrapper.extend_and_set(n_id, data_of_edge)

                yield neighbor

                # Needs to be expanded, in stack order
                to_expand_append(neighbor)

                if compute_depth:
                    # Store marker False: when reached, we are entering a vertex
                    to_leave_marker_append(False)


class TraversalNeighborsThenDepth(
    Generic[T_vertex, T_labels],
    TraversalNeighborsThenDepthFlex[T_vertex, T_vertex, T_labels],
):
    """
    Eases the use of `TraversalNeighborsThenDepthFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    Uses the following standard arguments for the respective parameters of
    the parent class:

    - vertex_to_id = `vertex_as_id`
    - gear = `GearDefault`
    - `T_vertex_id` = `T_vertex`

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalNeighborsThenDepthFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalNeighborsThenDepthFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalNeighborsThenDepthFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


class TraversalTopologicalSortFlex(
    _TraversalWithoutWeightsBasic[T_vertex, T_vertex_id, T_labels]
):
    """
    Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: See `NextVertices` function. If None, provide next_edges
     or next_labeled_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertex equals
       None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
      next_vertices and next_edges equal None. If given, paths will record the given
      labels.

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
       can be reached only once, is_tree can be set to True. This improves performance,
       but attribute *visited* of the traversal will not be updated during and after
       the traversal.

    **Algorithm:** Topological Search, non-recursive, based on stack, vertices are
    reported when they "are left" for backtracking.

    **Properties:** Vertices are reported in topological ordering, i.e. a linear
    ordering of the vertices such that for every directed edge *uv* from vertex *u* to
    vertex *v* ("*u* depends on *v*"), *v* comes before *u* in the ordering. If the
    graph contains a cycle that can be reached within the sorting process, a
    RuntimeError exception is raised and a cyclic path from a start vertex is provided.

    Vertices are expanded following the strategy `nographs.TraversalDepthFirst`.

    For topological search, a vertex is regarded as visited when it has been expanded
    (see search state) or if it is a start vertex. Note this difference in comparison
    to other traversals that mark a vertex as visited when it is reported.

    **Input:** Directed graph. One or more start vertices. Vertices must be
    hashable, or hashable id can be provided. Unlabeled or labeled edges. Optional
    calculation limit.

    **Search state:** When a vertex is
    *expanded* (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        (
            self._next_edge_or_vertex,
            edges_with_data,
            labeled_edges,
        ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        # the following values are not used, and initialized during traversal
        self.depth: int = -1
        """  At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self.cycle_from_start: list[T_vertex] = []
        """ If the graph contains a cycle that can be reached within the sorting
        process, a RuntimeError exception is raised, and the traversal provides
        a cyclic path from a start vertex in attribute cycle_from_start."""

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The vertices the search should start at. Only
            allowed if start_vertex equals None.

        :param build_paths: If true, build paths from some start vertex to each visited
            vertex.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param already_visited: If provided, this set is used instead of an internal
            one to keep vertices (resp. their hashable ids from vertex_to_id),
            that have already been visited. This parameter can be used to get online
            access to the internal bookkeeping of visited vertices, or to preload
            vertices that should never be visited.

            Attention: TraversalTopologicalSortFlex requires, that the collection
            given as argument for parameter already_visited is compatible
            (in any sense) with the collection that gear.vertex_id_set()
            returns. If you have chosen GearDefault, you can just use a dict.
            Otherwise, create the collection by calling gear.vertex_id_set() or use the
            collection that another traversal with the same gear gives as attribute
            visited.

        :return: Traversal, that has been started, e.g., statements like *iter()*,
            *next()*, *for* and the methods "go*" of the Traversal can now be used.
        """

        _start_from_needs_traversal_object(self)
        self._start_with_or_without_labels_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
        )
        self.depth = 0
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        # Copy _TraversalWithoutWeights attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex
        visited = self.visited

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            visited_index_and_bit_method,
        ) = access_to_vertex_set(visited)
        (
            predecessors_uses_sequence,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            attributes_uses_sequence,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Typing preparation of inner loop (for details see DFS) -----

        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        data_of_edge: T_labels  # Re-establish type "after" the "hole"

        # Two separate implementations for the cases is_tree and not is_tree that follow
        # different concepts, because a combined approach makes both cases significantly
        # slower
        if is_tree:
            # Since the graph is a tree, we need no cycle check and no skipping of
            # already seen vertices.
            # We just use a stack for vertices we have to enter or leave, and store
            # None on top of the vertices we need to enter in order to differentiate
            # the two cases.

            # ----- Initialize specific bookkeeping -----

            self.cycle_from_start = []
            # Sequence used as stack of vertices that we need to enter & expand (if
            # it is not on the trace, see below) or leave & report (otherwise)
            to_expand_or_leave = self._gear.sequence_of_vertices(self._start_vertices)

            # Sequence of flag bytes (store in a Q array) marking the vertices to leave
            # by 1 and the vertices to enter by 0.
            # Initially, store a zero flag for each start vertex.
            to_leave_markers = array.array(
                "B", itertools.repeat(False, len(to_expand_or_leave))
            )

            # Get method references of specific bookkeeping (avoid attribute resolution)
            to_expand_or_leave_append = to_expand_or_leave.append
            to_expand_or_leave_pop = to_expand_or_leave.pop
            to_leave_markers_pop = to_leave_markers.pop
            to_leave_markers_append = to_leave_markers.append

            # ----- Inner loop -----

            while to_expand_or_leave:
                if to_leave_markers[-1]:
                    # Vertex is to be left: We "leave" and report it, and remove marker
                    self.depth -= 1
                    to_leave_markers_pop()
                    vertex = to_expand_or_leave_pop()  # handle last added vertex first
                    yield vertex
                    continue

                # Vertex is to be expanded: We "expand" it,
                # but leave it on the stack, so that it will be "left" later on.
                vertex = to_expand_or_leave[-1]
                # We change the marker in order to remember that we will have to
                # leave (not enter) it
                to_leave_markers[-1] = True

                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    n_id: T_vertex_id = (
                        maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else neighbor
                    )

                    if build_paths:
                        # We have to store the predecessor here, because at time of
                        # visit, it is already lost. And we cannot yield here,
                        # because only the first of the neighbors will indeed be
                        # visited next.
                        # But since we are in a tree, no other predecessor can
                        # be stored for that vertex later on.

                        # Store the predecessor (vertex) of the neighbor
                        try:
                            predecessors_sequence[n_id] = vertex
                        except IndexError:
                            predecessors_wrapper.extend_and_set(n_id, vertex)
                        # Store the labels of the edge to the neighbor
                        if labeled_edges:
                            data_of_edge = edge_or_vertex[-1]
                            try:
                                attributes_sequence[n_id] = data_of_edge
                            except IndexError:
                                attributes_wrapper.extend_and_set(n_id, data_of_edge)

                    # Put vertex on the stack
                    to_expand_or_leave_append(neighbor)
                    # Remember that we have to expand it
                    to_leave_markers_append(False)

                self.depth += 1

        else:  # not is_tree
            # Since the graph is not guaranteed to be a tree, we need a cycle check and
            # need to skip already seen vertices.
            # For detecting cycles, we store the vertices, that are on the current
            # path, in a set. We use a stack for storing the vertices we have to
            # enter or leave (when such a vertex is in the path set, we need to leave
            # the vertex).

            # ----- Initialize specific bookkeeping -----

            self.cycle_from_start = []

            # Sequence used as stack of vertices that we need to enter & expand (if
            # it is not on the trace, see below) or leave & report (otherwise)
            to_enter_or_leave = self._gear.sequence_of_vertices(self._start_vertices)

            # Set of vertices along the current path
            # (We need this for fast cycle detection. We could use additionally
            # a trace sequence to speed up the check if the current vertex is
            # the top vertex of the trace instead of checking if it is "in" the
            # trace, but this would cost maintenance runtime and memory for the
            # sequence).
            trace_set = self._gear.vertex_id_set(())
            (
                trace_set_uses_sequence,
                trace_set_sequence,
                trace_set_wrapper,
                trace_set_uses_bits,
                trace_set_index_and_bit_method,
            ) = access_to_vertex_set(trace_set)

            # Check compatibility of visited and trace_set. It is used for
            # performance optimization later on.
            assert (
                visited_uses_sequence == trace_set_uses_sequence
                and visited_uses_bits == trace_set_uses_bits
            ), (
                "Collection already_visited is incompatible "
                + "with gear.sequence_of_vertices"
            )
            sets_use_sequences = visited_uses_sequence
            del visited_uses_sequence, trace_set_uses_sequence
            sets_use_bits = visited_uses_bits
            del visited_uses_bits, trace_set_uses_bits
            if sets_use_sequences and sets_use_bits:
                assert visited_index_and_bit_method is trace_set_index_and_bit_method, (
                    "Collection already_visited is incompatible "
                    + "with gear.sequence_of_vertices"
                )
            sets_index_and_bit_method = visited_index_and_bit_method
            del visited_index_and_bit_method, trace_set_index_and_bit_method

            # Get method references of specific bookkeeping (avoid attribute resolution)
            to_visit_pop = to_enter_or_leave.pop
            to_visit_append = to_enter_or_leave.append
            trace_set_add = trace_set.add
            trace_set_discard = trace_set.discard

            # ----- Inner loop -----

            while to_enter_or_leave:
                vertex = to_enter_or_leave[-1]  # visit/report last added vertex first
                v_id: T_vertex_id = (
                    maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else vertex
                )

                if not sets_use_sequences:
                    # Standard implementation for "normal" MutableSet
                    if v_id in trace_set:
                        # Back to trace, from visits/reports of further vertices,
                        # that trace vertices depend on: We "leave" and report the head
                        # vertex of the trace
                        # (A note about the above "in" check:
                        # If v_id is in the set, it needs to be
                        # the last id added there. But this does not help us, since
                        # sets are not ordered as dicts nowadays are).
                        self.depth -= 1
                        to_visit_pop()
                        trace_set_discard(v_id)
                        yield vertex
                        continue
                    # Ignore v_id if visited, else include vertex n_id in visited set.
                    # Ignore this precondition for trees and start vertices.
                    if self.depth > 0:
                        # Standard implementation for "normal" MutableMapping
                        if v_id in visited:
                            to_visit_pop()
                            continue
                        visited_add(v_id)
                    # Now, vertex belongs to trace from start. As long as this is so,
                    # seeing it as neighbor would be a cycle.
                    trace_set_add(v_id)

                elif sets_use_bits:
                    # Same as above, but with bits in byte sequence
                    sequence_key, bit_number = sets_index_and_bit_method(v_id, 8)
                    bit_mask = 1 << bit_number
                    try:
                        value = trace_set_sequence[sequence_key]
                        if value & bit_mask:
                            self.depth -= 1
                            to_visit_pop()
                            trace_set_sequence[sequence_key] = value - bit_mask
                            yield vertex
                            continue
                    except IndexError:
                        pass
                    if self.depth > 0:
                        try:
                            value = visited_sequence[sequence_key]
                            if value & bit_mask:
                                to_visit_pop()
                                continue
                            visited_sequence[sequence_key] = value + bit_mask
                        except IndexError:
                            visited_wrapper.extend_and_set(sequence_key, bit_mask)
                    try:
                        trace_set_sequence[sequence_key] += bit_mask
                    except IndexError:
                        trace_set_wrapper.extend_and_set(sequence_key, bit_mask)

                else:
                    # Same as above, but with booleans in byte sequence
                    try:
                        if trace_set_sequence[v_id]:
                            self.depth -= 1
                            to_visit_pop()
                            trace_set_sequence[v_id] = False
                            yield vertex
                            continue
                    except IndexError:
                        pass
                    if self.depth > 0:
                        try:
                            if visited_sequence[v_id]:
                                to_visit_pop()
                                continue
                            visited_sequence[v_id] = True
                        except IndexError:
                            visited_wrapper.extend_and_set(v_id, True)
                    try:
                        trace_set_sequence[v_id] = True
                    except IndexError:
                        trace_set_wrapper.extend_and_set(v_id, True)

                # We "expand" the vertex
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    n_id2: T_vertex_id = (
                        maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else neighbor
                    )

                    # If neighbor is already visited and in trace_set: cycle found
                    # If neighbor is already visited: ignore it (in case of path
                    # generation, this is necessary, and otherwise, it is a small
                    # optimization.)
                    if not sets_use_sequences:
                        # Standard implementation for "normal" MutableSet
                        if n_id2 in visited:
                            if n_id2 in trace_set:
                                # We found a dependency (edge) back to a vertex, whose
                                # dependencies we are currently following (trace). We
                                # build and report this trace: a cycle.
                                self._report_cycle(
                                    neighbor,
                                    to_enter_or_leave,
                                    trace_set,
                                    maybe_vertex_to_id,
                                )
                            # Visited but does not close a cycle: ignore it
                            continue
                    elif sets_use_bits:
                        # Same as above, but with bits in byte sequence
                        sequence_key, bit_number = sets_index_and_bit_method(n_id2, 8)
                        bit_mask = 1 << bit_number
                        try:
                            value = visited_sequence[sequence_key]
                            if value & bit_mask:
                                try:
                                    if trace_set_sequence[sequence_key] & bit_mask:
                                        self._report_cycle(
                                            neighbor,
                                            to_enter_or_leave,
                                            trace_set,
                                            maybe_vertex_to_id,
                                        )
                                except IndexError:
                                    # In order to become visited, a vertex needs to
                                    # get into the trace set and then be discarded
                                    # from it. Thus, if a vertex is visited, the
                                    # trace set sequence already has the necessary
                                    # length to store it. So, no IndexError can happen
                                    # here.
                                    raise AssertionError(
                                        "Internal error in TS"
                                    )  # pragma: no cover
                                continue
                        except IndexError:
                            pass
                    else:
                        # Same as above, but with booleans in byte sequence
                        try:
                            if visited_sequence[n_id2]:
                                try:
                                    if trace_set_sequence[n_id2]:
                                        self._report_cycle(
                                            neighbor,
                                            to_enter_or_leave,
                                            trace_set,
                                            maybe_vertex_to_id,
                                        )
                                except IndexError:
                                    # See above case for the reason for the pragma
                                    raise AssertionError(
                                        "Internal error in TS"
                                    )  # pragma: no cover
                                continue
                        except IndexError:
                            pass

                    if build_paths:
                        # We have to store the predecessor here, because at time of
                        # visit, it is already lost. And we cannot yield here,
                        # because TopologicalSorted reports not until leaving vertices.
                        # But since the visiting order is defined by a stack we know
                        # that for each vertex, the predecessor stored last is the
                        # edge visited first, and after that no other predecessor can
                        # be stored for that vertex.
                        try:
                            predecessors_sequence[n_id2] = vertex
                        except IndexError:
                            predecessors_wrapper.extend_and_set(n_id2, vertex)
                        if labeled_edges:
                            data_of_edge = edge_or_vertex[-1]
                            try:
                                attributes_sequence[n_id2] = data_of_edge
                            except IndexError:
                                attributes_wrapper.extend_and_set(n_id2, data_of_edge)

                    # Needs to be visited, in stack order
                    to_visit_append(neighbor)

                # Update depth. The following vertices are one level deeper.
                self.depth += 1

    def _report_cycle(
        self,
        neighbor: T_vertex,
        to_visit: MutableSequenceOfVertices[T_vertex],
        trace_set: VertexIdSet[T_vertex_id],
        maybe_vertex_to_id: Optional[VertexToID[T_vertex, T_vertex_id]],
    ) -> None:
        trace = list()
        for vertex in to_visit:
            v_id2: T_vertex_id = (
                maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else vertex
            )
            if v_id2 in trace_set:
                trace.append(vertex)
        trace.append(neighbor)
        self.cycle_from_start = trace
        raise RuntimeError("Graph contains cycle")


class TraversalTopologicalSort(
    Generic[T_vertex, T_labels],
    TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels],
):
    """
    Eases the use of `TraversalTopologicalSortFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    Uses the following standard arguments for the respective parameters of
    the parent class:

    - vertex_to_id = `vertex_as_id`
    - gear = `GearDefault`
    - `T_vertex_id` = `T_vertex`

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


# --------------- Traversal strategies for weighted edges -------------


class _TraversalWithWeights(
    Generic[T_vertex, T_vertex_id, T_weight, T_labels],
    Traversal[T_vertex, T_vertex_id, T_labels],
    ABC,
):
    """A Traversal that needs weighted edges and uses a gear suitable for this."""

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        self._gear = gear
        super().__init__(labeled_edges, is_tree, vertex_to_id)


class _TraversalWithDistances(
    _TraversalWithWeights[T_vertex, T_vertex_id, T_weight, T_labels],
    ABC,
):
    """
    A _TraversalWithWeights that provides a distances collection as part of
    its state.
    """

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        self.distances: VertexIdToDistanceMapping[
            T_vertex_id, T_weight
        ] = NoDistancesMapping[T_vertex_id, T_weight]()
        """ Provisional or final distance values of some vertices
        (distance from a start vertex). Without option *keep_distances*,
        the value for a vertex is removed once the vertex has been reported. With
        option *keep_distances*, values are never removed, and that means: During a
        traversal, the distance values for already reported vertices can be found in
        the collection. After an exhaustive search, the collection contains exactly
        and only the distances of all vertices that are reachable from the start
        vertices and of the start vertices themselves.
        """

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Assignments in distances are only valid for reported vertices. Thus,
        # we need to convert only keys/values for requested vertices to a string,
        # not the whole MutableMapping. So, we special case this attribute here.
        del state["distances"]
        if vertices is not None:
            vertex_to_id, distances = self._vertex_to_id, self.distances
            state["distances"] = StrRepr.from_iterable(
                (v_id := vertex_to_id(vertex), distances[v_id]) for vertex in vertices
            )
        super()._improve_state(state, vertices)


class _TraversalWithDistance(
    _TraversalWithDistances[T_vertex, T_vertex_id, T_weight, T_labels],
    ABC,
):
    """
    A _TraversalWithDistances that provides a distance as part of its staste.
    If offers the go_for_distance_range method based on the distance.
    """

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        # The following value is not used by NoGraphs. It is only set
        # to have some initialization.
        self.distance: T_weight = self._gear.infinity()
        """ The length of the shortest path (sum of edge weights) from a
        start vertex to the visited vertex
        """

    def go_for_distance_range(self, start: Real, stop: Real) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator. During the traversal,
        the iterator skips vertices as long as their distance is lower than *start*.
        From then on, is reports the found vertices. It stops when the reached
        distance is equal to or higher than *stop*.

        Note: The first vertex with a distance equal or higher than stop will be
        consumed from the traversal, but will not be reported, so it is lost (compare
        itertools.takewhile).
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_distance_range can only be called "
                + "on a Traversal object."
            )

        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function
        def my_generator() -> Iterator[T_vertex]:
            for v in self._generator:
                if self.distance >= start:
                    if self.distance < stop:
                        yield v
                    break
            for v in self._generator:
                if self.distance >= stop:
                    break
                yield v

        return my_generator()


class TraversalShortestPathsFlex(
    _TraversalWithDistance[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    | Bases: Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`],
    | `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `Gear`.

    :param next_edges: See `NextWeightedEdges` function. If None, provide
      next_labeled_edges.

    :param next_labeled_edges: See `NextWeightedLabeledEdges` function. Only allowed
      if next_edges equals None. If given, paths will record the given labels.

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
      can be reached only once, is_tree can be set to True. This improves performance,
      but attribute *distances* of the traversal will not be updated during and after
      the traversal.

    **Algorithm:** Shortest paths algorithm of Dijkstra, non-recursive, based on heap.

    **Properties:** Vertices are reported (and expanded) ordered by increasing distance
    (minimally necessary sum of edge weights) from a start vertex.

    **Input:** Weighted directed graph. One or more start vertices. Vertices must be
    hashable, or hashable id can be provided. Weights need to be non-negative.
    Optional calculation limit.

    **Search state:** When a vertex is *expanded* (traversal calls next_edges or
    next_labeled_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *distance*, *depth*, *paths*, and *distances*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalShortestPathsFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalShortestPathsFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        self._next_edges, labeled_edges = _create_unified_next_weighted(
            next_edges, next_labeled_edges
        )
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        self._known_distances: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None
        self._keep_distances = False

        # The following value is not used by NoGraphs. It is only set
        # to have some initialization.
        self.depth: int = -1
        """  At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self._start_vertices_and_ids = tuple[tuple[T_vertex, T_vertex_id]]()

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        keep_distances: bool = False,
        known_distances: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None,
    ) -> TraversalShortestPathsFlex[T_vertex, T_vertex_id, T_weight, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices the search should start
            at. Only allowed if start_vertex equals None.

        :param build_paths: If true, build paths from start vertices for each reported
            vertex, and an empty path for each start vertex.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param keep_distances: If True, the found distances of vertices are
            collected in traversal attribute distances, and not deleted after
            having reported the vertex. See attribute distances.

        :param known_distances: If provided, this mapping is used instead of an internal
            one to keep distance candidates and final distances values of reported
            vertices (resp. their hashable ids from vertex_to_id is used as key) from
            some start vertex.

            For vertices without known distance, it must yield float('infinity'). The
            internal default implementation uses a collections.defaultdict. Typical
            use cases are: 1) preloading known distances of vertices, and the
            vertices should not be visited if no smaller distance is found during the
            traversal, and 2) providing your own way for storing the distances.

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        # ----- Initialize method specific public bookkeeping -----
        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            self._gear,
        )
        self._keep_distances = keep_distances
        self._known_distances = known_distances

        # Explicitly list start vertices and their id. Needed several times.
        self._start_vertices_and_ids = tuple(
            iter_start_vertices_and_ids(self._start_vertices, self._vertex_to_id)
        )

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given. Each start vertex has distance 0
        # from a start vertex (itself), if not defined otherwise.
        zero = self._gear.zero()
        self.distances = define_distances(
            self._gear,
            self._known_distances,
            ((vertex_id, zero) for vertex, vertex_id in self._start_vertices_and_ids),
            self._is_tree,
        )

        # The following two values are not used by NoGraphs. They are only set
        # to have some defined values before the traversal iterator sets them.
        self.distance = self._gear.infinity()
        self.depth = 0

        super()._start()
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Gear attributes into method scope (faster access)
        infinity = self._gear.infinity()

        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Copy traversal specific attributes into method scope
        next_edges = self._next_edges
        keep_distances = self._keep_distances

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)
        zero = self._gear.zero()

        # ----- Initialize method specific private bookkeeping -----

        # Unique number, that prevents heapq from sorting by vertices in case of a
        # tie in the sort field, because vertices do not need to be pairwise
        # comparable. The integers from -5 to 256 are used first, because they are
        # internalized (pre-calculated, and thus fastest). We count downwards like we
        # do in A* search. There, it is preferable, because a LIFO behavior makes A*
        # often faster. Here, we do it simply to do it the same way.
        unique_no = itertools.count(256, -1)

        # Get references of used gear objects and methods (avoid attribute resolution)
        _, distances_sequence, distances_wrapper = access_to_vertex_mapping(
            self.distances
        )

        # So far, the start vertices are to be visited. Each has an edge count of 0.
        # (No index exception possible at the following indexed access)
        to_visit = [  # used as collection.heapq of tuples, the lowest distance first
            (distances_sequence[vertex_id], next(unique_no), vertex, 0)
            for vertex, vertex_id in self._start_vertices_and_ids
        ]
        heapify(to_visit)

        # ----- Inner loop -----

        while to_visit:
            # Visit path with the lowest distance first
            path_weight, _, vertex, path_edge_count = heappop(to_visit)

            # A vertex can get added to the heap multiple times. We want to process
            # it only once, the first time it is removed from the heap, because this
            # is the case with the shortest distance from start.
            if not is_tree:
                v_id: T_vertex_id = (
                    maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else vertex
                )

                # (No index exception possible at the following indexed access)
                if distances_sequence[v_id] < path_weight:
                    continue
                if not keep_distances:
                    # (Allow garbage collector to free distance value if nowhere else
                    # needed any more)
                    distances_sequence[v_id] = zero  # No index exception possible here

            # Export traversal data to traversal attributes
            self.distance = path_weight
            self.depth = path_edge_count

            # We now know the distance of the vertex, so we report it.
            if path_edge_count > 0:  # do not report start vertex
                yield vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            # Expand vertex. New neighbors are one edge count deeper than vertex.
            n_path_edge_count = path_edge_count + 1
            for edge in next_edges(vertex, self):
                neighbor, weight = edge[0], edge[1]

                n_path_weight = weight + path_weight
                # (Distance values equal to or higher than the chosen infinity value of
                # the gear are invalid and cannot be handled further.)
                if infinity <= n_path_weight:
                    self._gear.raise_distance_infinity_overflow_error(n_path_weight)

                # If the found path to the neighbor is not shorter than the shortest
                # such path found so far, we can safely ignore it. Otherwise, it is a
                # new candidate for a shortest path to the neighbor, and we push it to
                # the heap.
                if build_paths or not is_tree:
                    n_id: T_vertex_id = (
                        maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                        if maybe_vertex_to_id
                        else neighbor
                    )

                    if not is_tree:
                        try:
                            if distances_sequence[n_id] <= n_path_weight:
                                continue
                            distances_sequence[n_id] = n_path_weight
                        except IndexError:
                            distances_wrapper.extend_and_set(n_id, n_path_weight)

                    # If we are to generate a path, we have to do it here, since the
                    # edge we have to add to the path prefix is not stored on the heap
                    if build_paths:
                        try:
                            predecessors_sequence[n_id] = vertex
                        except IndexError:
                            predecessors_wrapper.extend_and_set(n_id, vertex)
                        if labeled_edges:
                            # self._labeled_edges -> next_edges (a NextWeightedEdges)
                            # is a NextWeightedLabeledEdges -> edge[-1] is a T_labels
                            data_of_edge: T_labels = edge[
                                -1
                            ]  # type: ignore[assignment]
                            try:
                                attributes_sequence[n_id] = data_of_edge
                            except IndexError:
                                attributes_wrapper.extend_and_set(n_id, data_of_edge)

                heappush(
                    to_visit,
                    (
                        n_path_weight,
                        next(unique_no),
                        neighbor,
                        n_path_edge_count,
                    ),
                )


class TraversalShortestPaths(
    Generic[T_vertex, T_weight, T_labels],
    TraversalShortestPathsFlex[T_vertex, T_vertex, Union[T_weight, float], T_labels],
):
    """
    Eases the use of `TraversalShortestPathsFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       TraversalShortestPaths[T_vertex, T_weight, T_labels](*args, **keywords)

    is a short form for

    .. code-block:: python

       TraversalShortestPathsFlex[
           T_vertex, T_vertex, Union[T_weight, float], T_labels],
      ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - The used weights are defined by Union[T_weight, float], see `GearDefault`
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalShortestPathsFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalShortestPathsFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


class TraversalAStarFlex(
    _TraversalWithDistances[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    | Bases: Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`],
    | `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `Gear`.

    :param next_edges: See `NextWeightedEdges` function. If None, provide
      next_labeled_edges.

    :param next_labeled_edges: See `NextWeightedLabeledEdges` function. Only allowed
      if next_edges equals None. If given, paths will record the given labels.

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
       can be reached only once, is_tree can be set to True. This improves performance,
       but if *start_from* has been called with parameter *known_path_length_guesses*
       given, this collection will not be updated during the traversal.

    **Algorithm:** The search algorithm A*, non-recursive, based on heap.

    **Input:** Weighted directed graph. One or more start vertices. Vertices must be
    hashable, or hashable id can be provided. Weights need to be non-negative.
    A heuristic function that estimates the cost of the cheapest path from a given
    vertex to the goal (resp. to any of your goal vertices, if you have more than
    one), and never overestimates the actual needed costs ("admissible heuristic
    function"). Optionally, a calculation limit.

    **Properties:** Vertices are reported and expanded ordered by increasing path
    length (sum of edge weights) of the shortest paths from a start vertex to the
    respective vertex that have been found so far.

    When the goal is reported, the path stored for it in *paths* is a shortest
    path from start to goal and the path_length of the search state is the distance
    of the goal from start.

    In case the used heuristic function is *consistent* (i.e., following an edge from
    one vertex to another never reduces the estimated costs to get to the goal by
    more than the weight of the edge), further guarantees hold: Each vertex is only
    visited once. And for each visited vertex, the respective path_length and depth
    (and optionally, the path) are the data of the shortest existing path from start
    (not only from the shortest path found so far).

    **Search state:** When a vertex is *expanded* (traversal calls next_edges or
    next_labeled_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *path_length*, *depth*, *paths*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalAStarFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalAStarFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        self._next_edges, labeled_edges = _create_unified_next_weighted(
            next_edges, next_labeled_edges
        )
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        # The following three values are not used by NoGraphs. They are only set
        # to have some initialization.
        self.path_length: T_weight = self._gear.infinity()
        """ Length (sum of edge weights) of the found path to the
        vertex (for the goal vertex: a shortest path)
        """
        self.depth: int = -1
        """  At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        """
        self._start_vertices_and_ids = tuple[tuple[T_vertex, T_vertex_id]]()

        self._heuristic: Optional[Callable[[T_vertex], Real]] = None
        self._known_distances: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None
        self._known_path_length_guesses: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None
        self._path_length_guesses: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None

    def start_from(
        self,
        heuristic: Callable[[T_vertex], Real],
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        known_distances: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None,
        known_path_length_guesses: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None,
    ) -> TraversalAStarFlex[T_vertex, T_vertex_id, T_weight, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param heuristic: The admissible and consistent heuristic function that
            estimates the cost of the cheapest path from a given vertex to the goal
            (resp. one of the goals).

        :param start_vertex: The vertex the search should start at. Provide either
            start_vertex or start_vertices, but not both.

        :param start_vertices: The set of vertices the search should start
            at. Provide either start_vertex or start_vertices, but not both.

        :param build_paths: If true, build paths from start vertices for each reported
            vertex, and an empty path for each start vertex.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param known_distances: If provided, this mapping is used instead of an internal
            one to keep the distances of vertices that have already been visited
            (resp. their hashable ids from vertex_to_id is used as key) from some
            start vertex. For vertices without known distance, it must yield float(
            'infinity'). The internal default implementation uses a
            collections.defaultdict.

            Typical use cases are: 1) preloading known distances of vertices, and the
            vertices should not be visited if no smaller distance is found during the
            traversal, or 2) getting online access to the internal bookkeeping of
            visited vertices and their distances, or 3) providing your own way for
            storing the distance of a vertex that has already been visited.

        :param known_path_length_guesses: Like known_distances, but for keeping the sum
            distance+heuristic for vertices.

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            self._gear,
        )

        self._heuristic = heuristic
        self._known_distances = known_distances
        self._known_path_length_guesses = known_path_length_guesses

        # Explicitly list start vertices and their id. Needed several times.
        self._start_vertices_and_ids = tuple(
            iter_start_vertices_and_ids(self._start_vertices, self._vertex_to_id)
        )

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given.
        # Each start vertex has distance 0 from a start vertex (itself),
        # and a path_length_guess of distance + heuristic(vertex), both if not
        # defined otherwise.
        zero = self._gear.zero()
        self.distances = define_distances(
            self._gear,
            self._known_distances,
            ((vertex_id, zero) for vertex, vertex_id in self._start_vertices_and_ids),
            self._is_tree,
        )

        # The following two values are not used by NoGraphs. They are only set
        # to have some defined values before the traversal iterator sets them.
        self.path_length = self._gear.infinity()
        self.depth = 0

        super()._start()
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # Copy Gear attributes into method scope (faster access)
        infinity = self._gear.infinity()

        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        is_tree = self._is_tree
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        predecessors = self._predecessors
        attributes = self._attributes

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        # Copy traversal specific attributes into method scope
        next_edges = self._next_edges
        heuristic = self._heuristic

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Initialize method specific private bookkeeping -----

        # Unique number, that prevents heapq from sorting by vertices in case of a
        # tie in the sort field, because vertices do not need to be pairwise
        # comparable. The numbers are generated in decreasing order to make the min
        # heap behave like a LIFO queue in case of ties. The integers from -5 to 256
        # are used first, because they are internalized (pre-calculated, and thus
        # fastest).
        unique_no = itertools.count(256, -1)

        # Get references of used gear objects and methods (avoid attribute resolution)
        _, distances_sequence, distances_wrapper = access_to_vertex_mapping(
            self.distances
        )

        assert heuristic is not None  # set by __init__
        path_length_guesses = define_distances(
            self._gear,
            self._known_path_length_guesses,
            (
                (vertex_id, distances_sequence[vertex_id] + heuristic(vertex))
                for vertex, vertex_id in self._start_vertices_and_ids
            ),
            is_tree,
        )
        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            path_length_guesses_sequence,
            path_length_guesses_wrapper,
        ) = access_to_vertex_mapping(path_length_guesses)

        # So far, the start vertices are to be visited. Each has an edge count of 0,
        # and its path length guess is the one computed above.
        to_visit = [  # used as collection.heapq of tuples, the lowest distance first
            (path_length_guesses_sequence[vertex_id], next(unique_no), vertex, 0)
            for vertex, vertex_id in self._start_vertices_and_ids
        ]
        heapify(to_visit)

        # ----- Inner loop -----

        while to_visit:
            # Visit path with the lowest path_length_guess first
            path_length_guess, _, vertex, path_edge_count = heappop(to_visit)

            # A vertex can get added to the heap multiple times.

            # For consistent heuristics: We want to process the vertex only once, the
            # first time it is removed from the heap, because this is the case with the
            # shortest distance estimation. If the heuristic is not consistent: Only
            # when the new distance estimation is better than the best found so far, we
            # want to process the vertex again.
            v_id: T_vertex_id = (
                maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else vertex
            )

            # (No index exception possible at the following indexed access)
            if not is_tree and path_length_guess > path_length_guesses_sequence[v_id]:
                continue

            # (No index exception possible here)
            path_weight = distances_sequence[v_id]

            # Export traversal data to traversal attributes
            self.path_length = path_weight
            self.depth = path_edge_count

            # We now know the distance of the vertex, so we report it.
            if path_edge_count > 0:  # do not report start vertex
                yield vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            # Expand vertex. New neighbors are one edge count deeper than vertex.
            n_path_edge_count = path_edge_count + 1
            for edge in next_edges(vertex, self):
                neighbor, weight = edge[0], edge[1]

                n_path_weight = weight + path_weight
                # (Distance values equal to or higher than the chosen infinity value of
                # the gear are invalid and cannot be handled further.)
                if infinity <= n_path_weight:
                    self._gear.raise_distance_infinity_overflow_error(n_path_weight)

                # If the found path to the neighbor is not shorter than the shortest
                # such path found so far, we can safely ignore it. Otherwise, it is a
                # new candidate for a shortest path to the neighbor, and we push it to
                # the heap.
                n_id: T_vertex_id = (
                    maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else neighbor
                )

                try:
                    if not is_tree and distances_sequence[n_id] <= n_path_weight:
                        continue
                    distances_sequence[n_id] = n_path_weight
                except IndexError:
                    # n_id not in distances_collection. To be regarded as value
                    # infinity, i.e., n_path_weight is smaller.
                    distances_wrapper.extend_and_set(n_id, n_path_weight)

                # If we are to generate a path, we have to do it here, since the edge
                # we have to add to the path prefix is not stored on the heap
                if build_paths:
                    try:
                        predecessors_sequence[n_id] = vertex
                    except IndexError:
                        predecessors_wrapper.extend_and_set(n_id, vertex)
                    if labeled_edges:
                        data_of_edge: T_labels = edge[-1]  # type: ignore[assignment]
                        try:
                            attributes_sequence[n_id] = data_of_edge
                        except IndexError:
                            attributes_wrapper.extend_and_set(n_id, data_of_edge)

                h = heuristic(neighbor)
                if h == infinity:
                    n_guess = infinity
                else:
                    n_guess = n_path_weight + h
                    # (Distance values equal to or higher than the chosen infinity
                    # value of the gear are invalid and cannot be handled further.)
                    if infinity <= n_guess:
                        self._gear.raise_distance_infinity_overflow_error(n_guess)

                if not is_tree:
                    try:
                        path_length_guesses_sequence[n_id] = n_guess
                    except IndexError:
                        path_length_guesses_wrapper.extend_and_set(n_id, n_guess)
                heappush(
                    to_visit,
                    (n_guess, next(unique_no), neighbor, n_path_edge_count),
                )


class TraversalAStar(
    Generic[T_vertex, T_weight, T_labels],
    TraversalAStarFlex[T_vertex, T_vertex, Union[T_weight, float], T_labels],
):
    """
    Eases the use of `TraversalAStarFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       TraversalAStar[T_vertex, T_weight, T_labels](*args, **keywords)

    is a short form for

    .. code-block:: python

       TraversalAStarFlex[
           T_vertex, T_vertex, Union[T_weight, float], T_labels],
       ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - The used weights are defined by Union[T_weight, float], see `GearDefault`
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalAStarFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalAStarFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )


class TraversalMinimumSpanningTreeFlex(
    _TraversalWithWeights[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    | Bases: Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`],
    | `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `Gear`.

    :param next_edges: See `NextWeightedEdges` function. If None, provide
      next_labeled_edges.

    :param next_labeled_edges: See `NextWeightedLabeledEdges` function. Only allowed
      if next_edges equals None. If given, paths will record the given labels.

    **Algorithm:**  Minimum spanning tree ("MST") algorithm of Jarnik, Prim, Dijkstra.
    Non-recursive, based on heap. A so-called *tie breaker* is implemented, that
    prioritizes edges that have been found more recently about edges that have been
    found earlier. This is a typical choice that often improves search performance.

    **Properties:** Only edges of the MST from start vertices are reported. Each
    vertex is reported (as end vertex of an edge) and expanded only once. Computed
    paths only use MST edges.

    **Input:** Weighted undirected graph, given as directed edges with the same
    weight in both directions. One or more start vertices (e.g. for components in
    unconnected graphs). Optional calculation limit.

    **Search state:** When a vertex is *expanded* (traversal calls next_edges or
    next_labeled_edges) or an edge is *reported* (an iterator of the traversal returns
    the vertex it leads to), the traversal provides updated values for the attributes
    *edge* and *paths*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalMinimumSpanningTreeFlex[
                    T_vertex, T_vertex_id, T_weight, T_labels
                ],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalMinimumSpanningTreeFlex[
                    T_vertex, T_vertex_id, T_weight, T_labels
                ],
                T_weight,
                T_labels,
            ]
        ] = None,
    ) -> None:
        self._next_edges, labeled_edges = _create_unified_next_weighted(
            next_edges, next_labeled_edges
        )
        super().__init__(labeled_edges, False, vertex_to_id, gear)
        self.edge: Optional[WeightedFullEdge[T_vertex, T_weight, T_labels]] = None
        """ Tuple of from_vertex, to_vertex, the weight of the edge,
        and additional data you have provided with the edge (if so).
        """

        # The following value is not used by NoGraphs. It is only set
        # to have some initialization.
        self._start_vertices_and_ids = tuple[tuple[T_vertex, T_vertex_id]]()

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
    ) -> TraversalMinimumSpanningTreeFlex[T_vertex, T_vertex_id, T_weight, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices the search should start
            at. Only allowed if start_vertex equals None. Leads to a result
            consisting of several trees that are only connected if the start vertices
            are connected.

        :param build_paths: If true, build paths from start vertices for each reported
            vertex, and an empty path for each start vertex.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        # ----- Initialize method specific public bookkeeping -----
        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            self._gear,
        )

        # Explicitly list start vertices and their id. Needed several times.
        self._start_vertices_and_ids = tuple(
            iter_start_vertices_and_ids(self._start_vertices, self._vertex_to_id)
        )

        # The following value is not used by NoGraphs. It is only set
        # to have some defined value before the traversal iterator sets them.
        self.edge = None

        super()._start()
        return self

    def _traverse(self) -> Iterator[T_vertex]:
        # ----- Prepare efficient environment for inner loop -----
        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        build_paths = self._build_paths
        calculation_limit = self._calculation_limit
        predecessors = self._predecessors
        attributes = self._attributes

        # Copy traversal specific attributes into method scope
        next_edges = self._next_edges

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            predecessors_sequence,
            predecessors_wrapper,
        ) = access_to_vertex_mapping_expect_none(predecessors)
        (
            _,
            attributes_sequence,
            attributes_wrapper,
        ) = access_to_vertex_mapping_expect_none(attributes)

        # ----- Initialize method specific private bookkeeping -----

        # At start, only the start vertices are regarded as visited
        # (The protocol VertexSet abandons checking the element type, see
        #  VertexSet. Flake8 and MyPy accept this, PyCharm does not and need
        #   noinspection.)
        # noinspection PyTypeChecker
        visited: VertexIdSet[T_vertex_id] = self._gear.vertex_id_set(
            vertex_id for vertex, vertex_id in self._start_vertices_and_ids
        )

        # Check if we already go over the calculation limit when we evaluate the
        # edges from start vertices ("expanding the start vertices"). This avoids a
        # step by step check that slows down the to_visit loop for large sets of
        # start vertices. Note: A calculation limit below 0 leads nowhere ever to an
        # exception. So, neither here.
        if calculation_limit is not None and calculation_limit >= 0:
            if (
                calculation_limit := calculation_limit
                - len(self._start_vertices_and_ids)
            ) < 0:
                raise RuntimeError("Number of visited vertices reached limit")

        # So far, the edges from the start vertices are to be visited as candidates
        # for edges of a MST. (Unique number prevents heapq from sorting by (possibly
        # not comparable) fields)
        unique_no = itertools.count()
        to_visit: list[
            tuple[
                T_weight, int, T_vertex, WeightedOutEdge[T_vertex, T_weight, T_labels]
            ]
        ] = [  # used as collection.heapq, the lowest edge weight first
            (edge[1], next(unique_no), vertex, edge)
            for vertex in self._start_vertices
            for edge in next_edges(vertex, self)
        ]
        heapify(to_visit)

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            index_and_bit_method,
        ) = access_to_vertex_set(visited)

        # ----- Inner loop -----

        while to_visit:
            # Visit edge with the lowest weight first
            _weight, _, vertex, to_edge = heappop(to_visit)
            to_vertex = to_edge[0]

            # A vertex can get added to the heap multiple times, as end vertex of
            # several edges. We want to process it only once, as end vertex of a MST
            # edge.
            # The shortest edge from a visited vertex that leads to a vertex not
            # visited so far, must be an edge of the MST.
            to_id: T_vertex_id = (
                maybe_vertex_to_id(to_vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else to_vertex
            )

            if visited_uses_sequence:
                try:
                    if visited_sequence[to_id]:
                        continue
                    visited_sequence[to_id] = True
                except IndexError:
                    visited_wrapper.extend_and_set(to_id, True)
            else:
                if to_id in visited:
                    continue
                visited_add(to_id)

            if build_paths:
                try:
                    predecessors_sequence[to_id] = vertex
                except IndexError:
                    predecessors_wrapper.extend_and_set(to_id, vertex)
                if labeled_edges:
                    # self._labeled_edges -> next_edges (a NextWeightedEdges) is a
                    # NextWeightedLabeledEdges -> edge[-1] is a T_labels.
                    data_of_edge: T_labels = to_edge[-1]  # type: ignore[assignment]
                    try:
                        attributes_sequence[to_id] = data_of_edge
                    except IndexError:
                        attributes_wrapper.extend_and_set(to_id, data_of_edge)

            # Export traversal data to traversal attribute and report vertex
            # (Expression type follows from types of vertex and to_edge and the
            #  definition of WeightedFullEdge. MyPy + PyCharm cannot derive this.)
            # noinspection PyTypeChecker
            full_edge: WeightedFullEdge[T_vertex, T_weight, T_labels] = (
                vertex,
            ) + to_edge  # type: ignore[assignment]
            self.edge = full_edge
            yield to_vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for n_to_edge in next_edges(to_vertex, self):
                n_to_vertex, n_weight = n_to_edge[0], n_to_edge[1]
                # If the edge leads to a vertex that is, so far, not reached by edges
                # of the MST, it is a candidate for a MST edge. We push it to the heap.
                n_to_id: T_vertex_id = (
                    maybe_vertex_to_id(n_to_vertex)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else n_to_vertex
                )

                try:
                    if (
                        (visited_sequence[n_to_id])
                        if visited_uses_sequence
                        else (n_to_id in visited)
                    ):
                        continue
                except IndexError:
                    pass  # IndexError means case sequence and n_to_id is not visited
                heappush(
                    to_visit,
                    (n_weight, next(unique_no), to_vertex, n_to_edge),
                )


class TraversalMinimumSpanningTree(
    Generic[T_vertex, T_weight, T_labels],
    TraversalMinimumSpanningTreeFlex[
        T_vertex, T_vertex, Union[T_weight, float], T_labels
    ],
):
    """
    Eases the use of `TraversalMinimumSpanningTreeFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       TraversalMinimumSpanningTree[T_vertex, T_weight, T_labels](*args, **keywords)

    is a short form for

    .. code-block:: python

       TraversalMinimumSpanningTreeFlex[
           T_vertex, T_vertex, Union[T_weight, float], T_labels],
       ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - The used weights are defined by Union[T_weight, float], see `GearDefault`
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_edges: Optional[
            NextWeightedEdges[
                T_vertex,
                TraversalMinimumSpanningTreeFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
            ]
        ] = None,
        *,
        next_labeled_edges: Optional[
            NextWeightedLabeledEdges[
                T_vertex,
                TraversalMinimumSpanningTreeFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
                T_labels,
            ]
        ] = None,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_edges,
            next_labeled_edges=next_labeled_edges,
        )
