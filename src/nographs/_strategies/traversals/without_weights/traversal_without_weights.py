from __future__ import annotations

from abc import ABC
from typing import Optional, Any
from _collections_abc import Iterable, Collection

from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
)
from nographs._gears import GearWithoutDistances, VertexIdSet
from ..traversal import (
    Traversal,
    _start_from_needs_traversal_object,
)
from ...type_aliases import (
    NextVertices,
    T_strategy,
    NextEdges,
    NextLabeledEdges,
    NextEdgesOrVertices,
)
from ...utils import (
    NoVisitedSet,
    define_visited,
    iter_start_ids,
    StrRepr,
)


def _create_unified_next(
    next_vertices: Optional[NextVertices[T_vertex, T_strategy]],
    next_edges: Optional[NextEdges[T_vertex, T_strategy]],
    next_labeled_edges: Optional[NextLabeledEdges[T_vertex, T_strategy, T_labels]],
) -> tuple[NextEdgesOrVertices[T_vertex, T_strategy, T_labels], bool, bool]:
    """Check configuration of given next_vertices, next_edges, and next_labeled_edges
    and calculate unified NextEdgesOrVertices
    and whether we have edges with data (weights and/or labels) and/or labeled_edges.
    """
    next_edges_or_vertices: NextEdgesOrVertices[T_vertex, T_strategy, T_labels]
    if next_vertices is not None:
        if next_edges is not None:
            raise RuntimeError("Both next_vertices and next_edges provided.")
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_vertices and next_labeled_edges provided.")
        next_edges_or_vertices = next_vertices
        edges_with_data = False
        labeled_edges = False
    elif next_edges is not None:
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_edges and next_labeled_edges provided.")
        next_edges_or_vertices = next_edges
        edges_with_data = True
        labeled_edges = False
    else:
        if next_labeled_edges is None:
            raise RuntimeError(
                "Neither next_vertices nor next_edges "
                + "nor next_labeled_edges provided."
            )
        next_edges_or_vertices = next_labeled_edges
        edges_with_data = True
        labeled_edges = True
    return next_edges_or_vertices, edges_with_data, labeled_edges


class _TraversalWithoutWeights(Traversal[T_vertex, T_vertex_id, T_labels], ABC):
    """
    A traversal that needs no weight type. Edges can be given with or without data.
    """

    def __init__(
        self,
        edges_with_data: bool,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    ) -> None:
        """
        :param edges_with_data: Edges tuples, not just successor vertices
        :param gear: The traversal will use this gear

        For the other parameters, see super class.
        """
        super().__init__(labeled_edges, is_tree, vertex_to_id)
        self._edges_with_data = edges_with_data
        self._gear = gear


class _TraversalWithoutWeightsWithVisited(
    _TraversalWithoutWeights[T_vertex, T_vertex_id, T_labels], ABC
):
    """A _TraversalWithoutWeights with attribute visited."""

    def __init__(
        self,
        edges_with_data: bool,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    ) -> None:
        super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
        self.visited: VertexIdSet[T_vertex_id] = NoVisitedSet[T_vertex_id]()
        """ A collection that contains the visited vertices (resp. their hashable ids
        from vertex_to_id). After an exhaustive search, it contains
        the vertices (resp. vertex ids) reachable from the start vertices.
        """

    def _start_without_weights_with_visited(
        self,
        start_vertex: Optional[T_vertex],
        start_vertices: Optional[Iterable[T_vertex]],
        build_paths: bool,
        calculation_limit: Optional[int],
        already_visited: Optional[VertexIdSet[T_vertex_id]],
        empty_path_for_start_vertices: bool = True,
        visited_for_start_vertices: bool = True,
    ) -> None:
        """
        Check configuration of start_vertex and start_vertices. Set attributes
        _start_vertices, _build_path, paths, _predecessors, _attributes,
        and visited.
        Empty paths for start vertices are only set if demanded (default: True).
        Start vertices are only set as visited if demanded (default: True).
        """
        _start_from_needs_traversal_object(self)
        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            calculation_limit,
            self._gear,
            empty_path_for_start_vertices,
        )
        if visited_for_start_vertices and not isinstance(start_vertices, Collection):
            # We will consume vertices by the call of *iter_start_ids*, so we
            # first make a collection out of start_vertices, except they
            # are already given as a collection
            self._start_vertices = self._gear.sequence_of_vertices(self._start_vertices)
        self.visited = define_visited(
            self._gear,
            already_visited,
            (
                iter_start_ids(self._start_vertices, self._vertex_to_id)
                if visited_for_start_vertices
                else ()
            ),
            self._is_tree,
        )

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Visited, a MutableSet, is typically not ordered. str(self.visited)
        # results in different strings for different interpreters (PyPy) and
        # the keys are not sorted. Here, we create a normalized description.
        del state["visited"]
        state["visited"] = StrRepr.from_set(self.visited)
        super()._improve_state(state, vertices)
