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

"$$ import_from('$$/MTraversalWithoutWeights.py') $$"


class TraversalBreadthFirstFlex(
    _TraversalWithoutWeightsWithVisited[T_vertex, T_vertex_id, T_labels]
):
    """
    # $$ insert_from('$$/cls_traversal/doc_start.rst')

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

    # $$ insert_from('$$/cls_traversal/doc_input.rst')

    **Search state:** When a vertex is *expanded*
    (traversal calls next_vertices, next_edges or next_labeled_edges)
    or *reported* (an iterator of the traversal returns it),
    the traversal provides updated values for the attributes
    *depth*, *paths*, and *visited*.
    """

    def __init__(
        self,
        # $$ MStrategyWithoutWeights.init_signature('TraversalBreadthFirstFlex')
    ) -> None:
        "$$ MStrategyWithoutWeights.init_code(search_depth_is_vertex_depth=True) $$"
        self._report_depth_increase = False

    def start_from(
        self,
        # $$ insert_from('$$/method_start_from/signature.py')
        _report_depth_increase: bool = False,  # hidden parameter for internal use
    ) -> TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]:
        """
        # $$ insert_from('$$/method_start_from/doc_start.rst')
        # $$ insert_from('$$/method_start_from/doc_already_visited_std.txt')
        # $$ insert_from('$$/method_start_from/doc_end.rst')
        """
        "$$ insert_from('$$/method_start_from/code_start.py') $$"
        self._report_depth_increase = _report_depth_increase

        super()._start()
        return self

    def _traverse(self) -> Generator[T_vertex, None, Any]:
        "$$ insert_from('$$/method_traverse/code_start_with_tree_and_visited.py') $$"

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

        "$$ insert_from('$$/method_traverse/code_prepare_edges_loop.py') $$"

        # ----- Inner loop -----

        while to_expand:
            for vertex in to_expand:
                "$$ MCalculationLimit.step() $$"

                for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                    neighbor = edge_or_vertex[0] if edges_with_data else edge_or_vertex

                    if not is_tree or build_paths:
                        "$$ MStrategy.vertex_to_id('neighbor', 'n_id') $$"

                        # If not is_tree: Ignore neighbor if already seen, and
                        # else include its ID in visited set.
                        """$$ MVertexSet.if_visited_continue_else_add(
                                  'visited', 'n_id', 'not is_tree')
                        $$"""

                        if build_paths:
                            """$$ MVertexMappingExpectNone.store_vertex_and_edge_data(
                                      'predecessors', 'attributes',
                                      'vertex', 'n_id', 'edge_or_vertex[-1]')
                            $$"""

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


"$$ MStrategyWithoutWeights.standard_for_flex('TraversalBreadthFirst') $$"
