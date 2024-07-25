from __future__ import annotations

import array
from typing import Optional, Any, Generic
from collections.abc import Iterable, Generator
from enum import Flag, auto

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
    access_to_vertex_mapping,
)
from ...type_aliases import (
    NextVertices,
    NextEdges,
    NextLabeledEdges,
)
from ...utils import (
    StrRepr,
)
from ..traversal import (
    Traversal,
    _start_from_needs_traversal_object,
)
from .traversal_without_weights import (
    _create_unified_next,
    _TraversalWithoutWeightsWithVisited,
)

"$$ import_from('$$/MTraversalWithoutWeights.py') $$"
"$$ import_from('$$/../../MVertexMapping.py') $$"


class DFSEvent(Flag):
    """
    An enumeration of the events that can trigger the report of a vertex / edge by
    TraversalDepthFirst.

    Events reporting that a vertex is entered or left:

    - ENTERING_START: A start vertex has been entered and the traversal starts
      there.

    - LEAVING_START: A start vertex has been left (the traversal may continue
      with the next one).

    - ENTERING_SUCCESSOR: A vertex is entered, when an edge
      that leads to it is followed. In mode *DFS_TREE*, only *DFS-tree edges*
      are followed.

    - LEAVING_SUCCESSOR: A vertex is left, when an edge that leads to it
      and has been followed, is now followed in reversed direction, during
      backtracking from the edge. In mode *DFS_TREE*, only *DFS-tree edges*
      are followed.

    Events reporting that a vertex (or an edge) has been detected but will not be
    entered (resp. followed):

    - SKIPPING_START: A start vertex was about to be entered, as start of a
      traversal from there, but it has already been visited as descendant of
      another start vertex, and thus, it is skipped.

    - BACK_EDGE: An edge *(u, v)* is found, where v has already been entered,
      but not left so far. In other words, *v* is on the trace (path that
      leads to *u* within the tree).

    - FORWARD_EDGE: An edge *(u, v)* is found, where *v* has already been
      left, and it had been entered after *u*. *(u, v)* is a shortcut
      forwards in the tree branch from *u* to *v*, so to speak.

    - CROSS_EDGE: An edge *(u, v)* is found, where *v* has already been left,
      and it had been entered before *u*. This means, in the DFS tree,
      *u* and *v* do not have any ancestor or descendant relationship
      between them.

    Events that combine other events as a group (*group-events*):

    - SOME_NON_TREE_EDGE: One of the events FORWARD_EDGE, BACK_EDGE, or CROSS_EDGE
      occurred, but it has not been determined which of these events.

    - FORWARD_OR_CROSS_EDGE: One of the events FORWARD_EDGE or CROSS_EDGE
      occurred, but it has not been determined which of these events.


    Aliases for sets of events:

    - NONE = 0

    - ENTERING = ENTERING_START | ENTERING_SUCCESSOR
    - LEAVING = LEAVING_START | LEAVING_SUCCESSOR

    - IN_OUT_START = ENTERING_START | LEAVING_START
    - IN_OUT_SUCCESSOR = ENTERING_SUCCESSOR | LEAVING_SUCCESSOR
    - IN_OUT = IN_OUT_START | IN_OUT_SUCCESSOR

    - NON_TREE_EDGES = FORWARD_EDGE | BACK_EDGE | CROSS_EDGE
    - EDGES = ENTERING_SUCCESSOR | NON_TREE_EDGES

    - ALL = IN_OUT | SKIPPING_START | NON_TREE_EDGES
    """

    ENTERING_START = auto()
    LEAVING_START = auto()

    ENTERING_SUCCESSOR = auto()
    LEAVING_SUCCESSOR = auto()

    SKIPPING_START = auto()
    BACK_EDGE = auto()
    FORWARD_EDGE = auto()
    CROSS_EDGE = auto()

    SOME_NON_TREE_EDGE = auto()
    FORWARD_OR_CROSS_EDGE = auto()

    NONE = 0

    ENTERING = ENTERING_START | ENTERING_SUCCESSOR
    LEAVING = LEAVING_START | LEAVING_SUCCESSOR

    IN_OUT_START = ENTERING_START | LEAVING_START
    IN_OUT_SUCCESSOR = ENTERING_SUCCESSOR | LEAVING_SUCCESSOR
    IN_OUT = IN_OUT_START | IN_OUT_SUCCESSOR

    NON_TREE_EDGES = FORWARD_EDGE | BACK_EDGE | CROSS_EDGE
    EDGES = ENTERING_SUCCESSOR | NON_TREE_EDGES

    ALL = IN_OUT | SKIPPING_START | NON_TREE_EDGES


