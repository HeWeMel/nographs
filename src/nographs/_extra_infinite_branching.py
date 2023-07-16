from __future__ import annotations

from typing import Any, Union, Generic, Optional
from collections.abc import Iterable, Iterator
from abc import ABC

from ._types import (
    T_vertex_id,
    T_weight,
    WeightedUnlabeledOutEdge,
    WeightedOutEdge,
    vertex_as_id,
)
from ._gears import (
    Gear,
    GearDefault,
    VertexIdToDistanceMapping,
)
from ._strategies import (
    NextWeightedEdges,
)
from ._traversals import (
    define_distances,
    Traversal,
    _TraversalWithDistance,
    TraversalShortestPathsFlex,
)


State = tuple[T_vertex_id, int]


class _TraversalInfBranching(
    Generic[T_vertex_id, T_weight],
    _TraversalWithDistance[T_vertex_id, T_vertex_id, T_weight, Any],
    ABC,
):
    """
    A _TraversalWithDistance where additionally to a gear an internal gear
    for States as vertices are kept, and labels are not used.

    For internal use only. Hidden in API documentation.
    """

    def __init__(
        self,
        gear: Gear[T_vertex_id, T_vertex_id, T_weight, Any],
        internal_gear: Gear[State[T_vertex_id], State[T_vertex_id], T_weight, Any],
    ) -> None:
        self._internal_gear = internal_gear
        super().__init__(False, False, vertex_as_id, gear)


