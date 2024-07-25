from __future__ import annotations

from collections.abc import (
    Iterator,
    Iterable,
    MutableSet,
    MutableMapping,
)
from typing import Optional, Any, cast

from nographs._gear_collections import (
    get_wrapper_from_vertex_set,
    get_wrapper_from_vertex_mapping,
)
from nographs._gears import (
    GearWithoutDistances,
    Gear,
    VertexIdSet,
    VertexIdToVertexMapping,
    VertexIdToDistanceMapping,
    VertexIdToEdgeLabelsMapping,
)
from nographs._paths import (
    Paths,
    PathsOfUnlabeledEdges,
    PathsOfLabeledEdges,
    DummyPredecessorOrLabelsMapping,
    PathsDummy,
)
from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_weight,
    T_labels,
    VertexToID,
    vertex_as_id,
)


# --------------- classes -------------


class StrRepr:
    """Provides a specifically "normalized" string representation of data."""

    def __init__(self, s: str) -> None:
        self.s = s

    @classmethod
    def from_iterable(cls, i: Iterable[tuple[Any, Any]]) -> StrRepr:
        """
        Provides a string representation of an iterable of key/value tuples,
        that look like the output from a dict with these items.

        (The 'keys' do not need to be hashable.)
        """
        return cls("{" + ", ".join(repr(k) + ": " + repr(v) for k, v in i) + "}")

    @classmethod
    def from_set(cls, c: MutableSet[Any]) -> StrRepr:
        """
        Provides a string representation of a *MutableSet*,
        that looks like the string representation of a *Set* with these items,
        but the elements are lexicographically sorted.

        The result is independent of the methods repr() and str() of the
        *MutableSet*. (The elements do not need to be hashable.)
        """
        return cls("{" + ", ".join(sorted(repr(k) for k in c)) + "}")

    def __repr__(self) -> str:
        return self.s


# --------------- internal support functions -------------


def iter_start_ids(
    start_vertices: Iterable[T_vertex], vertex_to_id: VertexToID[T_vertex, T_vertex_id]
) -> Iterable[T_vertex_id]:
    """Compute vertex ids for given start vertices and allow for iterating
    them"""
    if vertex_to_id == vertex_as_id:
        # If the identity function (in a mathematical sense)
        # vertex_as_id is used with correct typing, this means that
        # T_vertex is a subtype of T_vertex_id (typically: identical).
        # So, instead of applying the function, we could just cast the vertices
        # to vertex ids. For improved performance, we cast the whole iterator.
        return cast(Iterable[T_vertex_id], start_vertices)

    return (vertex_to_id(vertex) for vertex in start_vertices)


def iter_start_vertices_and_ids(
    start_vertices: Iterable[T_vertex], vertex_to_id: VertexToID[T_vertex, T_vertex_id]
) -> Iterable[tuple[T_vertex, T_vertex_id]]:
    """Compute vertex ids for given start vertices and allow for iterating
    pairs of vertex and vertex id."""
    if vertex_to_id == vertex_as_id:
        # If the identity function (in a mathematical sense)
        # vertex_as_id is used with correct typing, this means that
        # T_vertex is a subtype of T_vertex_id (typically: identical).
        # So, instead of applying the function, we could just cast the vertices
        # to vertex ids. For improved performance, we cast the whole iterator.
        vertices_and_vertices = ((vertex, vertex) for vertex in start_vertices)
        vertices_and_ids = cast(
            Iterator[tuple[T_vertex, T_vertex_id]], vertices_and_vertices
        )
        return vertices_and_ids

    return ((vertex, vertex_to_id(vertex)) for vertex in start_vertices)


def define_visited(
    gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    already_visited: Optional[VertexIdSet[T_vertex_id]],
    iter_start_ids: Iterable[T_vertex_id],
    is_tree: bool,
) -> VertexIdSet[T_vertex_id]:
    """Use and return already_visited, if provided, for storing visited vertices,
    and otherwise a new VertexIdSet. Mark start vertices as visited."""
    if already_visited is None:
        return gear.vertex_id_set(() if is_tree else iter_start_ids)

    if not is_tree:
        if (wrapper := get_wrapper_from_vertex_set(already_visited)) is None:
            method_add = already_visited.add
            for v_id in iter_start_ids:
                method_add(v_id)
        else:
            wrapper.update_from_keys(iter_start_ids)
    return already_visited