class DFSMode(Flag):
    """
    An enumeration of the traversing mode to be used by TraversalDepthFirst.

    The modes are:

    - DFS_TREE: The traversal follows the edges of the DFS tree. If demanded,
      non-tree edges are reported, but not followed. Vertices are only
      visited once.

    - ALL_PATHS: A simple path is a path that does not contain a vertex twice.
      In this mode, the traversal follows all edges, also edges leading to
      vertices that have already been visited. But edges to vertices, that are
      already on the trace (current path from a start vertex to the current
      vertex) are ignored. For example, this can be used to search in the set
      of all possible simple paths from some edges to some others.

    - ALL_WALKS: A walk is a sequence of nodes in which each adjacent pair of
      nodes in the sequence is adjacent in the graph.
      A walk can contain the same vertex or edge more than once.
      In this more, the traversal follows all edges, also edges leading to
      vertices that have already been followed as part of the trace (the
      current walk from a start vertex to the current vertex).
    """

    DFS_TREE = auto()
    ALL_PATHS = auto()
    ALL_WALKS = auto()


class TraversalDepthFirstFlex(
    _TraversalWithoutWeightsWithVisited[T_vertex, T_vertex_id, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

    **Algorithm:** Depth First Search ("DFS"), non-recursive implementation.
    By default, a vertex is reported when its expansion starts (its
    successors are about to be read from the graph).

    **Properties**:
    Visits and expands unvisited vertices in depth first order, i.e.,
    the graphs is explored as far as possible along each branch before
    backtracking.
    Starts at some unvisited start vertex, and after an exhaustive traversal
    from there, continues with another start vertex that has not been visited
    so far.

    By default, it reports a vertex when it visits it.

    # $$ insert_from('$$/cls_traversal/doc_input.rst')

    **Search state:** When a vertex is *expanded*
    (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, *visited*, *event*, *trace*, *trace_labels*,
    *on_trace*, and *index*.
    """

    def __init__(
        self,
        # $$ MStrategyWithoutWeights.init_signature('TraversalDepthFirstFlex')
    ) -> None:
        "$$ MStrategyWithoutWeights.init_code(depth_computation_optional = True) $$"
        # The following values are not used. They are initialized during start_from.
        self._report = DFSEvent.NONE
        self._mode = DFSMode.DFS_TREE
        self._compute_depth = False
        self._compute_trace = False
        self._compute_on_trace = False
        self._compute_index = False

        self.event = DFSEvent.NONE
        """ Event that happened when a vertex is reported """
        self.trace = self._gear.sequence_of_vertices([])
        """ Sequence of the vertices on the current path from a start vertex to the
        current vertex. See option *compute_trace*.
        When a back edge, cross edge, or a forward edge is reported, the edge is
        temporarily appended to the trace to make it visible there,
        although such an edge is ignored otherwise (e.g., the traversal does not
        follow the edge, traversal.depth is not updated, and the vertex it leads
        to is not taken to *on_trace*)."""
        self.trace_labels = self._gear.sequence_of_edge_labels([])
        """ Sequence of the edge attributes of the edges on the current path
        (the first edge goes from a start vertex to a successor).
        See attribute *trace* and option *compute_trace*."""
        self.on_trace = self._gear.vertex_id_set([])
        """ Set of the vertices on the current path from a start vertex to the
        current vertex. See option *compute_on_trace*. When a cross edge or a forward
        edge is reported, the vertex it leads to will not be added to *on_trace*,
        unlike *trace* (see there). """
        self.index = self._gear.vertex_id_to_number_mapping([])
        """ Mapping that numbers vertices in pre-order, i.e., the vertex gets its
        number when it is entered. The vertices are numbered starting with *1*.
        See option *compute_index*.
        """

    def start_from(
        self,
        # $$ insert_from('$$/method_start_from/signature.py')
        report: DFSEvent = DFSEvent.ENTERING_SUCCESSOR,
        mode: DFSMode = DFSMode.DFS_TREE,
        compute_depth: bool = False,
        compute_trace: bool = False,
        compute_on_trace: bool = False,
        compute_index: bool = False,
    ) -> TraversalDepthFirstFlex[T_vertex, T_vertex_id, T_labels]:
        """
        # $$ insert_from('$$/method_start_from/doc_start.rst')
        # $$ insert_from('$$/method_start_from/doc_already_visited_std.txt')
        :param report: See `DFSEvent`.
          When one of the chosen events occurs, the vertex is reported.

          The group-events cannot be combined with the events contained in the
          group (see `DFSEvent`).

          If events other than ENTERING_SUCCESSOR and ENTERING_START
          are required, option *compute_trace* (see below) will automatically be
          used.

          If group-event FORWARD_OR_CROSS_EDGE is required, and the graph
          is no tree (is_tree == False), option *compute_on_trace* (see below)
          will automatically be set.

          If events from NON_TREE_EDGES are required, and the graph
          is no tree (is_tree == False), the options
          *compute_on_trace* and *compute_index* (see below)
          will automatically be set.

        :param mode:
          See `DFSMode`. The mode the search operates in.

          Mode ALL_PATHS cannot be combined with the reporting of events
          FORWARD_EDGE and CROSS_EDGE, and event-groups containing them,
          since these events are only defined for DFS-trees.
          In mode ALL_PATHS, option *compute_on_trace* (see below)
          will automatically be set.

          Mode ALL_WALKS cannot be
          combined with reporting non-tree edges, neither
          alone (events from NON_TREE_EDGES)
          nor in group-events
          (events SOME_NON_TREE_EDGE or FORWARD_OR_CROSS_EDGE),
          since forward and cross edges are only defined for DFS-trees,
          and back edges only for DFS-trees and for paths.
          The mode cannot be used for trees
          (parameter *is_tree* when creating the traversal),
          and `visited` is not computed.

        # $$ insert_from('$$/method_start_from/doc_compute_depth.txt')
        :param compute_index: If True, the attribute *index* is updated
          during the traversal, and option *compute_trace*
          (see below) will automatically be used. *compute_index* is not
          compatible with parameter *already_visited*.

        :param compute_on_trace: If True, attribute `on_trace` is updated
          during the traversal, and option *compute_trace* will automatically
          be set. The computation of set `on_trace` cannot be combined
          with mode ALL_WALKS.

        :param compute_trace: If True, attribute `trace` is updated during the
          traversal.
        # $$ insert_from('$$/method_start_from/doc_end.rst')

        .. versionchanged:: 3.4

           Start vertices are evaluated successively.
           Parameters *report*, *mode*, *compute_trace*, *compute_on_trace*,
           and *compute_index* added.
        """
        _start_from_needs_traversal_object(self)
        self._start_without_weights_with_visited(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
            empty_path_for_start_vertices=False,
            visited_for_start_vertices=False,
        )
        # Set the externally visible depth to the sensible initial value 0.
        # But if depth is not to be computed, use value -1 instead.
        self.depth = 0 if compute_depth else -1

        # Derive further options (and possible incompatibilities) from given options
        if DFSEvent.SOME_NON_TREE_EDGE in report and (DFSEvent.NON_TREE_EDGES & report):
            raise RuntimeError(
                "Reporting of non-tree edges as a group and as individual edge "
                "type cannot be combined."
            )
        if DFSEvent.FORWARD_OR_CROSS_EDGE in report and (
            (DFSEvent.FORWARD_EDGE | DFSEvent.CROSS_EDGE) & report
        ):
            raise RuntimeError(
                "Reporting of forward or cross edges as a group and as individual edge "
                "type cannot be combined."
            )
        if not self._is_tree:
            # In a tree, there cannot be non-tree edges. So, we do not need
            # bookkeeping to detect such edges.
            # If we are not in a tree, we need some special bookkeeping.
            if (
                report & (DFSEvent.NON_TREE_EDGES | DFSEvent.FORWARD_OR_CROSS_EDGE)
                or mode == DFSMode.ALL_PATHS
            ):
                # For reporting the concrete type of non-tree edges, or
                # FORWARD_OR_CROSS_EDGE, we need the *on_trace* set.
                # In case of back edges, we need it to detect them.
                # In case of forward and cross edges or the group of either a forward
                # or a cross edge, we need it to exclude the case of a back edge.
                compute_on_trace = True
            if report & (DFSEvent.FORWARD_EDGE | DFSEvent.CROSS_EDGE):
                # Here, we need a vertex index to distinguish between the
                # tho cases.
                compute_index = True
        if (
            report not in (DFSEvent.ENTERING_SUCCESSOR | DFSEvent.ENTERING_START)
            or compute_index
            or compute_on_trace
        ):
            # Only the algorithms that computes a trace can report other
            # events than entering of normal or start vertices and can compute
            # vertex indexes and the on_trace set
            compute_trace = True

        # Prevent illegal option combinations
        if report & (
            DFSEvent.NON_TREE_EDGES
            | DFSEvent.SOME_NON_TREE_EDGE
            | DFSEvent.FORWARD_OR_CROSS_EDGE
        ) and (self._is_tree or mode in DFSMode.ALL_WALKS):
            raise RuntimeError(
                "The events BACK_EDGE, FORWARD_EDGE, and CROSS_EDGE, "
                "and groups containing them, "
                "cannot be computed for trees and for traversals in mode "
                "*ALL_WALKS*."
            )
        if compute_on_trace and (self._is_tree or mode == DFSMode.ALL_WALKS):
            raise RuntimeError(
                "Computation of the on-trace is not allowed for trees and for "
                "traversals in mode *ALL_WALKS*."
            )
        if (
            report
            & (
                DFSEvent.FORWARD_EDGE
                | DFSEvent.CROSS_EDGE
                | DFSEvent.SOME_NON_TREE_EDGE
                | DFSEvent.FORWARD_OR_CROSS_EDGE
            )
            and mode == DFSMode.ALL_PATHS
        ):
            raise RuntimeError(
                "The events FORWARD_EDGE and CROSS_EDGE, "
                "and groups containing them, "
                "cannot be computed for traversals in mode *ALL_PATHS*."
            )
        if build_paths and mode == DFSMode.ALL_WALKS:
            raise RuntimeError(
                "Paths cannot be computed in mode *ALL_WALKS*, because "
                "walks can be cyclic."
            )
        if compute_index and already_visited is not None:
            raise RuntimeError(
                "Parameter *already_visited* not allowed when vertex indexes "
                "are demanded."
            )

        self._report = report
        self._mode = mode
        self._compute_depth = compute_depth
        self._compute_trace = compute_trace
        self._compute_on_trace = compute_on_trace
        self._compute_index = compute_index
        self.event = DFSEvent.NONE
        self.trace = self._gear.sequence_of_vertices([])
        self.on_trace = self._gear.vertex_id_set([])
        self.trace_labels = self._gear.sequence_of_edge_labels([])
        self.index = self._gear.vertex_id_to_number_mapping([])

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
        # We provide two different implementations: the first with many features,
        # and the second optimized for speed and memory for a typical configuration
        # of options.
        if self._compute_trace or self._mode != DFSMode.DFS_TREE:
            return self._traverse_with_trace()
        else:
            return self._traverse_without_trace()

    def _traverse_with_trace(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start_with_tree_and_visited.py') $$"

        # Copy Traversal-specific attributes into method scope (faster access)
        report = self._report
        mode = self._mode
        compute_depth = self._compute_depth
        compute_on_trace = self._compute_on_trace
        compute_index = self._compute_index
        trace = self.trace
        on_trace = self.on_trace
        trace_labels = self.trace_labels
        index = self.index

        # Create individual flags for events that are to be reported
        # (Avoids attribute resolution both for checking if an event has
        # to be reported and for the value that is then to report)
        event_entering = DFSEvent.ENTERING_SUCCESSOR
        event_entering_start = DFSEvent.ENTERING_START
        report_leaving = DFSEvent.LEAVING_SUCCESSOR & report
        report_leaving_start = DFSEvent.LEAVING_START & report
        report_skipping_start = DFSEvent.SKIPPING_START & report
        report_non_tree_edges = DFSEvent.NON_TREE_EDGES & report
        report_forward_edge = DFSEvent.FORWARD_EDGE & report
        report_back_edge = DFSEvent.BACK_EDGE & report
        report_cross_edge = DFSEvent.CROSS_EDGE & report
        report_some_non_tree_edge = DFSEvent.SOME_NON_TREE_EDGE & report
        report_forward_or_cross_edge = DFSEvent.FORWARD_OR_CROSS_EDGE & report
        report_none = DFSEvent.NONE
        # The same for the mode
        mode_dfs_tree = mode & DFSMode.DFS_TREE
        # mode_simple_paths = mode & DFSMode.ALL_PATHS
        mode_walks = mode & DFSMode.ALL_WALKS

        # ----- Initialize method specific bookkeeping -----

        if compute_depth:
            # Since a start vertex is the first that is put on the trace, we have to
            # start one lower
            self.depth -= 1

        # Vertices to enter or leave
        to_visit = self._gear.sequence_of_vertices([])
        to_visit_append = to_visit.append
        to_visit_pop = to_visit.pop
        # For non-start vertices in to_visit: edge attributes of edge to them
        to_visit_labels = self._gear.sequence_of_edge_labels([])
        to_visit_labels_append = to_visit_labels.append
        to_visit_labels_pop = to_visit_labels.pop
        # Sequence of flag bytes (store in a Q array) marking the vertices in
        # to_visit that we want to leave by 1 and the vertices to enter by 0.
        # Initially, store a zero flag for each start vertex.
        to_leave_markers = array.array("B")
        to_leave_markers_append = to_leave_markers.append

        # Get references of the methods of the gear objects this traversal uses
        # (avoid attribute resolution)
        trace_append = trace.append
        trace_pop = trace.pop
        on_trace_add = on_trace.add
        trace_labels_append = trace_labels.append
        trace_labels_pop = trace_labels.pop
        "$$ MVertexSet.access(name='on_trace', ops=['add', 'discard']) $$"
        "$$ MVertexSet.combine_access('visited', 'on_trace', 'set') $$"

        # Start times of vertices (the collection implicitly default to 0)
        "$$ MVertexMapping.access('index') $$"

        # We start the time at number 1, because vertices without time have time
        # 0, and we want to distinguish the two cases.
        time = 1

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"
        labels: T_labels

        for start_vertex in self._start_vertices:
            # A start vertex needs to be visited and entered, and it has an empty path
            to_visit_append(start_vertex)
            to_leave_markers_append(False)

            # ----- Inner loop -----

            while True:
                # Leave vertices in the trace (stack) that we already fully processed
                # (backtracking along edges) and find the vertex to enter next.
                # If there is none, we are finished with processing the current
                # start vertex.

                no_leaving_reported_so_far = True
                # (noinspection necessary due to bug PY-9479, also below...)
                # noinspection PyUnboundLocalVariable
                while to_leave_markers:
                    marker = to_leave_markers.pop()
                    if not marker:
                        # Not a leave marker, but an enter marker. Break loop
                        # of handling leave markers.
                        break
                    # We got marker "leave a vertex" and leave one vertex
                    vertex = trace[-1]
                    # Report leaving, if demanded, and update the trace
                    if to_leave_markers:
                        # We are leaving a vertex that is not the only one on the trace
                        # (Note: We cannot compare vertex != start_vertex here, because
                        # a start vertex can re-occur as target of a back edge, and
                        # then, the trace is not empty!)
                        if report_leaving:
                            if no_leaving_reported_so_far:
                                self.event = report_leaving
                                no_leaving_reported_so_far = False
                            yield vertex
                        if labeled_edges:
                            trace_labels_pop()
                    else:
                        # We are leaving the only vertex on the trace
                        if report_leaving_start:
                            self.event = report_leaving_start
                            yield vertex
                    # Pop vertex from trace
                    _ = trace_pop()
                    # Remove vertex from on_trace set
                    if compute_on_trace:
                        "$$ MStrategy.vertex_to_id('vertex', 'r_id') $$"
                        "$$ MVertexSet.remove('on_trace', 'r_id', 'set') $$"
                    # Update depth
                    if compute_depth:
                        self.depth -= 1
                else:
                    # Last marker has been read. We are done with the start_vertex and
                    # all its successors. Break loop of handling markers and vertices
                    # to visit.
                    break

                # Enter marker found. Follow an edge in its forward direction.
                # The last added vertex is the first to (possibly) enter (depth-first)
                # print(">>", to_visit, to_visit_labels)
                vertex = to_visit_pop()
                if labeled_edges and to_visit:
                    # Further vertices to visit means vertex is here not in role of
                    # a start vertex. Thus, we followed an edge. Thus, if edges
                    # are labeled, we have a label. And get it.
                    # (Note: We cannot compare vertex != start_vertex here, because
                    # a start vertex can re-occur as target of a back edge, and
                    # then, we need to get the labels!)
                    labels = to_visit_labels_pop()
                    # print(">>>", vertex, labels)
                "$$ MStrategy.vertex_to_id('vertex', 'v_id') $$"

                # If the graph is no tree: We might come to a vertex that we have
                # already visited and need to check and handle this; and we have to
                # update the visited set.
                # In mode ALL_WALKS, we ignore all this
                if not is_tree and mode != mode_walks:

                    event = report_none

                    # Find out if vertex has already been visited and entering
                    # it again is forbidden.
                    # In mode DFS_TREE, "visited" means here that the vertex is in
                    # set visited (because it has already been visited as descendant
                    # of another vertex, or because it is given as start vertex twice),
                    # and in mode ALL_PATHS that it already is on_trace.
                    re_visit = False
                    if mode == mode_dfs_tree:
                        """$$
                            MVertexSet.compile_access('v_id', '', 'set', '''\
                            $visited.if_contains_vertex_id_prepare_remove_and_elseadd:
                                re_visit = True
                            $visited.else_prepared_add_endif
''')$$"""
                        if re_visit and not trace:
                            # We try to enter a start vertex when the trace is
                            # empty, but is has already been visited (can only
                            # happen in mode DFS_TREE.)
                            if report_skipping_start:
                                self.event = report_skipping_start
                                trace_append(vertex)
                                yield vertex
                                trace_pop()
                            continue

                    else:  # mode ALL_PATHS, since ALL_WALKS has been excluded above
                        """$$
                            MVertexSet.compile_access('v_id', '', 'set', '''\
                            $on_trace.if_contains_vertex_id_prepare_remove_and_elseadd:
                                re_visit = True
                                event = report_back_edge
                            $on_trace.else_prepared_add_endif
''')$$"""
                    if re_visit:
                        # Report re-visit of non-start vertex, and ignore the
                        # vertex (continue).

                        if report_some_non_tree_edge:
                            # We need to report all kinds of non-tree edges as a group
                            event = report_some_non_tree_edge

                        elif (
                            report_non_tree_edges
                            | report_forward_or_cross_edge
                            | report_back_edge
                            | report_forward_edge
                            | report_cross_edge
                        ):
                            # We need to report a more concrete type that just
                            # some_non_tree_edge

                            # Detect back edge, if not already done
                            if report_back_edge and event != report_back_edge:
                                """$$
                                    # Needs to be done when index of previous access to
                                    # v_id is still valid.
                                    # We know, that v_id has already been in on_trace,
                                    # because it has already been visited, but we do
                                    # now know, if it is currently contained in the set.
                                    # Thus, we use the respective version of endif.
                                    MVertexSet.compile_access('v_id', '', 'set', '''\
                                    $on_trace.if_contains_vertex_id:
                                        event = report_back_edge
                                    $on_trace.endif_with_vertex_included_in_past
''', already_indexed=True)$$"""

                            # If we have no back edge, distinguish between forward and
                            # cross edge
                            if event == report_none and (
                                report_forward_edge | report_cross_edge != report_none
                            ):
                                parent = trace[-1]
                                "$$ MStrategy.vertex_to_id('parent', 'p_id') $$"
                                vertex_index = """$$
                                    MVertexMapping.get_included('index', 'v_id') $$"""
                                parent_index = """$$
                                    MVertexMapping.get_included('index', 'p_id') $$"""
                                event = (
                                    report_forward_edge
                                    if parent_index < vertex_index
                                    else report_cross_edge
                                )
                        else:
                            continue

                        if event and event in report:
                            # Report the edge. Append it temporarily to the end of
                            # the trace and remove it again.
                            self.event = event
                            trace_append(vertex)
                            if labeled_edges:
                                trace_labels_append(labels)
                            yield vertex
                            trace_pop()
                            if labeled_edges:
                                trace_labels_pop()

                        continue

                    # The vertex has not been visited before, and we are still
                    # in case "not is_tree and mode != mode_walks"

                    if compute_on_trace:
                        # Add to trace set, if not already done
                        """$$
                            # This macro call needs to be used directly after the one that
                            # accessed *visited* in order to re-use the correct index.
                            # And only if this other macro call has not been skipped
                            # because is_tree.
                            MVertexSet.compile_access('v_id', '', 'set', '''\
                            $on_trace.add_vertex_id
''', already_indexed = True)$$"""

                # It is allowed to visit the vertex, so we visit it now.
                # (The trace has already been maintained, if necessary.)

                if compute_index:
                    "$$ MVertexMapping.set('index', 'v_id', 'time') $$"
                    time += 1

                if build_paths:
                    if trace:
                        # We are not visiting a start vertex. Store edge to it.
                        """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                                  'predecessors', 'attributes',
                                  'trace[-1]', 'v_id', 'labels')
                        $$"""
                    else:
                        # We are visiting a start vertex. Store empty path for it.
                        "$$ MStrategy.vertex_to_id('start_vertex', 'vs_id')$$"
                        """$$ MVertexMappingExpectNone.store_vertex_if_empty(
                                  'predecessors', 'start_vertex', 'vs_id') $$"""

                # Store the marker True: When it is reached later on, we will know
                # that we have to leave the vertex again.
                # noinspection PyUnboundLocalVariable
                to_leave_markers_append(True)

                if compute_depth:
                    self.depth += 1

                # self.event = event = event_entering if trace else event_entering_start
                self.event = event = (
                    event_entering_start if vertex == start_vertex else event_entering
                )

                if labeled_edges and trace:
                    trace_labels_append(labels)
                trace_append(vertex)

                # Report that we enter a vertex (all state attributes have to be
                # updated before)
                if report & event:
                    try:
                        yield vertex
                    except StopIteration:
                        # We confirm the skip signal and skip the expansion
                        yield vertex
                        continue

                "$$ MCalculationLimit.step() $$"

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    # Needs to be visited, in stack order
                    to_visit_append(neighbor)
                    if labeled_edges:
                        # Proof for correctness of the type hole:
                        # self._labeled_edges -> next_edges (a NextWeightedEdges) is
                        # a NextWeightedLabeledEdges -> {edge_data_expr} is a T_labels
                        labels = edge_or_vertex[-1]  # type: ignore[assignment]
                        to_visit_labels_append(labels)

                    # Store marker False: when it is reached later on, we know
                    # that we have to enter the vertex now
                    to_leave_markers_append(False)

    def _traverse_without_trace(self) -> Generator[T_vertex, None, Any]:
        """This implementation does not maintain the trace.
        If a vertex is visited, there is no parent information, and if
        a vertex is left, the vertex is now known.
        Thus, it can only report ENTERING_SUCCESSOR and ENTERING_START,
        cannot maintain the on-trace set, and cannot run in mode
        ALL_PATHS.
        Additionally, it does not offer vertex indices and mode ALL_WALKS,
        but this could probably be added if necessary."""

        "$$ insert_from('$$/method_traverse/code_start_with_tree_and_visited.py') $$"
        visited = self.visited
        "$$ MVertexSet.access(name='visited') $$"

        # Copy Traversal-specific attributes into method scope (faster access)
        compute_depth = self._compute_depth
        report = self._report

        # Copy Traversal-specific constants into method scope (faster access)
        event_entering = DFSEvent.ENTERING_SUCCESSOR
        event_entering_start = DFSEvent.ENTERING_START

        # ----- Initialize method specific bookkeeping -----

        depth = -1  # The inner loop starts with incrementing, so, we pre-decrement
        if not compute_depth:
            self.depth = depth  # In this case, we leave the -1 the whole time

        # vertices to enter or leave
        to_visit = self._gear.sequence_of_vertices([])
        to_visit_append = to_visit.append
        to_visit_pop = to_visit.pop

        if compute_depth:
            # Sequence of flag bytes (store in a Q array) marking the vertices
            # to leave by 1 and the vertices to enter by 0.
            to_leave_markers = array.array("B")
            to_leave_markers_pop = to_leave_markers.pop
            to_leave_markers_append = to_leave_markers.append

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"

        for start_vertex in self._start_vertices:
            to_visit_append(start_vertex)
            if compute_depth:
                to_leave_markers_append(False)
            if build_paths:
                # If the start vertex is not already visited, store empty path
                # for it
                "$$ MStrategy.vertex_to_id('start_vertex', 'sv_id')$$"
                """$$ MVertexMappingExpectNone.store_vertex_if_empty(
                          'predecessors', 'start_vertex', 'sv_id') $$"""

            # ----- Inner loop -----
            while True:
                if compute_depth:
                    # Update depth w.r.t. all vertices we are leaving before afterwards,
                    # we enter the next one.
                    # This also done for the start vertex, before exiting the
                    # inner loop, in order to reset the sequence to_leave_markers
                    # (Instead of this, we could use "del s[:]" above, but this
                    # requires the MutableSequence to support slice objects as key for
                    # __delitem__ - what is often given, but not guaranteed)
                    # (noinspection necessary due to bug PY-9479, also below...)
                    # noinspection PyUnboundLocalVariable
                    while to_leave_markers and to_leave_markers_pop():
                        # We decrement the depth for each vertex we are "leaving".
                        depth -= 1

                if not to_visit:
                    # No vertices to visit are left: The start vertex and its
                    # descendants are processed. We can leave the loop.
                    break

                # Next vertex to enter (except it is already visited)
                vertex = to_visit_pop()
                if not is_tree:
                    # Ignore vertex if already visited, and
                    # else include its ID in visited set.
                    "$$ MStrategy.vertex_to_id('vertex', 'v_id')$$"
                    """$$ MVertexSet.if_visited_continue_else_add(
                              'visited', 'v_id', '') $$"""

                # We will now enter the vertex
                if compute_depth:
                    depth += 1
                    self.depth = depth
                    # Store marker True: when reached, we are leaving a vertex
                    # noinspection PyUnboundLocalVariable
                    to_leave_markers_append(True)

                if vertex == start_vertex:
                    # In this variant (!) of DFS, below, only neighbors that are
                    # not visited so far are taken to to_visited. Since start_vertex
                    # is visited immediately in its role as start vertex, this means,
                    # it cannot occur again in the role of a neighbor. So, here, we
                    # know, that we are in the case event_entering_start.
                    # Set event, both for a possible report here and for
                    # expanding the vertex
                    self.event = event_entering_start
                    if report & event_entering_start:
                        try:
                            yield vertex
                        except StopIteration:
                            # We confirm the skip signal and skip the expansion.
                            # Since this also skips resetting the event type,
                            # we need to do it here before continuing.
                            yield vertex
                            self.event = event_entering
                            continue

                else:
                    if report & event_entering:
                        # The event has already been reset to report_entering
                        # (see below)
                        try:
                            yield vertex
                        except StopIteration:
                            # We confirm the skip signal and skip the expansion.
                            yield vertex
                            continue

                "$$ MCalculationLimit.step() $$"

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    if not is_tree or build_paths:
                        "$$ MStrategy.vertex_to_id('neighbor', 'n_id') $$"

                        # Ignore neighbor if already visited/expanded, i.e., not put
                        # it onto the stack to_visit.
                        # If we do not build paths, this is just a variant of the
                        # algorithms: The results do not change, since visited
                        # vertices will not be visited again.
                        # But in case that we create paths, it is necessary: We like
                        # to store the predecessor of the neighbor directly here,
                        # when we first see the neighbor and have the predecessor
                        # still present. And we need to make sure not to overwrite
                        # the real predecessor of a vertex that has been already
                        # expanded. If the neighbor has not been visited, it is
                        # safe (and necessary) to overwrite a pre-existing
                        # predecessor of neighbor because a later found edge
                        # (predecessor, neighbor) will be evaluated first (to_visit
                        # is a stack) and so, this predecessor need to "win".
                        # (If-nesting optimized for first case)
                        """$$ MVertexSet.if_visited_continue(
                                  'visited', 'n_id', '')
                        $$"""

                        if build_paths:
                            """$$
                            MVertexMappingExpectNone.store_vertex_and_edge_data(
                                'predecessors', 'attributes',
                                    'vertex', 'n_id', 'edge_or_vertex[-1]')
                            $$"""

                    # Needs to be visited, in stack order
                    to_visit_append(neighbor)

                    if compute_depth:
                        # Store marker False: when reached, we are entering a vertex
                        to_leave_markers_append(False)

                if vertex == start_vertex:
                    # We directly reset the event to report_entering after having
                    # processed the start vertex, because this is less expensive
                    # than doing it every time re report a non-start vertex.
                    # And we do it only if necessary, because the *if* is less
                    # expensive than the attribute access.
                    self.event = event_entering

        # After the traversal, set depth to something that the user can understand,
        # here: -1 is the value given if no depth computation is demanded, -1 is the
        # initial value before the first vertex has been entered, and -1
        # is the depth after having backtracked from a start vertex (that is at
        # depth 0). The documentation does not specify a value here.
        self.depth = -1

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:

        # For events: replace repr() text by str() text, because state as optimized
        # for readability
        if state["event"]:
            state["event"] = str(state["event"])

        # If ony of these attributes is not computed, do not show it as part of the
        # state
        for attribute in ["event", "trace", "on_trace", "trace_labels"]:
            if not state[attribute]:
                del state[attribute]

        # Assignments in times are only valid for reported vertices. Thus,
        # we need to convert only keys/values for requested vertices to a string,
        # not the whole MutableMapping. So, we special case this attribute here.
        vertex_to_id = self._vertex_to_id
        for times_key, times_collection in [
            ("index", self.index),
        ]:
            del state[times_key]
            # List content for the given vertices, but leave out key without values
            # or default value 0.
            # (Explicitly check "v_id in collection", because simply accessing
            # always returns (and for defaultdict: also set) the default value)
            if vertices is not None:
                # content = [
                #     (v_id, timestamp)
                #     for vertex in vertices
                #     if (timestamp := times_collection[v_id := vertex_to_id(vertex)])
                # ]
                content = [
                    (v_id, time)
                    for vertex in vertices
                    if (v_id := vertex_to_id(vertex)) in times_collection
                    and (time := times_collection[v_id]) != 0
                ]
                if content:
                    state[times_key] = StrRepr.from_iterable(content)

        super()._improve_state(state, vertices)

    def __iter__(
        self,
    ) -> Generator[
        T_vertex, None, None
    ]:  # Type alias needed due to a sphinx limitation
        """
        Like `nographs.Traversal.__iter__`, but return a generator
        instead of an interator.

        If *StopIteration()* is thrown into the generator:

        - When a vertex has been entered (events
          *DFSEvent.ENTERING_START* or *DFSEvent.ENTERING_SUCCESSOR* is reported),
          do not expand the vertex and reported it again as a confirmation.
        - In any other situation, raise a *RuntimeError* (according to *PEP 497*,
          see https://peps.python.org/pep-0479).

        .. versionchanged:: 3.4

           Now returns a generator instead of just an iterator, and
           a thrown *StopIteration* is handled, see above.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go can only be called on a Traversal object.")
        return self._generator

    def skip_expanding_entered_vertex(self) -> None:
        """If called when a vertex has been entered (events
        *DFSEvent.ENTERING_START* or *DFSEvent.ENTERING_SUCCESSOR*),
        skip the expansion of this vertex.

        If called when another event happened, raise a *RuntimeError*.

        (The method simply throws a *StopIteration* at *traversal.__iter__()*.)

        .. versionchanged:: 3.4

           Method added.
        """
        self._generator.throw(StopIteration())


"$$ MStrategyWithoutWeights.standard_for_flex('TraversalDepthFirst') $$"