class TraversalShortestPathsInfBranchingSortedFlex(
    _TraversalInfBranching[T_vertex_id, T_weight],
    ABC,
):
    """
    | Bases: Generic[`T_vertex_id`, `T_weight`],
    | `Traversal` [`T_vertex_id`, `T_vertex_id`, Any]

    **Algorithm:** Weighted shortest paths in infinitely branching
    graphs with sorted edges, implemented by
    `problem reduction <infinite_branching_in_nographs>`
    to a Dijkstra shortest paths problem.

    **Properties:** Vertices are reported (and expanded) ordered by increasing distance
    (minimally necessary sum of edge weights) from a start vertex.

    **Input:** Weighted directed graph. Weights need to be non-negative.

    Infinite branching is allowed. The (possibly infinitely many) edges per vertex
    need to be given sorted by ascending length. The algorithm can only be used
    if for computing the next shortest path to be reported, in all cases, only a
    finite incremental search is necessary.

    One or more start vertices.
    Vertices need to be hashable (a vertex is directly used as
    `vertex id <T_vertex_id>`).

    Labels of edges are allowed, but will be ignored. If path generation is
    demanded, labels and weights are not taken into the paths.

    **Search state:** When a vertex is *expanded* (traversal calls next_edges or
    next_labeled_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *distance*, *paths*, and *distances*.

    :param gear: See `gears API <gears_api>` and class `Gear`.
      Used for storing and returning results (graph data in the domain of the
      given problem).

    :param internal_gear: See `gears API <gears_api>` and class `Gear`.
      Used for storing internal results (graph data in the domain of the
      problem, that the given problem is reduced to).

    :param next_edges: See `NextWeightedEdges` function. If None, provide
      next_labeled_edges.
    """

    def __init__(
        self,
        gear: Gear[T_vertex_id, T_vertex_id, T_weight, Any],
        internal_gear: Gear[State[T_vertex_id], State[T_vertex_id], T_weight, Any],
        next_edges: NextWeightedEdges[
            T_vertex_id,
            TraversalShortestPathsInfBranchingSortedFlex[T_vertex_id, T_weight],
            T_weight,
        ],
    ) -> None:
        # Re-declared (identically), just for giving specific docstring
        self.distances: VertexIdToDistanceMapping[T_vertex_id, T_weight]
        """ Final distance values of some vertices (distance from a start vertex).
        It is only filled if option *store_distances* is used.
        After an exhaustive search, the collection contains exactly
        and only the distances of all vertices that are reachable from the start
        vertices and of the start vertices themselves.
        """

        super().__init__(gear, internal_gear)
        self._next_edges = next_edges
        # The following values are not used by NoGraphs. They is only set
        # to have some initialization.
        self._store_distances = False

    def start_from(
        self,
        start_vertex: Optional[T_vertex_id] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex_id]] = None,
        build_paths: bool = False,
        combined_calculation_limit: Optional[int] = None,
        store_distances: bool = False,
    ) -> TraversalShortestPathsInfBranchingSortedFlex[T_vertex_id, T_weight]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices the search should start
            at. Only allowed if start_vertex equals None.

        :param build_paths: If true, build paths from start vertices for each reported
            vertex, and an empty path for each start vertex. The class can only
            generate paths of unweighted and unlabeled paths.

        :param combined_calculation_limit: If provided, maximal number of vertices
            and edges in sum (note the difference here to the meaning of the option
            for other strategies!) to process (read in) from your graph. If it is
            exceeded, a RuntimeError will be raised.

        :param store_distances: If True, the found distances of vertices are
            stored in traversal attribute distances. See attribute distances.

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
            combined_calculation_limit,
            self._gear,
        )
        self._store_distances = store_distances

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given. Each start vertex has distance 0
        # from a start vertex (itself), but only if store_distances is demanded.
        zero = self._gear.zero()
        self.distances = define_distances(
            self._gear,
            None,
            ((vertex, zero) for vertex in self._start_vertices)
            if store_distances
            else (),
            self._is_tree,
        )

        # The following value is not used by NoGraphs. It are only set
        # to have some defined values before the traversal iterator sets it.
        self.distance = self._gear.infinity()

        super()._start()
        return self

    def _traverse(self) -> Iterator[T_vertex_id]:
        def next_state_edges(
            state: State[T_vertex_id],
            p_traversal: TraversalShortestPathsFlex[
                State[T_vertex_id], State[T_vertex_id], T_weight, Any
            ],
        ) -> Iterator[WeightedUnlabeledOutEdge[State[T_vertex_id], T_weight]]:
            vertex, edge_no = state
            base_state = (vertex, 0)  # state representing "vertex entered"
            base_state_distance = p_traversal.distances[base_state]  # distance there
            if edge_no == 0:
                # In the base state of vertex, start the iteration through its edges
                self.distance = base_state_distance
                iterator = iter(self._next_edges(vertex, self))
                state_iterators[vertex] = iterator
            else:
                # In other states, continue iterating though the edges of vertex
                iterator = state_iterators[vertex]
            try:
                # Get end vertex and length of next edge from vertex
                res = next(iterator)
                next_vertex, length_from_base = res[0], res[1]

                # Transform length and distance to those in search graph
                next_distance = base_state_distance + length_from_base
                state_distance = p_traversal.distances[state]
                state_edge_length = next_distance - state_distance
                # Edge to synthetic vertex that stands for "next vertex, first edge"
                yield (next_vertex, 0), state_edge_length
                # Edge to synthetic vertex that stands for "same vertex, next edge"
                yield (vertex, edge_no + 1), state_edge_length
            except StopIteration:
                # The iterator gave us all edges from vertex. We can delete it now.
                del state_iterators[vertex]

        # Copy Traversal attributes into method scope (faster access)
        build_paths = self._build_paths
        predecessors = self._predecessors
        store_distances = self._store_distances
        distances = self.distances

        # Mapping from vertex to edge iterator
        state_iterators = dict[
            T_vertex_id, Iterator[WeightedOutEdge[T_vertex_id, T_weight, Any]]
        ]()
        # Generate shortest paths starting at state "start vertex, first edge"
        start_states = [(start_vertex, 0) for start_vertex in self._start_vertices]
        traversal = TraversalShortestPathsFlex[
            State[T_vertex_id], State[T_vertex_id], T_weight, Any
        ](vertex_as_id, self._internal_gear, next_state_edges)
        _ = traversal.start_from(
            start_vertices=start_states,
            build_paths=self._build_paths,
            calculation_limit=self._calculation_limit,
            keep_distances=True,
        )
        # Filter the base states "vertex, first edge" from the reported states.
        traversal_paths_iter_vertices_to_start = traversal.paths.iter_vertices_to_start
        for state in traversal:
            vertex, edge_no = state
            if edge_no == 0:
                # The distance of the state in the search graph is the distance
                # of vertex in the original graph
                self.distance = traversal.distance
                if build_paths:
                    # The predecessor state contains the predecessor vertex
                    i = traversal_paths_iter_vertices_to_start(state)
                    _ = next(i)  # equals state
                    prev_vertex, _ = next(i)  # predecessor of state
                    predecessors[vertex] = prev_vertex
                if store_distances:
                    # If demanded, save distance to distances collection
                    distances[vertex] = traversal.distance
                # Report the current vertex
                yield vertex


class TraversalShortestPathsInfBranchingSorted(
    TraversalShortestPathsInfBranchingSortedFlex[T_vertex_id, Union[T_weight, float]],
):
    """
    Eases the use of `TraversalShortestPathsInfBranchingSortedFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       TraversalShortestPathsInfBranchingSorted[T_vertex_id, T_weight](
           *args, **keywords
       )

    is a short form for

    .. code-block:: python

       TraversalShortestPathsInfBranchingSortedFlex[
           T_vertex_id, Union[T_weight, float]],
      ](nog.vertex_as_id, nog.GearDefault(), nog.GearDefault(), *args, **keywords)

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - The used weights are defined by Union[T_weight, float], see `GearDefault`
    """

    def __init__(
        self,
        next_edges: NextWeightedEdges[
            T_vertex_id,
            TraversalShortestPathsInfBranchingSortedFlex[
                T_vertex_id, Union[T_weight, float]
            ],
            T_weight,
        ],
    ):
        super().__init__(
            GearDefault[T_vertex_id, T_vertex_id, T_weight, Any](),
            GearDefault[
                State[T_vertex_id], State[T_vertex_id], Union[T_weight, float], Any
            ](),
            next_edges,
        )
