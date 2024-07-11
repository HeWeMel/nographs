from __future__ import annotations

import itertools
from heapq import heapify, heappop, heappush
from typing import Optional, Any, Generic, Union
from collections.abc import Iterable, Generator

from nographs._types import (
    T_vertex,
    T_labels,
    VertexToID,
    T_vertex_id,
    T_weight,
    vertex_as_id,
    WeightedFullEdge,
    WeightedOutEdge,
)
from nographs._gears import (
    Gear,
    GearDefault,
    VertexIdSet,
)
from nographs._gear_collections import (
    access_to_vertex_set,
    access_to_vertex_mapping_expect_none,
)
from ...type_aliases import (
    NextWeightedEdges,
    NextWeightedLabeledEdges,
)
from ...utils import iter_start_vertices_and_ids
from ..traversal import Traversal
from .traversal_with_weights import _create_unified_next_weighted, _TraversalWithWeights


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
        If you provide more than one start vertex, the result consists of several
        trees that are only connected if the start vertices are connected.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices the search should start
            at. Only allowed if start_vertex equals None.

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

        # ----- Initialize method specific public bookkeeping -----

        # The following value is not used by NoGraphs. It is only set
        # to have some defined value before the traversal iterator sets them.
        self.edge = None

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
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
            for vertex, vertex_id in self._start_vertices_and_ids
            for edge in next_edges(vertex, self)
        ]
        heapify(to_visit)

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Get references of used gear objects and methods (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            visited_index_and_bit_method,
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

            # (If-nesting optimized for first case)
            if not visited_uses_sequence:
                # Standard implementation for "normal" MutableMapping
                if to_id in visited:
                    continue
                visited_add(to_id)
            elif visited_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = visited_index_and_bit_method(to_id, 8)
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
                    if visited_sequence[to_id]:
                        continue
                    visited_sequence[to_id] = True
                except IndexError:
                    visited_wrapper.extend_and_set(to_id, True)

            if build_paths:
                # Store the predecessor (vertex) of the neighbor
                try:
                    predecessors_sequence[to_id] = vertex
                except IndexError:
                    predecessors_wrapper.extend_and_set(to_id, vertex)
                # Store the labels of the edge to the neighbor
                if labeled_edges:
                    # Proof for correctness of the type hole:
                    # self._labeled_edges -> next_edges (a NextWeightedEdges)
                    # is a NextWeightedLabeledEdges -> to_edge[-1] is a T_labels
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

                if not visited_uses_sequence:
                    # Standard implementation for "normal" MutableMapping:
                    if n_to_id in visited:
                        continue
                elif visited_uses_bits:
                    # Same as above, but with bits in byte sequence
                    sequence_key, bit_number = visited_index_and_bit_method(n_to_id, 8)
                    try:
                        if visited_sequence[sequence_key] & (1 << bit_number):
                            continue
                    except IndexError:
                        pass
                else:
                    # Same as above, but with booleans in byte sequence
                    try:
                        if visited_sequence[n_to_id]:
                            continue
                    except IndexError:
                        pass

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
