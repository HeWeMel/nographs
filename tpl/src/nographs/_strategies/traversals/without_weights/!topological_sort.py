from __future__ import annotations

import array
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
    MutableSequenceOfVertices,
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


class TraversalTopologicalSortFlex(
    _TraversalWithoutWeightsWithVisited[T_vertex, T_vertex_id, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

    **Algorithm:** Topological Search, non-recursive implementation.
    Vertices are reported when they "are left" for backtracking.

    **Properties:** Vertices are reported in topological ordering, i.e. a
    linear ordering of the vertices such that for every directed edge *uv*
    from vertex *u* to vertex *v* ("*u* depends on *v*"), *v* comes before
    *u* in the ordering. If the graph contains a cycle that can be reached
    within the sorting process, a RuntimeError exception is raised and a
    cyclic path from a start vertex is provided.

    Vertices are expanded following the strategy
    `nographs.TraversalDepthFirst`.

    A vertex is considered visited from the moment its expansion begins.
    Start vertices are considered visited directly from the start of the
    traversal.

    # $$ insert_from('$$/cls_traversal/doc_input.rst')

    **Search state:** When a vertex is *expanded*
    (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        # $$ MStrategyWithoutWeights.init_signature('TraversalTopologicalSortFlex')
    ) -> None:
        "$$ MStrategyWithoutWeights.init_code() $$"
        self.cycle_from_start: list[T_vertex] = []  # value not used, see above
        """ If the graph contains a cycle that can be reached within the sorting
        process, a RuntimeError exception is raised, and the traversal provides
        a cyclic path from a start vertex in attribute cycle_from_start."""

    def start_from(
        self,
        # $$ insert_from('$$/method_start_from/signature.py')
    ) -> TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]:
        """
        # $$ insert_from('$$/method_start_from/doc_start.rst')
        # $$ insert_from('$$/method_start_from/doc_already_visited_compatible.txt')
        # $$ insert_from('$$/method_start_from/doc_end.rst')
        """

        "$$ insert_from('$$/method_start_from/code_start.py') $$"

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
        # Two separate implementations for the cases is_tree and not is_tree that follow
        # different concepts, because a combined approach makes both cases significantly
        # slower
        if self._is_tree:
            return self._traverse_in_tree()
        else:
            return self._traverse_in_non_tree()

    def _traverse_in_tree(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start.py') $$"

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"

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

            "$$ MCalculationLimit.step() $$"

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                "$$ MStrategy.vertex_to_id('neighbor', 'n_id')$$"

                if build_paths:
                    # We have to store the predecessor here, because at time of
                    # visit, it is already lost. And we cannot yield here,
                    # because only the first of the neighbors will indeed be
                    # visited next.
                    # But since we are in a tree, no other predecessor can
                    # be stored for that vertex later on.
                    """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                              'predecessors', 'attributes',
                              'vertex', 'n_id', 'edge_or_vertex[-1]')
                    $$"""

                # Put vertex on the stack
                to_expand_or_leave_append(neighbor)
                # Remember that we have to expand it
                to_leave_markers_append(False)

            self.depth += 1

    def _traverse_in_non_tree(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start.py') $$"
        visited = self.visited
        "$$ MVertexSet.access(name='visited') $$"

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"

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
        to_visit_pop = to_enter_or_leave.pop
        to_visit_append = to_enter_or_leave.append

        # Set of vertices along the current path
        # (We need this for fast cycle detection. We could use additionally
        # a trace sequence to speed up the check if the current vertex is
        # the top vertex of the trace instead of checking if it is "in" the
        # trace, but this would cost maintenance runtime and memory for the
        # sequence).
        trace_set = self._gear.vertex_id_set(())
        "$$ MVertexSet.access(name='trace_set', ops=['add', 'discard']) $$"

        "$$ MVertexSet.combine_access('visited', 'trace_set', 'set') $$"

        # ----- Inner loop -----

        while to_enter_or_leave:
            vertex = to_enter_or_leave[-1]  # visit/report last added vertex first
            "$$ MStrategy.vertex_to_id('vertex', 'v_id')$$"

            # If v_id is in trace_set:
            #   Back to trace, from visits/reports of further vertices,
            #   that trace vertices depend on: We "leave" and report the head
            #   vertex of the trace
            #   (A note about the above "in" check:
            #   If v_id is in the set, it needs to be
            #   the last id added there. But this does not help us, since
            #   sets are not ordered as dicts nowadays are).
            # Otherwise:
            #   Ignore v_id if visited, else include vertex n_id in visited set.
            #   Then, take it to the trace.
            """$$
                MVertexSet.compile_access('v_id', '', 'set', '''\
                $trace_set.if_contains_vertex_id_prepare_remove_and_elseadd:
                    self.depth -= 1
                    to_visit_pop()
                    $trace_set.prepared_remove_vertex_id
                    yield vertex
                    continue
                $traceset.endif
                if self.depth > 0:
                    $visited.if_contains_vertex_id_prepare_remove_and_elseadd:
                        to_visit_pop()
                        continue
                    $visited.else_prepared_add_endif
                $trace_set.add_vertex_id
                ''')
$$"""

            # We "expand" the vertex
            "$$ MCalculationLimit.step() $$"

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                "$$ MStrategy.vertex_to_id('neighbor', 'n_id2')$$"

                # If neighbor is already visited and in trace_set:
                #   We found a dependency (edge) back to a vertex, whose
                #   dependencies we are currently following (trace). We
                #   build and report this trace: a cycle.
                # If neighbor is already visited:
                #   ignore it (in case of path generation, this is necessary, and
                #   otherwise, it is a small optimization.)
                # Note: In order to become visited, a vertex needs to
                # get into the trace set and then be discarded
                # from it. Thus, in the inner if, we know that the neighbour
                # has already been in the trace set sometimes.
                """$$
                    MVertexSet.compile_access('n_id2', '', 'set', '''\
                    $visited.if_contains_vertex_id:
                        $trace_set.if_contains_vertex_id:
                            self._report_cycle(
                                neighbor,
                                to_enter_or_leave,
                                trace_set,
                                maybe_vertex_to_id,
                            )
                        $traceset.endif_with_vertex_included_in_past
                        continue
                    $traceset.endif
                    ''')
$$"""

                if build_paths:
                    # We have to store the predecessor here, because at time of
                    # visit, it is already lost. And we cannot yield here,
                    # because TopologicalSorted reports not until leaving vertices.
                    # But since the visiting order is defined by a stack we know
                    # that for each vertex, the predecessor stored last is the
                    # edge visited first, and after that no other predecessor can
                    # be stored for that vertex.
                    """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                              'predecessors', 'attributes',
                              'vertex', 'n_id2', 'edge_or_vertex[-1]')
                    $$"""

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
            "$$ MStrategy.vertex_to_id('vertex', 'v_id2')$$"
            if v_id2 in trace_set:
                trace.append(vertex)
        trace.append(neighbor)
        self.cycle_from_start = trace
        raise RuntimeError("Graph contains cycle")


"$$ MStrategyWithoutWeights.standard_for_flex('TraversalTopologicalSort') $$"
