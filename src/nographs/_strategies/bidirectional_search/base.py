from __future__ import annotations

from typing import Optional, Any

from nographs._types import (
    T_vertex,
    T_weight,
    T_labels,
)
from ..type_aliases import (
    T_strategy,
    BNextVertices,
    BNextEdges,
    BNextEdgesOrVertices,
    BNextWeightedMaybeLabeledEdges,
    BNextLabeledEdges,
    BNextWeightedEdges,
    BNextWeightedLabeledEdges,
)


# --------------- internal support functions -------------


def _search_needs_search_object(obj: Any, needed_class: type) -> None:
    if not isinstance(obj, needed_class):
        raise RuntimeError(
            "Method start_from can only be called on a search strategy object."
        )


def _create_unified_next_bidirectional(
    next_vertices: Optional[BNextVertices[T_vertex, T_strategy]],
    next_edges: Optional[BNextEdges[T_vertex, T_strategy]],
    next_labeled_edges: Optional[BNextLabeledEdges[T_vertex, T_strategy, T_labels]],
) -> tuple[BNextEdgesOrVertices[T_vertex, T_strategy, T_labels], bool, bool]:
    """Check configuration of given next_vertices, next_edges, and next_labeled_edges
    function pairs
    and calculate a pair of unified NextEdgesOrVertices
    and whether we have edges with data (weights and/or labels) and/or labeled_edges.
    """
    next_edges_or_vertices: BNextEdgesOrVertices[T_vertex, T_strategy, T_labels]
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


def _create_unified_next_weighted_bidirectional(
    next_edges: Optional[BNextWeightedEdges[T_vertex, T_strategy, T_weight]],
    next_labeled_edges: Optional[
        BNextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels]
    ],
) -> tuple[
    BNextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
    bool,
]:
    """Check configuration of given next_edges and next_labeled_edges function pairs
    and calculate a pair of unified _NextWeightedMaybeLabeledEdges and whether we have
    labeled_edges.
    """
    next_maybe_labeled_edges: BNextWeightedMaybeLabeledEdges[
        T_vertex, T_strategy, T_weight, T_labels
    ]
    if next_edges is not None:
        if next_labeled_edges is not None:
            raise RuntimeError("Both next_edges and next_labeled_edges provided.")
        next_maybe_labeled_edges = next_edges
        labeled_edges = False
    else:
        if next_labeled_edges is None:
            raise RuntimeError("Neither next_edges and next_labeled_edges provided.")
        next_maybe_labeled_edges = next_labeled_edges
        labeled_edges = True
    return next_maybe_labeled_edges, labeled_edges
