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

"$$ import_from('$$/MTraversalWithWeights.py') $$"


class TraversalMinimumSpanningTreeFlex(
    _TraversalWithWeights[T_vertex, T_vertex_id, T_weight, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

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
        # $$ MStrategyWithWeights.init_signature('TraversalMinimumSpanningTreeFlex')
    ) -> None:
        # $$ MStrategyWithWeights.init_code(is_tree='False')

        self.edge: Optional[WeightedFullEdge[T_vertex, T_weight, T_labels]] = None
        """ Tuple of from_vertex, to_vertex, the weight of the edge,
        and additional data you have provided with the edge (if so).
        """

        # The following value is not used by NoGraphs. It is only set
        # to have some initialization.
        self._start_vertices_and_ids = tuple[tuple[T_vertex, T_vertex_id]]()

    def start_from(
        self,
        # $$ insert_from('$$/method_start_from/signature_standard.py')
    ) -> TraversalMinimumSpanningTreeFlex[T_vertex, T_vertex_id, T_weight, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.
        If you provide more than one start vertex, the result consists of several
        trees that are only connected if the start vertices are connected.

        # $$ insert_from('$$/method_start_from/doc_std.rst')

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        "$$ insert_from('$$/method_start_from/code_start.py') $$"

        # The following value is not used by NoGraphs. It is only set
        # to have some defined value before the traversal iterator sets them.
        self.edge = None

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start.py') $$"

        # Get references of used gear objects and methods (avoid attribute resolution)
        "$$ MVertexMappingExpectNone.access(name='predecessors') $$"
        "$$ MVertexMappingExpectNone.access(name='attributes') $$"

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
        # $$ MCalculationLimit.step("len(self._start_vertices_and_ids)")

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

        "$$ MCalculationLimit.prepare() $$"

        # Get references of used gear objects and methods (avoid attribute resolution)
        "$$ MVertexSet.access(name='visited') $$"

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
            "$$ MStrategy.vertex_to_id('to_vertex', 'to_id') $$"

            "$$ MVertexSet.if_visited_continue_else_add('visited', 'to_id', '') $$"

            if build_paths:
                """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                          'predecessors', 'attributes',
                          'vertex', 'to_id',
                          'to_edge[-1]', from_edge=True)
                $$"""

            # Export traversal data to traversal attribute and report vertex
            # (Expression type follows from types of vertex and to_edge and the
            #  definition of WeightedFullEdge. MyPy + PyCharm cannot derive this.)
            # noinspection PyTypeChecker
            full_edge: WeightedFullEdge[T_vertex, T_weight, T_labels] = (
                vertex,
            ) + to_edge  # type: ignore[assignment]
            self.edge = full_edge
            yield to_vertex

            "$$ MCalculationLimit.step() $$"

            for n_to_edge in next_edges(to_vertex, self):
                n_to_vertex, n_weight = n_to_edge[0], n_to_edge[1]
                # If the edge leads to a vertex that is, so far, not reached by edges
                # of the MST, it is a candidate for a MST edge. We push it to the heap.
                "$$ MStrategy.vertex_to_id('n_to_vertex', 'n_to_id') $$"

                "$$ MVertexSet.if_visited_continue('visited', 'n_to_id', '') $$"

                heappush(
                    to_visit,
                    (n_weight, next(unique_no), to_vertex, n_to_edge),
                )


"$$ MStrategyWithWeights.standard_for_flex('TraversalMinimumSpanningTree') $$"
