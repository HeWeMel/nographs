from __future__ import annotations

from abc import ABC

from collections.abc import (
    Callable,
    Iterator,
    Iterable,
    MutableSet,
    MutableMapping,
)
from typing import TypeVar, Optional, Any, Union, cast, Generic

from ._gear_collections import (
    get_wrapper_from_vertex_set,
    get_wrapper_from_vertex_mapping,
)
from ._gears import (
    GearWithoutDistances,
    Gear,
    VertexIdSet,
    VertexIdToVertexMapping,
    VertexIdToDistanceMapping,
    VertexIdToPathEdgeDataMapping,
)
from ._paths import (
    Paths,
    PathsOfUnlabeledEdges,
    PathsOfLabeledEdges,
    DummyPredecessorOrAttributesMapping,
    PathsDummy,
)
from ._types import (
    T_vertex,
    T_vertex_id,
    T_weight,
    T_labels,
    VertexToID,
    vertex_as_id,
    WeightedUnlabeledOutEdge,
    WeightedLabeledOutEdge,
    UnweightedLabeledOutEdge,
    LabeledOutEdge,
    OutEdge,
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


class Strategy(ABC, Generic[T_vertex, T_vertex_id, T_labels]):
    """Base class of the traversal strategies and search strategies of NoGraphs."""

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        """Improve the state description

        :param state: State in current form
        :param vertices: If the strategy can provide additional state data w.r.t. these
            vertices, it will do so.
        """
        pass

    def state_to_str(self, vertices: Optional[Iterable[T_vertex]] = None) -> str:
        """Return a human-readable description of the public state of the strategy as
        a string.

        Implementation details, not covered by the semantic versioning:

        Currently, the method aims at providing a uniform behaviour over different
        platforms (*CPython* and *PyPy*) and collection types (Gears with different
        *MutableSet* and *MutableMapping* implementations). It behaves roughly as
        follows:

        - A *MutableSet*, e.g. attribute *visited*, is described similar to a *set*,
          but items are sorted lexicographically in their string representations
          (this bridges differences between *CPython* and *PyPy*).

        - Attribute *Paths* is described similar to a *dict* (although keys can contain
          unhashable values, and only paths for the given *vertices* are described).

        - A *MutableMapping*, e.g. attribute *distance*, is described similarly to a
          *dict*, also in cases, where it is not a *dict*, and although the items
          for only the given *vertices* are described.

        :param vertices: If the strategy can provide additional state data w.r.t. these
            vertices, it will do so.
        """
        state = dict((k, v) for k, v in self.__dict__.items() if k[0] != "_")
        self._improve_state(state, vertices)
        return str(state)


# --------------- exported types -------------

# todo: Warning: The following types are manually documented in api.rst

# next vertices and next edges functions for traversals
# that work with and without weights

T_strategy = TypeVar("T_strategy", bound=Strategy)

NextVertices = Callable[[T_vertex, T_strategy], Iterable[T_vertex]]

NextEdges = Callable[[T_vertex, T_strategy], Iterable[OutEdge[T_vertex, Any, Any]]]

NextLabeledEdges = Callable[
    [T_vertex, T_strategy], Iterable[LabeledOutEdge[T_vertex, Any, T_labels]]
]

# next edges functions for traversal that work with weights
NextWeightedEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            WeightedUnlabeledOutEdge[T_vertex, T_weight],
            WeightedLabeledOutEdge[T_vertex, T_weight, Any],
        ]
    ],
]

NextWeightedLabeledEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[WeightedLabeledOutEdge[T_vertex, T_weight, T_labels]],
]

# The same, but as a tuple, for bidirectional search strategies

BNextVertices = tuple[
    NextVertices[T_vertex, T_strategy],
    NextVertices[T_vertex, T_strategy],
]

BNextEdges = tuple[
    NextEdges[T_vertex, T_strategy],
    NextEdges[T_vertex, T_strategy],
]

BNextLabeledEdges = tuple[
    NextLabeledEdges[T_vertex, T_strategy, T_labels],
    NextLabeledEdges[T_vertex, T_strategy, T_labels],
]

BNextWeightedEdges = tuple[
    NextWeightedEdges[T_vertex, T_strategy, T_weight],
    NextWeightedEdges[T_vertex, T_strategy, T_weight],
]

BNextWeightedLabeledEdges = tuple[
    NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
    NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
]


# --------------- package internal types -------------

NextEdgesOrVertices = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            T_vertex,
            WeightedUnlabeledOutEdge[T_vertex, Any],
            UnweightedLabeledOutEdge[T_vertex, T_labels],
            WeightedLabeledOutEdge[T_vertex, Any, T_labels],
        ]
    ],
]

NextWeightedMaybeLabeledEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            WeightedUnlabeledOutEdge[T_vertex, T_weight],
            WeightedLabeledOutEdge[T_vertex, T_weight, T_labels],
        ]
    ],
]


# The same, but as a tuple, for bidirectional search strategies

BNextEdgesOrVertices = tuple[
    NextEdgesOrVertices[T_vertex, T_strategy, T_labels],
    NextEdgesOrVertices[T_vertex, T_strategy, T_labels],
]

BNextWeightedMaybeLabeledEdges = tuple[
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
]


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
    VertexIdToPathEdgeDataMapping[T_vertex_id, T_labels],
]:
    """Translate from configuration of path generation to setting of
    paths, predecessors and attributes collection. Store empty paths for start
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
        attributes: Optional[VertexIdToPathEdgeDataMapping[T_vertex_id, T_labels]]
        if labeled_edges:
            attributes = gear.vertex_id_to_path_attributes_mapping(())
            paths = PathsOfLabeledEdges[T_vertex, T_vertex_id, T_labels](
                predecessor, attributes, vertex_to_id
            )
        else:
            paths = PathsOfUnlabeledEdges[T_vertex, T_vertex_id](
                predecessor, vertex_to_id
            )
            attributes = DummyPredecessorOrAttributesMapping[T_vertex_id, T_labels]()
        return paths, predecessor, attributes
    else:
        return (
            PathsDummy[T_vertex, T_vertex_id, T_labels](vertex_to_id),
            DummyPredecessorOrAttributesMapping[T_vertex_id, T_vertex](),
            DummyPredecessorOrAttributesMapping[T_vertex_id, T_labels](),
        )


class NoIterator(Generic[T_vertex]):
    """An iterator that raises RuntimeError instead of iterating.

    When the application requests an iterator from a traversal that has not been
    started so far and uses this iterator, this is a programming error in the
    application: When the traversal is started, the iterator will be replaced, but the
    application will still have and maybe use the one it has requested to early. Thus,
    the traversal returns a _NoIterator in this case, so that any use of it clearly
    shows the problem.
    """

    def __next__(self) -> T_vertex:
        """
        >>> next(NoIterator())
        Traceback (most recent call last):
        RuntimeError: Traversal not started, iteration not possible
        """
        raise RuntimeError("Traversal not started, iteration not possible")

    def __iter__(self) -> Iterator[T_vertex]:
        """
        >>> iter(NoIterator())
        Traceback (most recent call last):
        RuntimeError: Traversal not started, iteration not possible
        """
        raise RuntimeError("Traversal not started, iteration not possible")


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