def define_distances(
    gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
    known_distances: Optional[VertexIdToDistanceMapping[T_vertex_id, T_weight]],
    iter_start_ids_and_distances: Iterable[tuple[T_vertex_id, T_weight]],
    is_tree: bool,
) -> VertexIdToDistanceMapping[T_vertex_id, T_weight]:
    """Use and return known_distances, if provided, for storing vertex distances, and
    otherwise new VertexIdToDistanceMapping. Store the distances given for the
    start vertices."""
    if known_distances is None:
        return gear.vertex_id_to_distance_mapping(iter_start_ids_and_distances)

    if not is_tree:
        if (wrapper := get_wrapper_from_vertex_mapping(known_distances)) is None:
            method_setdefault = known_distances.setdefault
            for v_id, distance in iter_start_ids_and_distances:
                method_setdefault(v_id, distance)
        else:
            wrapper.update_default(iter_start_ids_and_distances)

    return known_distances


def create_paths(
    build_paths: bool,
    gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
    labeled_edges: bool,
    vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    start_vertices: Iterable[T_vertex],
) -> tuple[
    Paths[T_vertex, T_vertex_id, T_labels],
    VertexIdToVertexMapping[T_vertex_id, T_vertex],
    VertexIdToEdgeLabelsMapping[T_vertex_id, T_labels],
]:
    """Translate from configuration of path generation to setting of
    paths, predecessors and labels collection. Store empty paths for start
    vertices. If no paths should be build, create dummy Paths container."""

    if build_paths:
        # Create container for predecessors.
        # From each start vertex, store an empty paths to itself.
        predecessor = gear.vertex_id_to_vertex_mapping(
            (
                (vertex_id, vertex)
                for vertex, vertex_id in iter_start_vertices_and_ids(
                    start_vertices, vertex_to_id
                )
            )
        )
        paths: Paths[T_vertex, T_vertex_id, T_labels]
        labels: Optional[VertexIdToEdgeLabelsMapping[T_vertex_id, T_labels]]
        if labeled_edges:
            labels = gear.vertex_id_to_edge_labels_mapping(())
            paths = PathsOfLabeledEdges[T_vertex, T_vertex_id, T_labels](
                predecessor, labels, vertex_to_id
            )
        else:
            paths = PathsOfUnlabeledEdges[T_vertex, T_vertex_id](
                predecessor, vertex_to_id
            )
            labels = DummyPredecessorOrLabelsMapping[T_vertex_id, T_labels]()
        return paths, predecessor, labels
    else:
        return (
            PathsDummy[T_vertex, T_vertex_id, T_labels](vertex_to_id),
            DummyPredecessorOrLabelsMapping[T_vertex_id, T_vertex](),
            DummyPredecessorOrLabelsMapping[T_vertex_id, T_labels](),
        )


class NoVisitedSet(MutableSet[T_vertex_id]):
    """A MutableSet for vertex ids that raises an exception on each operation.

    When the application accesses a state attribute of a traversal and the attribute is
    not initialized so far (i.e., before the first vertex has been expanded or
    reported), the traversal shows this problem to the application by returning
    a clearly functionless _NoVisitedSet in attribute *visited*.
    """

    def __contains__(self, key: object) -> bool:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __iter__(self) -> Iterator[T_vertex_id]:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __len__(self) -> int:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def discard(self, value: T_vertex_id) -> None:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def add(self, value: T_vertex_id) -> None:
        raise RuntimeError("Traversal not started, no data to be accessed")


class NoDistancesMapping(MutableMapping[T_vertex_id, T_weight]):
    """A MutableMapping from vertex ids to distances that raises an exception on each
    operation.

    When the application accesses a state attribute of a traversal and the attribute is
    not initialized so far (i.e., before the first vertex has been expanded or
    reported), the traversal shows this problem to the application by returning
    a clearly functionless _NoDistancesMapping in attribute *distances*.
    """

    def __getitem__(self, key: T_vertex_id) -> T_weight:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __delitem__(self, key: T_vertex_id) -> None:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __iter__(self) -> Iterator[T_vertex_id]:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __len__(self) -> int:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __contains__(self, key: object) -> bool:
        raise RuntimeError("Traversal not started, no data to be accessed")

    def __setitem__(self, key: T_vertex_id, value: T_weight) -> None:
        raise RuntimeError("Traversal not started, no data to be accessed")
