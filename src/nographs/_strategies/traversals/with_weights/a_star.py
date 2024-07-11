from __future__ import annotations

import itertools
from heapq import heapify, heappop, heappush
from numbers import Real
from typing import Optional, Any, Generic, Union
from collections.abc import Callable, Iterable, Generator

from nographs._types import (
    T_vertex,
    T_labels,
    VertexToID,
    T_vertex_id,
    T_weight,
    vertex_as_id,
)
from nographs._gears import (
    Gear,
    GearDefault,
    VertexIdToDistanceMapping,
)
from nographs._gear_collections import (
    access_to_vertex_mapping_expect_none,
    access_to_vertex_mapping,
)
from ...type_aliases import NextWeightedEdges, NextWeightedLabeledEdges
from ...utils import define_distances, iter_start_vertices_and_ids
from ..traversal import Traversal
from .traversal_with_weights import (
    _create_unified_next_weighted,
    _TraversalWithDistances,
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

    **Input:** Weighted directed graph. Weights need to be non-negative.
    One or more start vertices. Optional calculation limit.
    A heuristic function that estimates the cost of the cheapest path from a given
    vertex to the goal (resp. to any of your goal vertices, if you have more than
    one), and never overestimates the actual needed costs ("admissible heuristic
    function").

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

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices the search should start
            at. Only allowed if start_vertex equals None.

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

        # Explicitly list start vertices and their id. Needed several times.
        self._start_vertices_and_ids = tuple(
            iter_start_vertices_and_ids(self._start_vertices, self._vertex_to_id)
        )

        # ----- Initialize method specific public bookkeeping -----
        self._heuristic = heuristic
        self._known_distances = known_distances
        self._known_path_length_guesses = known_path_length_guesses

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given. Each start vertex has distance 0
        # from a start vertex (itself), if not defined otherwise.
        # Here, the distances need to be initialized even if is_tree == True, since
        # the algorithm stores path length guesses in the heap and always uses
        # the distances from the collection.
        zero = self._gear.zero()
        self.distances = define_distances(
            self._gear,
            self._known_distances,
            ((vertex_id, zero) for vertex, vertex_id in self._start_vertices_and_ids),
            False,
        )

        # The following two values are not used by NoGraphs. They are only set
        # to have some defined values before the traversal iterator sets them.
        self.path_length = self._gear.infinity()
        self.depth = 0

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

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Copy Gear attributes into method scope (faster access)
        infinity = self._gear.infinity()

        # Copy traversal specific attributes into method scope
        is_tree = self._is_tree
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
        distances = self.distances
        _, distances_sequence, distances_wrapper = access_to_vertex_mapping(distances)

        # Each start vertex has path_length_guess of distance + heuristic(vertex),
        # if not defined otherwise.
        assert heuristic is not None  # set by __init__
        path_length_guesses = define_distances(
            self._gear,
            self._known_path_length_guesses,
            (
                (
                    vertex_id,
                    distances_sequence[vertex_id] + heuristic(vertex),
                )
                for vertex, vertex_id in self._start_vertices_and_ids
            ),
            is_tree,
        )
        # Get references of used gear objects and methods (avoid attribute resolution)
        _, path_length_guesses_sequence, path_length_guesses_wrapper = (
            access_to_vertex_mapping(path_length_guesses)
        )

        # So far, the start vertices are to be visited. Each has an edge count of 0,
        # and its path length guess is the one computed above.
        to_visit = [  # used as collection.heapq of tuples, the lowest distance first
            (
                path_length_guesses_sequence[
                    vertex_id
                ],  # (This comment is just to prevent Black from moving the comma up)
                next(unique_no),
                vertex,
                0,
            )
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
                # (Distance values equal to or higher than the chosen infinity
                # value of the gear are invalid and cannot be handled further.)
                if infinity <= n_path_weight:
                    self._gear.raise_distance_infinity_overflow_error(n_path_weight)

                # If the found path to the neighbor is not shorter than the shortest
                # such path found so far, and we are not in a tree, we can safely
                # ignore the path. Otherwise, it is a new candidate for a shortest
                # path to the neighbor, and we push it to the heap.
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
                    # Store the predecessor (vertex) of the neighbor
                    try:
                        predecessors_sequence[n_id] = vertex
                    except IndexError:
                        predecessors_wrapper.extend_and_set(n_id, vertex)
                    # Store the labels of the edge to the neighbor
                    if labeled_edges:
                        # Proof for correctness of the type hole:
                        # self._labeled_edges -> next_edges (a NextWeightedEdges)
                        # is a NextWeightedLabeledEdges -> edge[-1] is a T_labels
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
