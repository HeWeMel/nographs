from __future__ import annotations

import copy
from typing import Optional, Any, Generic
from collections.abc import Iterable, Iterator, Generator


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
    Traversal,
    _start_from_needs_traversal_object,
)
from .traversal_without_weights import (
    _create_unified_next,
    _TraversalWithoutWeightsWithVisited,
)


class TraversalBreadthFirstFlex(
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

    **Algorithm:** Breadth First Search ("BFS"), non-recursive implementation.
    Vertices are reported when they are "seen" (read from the graph) for the
    first time.

    **Properties:**
    Reports vertices in Breadth First order, i.e.,
    with ascending depth (edge count of the path with the fewest edges from a
    start vertex). All computed paths are *shortest paths* , i.e., paths with
    minimal number of edges from a start vertex to their end vertex.

    A vertex is considered visited when it has been reported or if it is a
    start vertex.

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
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels],
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

        For the special case of this traversal, it equals the
        *depth of the vertex* (minimal number of edges needed to come to it
        from a start vertex).
        When a traversal has been started, but no vertex has been reported or expanded
        so far, the depth is 0 (depth of the start vertices).
        """
        self._report_depth_increase = False

    def start_from(
        self,
        start_vertex: Optional[T_vertex] = None,
        *,
        start_vertices: Optional[Iterable[T_vertex]] = None,
        build_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[VertexIdSet[T_vertex_id]] = None,
        _report_depth_increase: bool = False,  # hidden parameter for internal use
    ) -> TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]:
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
            vertices that should never be visited, or to provide your own way for
            storing the information that a vertex has already been visited.

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
        self._report_depth_increase = _report_depth_increase

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

        # Copy further traversal attributes into method scope (faster access)
        is_tree = self._is_tree
        visited = self.visited

        # Get further references of used gear objects and methods
        # (avoid attribute resolution)
        visited_add = visited.add
        (
            visited_uses_sequence,
            visited_sequence,
            visited_wrapper,
            visited_uses_bits,
            visited_index_and_bit_method,
        ) = access_to_vertex_set(visited)

        # Copy Traversal-specific attributes into method scope (faster access)
        report_depth_increase = self._report_depth_increase

        # ----- Initialize method specific bookkeeping -----

        # Two lists used as FIFO queue with just two buckets
        # (using a queue and counting down the size of current depth horizon is slower,
        # and creating a new list instead of clear() is also slower)
        to_expand = self._gear.sequence_of_vertices(self._start_vertices)
        next_to_expand = self._gear.sequence_of_vertices(())

        # During an ongoing expansion of some vertex we will already report the
        # new found neighbors. For the former, the depth needs to remain the old
        # one, while for the latter, it needs to be one higher. In order to avoid
        # a cascade of +1 and -1 on the depth, we just use a copy of the traversal,
        # that hangs by one in the depth, and give this to next_edge_or_vertices.
        prev_traversal = copy.copy(self)  # copy of self, for keeping previous depth
        self.depth = 1  # used for reporting (prev_traversal starts at 0)

        # Get method references of specific bookkeeping (avoid attribute resolution)
        to_expand_append = to_expand.append
        next_to_expand_append = next_to_expand.append

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

        # ----- Inner loop -----

        while to_expand:
            for vertex in to_expand:
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    if not is_tree or build_paths:
                        n_id: T_vertex_id = (
                            maybe_vertex_to_id(neighbor)  # type: ignore[assignment]
                            if maybe_vertex_to_id
                            else neighbor
                        )

                        # If not is_tree: Ignore neighbor if already seen, and
                        # else include its ID in visited set.
                        # (If-nesting optimized for first case)
                        if not is_tree and not visited_uses_sequence:
                            # Standard implementation for "normal" MutableMapping
                            if n_id in visited:
                                continue
                            visited_add(n_id)
                        elif not is_tree and visited_uses_bits:
                            # Same as above, but with bits in byte sequence
                            sequence_key, bit_number = visited_index_and_bit_method(
                                n_id, 8
                            )
                            bit_mask = 1 << bit_number
                            try:
                                value = visited_sequence[sequence_key]
                                if value & bit_mask:
                                    continue
                                visited_sequence[sequence_key] = value | bit_mask
                            except IndexError:
                                visited_wrapper.extend_and_set(sequence_key, bit_mask)
                        elif not is_tree:
                            # Same as above, but with booleans in byte sequence
                            try:
                                if visited_sequence[n_id]:
                                    continue
                                visited_sequence[n_id] = True
                            except IndexError:
                                visited_wrapper.extend_and_set(n_id, True)

                        if build_paths:
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
                                    attributes_wrapper.extend_and_set(
                                        n_id, data_of_edge
                                    )

                    # Vertex has been seen, report it now
                    yield neighbor
                    # Needs to be expanded in the next round
                    next_to_expand_append(neighbor)

            if report_depth_increase and next_to_expand:
                # We are not finished yet, because we found new vertices to expand,
                # and we are about to increase the depth now, and it is demanded
                # to report this situation by reporting the last vertex reported so far
                # again. So we report it again.
                yield next_to_expand[-1]

            # Update external views (reporting/expanding) on depth
            self.depth += 1
            prev_traversal.depth += 1
            # Prepare state for next depth level of vertices
            to_expand, next_to_expand, to_expand_append, next_to_expand_append = (
                next_to_expand,
                to_expand,
                next_to_expand_append,
                to_expand_append,
            )
            del next_to_expand[:]

        # Correct the depth to the search depth of last visited vertex. If
        # start_vertices was given, and the argument was empty, the result will be -1.
        # The documentation does not specify this behaviour, but it might be expected.
        self.depth -= 2

    def go_for_depth_range(self, start: int, stop: int) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator. During the traversal,
        the iterator skips vertices as long as their depth is lower than *start*.
        From then on, is reports the found vertices. It stops when the reached depth
        is equal to or higher than *stop*.

        Note: The first vertex with a depth equal or higher than *stop* will be
        consumed from the traversal, but will not be reported, so it is lost (compare
        *itertools.takewhile*).

        :param start: Vertices lower than this are skipped.
        :param stop: Reporting stops when reached depth is equal or higher than this.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_depth_range can only be called "
                + "on a Traversal object."
            )

        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function
        def my_generator() -> Iterator[T_vertex]:
            for v in self._generator:
                if self.depth >= start:
                    if self.depth < stop:
                        yield v
                    break
            for v in self._generator:
                if self.depth >= stop:
                    break
                yield v

        return my_generator()


class TraversalBreadthFirst(
    Generic[T_vertex, T_labels], TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]
):
    """
    Eases the use of `TraversalBreadthFirstFlex` for typical cases.
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
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            NextEdges[T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]]
        ] = None,
        next_labeled_edges: Optional[
            NextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels],
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
