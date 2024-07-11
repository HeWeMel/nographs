from __future__ import annotations

from abc import ABC
from numbers import Real
from typing import Generic, Any, Optional, Iterable, Iterator

from nographs._types import (
    T_vertex,
    T_labels,
    VertexToID,
    T_vertex_id,
    T_weight,
)
from nographs._gears import (
    Gear,
    VertexIdToDistanceMapping,
)
from ...type_aliases import (
    NextWeightedMaybeLabeledEdges,
    NextWeightedEdges,
    NextWeightedLabeledEdges,
)
from ...utils import NoDistancesMapping, StrRepr
from ..traversal import Traversal
from ...type_aliases import (
    T_strategy,
)


def _create_unified_next_weighted(
    next_edges: Optional[NextWeightedEdges[T_vertex, T_strategy, T_weight]],
    next_labeled_edges: Optional[
        NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels]
    ],
) -> tuple[
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels], bool
]:
    """Check configuration of given next_edges and next_labeled_edges and calculate
    unified _NextWeightedMaybeLabeledEdges[] and whether we have labeled_edges."""
    next_maybe_labeled_edges: NextWeightedMaybeLabeledEdges[
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


class _TraversalWithWeights(
    Generic[T_vertex, T_vertex_id, T_weight, T_labels],
    Traversal[T_vertex, T_vertex_id, T_labels],
    ABC,
):
    """A Traversal that needs weighted edges and uses a gear suitable for this."""

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        self._gear = gear
        super().__init__(labeled_edges, is_tree, vertex_to_id)


class _TraversalWithDistances(
    _TraversalWithWeights[T_vertex, T_vertex_id, T_weight, T_labels],
    ABC,
):
    """
    A _TraversalWithWeights that provides a distances collection as part of
    its state.
    """

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        self.distances: VertexIdToDistanceMapping[T_vertex_id, T_weight] = (
            NoDistancesMapping[T_vertex_id, T_weight]()
        )
        """ Provisional or final distance values of some vertices
        (distance from a start vertex). Without option *keep_distances*,
        the value for a vertex is removed once the vertex has been reported. With
        option *keep_distances*, values are never removed, and that means: During a
        traversal, the distance values for already reported vertices can be found in
        the collection. After an exhaustive search, the collection contains exactly
        and only the distances of all vertices that are reachable from the start
        vertices and of the start vertices themselves.
        """

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Assignments in distances are only valid for reported vertices. Thus,
        # we need to convert only keys/values for requested vertices to a string,
        # not the whole MutableMapping. So, we special case this attribute here.
        del state["distances"]
        if vertices is not None:
            vertex_to_id, distances = self._vertex_to_id, self.distances
            state["distances"] = StrRepr.from_iterable(
                (v_id := vertex_to_id(vertex), distances[v_id]) for vertex in vertices
            )
        super()._improve_state(state, vertices)


class _TraversalWithDistance(
    _TraversalWithDistances[T_vertex, T_vertex_id, T_weight, T_labels],
    ABC,
):
    """
    A _TraversalWithDistances that provides a distance as part of its staste.
    If offers the go_for_distance_range method based on the distance.
    """

    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    ) -> None:
        super().__init__(labeled_edges, is_tree, vertex_to_id, gear)

        # The following value is not used by NoGraphs. It is only set
        # to have some initialization.
        self.distance: T_weight = self._gear.infinity()
        """ The length of the shortest path (sum of edge weights) from a
        start vertex to the visited vertex
        """

    def go_for_distance_range(self, start: Real, stop: Real) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator. During the traversal,
        the iterator skips vertices as long as their distance is lower than *start*.
        From then on, is reports the found vertices. It stops when the reached
        distance is equal to or higher than *stop*.

        Note: The first vertex with a distance equal or higher than stop will be
        consumed from the traversal, but will not be reported, so it is lost (compare
        itertools.takewhile).
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_distance_range can only be called "
                + "on a Traversal object."
            )

        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function
        def my_generator() -> Iterator[T_vertex]:
            for v in self._generator:
                if self.distance >= start:
                    if self.distance < stop:
                        yield v
                    break
            for v in self._generator:
                if self.distance >= stop:
                    break
                yield v

        return my_generator()
