from __future__ import annotations

import array
import copy
import itertools
from typing import Optional, Any, Generic
from collections.abc import Iterable, Generator

from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
    vertex_as_id,
)
from nographs._gears import (
    GearDefault,
    GearWithoutDistances,
    VertexIdSet,
)
from nographs._gear_collections import (
    access_to_vertex_set,
    access_to_vertex_mapping_expect_none,
)
from ...type_aliases import (
    NextVertices,
    NextEdges,
    NextLabeledEdges,
)
from ..traversal import (
    _start_from_needs_traversal_object,
)
from .traversal_without_weights import (
    _create_unified_next,
    _TraversalWithoutWeightsWithVisited,
)

"$$ import_from('$$/MTraversalWithoutWeights.py') $$"


class TraversalNeighborsThenDepthFlex(
    _TraversalWithoutWeightsWithVisited[T_vertex, T_vertex_id, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

    **Algorithm:** Variant of the Depth First Search ("DFS"),
    non-recursive implementation.
    Vertices are reported when they are "seen" (read from the graph) for the
    first time - thus not in DFS order!

    **Properties:**
    The graphs is explored as far as possible along each branch before
    backtracking, but in contrast to a Depth First Search, the algorithm
    first reports all successors of the current vertex and then goes deeper.
    A vertex is considered visited when it has been reported or if it is a
    start vertex.

    # $$ insert_from('$$/cls_traversal/doc_input.rst')

    **Search state:** When a vertex is *expanded*
    (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        # $$ MStrategyWithoutWeights.init_signature('TraversalNeighborsThenDepthFlex')
    ) -> None:
        "$$ MStrategyWithoutWeights.init_code(depth_computation_optional = True) $$"
        self._compute_depth = False  # value not used, initialized during traversal

    def start_from(
        self,
        # $$ insert_from('$$/method_start_from/signature.py')
        compute_depth: bool = False,
    ) -> TraversalNeighborsThenDepthFlex[T_vertex, T_vertex_id, T_labels]:
        """
        # $$ insert_from('$$/method_start_from/doc_start.rst')
        # $$ insert_from('$$/method_start_from/doc_already_visited_std.txt')
        # $$ insert_from('$$/method_start_from/doc_compute_depth.txt')
        # $$ insert_from('$$/method_start_from/doc_end.rst')
        """
        "$$ insert_from('$$/method_start_from/code_start.py') $$"
        self._compute_depth = compute_depth
        # Set the externally visible depth to the sensible initial value 0.
        # But if depth is not to be computed, use value -1 instead.
        self.depth = 0 if compute_depth else -1

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start_with_tree_and_visited.py') $$"

        # Copy Traversal-specific attributes into method scope (faster access)
        compute_depth = self._compute_depth

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

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"

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

            "$$ MCalculationLimit.step() $$"

            for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                if not is_tree or build_paths:
                    "$$ MStrategy.vertex_to_id('neighbor', 'n_id')$$"

                    # If not is_tree: Ignore neighbor if already seen, and
                    # else include its ID in visited set.
                    """$$ MVertexSet.if_visited_continue_else_add(
                              'visited', 'n_id', 'not is_tree') $$"""

                    if build_paths:
                        """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                                  'predecessors', 'attributes',
                                  'vertex', 'n_id', 'edge_or_vertex[-1]')
                        $$"""

                yield neighbor

                # Needs to be expanded, in stack order
                to_expand_append(neighbor)

                if compute_depth:
                    # Store marker False: when reached, we are entering a vertex
                    to_leave_marker_append(False)


"$$ MStrategyWithoutWeights.standard_for_flex('TraversalNeighborsThenDepth') $$"
