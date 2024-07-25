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


class TraversalTopologicalSortFlex(
    _TraversalWithoutWeightsWithVisited[T_vertex, T_vertex_id, T_labels]
):
    """
    Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: See `NextVertices` function. If None, provide next_edges
     or next_labeled_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertices equals
     None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
     next_vertices and next_edges equal None. If given, paths will record the given
     labels.

    :param is_tree: bool: If it is certain, that during each traversal run,
     each vertex can be reached only once, is_tree can be set to True. This
     improves performance, but attribute *visited* of the traversal will not be
     updated during and after the traversal.

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

    **Input:** Directed graph. Unlabeled or labeled edges. One or more start
    vertices. Optional calculation limit.

    **Search state:** When a vertex is *expanded*
    (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        (
            self._next_edge_or_vertex,
            edges_with_data,
            labeled_edges,
        ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        self.depth: int = -1  # value not used, initialized during traversal
        """
        At this *search depth*, the reported (resp. the expanded) vertex has been
        found. It equals the length (number of edges) of the created path to the
        vertex, if path creation is demanded.
        Note: The search depth does not need to be the depth of the vertex
        (see `TraversalBreadthFirstFlex`).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self.cycle_from_start: list[T_vertex] = []  # value not used, see above
        """ If the graph contains a cycle that can be reached within the sorting
        process, a RuntimeError exception is raised, and the traversal provides
        a cyclic path from a start vertex in attribute cycle_from_start."""

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
    ) -> TraversalTopologicalSortFlex[T_vertex, T_vertex_id, T_labels]:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The vertices the search should start at. Only
            allowed if start_vertex equals None.

        :param build_paths: If true, build paths from some start vertex to each visited
            vertex. Paths of start vertices are empty paths.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param already_visited: If provided, this set is used instead of an internal
            one to keep vertices (resp. their hashable ids from vertex_to_id),
            that have already been visited. This parameter can be used to get online
            access to the internal bookkeeping of visited vertices, or to preload
            vertices that should never be visited.

            Attention: TraversalTopologicalSortFlex requires, that the collection
            given as argument for parameter already_visited is compatible
            (in any sense) with the collection that gear.vertex_id_set()
            returns. If you have chosen GearDefault, you can just use a dict.
            Otherwise, create the collection by calling gear.vertex_id_set() or use the
            collection that another traversal with the same gear gives as attribute
            visited.

        :return: Traversal, that has been started, e.g., statements like *iter()*,
            *next()*, *for* and the methods "go*" of the Traversal can now be used.
        """

        _start_from_needs_traversal_object(self)
        self._start_without_weights_with_visited(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            already_visited,
        )
        self.depth = 0

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

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Copy _TraversalWithoutWeightsWithVisited attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex

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

        # ----- Typing preparation of inner loop -----

        # The following type Any opens no space for typing problems, since
        # the content of next_edge_or_vertex is type checked and iterates
        # objects of type T_vertex for edges_with_data==False and otherwise of
        # one of the following:
        #   WeightedUnlabeledOutEdge[T_vertex, Any],
        #   UnweightedLabeledOutEdge[T_vertex, T_labels],
        #   WeightedLabeledOutEdge[T_vertex, Any, T_labels],
        # And if labeled_edges==True, the first case is excluded.
        # (Any alternative code version of the inner loop without
        #  Any or 'type: ignore' is slower)
        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        data_of_edge: T_labels  # Re-establish type "after" the "hole"

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

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                n_id: T_vertex_id = (
                    maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else neighbor
                )

                if build_paths:
                    # We have to store the predecessor here, because at time of
                    # visit, it is already lost. And we cannot yield here,
                    # because only the first of the neighbors will indeed be
                    # visited next.
                    # But since we are in a tree, no other predecessor can
                    # be stored for that vertex later on.
                    # Store the predecessor (vertex) of the neighbor
                    try:
                        predecessors_sequence[n_id] = vertex
                    except IndexError:
                        predecessors_wrapper.extend_and_set(n_id, vertex)
                    # Store the labels of the edge to the neighbor
                    if labeled_edges:
                        data_of_edge = edge_or_vertex[-1]
                        try:
                            attributes_sequence[n_id] = data_of_edge
                        except IndexError:
                            attributes_wrapper.extend_and_set(n_id, data_of_edge)

                # Put vertex on the stack
                to_expand_or_leave_append(neighbor)
                # Remember that we have to expand it
                to_leave_markers_append(False)

            self.depth += 1

    def _traverse_in_non_tree(self) -> Generator[T_vertex, None, Any]:
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

        # Prepare limit check done by zero check
        if calculation_limit is not None:
            calculation_limit += 1

        # Copy _TraversalWithoutWeightsWithVisited attributes into method scope
        edges_with_data = self._edges_with_data
        next_edge_or_vertex = self._next_edge_or_vertex

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
        visited = self.visited
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            visited_index_and_bit_method,
        ) = access_to_vertex_set(visited)

        # ----- Typing preparation of inner loop -----

        # The following type Any opens no space for typing problems, since
        # the content of next_edge_or_vertex is type checked and iterates
        # objects of type T_vertex for edges_with_data==False and otherwise of
        # one of the following:
        #   WeightedUnlabeledOutEdge[T_vertex, Any],
        #   UnweightedLabeledOutEdge[T_vertex, T_labels],
        #   WeightedLabeledOutEdge[T_vertex, Any, T_labels],
        # And if labeled_edges==True, the first case is excluded.
        # (Any alternative code version of the inner loop without
        #  Any or 'type: ignore' is slower)
        edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
        neighbor: T_vertex  # Re-establish type "after" the "hole"
        data_of_edge: T_labels  # Re-establish type "after" the "hole"

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
        trace_set_add = trace_set.add
        trace_set_discard = trace_set.discard
        (
            trace_set_uses_sequence,
            trace_set_sequence,
            trace_set_wrapper,
            trace_set_uses_bits,
            trace_set_index_and_bit_method,
        ) = access_to_vertex_set(trace_set)

        # Check compatibility of visited and trace_set. It is used for
        # performance optimization later on.
        assert (
            visited_uses_sequence == trace_set_uses_sequence
            and visited_uses_bits == trace_set_uses_bits
        ), ("Collection visited is incompatible " + "with collection trace_set")
        set_uses_sequence = visited_uses_sequence
        del visited_uses_sequence, trace_set_uses_sequence
        set_uses_bits = visited_uses_bits
        del visited_uses_bits, trace_set_uses_bits
        if set_uses_sequence and set_uses_bits:
            assert visited_index_and_bit_method is trace_set_index_and_bit_method, (
                "Collection visited is incompatible " + "with collection trace_set"
            )
        set_index_and_bit_method = visited_index_and_bit_method
        del visited_index_and_bit_method, trace_set_index_and_bit_method

        # ----- Inner loop -----

        while to_enter_or_leave:
            vertex = to_enter_or_leave[-1]  # visit/report last added vertex first
            v_id: T_vertex_id = (
                maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else vertex
            )

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
            if not set_uses_sequence:
                # Standard implementation for "normal" MutableSet
                if v_id in trace_set:
                    self.depth -= 1
                    to_visit_pop()
                    trace_set_discard(v_id)
                    yield vertex
                    continue
                if self.depth > 0:
                    if v_id in visited:
                        to_visit_pop()
                        continue
                    else:
                        visited_add(v_id)
                trace_set_add(v_id)

            elif not set_uses_bits:
                # Same as above, but with booleans in byte sequence
                try:
                    if trace_set_sequence[v_id]:
                        self.depth -= 1
                        to_visit_pop()
                        trace_set_sequence[v_id] = False
                        yield vertex
                        continue
                except IndexError:
                    pass
                if self.depth > 0:
                    try:
                        if visited_sequence[v_id]:
                            to_visit_pop()
                            continue
                        else:
                            visited_sequence[v_id] = True
                    except IndexError:
                        visited_wrapper.extend_and_set(v_id, True)
                try:
                    trace_set_sequence[v_id] = True
                except IndexError:
                    trace_set_wrapper.extend_and_set(v_id, True)

            else:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = set_index_and_bit_method(v_id, 8)
                bit_mask = 1 << bit_number
                try:
                    value = trace_set_sequence[sequence_key]
                    if value & bit_mask:
                        self.depth -= 1
                        to_visit_pop()
                        trace_set_sequence[sequence_key] = value - bit_mask
                        yield vertex
                        continue
                except IndexError:
                    pass
                if self.depth > 0:
                    try:
                        value = visited_sequence[sequence_key]
                        if value & bit_mask:
                            to_visit_pop()
                            continue
                        else:
                            visited_sequence[sequence_key] = value | bit_mask
                    except IndexError:
                        visited_wrapper.extend_and_set(sequence_key, bit_mask)
                try:
                    trace_set_sequence[sequence_key] |= bit_mask
                except IndexError:
                    trace_set_wrapper.extend_and_set(sequence_key, bit_mask)

            # We "expand" the vertex
            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                n_id2: T_vertex_id = (
                    maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else neighbor
                )

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
                if not set_uses_sequence:
                    # Standard implementation for "normal" MutableSet
                    if n_id2 in visited:
                        if n_id2 in trace_set:
                            self._report_cycle(
                                neighbor,
                                to_enter_or_leave,
                                trace_set,
                                maybe_vertex_to_id,
                            )
                        continue

                elif not set_uses_bits:
                    # Same as above, but with booleans in byte sequence
                    try:
                        if visited_sequence[n_id2]:
                            try:
                                if trace_set_sequence[n_id2]:
                                    self._report_cycle(
                                        neighbor,
                                        to_enter_or_leave,
                                        trace_set,
                                        maybe_vertex_to_id,
                                    )
                            except IndexError:  # pragma: no cover
                                raise AssertionError(
                                    "Internal error: IndexError " "should never happen"
                                )
                            continue
                    except IndexError:
                        pass

                else:
                    # Same as above, but with bits in byte sequence
                    sequence_key, bit_number = set_index_and_bit_method(n_id2, 8)
                    bit_mask = 1 << bit_number
                    try:
                        if visited_sequence[sequence_key] & bit_mask:
                            try:
                                if trace_set_sequence[sequence_key] & bit_mask:
                                    self._report_cycle(
                                        neighbor,
                                        to_enter_or_leave,
                                        trace_set,
                                        maybe_vertex_to_id,
                                    )
                            except IndexError:  # pragma: no cover
                                raise AssertionError(
                                    "Internal error: IndexError " "should never happen"
                                )
                            continue
                    except IndexError:
                        pass

                if build_paths:
                    # We have to store the predecessor here, because at time of
                    # visit, it is already lost. And we cannot yield here,
                    # because TopologicalSorted reports not until leaving vertices.
                    # But since the visiting order is defined by a stack we know
                    # that for each vertex, the predecessor stored last is the
                    # edge visited first, and after that no other predecessor can
                    # be stored for that vertex.
                    # Store the predecessor (vertex) of the neighbor
                    try:
                        predecessors_sequence[n_id2] = vertex
                    except IndexError:
                        predecessors_wrapper.extend_and_set(n_id2, vertex)
                    # Store the labels of the edge to the neighbor
                    if labeled_edges:
                        data_of_edge = edge_or_vertex[-1]
                        try:
                            attributes_sequence[n_id2] = data_of_edge
                        except IndexError:
                            attributes_wrapper.extend_and_set(n_id2, data_of_edge)

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
            v_id2: T_vertex_id = (
                maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                if maybe_vertex_to_id
                else vertex
            )
            if v_id2 in trace_set:
                trace.append(vertex)
        trace.append(neighbor)
        self.cycle_from_start = trace
        raise RuntimeError("Graph contains cycle")


class TraversalTopologicalSort(
    Generic[T_vertex, T_labels],
    TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels],
):
    """
    Eases the use of `TraversalTopologicalSortFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    Uses the following standard arguments for the respective parameters of
    the parent class:

    - vertex_to_id = `vertex_as_id`
    - gear = `GearDefault`
    - `T_vertex_id` = `T_vertex`

    Implications:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            NextVertices[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalTopologicalSortFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ]
        ] = None,
        is_tree: bool = False,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
            is_tree=is_tree,
        )
