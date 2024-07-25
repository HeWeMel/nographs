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

"$$ import_from('$$/MTraversalWithWeights.py') $$"


class TraversalAStarFlex(
    _TraversalWithDistances[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
     can be reached only once, is_tree can be set to True. This improves performance,
     but if *start_from* has been called with parameter *known_path_length_guesses*
     given, this collection will not be updated during the traversal.

    **Algorithm:** The search algorithm A*, non-recursive, based on heap.

    # $$ insert_from('$$/cls_traversal/doc_input.rst')
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
        # $$ MStrategyWithWeights.init_signature('TraversalAStarFlex')
        is_tree: bool = False,
    ) -> None:
        # $$ MStrategyWithWeights.init_code('is_tree')

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
        # $$ insert_from('$$/method_start_from/signature_standard.py')
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

        # $$ insert_from('$$/method_start_from/doc_std.rst')

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

        "$$ insert_from('$$/method_start_from/code_start.py') $$"
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
        "$$ insert_from('$$/method_traverse/code_start.py') $$"

        "$$ MCalculationLimit.prepare() $$"

        # Copy Gear attributes into method scope (faster access)
        infinity = self._gear.infinity()

        # Copy traversal specific attributes into method scope
        is_tree = self._is_tree
        heuristic = self._heuristic

        # Get references of used gear objects and methods (avoid attribute resolution)
        "$$ MVertexMappingExpectNone.access(name='predecessors') $$"
        "$$ MVertexMappingExpectNone.access(name='attributes') $$"

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
        "$$ MVertexMapping.access(name='distances') $$"

        # Each start vertex has path_length_guess of distance + heuristic(vertex),
        # if not defined otherwise.
        assert heuristic is not None  # set by __init__
        path_length_guesses = define_distances(
            self._gear,
            self._known_path_length_guesses,
            (
                (
                    vertex_id,
                    """$$ MVertexMapping.get_included('distances', 'vertex_id')
                    $$"""
                    + heuristic(vertex),
                )
                for vertex, vertex_id in self._start_vertices_and_ids
            ),
            is_tree,
        )
        # Get references of used gear objects and methods (avoid attribute resolution)
        "$$ MVertexMapping.access('path_length_guesses') $$"

        # So far, the start vertices are to be visited. Each has an edge count of 0,
        # and its path length guess is the one computed above.
        to_visit = [  # used as collection.heapq of tuples, the lowest distance first
            (
                """$$ MVertexMapping.get_included('path_length_guesses', 'vertex_id')
                $$"""
                # (This comment is just to prevent Black from moving the comma up)
                ,
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
            "$$ MStrategy.vertex_to_id('vertex', 'v_id') $$"

            # (No index exception possible at the following indexed access)
            if (
                not is_tree
                and path_length_guess
                > """$$
                    MVertexMapping.get_included('path_length_guesses', 'v_id')$$"""
            ):
                continue

            # (No index exception possible here)
            path_weight = "$$ MVertexMapping.get_included('distances', 'v_id') $$"

            # Export traversal data to traversal attributes
            self.path_length = path_weight
            self.depth = path_edge_count

            # We now know the distance of the vertex, so we report it.
            if path_edge_count > 0:  # do not report start vertex
                yield vertex

            "$$ MCalculationLimit.step() $$"

            # Expand vertex. New neighbors are one edge count deeper than vertex.
            n_path_edge_count = path_edge_count + 1
            for edge in next_edges(vertex, self):
                neighbor, weight = edge[0], edge[1]

                n_path_weight = weight + path_weight
                "$$ MStrategyWithWeights.check_overflow('n_path_weight') $$"

                # If the found path to the neighbor is not shorter than the shortest
                # such path found so far, and we are not in a tree, we can safely
                # ignore the path. Otherwise, it is a new candidate for a shortest
                # path to the neighbor, and we push it to the heap.
                "$$ MStrategy.vertex_to_id('neighbor', 'n_id') $$"

                """$$ MVertexMapping.if_value_smaller_or_condition_set_else_continue(
                        'distances', 'n_id', 'n_path_weight', 'is_tree') $$"""

                # If we are to generate a path, we have to do it here, since the edge
                # we have to add to the path prefix is not stored on the heap
                if build_paths:
                    """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                              'predecessors', 'attributes',
                              'vertex', 'n_id',
                              'edge[-1]', from_edge=True)
                    $$"""

                h = heuristic(neighbor)
                if h == infinity:
                    n_guess = infinity
                else:
                    n_guess = n_path_weight + h
                    "$$ MStrategyWithWeights.check_overflow('n_guess') $$"

                if not is_tree:
                    "$$ MVertexMapping.set('path_length_guesses', 'n_id', 'n_guess') $$"
                heappush(
                    to_visit,
                    (n_guess, next(unique_no), neighbor, n_path_edge_count),
                )


"""$$ MStrategyWithWeights.standard_for_flex(
          'TraversalAStar', 'is_tree: bool = False,\n', 'is_tree=is_tree,\n')
$$"""
