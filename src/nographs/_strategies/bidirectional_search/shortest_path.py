from __future__ import annotations

import itertools
from heapq import heapify, heappop, heappush
from typing import Generic, Optional, Union
from collections.abc import Iterable, Collection

from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
    vertex_as_id,
    T_weight,
)
from nographs._gears import (
    Gear,
    GearDefault,
)
from nographs._path import (
    Path,
    PathOfLabeledEdges,
    PathOfUnlabeledEdges,
)
from nographs._gear_collections import (
    access_to_vertex_mapping_expect_none,
    access_to_vertex_mapping,
)
from ..type_aliases import (
    Strategy,
    BNextWeightedEdges,
    BNextWeightedLabeledEdges,
)
from ..utils import (
    create_paths,
    iter_start_vertices_and_ids,
    define_distances,
)
from .base import (
    _create_unified_next_weighted_bidirectional,
    _search_needs_search_object,
)


class BSearchShortestPathFlex(
    Strategy[T_vertex, T_vertex_id, T_labels],
    Generic[T_vertex, T_vertex_id, T_weight, T_labels],
):
    """
    Bases: `Strategy` [`T_vertex`, `T_vertex_id`, `T_labels`],
    Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `Gear`.

    :param next_edges: Tuple `BNextWeightedEdges` of two NextEdges functions.
      See paragraph *input* below for details. If None, provide next_labeled_edges.

    :param next_labeled_edges: Tuple `BNextWeightedLabeledEdges` of two NextEdges
      functions. See paragraph *input* below for details. The parameter is only
      allowed if next_edges equals None. If given, paths will record the given labels.

    **Algorithm:** Bidirectional version of the shortest paths algorithm of Dijkstra,
    non-recursive, based on heap.

    **Properties:** In both directions, vertices are visited by increasing distance
    (minimally necessary sum of edge weights) from a start (resp. a goal) vertex,
    till a shortest path (minimal sum of edge weights) from a start to a goal vertex
    is found. Each vertex is visited only once.

    **Input:** Weighted directed graph. One or more start vertices, and one or more
    goal vertices. Weights need to be non-negative. NextWeightedEdges (resp.
    NextWeightedLabeledEdges) functions both for the outgoing edges from a vertex
    and the incoming edges to a vertex have to be provided, and they need to describe
    the same graph. Optional calculation limit.

    Note: A shortest path from a vertex *v* to itself always exists, has length 0,
    and will be found by the class, whilst TraversalShortestPaths does not report
    start vertices and thus,
    TraversalShortestPaths(<something>).start_at(v).go_to(v) fails.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
        next_edges: Optional[
            BNextWeightedEdges[
                T_vertex,
                BSearchShortestPathFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
            ],
        ] = None,
        *,
        next_labeled_edges: Optional[
            BNextWeightedLabeledEdges[
                T_vertex,
                BSearchShortestPathFlex[T_vertex, T_vertex_id, T_weight, T_labels],
                T_weight,
                T_labels,
            ],
        ] = None,
    ) -> None:
        self._vertex_to_id = vertex_to_id
        self._gear = gear

        (
            self._next_edges,
            self._labeled_edges,
        ) = _create_unified_next_weighted_bidirectional(next_edges, next_labeled_edges)

    def start_from(
        self,
        start_and_goal_vertex: Optional[tuple[T_vertex, T_vertex]] = None,
        *,
        start_and_goal_vertices: Optional[
            tuple[Iterable[T_vertex], Iterable[T_vertex]]
        ] = None,
        build_path: bool = False,
        calculation_limit: Optional[int] = None,
        fail_silently: bool = False,
    ) -> tuple[T_weight, Path[T_vertex, T_vertex_id, T_labels]]:
        """
        Start the search both from a start vertex and a goal vertex, resp. both
        from a set of start vertices and a set of goal vertices. Return the
        length of a shortest (sum of edge weights) path between the/a start vertex
        and the/a goal vertex. If building a path was requested, also return the path,
        and otherwise, return a dummy path object.

        If the search ends without having found a path, raise KeyError,
        or, if a silent fail is demanded, return infinity and a dummy path object.
        Here, infinity means the value for infinite distance that is defined by the
        used `Gear` (as provided by a call of gear.infinity()).

        NoGraphs gives no guarantees about a dummy path. Do not use it for anything.

        :param start_and_goal_vertex: The start vertex and the goal vertex of the
            search. If None, provide start_and_goal_vertices.

        :param start_and_goal_vertices: The set of start vertices and the set of
            goal vertices of the search. Only allowed if start_and_goal_vertex
            equals None.

        :param build_path: If true, build and return a path of the minimum possible
            length.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph in each of the searches in one of the two
            directions. If it is exceeded, a RuntimeError will be raised.

        :param fail_silently: If no path can be found, fail silently (see above)
            instead of raising an exception.
        """
        # steps that other strategies do in start_from

        _search_needs_search_object(self, BSearchShortestPathFlex)

        start_vertices: Iterable[T_vertex]
        goal_vertices: Iterable[T_vertex]
        if start_and_goal_vertex is not None:
            if start_and_goal_vertices is not None:
                raise RuntimeError(
                    "Both start_and_goal_vertex and "
                    + "start_and_goal_vertices provided."
                )
            start_vertex, goal_vertex = start_and_goal_vertex
            start_vertices, goal_vertices = [start_vertex], [goal_vertex]
        else:
            if start_and_goal_vertices is None:
                raise RuntimeError(
                    "Neither start_and_goal_vertex nor "
                    + "start_and_goal_vertices provided."
                )
            start_vertices, goal_vertices = start_and_goal_vertices
            if build_path:
                # Below, we will consume vertices by the call of *create_paths*, so we
                # first make a collection out of start_vertices resp. goal_vertices,
                # except they are already given as collection
                if not isinstance(start_vertices, Collection):
                    start_vertices = self._gear.sequence_of_vertices(start_vertices)
                if not isinstance(goal_vertices, Collection):
                    goal_vertices = self._gear.sequence_of_vertices(goal_vertices)

        paths_forwards, predecessors_forwards, attributes_forwards = create_paths(
            build_path,
            self._gear,
            self._labeled_edges,
            self._vertex_to_id,
            start_vertices,
        )
        paths_backwards, predecessors_backwards, attributes_backwards = create_paths(
            build_path,
            self._gear,
            self._labeled_edges,
            self._vertex_to_id,
            goal_vertices,
        )

        # Copy Gear attributes into method scope (faster access)
        infinity = self._gear.infinity()

        # Copy Traversal attributes into method scope (faster access)
        labeled_edges = self._labeled_edges
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
        zero = self._gear.zero()

        # Prepare limit check done by zero check
        if calculation_limit is None:
            calculation_limit_forwards = calculation_limit_backwards = -1  # unused
        else:
            calculation_limit += 1
            calculation_limit_forwards = calculation_limit_backwards = calculation_limit

        # Copy traversal specific attributes into method scope
        next_edges_forwards, next_edges_backwards = self._next_edges

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            predecessors_sequence_forwards,
            predecessors_wrapper_forwards,
        ) = access_to_vertex_mapping_expect_none(predecessors_forwards)
        (
            _,
            predecessors_sequence_backwards,
            predecessors_wrapper_backwards,
        ) = access_to_vertex_mapping_expect_none(predecessors_backwards)

        (
            _,
            attributes_sequence_forwards,
            attributes_wrapper_forwards,
        ) = access_to_vertex_mapping_expect_none(attributes_forwards)
        (
            _,
            attributes_sequence_backwards,
            attributes_wrapper_backwards,
        ) = access_to_vertex_mapping_expect_none(attributes_backwards)

        # ----- Initialize method specific bookkeeping -----

        # Unique number, that prevents heapq from sorting by vertices in case of a
        # tie in the sort field, because vertices do not need to be pairwise
        # comparable. The integers from -5 to 256 are used first, because they are
        # internalized (pre-calculated, and thus fastest). We count downwards like we
        # do in A* search. There, it is preferable, because a LIFO behavior makes A*
        # often faster. Here, we do it simply to do it the same way.
        # (We use two counters so that "the same integers" can be used in the search
        #  in both directions)
        unique_no_forwards = itertools.count(256, -1)
        unique_no_backwards = itertools.count(256, -1)

        # Explicitly list start vertices and their id. Needed several times.
        start_vertices_and_ids_forwards = tuple(
            iter_start_vertices_and_ids(start_vertices, self._vertex_to_id)
        )
        start_vertices_and_ids_backwards = tuple(
            iter_start_vertices_and_ids(goal_vertices, self._vertex_to_id)
        )

        # Get the right class for storing a path (labeled or not)
        path_cls: type[Path]
        if labeled_edges:
            path_cls = PathOfLabeledEdges[T_vertex, T_vertex_id, T_labels]
        else:
            path_cls = PathOfUnlabeledEdges[T_vertex, T_vertex_id, T_labels]

        # At least one start vertex and one goal vertex is necessary to find
        # a result. The case of having no start or goal vertex is handled
        # manually here, because if there is no start vertex, the step
        # "choose an arbitrary start vertex..." will fail for this search strategy.
        if (
            len(start_vertices_and_ids_forwards) == 0
            or len(start_vertices_and_ids_backwards) == 0
        ):
            return self._search_failed(path_cls, infinity, fail_silently)

        # Detect if a start vertex is also goal vertex, and report result manually.
        # (Without this manual handling, a non-self loop from such a start vertex back
        #  to itself with a length > 0 would be reported as smallest distance. This
        #  would be unexpected for users, since they expect that the distance from a
        #  vertex to itself is always 0.)
        common_vertex_ids = set(
            v_id for v, v_id in start_vertices_and_ids_forwards
        ).intersection(v_id for v, v_id in start_vertices_and_ids_backwards)
        if common_vertex_ids:
            for c_vertex, cv_id in start_vertices_and_ids_forwards:
                if cv_id in common_vertex_ids:
                    p = path_cls.from_vertex(c_vertex)
                    return zero, p

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given. Each start vertex has distance 0
        # from a start vertex (itself), if not defined otherwise.
        distances_forwards = define_distances(
            self._gear,
            None,
            (
                (vertex_id, zero)
                for vertex, vertex_id in start_vertices_and_ids_forwards
            ),
            False,
        )
        distances_backwards = define_distances(
            self._gear,
            None,
            (
                (vertex_id, zero)
                for vertex, vertex_id in start_vertices_and_ids_backwards
            ),
            False,
        )

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            _,
            distances_sequence_forwards,
            distances_wrapper_forwards,
        ) = access_to_vertex_mapping(distances_forwards)
        (
            _,
            distances_sequence_backwards,
            distances_wrapper_backwards,
        ) = access_to_vertex_mapping(distances_backwards)

        # So far, the start vertices are to be visited.
        # (No index exception possible at the following indexed access)
        # The following lists are used as collection.heapq of tuples, the lowest
        # distance first.
        to_visit_forwards = [
            (distances_sequence_forwards[vertex_id], next(unique_no_forwards), vertex)
            for vertex, vertex_id in start_vertices_and_ids_forwards
        ]
        heapify(to_visit_forwards)
        to_visit_backwards = [
            (distances_sequence_backwards[vertex_id], next(unique_no_backwards), vertex)
            for vertex, vertex_id in start_vertices_and_ids_backwards
        ]
        heapify(to_visit_backwards)

        # No connection between forwards and backwards search found so far
        # (The value of best_connection_node is not used. So, we initialize it just to
        #  any vertex)
        best_path_length = infinity
        best_connecting_node = start_vertices_and_ids_forwards[0][0]
        others_path_weight = zero

        # ----- Loop -----
        for (
            to_visit,
            distances_sequence,
            distances_wrapper,
            distances_sequence_other,
            next_edges,
            predecessors_sequence,
            predecessors_wrapper,
            attributes_sequence,
            attributes_wrapper,
            unique_no,
            forwards,
        ) in itertools.cycle(
            (
                (
                    to_visit_forwards,
                    distances_sequence_forwards,
                    distances_wrapper_forwards,
                    distances_sequence_backwards,
                    next_edges_forwards,
                    predecessors_sequence_forwards,
                    predecessors_wrapper_forwards,
                    attributes_sequence_forwards,
                    attributes_wrapper_forwards,
                    unique_no_forwards,
                    True,
                ),
                (
                    to_visit_backwards,
                    distances_sequence_backwards,
                    distances_wrapper_backwards,
                    distances_sequence_forwards,
                    next_edges_backwards,
                    predecessors_sequence_backwards,
                    predecessors_wrapper_backwards,
                    attributes_sequence_backwards,
                    attributes_wrapper_backwards,
                    unique_no_backwards,
                    False,
                ),
            )
        ):
            if not to_visit:
                # If the same edges are reported in both directions and there is a
                # path between a start vertex and a goal vertex, then neither the
                # forward nor the backward iteration can become exhausted before a
                # solution is found. Thus, running out of vertices in one of the
                # iterations mean there is no solution of the adjacency functions have
                # errors.
                return self._search_failed(path_cls, infinity, fail_silently)

            # Visit path with the lowest distance first
            path_weight, _, vertex = heappop(to_visit)

            # A vertex can get added to the heap multiple times. We want to process
            # it only once, the first time it is removed from the heap, because this
            # is the case with the shortest distance from start.
            v_id: T_vertex_id = (
                maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else vertex
            )

            if distances_sequence[v_id] < path_weight:
                continue

            if infinity != best_path_length <= path_weight + others_path_weight:
                # (Infinity handled manually: if best_path_length is infinity,
                # the sum to the right has to be regarded as being smaller, disregarding
                # its value, that could be higher in case of an overflow over
                # infinity.)
                break  # Finished. Nothing shorter than best_path_length will come.

            # store our length for the check when expanding in the opposite directions
            others_path_weight = path_weight

            if calculation_limit and not (
                (calculation_limit_forwards := calculation_limit_forwards - 1)
                if forwards
                else (calculation_limit_backwards := calculation_limit_backwards - 1)
            ):
                raise RuntimeError("Number of visited vertices reached limit")

            # We will expand this vertex

            # Expand vertex. New neighbors are one edge count deeper than vertex.
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
                    if distances_sequence[n_id] <= n_path_weight:
                        continue
                    distances_sequence[n_id] = n_path_weight
                except IndexError:
                    # n_id not in distances_collection. To be regarded as value
                    # infinity, i.e., n_path_weight is smaller.
                    distances_wrapper.extend_and_set(n_id, n_path_weight)

                # If we are to generate a path, we have to do it here, since the
                # edge we have to add to the path prefix is not stored on the heap
                if build_path:
                    try:
                        predecessors_sequence[n_id] = vertex
                    except IndexError:
                        predecessors_wrapper.extend_and_set(n_id, vertex)
                    if labeled_edges:
                        # self._labeled_edges  -> next_edges (a NextWeightedEdges) is a
                        # NextWeightedLabeledEdges -> edge[-1] is a T_labels.
                        data_of_edge: T_labels = edge[-1]  # type: ignore[assignment]
                        try:
                            attributes_sequence[n_id] = data_of_edge
                        except IndexError:
                            attributes_wrapper.extend_and_set(n_id, data_of_edge)

                heappush(to_visit, (n_path_weight, next(unique_no), neighbor))

                # If we already have an estimation for the distance from the neighbor
                # to the other end of the search and the resulting total distance
                # is better than the best we have seen so far, store the length and
                # the neighbor vertex.
                try:
                    if (
                        n_path_weight + distances_sequence_other[n_id]
                        >= best_path_length
                    ):
                        continue
                    best_path_length = n_path_weight + distances_sequence_other[n_id]
                    best_connecting_node = neighbor
                except IndexError:
                    # n_id not in distances_collection. To be regarded as value
                    # infinity, i.e., best_path_length is equal or smaller.
                    pass

            path = (
                path_cls.from_bidirectional_search(
                    paths_forwards, paths_backwards, best_connecting_node
                )
                if build_path
                else path_cls.of_nothing()
            )
        return best_path_length, path

    @staticmethod
    def _search_failed(
        path_cls: type[Path], infinity: T_weight, fail_silently: bool
    ) -> tuple[T_weight, Path[T_vertex, T_vertex_id, T_labels]]:
        """For a silent fail, return the value that marks that the search has failed:
        A tuple of the infinity value of the weights and an empty path. If no
        silent fail is requested, raise a key error telling that no goal vertex
        has been found."""
        if fail_silently:
            return infinity, path_cls.of_nothing()
        else:
            raise KeyError("No path to (a) goal vertex found")


class BSearchShortestPath(
    Generic[T_vertex, T_weight, T_labels],
    BSearchShortestPathFlex[T_vertex, T_vertex, Union[T_weight, float], T_labels],
):
    """
    Eases the use of `BSearchShortestPathFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       BSearchShortestPath[T_vertex, T_weight, T_labels](*args, **keywords)

    is a short form for

    .. code-block:: python

       BSearchShortestPathFlex[
           T_vertex, T_vertex, Union[T_weight, float], T_labels],
      ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

    Implication:

    - `GearDefault` is used, see there how it and its superclass work
    - The used weights are defined by Union[T_weight, float], see `GearDefault`
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_edges: Optional[
            BNextWeightedEdges[
                T_vertex,
                BSearchShortestPathFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
            ],
        ] = None,
        *,
        next_labeled_edges: Optional[
            BNextWeightedLabeledEdges[
                T_vertex,
                BSearchShortestPathFlex[
                    T_vertex, T_vertex, Union[T_weight, float], T_labels
                ],
                T_weight,
                T_labels,
            ],
        ] = None,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_edges,
            next_labeled_edges=next_labeled_edges,
        )
