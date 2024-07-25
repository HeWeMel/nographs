""" Traversal strategies for unweighted graphs with or without edge labels """

from __future__ import annotations

from abc import abstractmethod
from collections.abc import (
    Iterator,
    Iterable,
    Generator,
    Collection,
)
from typing import Optional, Any, cast, overload, Literal

from nographs._gears import (
    GearWithoutDistances,
    VertexIdToVertexMapping,
    VertexIdToEdgeLabelsMapping,
)
from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
    vertex_as_id,
)
from nographs._paths import (
    Paths,
    DummyPredecessorOrLabelsMapping,
    PathsDummy,
)
from ..utils import (
    StrRepr,
    create_paths,
)
from ..strategy import Strategy


def no_generator() -> Generator[Any, None, None]:
    """
    >>> next(no_generator())
    Traceback (most recent call last):
    RuntimeError: Traversal not started, iteration not possible
    """
    raise RuntimeError("Traversal not started, iteration not possible")
    # noinspection PyUnreachableCode
    yield None


class Traversal(Strategy[T_vertex, T_vertex_id, T_labels], Iterable):
    """
    Abstract Class. Its subclasses provide methods to iterate through vertices
    and edges using some specific traversal strategies.
    """

    @abstractmethod
    def __init__(
        self,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
    ) -> None:
        """
        :param labeled_edges: The element *label* of an edge is set for edges
        :param is_tree: The traversal does not need to prevent re-visits
        :param vertex_to_id: See *VertexToID*
        """
        # -- Attributes of graph adaptation
        # The come from parameters of __init__ and do not change with _start_from.
        self._labeled_edges = labeled_edges
        self._is_tree = is_tree
        self._vertex_to_id = vertex_to_id

        # -- Further, general attributes set and needed by all traversal strategies
        # They have to be initialized when a traversal is started or re-started,
        # see method _start_from. Thus, here, they are only initialized in a generic
        # default way.

        # Internal attributes
        self._generator: Generator[T_vertex, None, Any] = no_generator()
        self._start_vertices: Iterable[T_vertex] = tuple[T_vertex]()
        self._build_paths: bool = False
        self._calculation_limit: Optional[int] = None

        # External paths attributes
        self.paths: Paths[T_vertex, T_vertex_id, T_labels] = PathsDummy[
            T_vertex, T_vertex_id, T_labels
        ](vertex_to_id)
        """ The container *paths* holds the created paths, if path creation has been
        demanded. If labeled edges were provided (parameter *next_labeled_edges*), the
        paths contain them instead of just vertices.
        """
        self._predecessors: VertexIdToVertexMapping[T_vertex_id, T_vertex] = (
            DummyPredecessorOrLabelsMapping[T_vertex_id, T_vertex]()
        )
        self._attributes: VertexIdToEdgeLabelsMapping[T_vertex_id, T_labels] = (
            DummyPredecessorOrLabelsMapping[T_vertex_id, T_labels]()
        )

    def _start_from(
        self,
        start_vertex: Optional[T_vertex],
        start_vertices: Optional[Iterable[T_vertex]],
        build_paths: bool,
        calculation_limit: Optional[int],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        empty_path_for_start_vertices: bool = True,
    ) -> None:
        """
        Initialize the traversal attributes that have to be initialized when
        the traversal is started or re-started, see __init__. The configuration of
        start_vertex and start_vertices is checked before it is used.
        """
        # Check start vertices options. Compute multi-vertices form from single vertex.
        if start_vertex is not None:
            if start_vertices is not None:
                raise RuntimeError("Both start_vertex and start_vertices provided.")
            self._start_vertices = (start_vertex,)
        else:
            if start_vertices is None:
                raise RuntimeError("Neither start_vertex nor start_vertices provided.")
            if (
                build_paths
                and empty_path_for_start_vertices
                and not isinstance(start_vertices, Collection)
            ):
                # Below, we will consume vertices by the call of *create_path*, so we
                # first make a collection out of start_vertices, except they
                # are already given as collection
                self._start_vertices = gear.sequence_of_vertices(start_vertices)
            else:
                self._start_vertices = start_vertices

        # Create and store path container and path setting
        self._build_paths = build_paths
        self.paths, self._predecessors, self._attributes = create_paths(
            build_paths,
            gear,
            self._labeled_edges,
            self._vertex_to_id,
            self._start_vertices if empty_path_for_start_vertices else (),
        )

        # store calculation limit
        self._calculation_limit = calculation_limit

    def _start(self) -> None:
        self._generator = self._traverse()

    def __iter__(
        self,
    ) -> Iterator[T_vertex]:  # Type alias needed do to a sphinx limitation
        """
        Return the iterator of a started traversal. This allows for using a
        `Traversal` in *for* loops or as parameter to a call of function
        *next()*.

        Subsequent calls return the same iterator again. This allows for using
        the same `Traversal` in subsequent *for* loops or *next()* calls, as
        long as the iterator is not exhausted.

        The iterator yields vertices reported by the traversal algorithm.
        When a vertex is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`)."""
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go can only be called on a Traversal object.")
        return self._generator

    def __next__(self) -> T_vertex:
        """Returns the next vertex reported by the (started) traversal. This
        allows for calls like *next(traversal)*.

        Delegates to the iterator of the traversal."""
        return next(self._generator)

    def go_for_vertices_in(
        self, vertices: Iterable[T_vertex], fail_silently: bool = False
    ) -> Iterator[T_vertex]:
        """
        For a started traversal, return an iterator that fetches vertices
        from the traversal, reports a vertex if it is in *vertices*, and stops when
        all the *vertices* have been found and reported.

        If the iterator has no more vertices to report (graph is exhausted) without
        having found all the *vertices*, KeyError is raised, or the traversal just
        terminates, if a silent fail is demanded.

        If *vertices* does not provide any vertices, an empty iterator is returned.

        If a `VertexToID` function is used, the method searches for vertices
        that have the same id as one of the *vertices*.

        Whenever a vertex is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).

        :param vertices: Vertices to find
        :param fail_silently: Terminate, but do not raise KeyError, when graph
            is exhausted.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_vertices_in can only be called "
                + "on a Traversal object."
            )
        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function

        def my_generator() -> Iterator[T_vertex]:
            vertex_to_id = self._vertex_to_id
            if vertex_to_id == vertex_as_id:
                vertex_set = set(cast(Iterable[T_vertex_id], vertices))
                v_count = len(vertex_set)
                if v_count:
                    for v in self._generator:
                        if v not in vertex_set:
                            continue
                        yield v
                        v_count -= 1
                        if v_count == 0:
                            break
            else:
                vertex_set = set(vertex_to_id(vertex) for vertex in vertices)
                v_count = len(vertex_set)
                if v_count:
                    for v in self._generator:
                        if vertex_to_id(v) not in vertex_set:
                            continue
                        yield v
                        v_count -= 1
                        if v_count == 0:
                            break
            if v_count > 0 and not fail_silently:
                raise KeyError("Not all of the given vertices have been found")

        return my_generator()

    @overload
    def go_to(
        self, vertex: T_vertex, fail_silently: Literal[False] = False
    ) -> T_vertex: ...

    @overload
    def go_to(
        self, vertex: T_vertex, fail_silently: Literal[True]
    ) -> Optional[T_vertex]: ...

    def go_to(
        self, vertex: T_vertex, fail_silently: bool = False
    ) -> Optional[T_vertex]:
        """
        For a started traversal, walk through the graph, stop at *vertex* and
        return it. If the traversal ends (traversal iterator is exhausted) without
        having found *vertex*, raise KeyError, or return None,
        if a silent fail is demanded.

        If a `VertexToID` function is used, the method searches for a vertex
        that has the same id as the given *vertex*.

        When *vertex* is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).

        :param vertex: Stop search at this vertex.

        :param fail_silently: Terminate and return None, but do not raise KeyError,
            when graph is exhausted.
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go_to can only be called on a Traversal object.")

        vertex_to_id = self._vertex_to_id
        if vertex_to_id == vertex_as_id:
            for v in self._generator:
                if v != vertex:
                    continue
                return v
            else:
                if fail_silently:
                    return None
                else:
                    raise KeyError("Vertex not found, graph exhausted.")
        else:
            vertex_id = vertex_to_id(vertex)
            for v in self._generator:
                if vertex_to_id(v) != vertex_id:
                    continue
                return v
            else:
                if fail_silently:
                    return None
                else:
                    raise KeyError("Vertex not found, graph exhausted.")

    @abstractmethod
    def _traverse(self) -> Generator[T_vertex, Any, Any]:
        """Has to be implemented in subclass"""

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        # Convert a Paths object to an object that can be converted to a str.
        # Paths in the paths object can be temporary values differing from the
        # final result, so we cannot iterate them, because this might show
        # misleading data (for this reason, they are not even itarable).
        # And a path in a paths object does not need to be hashable. So, we
        # cannot even convert the valid paths to a dict and from there to a
        # string.
        # Thus, we manually iterate the *vertices* and create something that
        # has a string representation that resembles a dict.
        del state["paths"]
        if vertices is not None:
            state["paths"] = (
                StrRepr.from_iterable(
                    (vertex, self.paths[vertex])
                    for vertex in vertices
                    if vertex in self.paths
                )
                if self._build_paths
                else dict()
            )
        super()._improve_state(state, vertices)


def _start_from_needs_traversal_object(obj: Any) -> None:
    if not isinstance(obj, Traversal):
        raise RuntimeError(
            "Method start_from can only be called on a Traversal object."
        )
