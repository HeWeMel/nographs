from __future__ import annotations

import itertools
from heapq import heapify, heappop, heappush
from typing import Optional, Any, Generic, Union
from collections.abc import Iterable, Generator

from nographs._gears import VertexIdToDistanceMapping
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
)
from nographs._gear_collections import (
    access_to_vertex_mapping,
    access_to_vertex_mapping_expect_none,
)
from ...type_aliases import (
    NextWeightedEdges,
    NextWeightedLabeledEdges,
)
from ...utils import iter_start_vertices_and_ids, define_distances
from ..traversal import Traversal
from .traversal_with_weights import (
    _create_unified_next_weighted,
    _TraversalWithDistance,
)

"$$ import_from('$$/MTraversalWithWeights.py') $$"


class TraversalShortestPathsFlex(
    _TraversalWithDistance[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

    :param is_tree: bool: If it is certain, that during each traversal run, each vertex
     can be reached only once, is_tree can be set to True. This improves performance,
     but attribute *distances* of the traversal will not be updated during and after
     the traversal.

    **Algorithm:** Shortest paths algorithm of Dijkstra, non-recursive, based on heap.

    **Properties:** Vertices are reported (and expanded) ordered by increasing distance
    (minimally necessary sum of edge weights) from a start vertex.

    # $$ insert_from('$$/cls_traversal/doc_input.rst')

    **Search state:** When a vertex is *expanded* (traversal calls next_edges or
    next_labeled_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *distance*, *depth*, *paths*, and *distances*.
    """

    def __init__(
        self,
        # $$ MStrategyWithWeights.init_signature('TraversalShortestPathsFlex')
        is_tree: bool = False,
    ) -> None:
        # $$ MStrategyWithWeights.init_code('is_tree')

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
        # $$ insert_from('$$/method_start_from/signature_standard.py')
        keep_distances: bool = False,
        known_distances: Optional[
            VertexIdToDistanceMapping[T_vertex_id, T_weight]
        ] = None,
    ) -> TraversalShortestPathsFlex[T_vertex, T_vertex_id, T_weight, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        # $$ insert_from('$$/method_start_from/doc_std.rst')

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

        "$$ insert_from('$$/method_start_from/code_start.py') $$"
        self._keep_distances = keep_distances
        self._known_distances = known_distances

        "$$ insert_from('$$/method_start_from/code_init_distances_and_zero.py') $$"

        # The following two values are not used by NoGraphs. They are only set
        # to have some defined values before the traversal iterator sets them.
        self.distance = self._gear.infinity()
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
        keep_distances = self._keep_distances

        # Get references of used gear objects and methods (avoid attribute resolution)
        "$$ MVertexMappingExpectNone.access(name='predecessors') $$"
        "$$ MVertexMappingExpectNone.access(name='attributes') $$"
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
        distances = self.distances
        "$$ MVertexMapping.access('distances') $$"

        # So far, the start vertices are to be visited. Each has an edge count of 0.
        # (We know: vertex_id in distances. No index exception possible here.)
        to_visit = [  # used as collection.heapq of tuples, the lowest distance first
            (
                ("""$$ MVertexMapping.get_included('distances', 'vertex_id') $$"""),
                next(unique_no),
                vertex,
                0,
            )
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
                "$$ MStrategy.vertex_to_id('vertex', 'v_id') $$"

                # (We know: v_id in distances. No index exception possible here.)
                if (
                    "$$ MVertexMapping.get_included('distances', 'v_id') $$"
                    < path_weight
                ):
                    continue
                if not keep_distances:
                    # Allow garbage collector to free distance value (not the entry in
                    # the collection!) if nowhere else needed any more. Note that
                    # we can only set to the zero value here, since we still have to
                    # exclude further longer paths to the vertex, and only zero does
                    # this job for all possible distances.
                    # (We know: v_id in distances. No index exception possible here.)
                    "$$ MVertexMapping.set_included('distances', 'v_id', 'zero') $$"

            # Export traversal data to traversal attributes
            self.distance = path_weight
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
                # such path found so far, we can safely ignore it. Otherwise, it is a
                # new candidate for a shortest path to the neighbor, and we push it to
                # the heap.
                if build_paths or not is_tree:
                    "$$ MStrategy.vertex_to_id('neighbor', 'n_id') $$"

                    if not is_tree:
                        """$$
                        MVertexMapping.if_value_smaller_set_else_continue(
                            'distances', 'n_id', 'n_path_weight') $$"""

                    # If we are to generate a path, we have to do it here, since the
                    # edge we have to add to the path prefix is not stored on the heap.
                    if build_paths:
                        """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                                  'predecessors', 'attributes',
                                  'vertex', 'n_id',
                                  'edge[-1]', from_edge=True)
                        $$"""

                heappush(
                    to_visit,
                    (
                        n_path_weight,
                        next(unique_no),
                        neighbor,
                        n_path_edge_count,
                    ),
                )


"""$$ MStrategyWithWeights.standard_for_flex(
          'TraversalShortestPaths', 'is_tree: bool = False,\n', 'is_tree=is_tree,\n')
$$"""
