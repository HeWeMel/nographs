from __future__ import annotations

import collections
import itertools
import copy
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Sequence, Iterable, Hashable
from heapq import heapify, heappop, heappush
from numbers import Real
from typing import TypeVar, Optional, Any

from nographs import Vertex, VertexToID, VertexIterator
from nographs import Paths, PathsOfUnlabeledEdges, PathsOfLabeledEdges


# --------------- types -------------

# Warning: The following types are manually documented in api.rst
NextVertices = Callable[[Vertex, "Traversal"], Iterable[Vertex]]
NextEdges = Callable[[Vertex, "Traversal"], Iterable[Sequence]]


# --------------- internal support functions -------------


def _iter_start_ids(
    start_vertices: Iterable[Vertex],
    vertex_to_id: Optional[Callable[[Vertex], Hashable]],
) -> Iterable[Hashable]:
    if vertex_to_id:
        return (vertex_to_id(vertex) for vertex in start_vertices)

    return start_vertices


def _define_visited(
    already_visited: Optional[set[Hashable]],
    iter_start_ids: Iterable[Hashable],
    is_tree: bool,
) -> set[Hashable]:
    """Use already_visited, if provided, for storing visited vertices, and
    otherwise new dict. Mark start vertices as visited.
    """
    if already_visited is None:
        return set() if is_tree else set(iter_start_ids)

    if not is_tree:
        already_visited.update(iter_start_ids)
    return already_visited


def _create_no_paths(labeled_path: bool):
    """ Create setting of paths, predecessors and edge_data for
    case that no paths should be built."""
    if labeled_path:
        raise RuntimeError("Option labeled_paths without option build_paths.")
    return None, None, None


def _create_paths(
    labeled_path: bool,
    labeled_edges: bool,
    vertex_to_id: Optional[VertexToID],
) -> tuple[Paths, dict, Optional[dict]]:
    """Translate from configuration of path generation to setting of
    paths, predecessors and edge_data. """

    predecessors = dict[Any, Any]()
    if not labeled_path:
        return (
            PathsOfUnlabeledEdges(predecessors, vertex_to_id),
            predecessors,
            None,
        )

    if not labeled_edges:
        raise RuntimeError("A labeled path can only be computed from labeled edges.")

    edge_data = dict[Any, Any]()
    return (
        PathsOfLabeledEdges(predecessors, edge_data, vertex_to_id),
        predecessors,
        edge_data,
    )


class NoIterator:
    def __next__(self):
        """
        >>> next(NoIterator())
        Traceback (most recent call last):
        RuntimeError: Traversal not started, iteration not possible
        """
        raise RuntimeError("Traversal not started, iteration not possible")

    def __iter__(self):
        """
        >>> iter(NoIterator())
        Traceback (most recent call last):
        RuntimeError: Traversal not started, iteration not possible
        """
        raise RuntimeError("Traversal not started, iteration not possible")


# -- traversal strategies for unweighted graphs with or without edge labels --


class Traversal(ABC):
    """
    Abstract Class. Its subclasses provide methods to iterate through vertices
    and edges using some specific traversal strategies.
    """

    @abstractmethod
    def __init__(
        self,
        next_edge_or_vertex: Callable,
        labeled_edges: bool,
        is_tree: bool,
        vertex_to_id: Optional[VertexToID],
    ):
        # attributes of graph adaptation
        self._next_edge_or_vertex = next_edge_or_vertex
        self._labeled_edges = labeled_edges
        self._is_tree = is_tree
        self._vertex_to_id = vertex_to_id

        # general attributes set and needed by all traversal strategies
        self._generator: Iterator = NoIterator()
        self._start_vertices: Optional[Iterable[Vertex]] = None
        self._build_paths: Optional[bool] = None
        self._labeled_paths: Optional[bool] = None
        self._calculation_limit: Optional[int] = None

        # attributes for path data, needed by all traversal strategies
        self.paths: Optional[Paths] = None
        self._predecessors: Optional[dict[Vertex, Any]] = None
        self._edge_data: Optional[dict[Vertex, Any]] = None

    def __iter__(
        self,
    ) -> VertexIterator:  # Type alias needed do to a sphinx limitation
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
        # if self._generator is None:
        #     raise RuntimeError("Traversal not started, iteration not possible")
        return self._generator

    def __next__(self) -> Vertex:
        """Returns the next vertex reported by the (started) traversal. This
        allows for calls like *next(traversal)*.

        Delegates to the iterator of the traversal."""
        return next(self._generator)

    def go_for_vertices_in(
        self, vertices: VertexIterator, fail_silently: bool = False
    ) -> VertexIterator:
        """
        For a started traversal, return an iterator that fetches vertices
        from the traversal, reports a vertex if it is in *vertices*, and stops when
        all of the *vertices* have been found and reported. If the iterator has no
        more vertices to report (graph is exhausted) without having found all of the
        *vertices*, KeyError is raised, or the traversal just terminates, if a silent
        fail is demanded.

        Whenever a vertex is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_vertices_in can only be called "
                + "on a Traversal object."
            )
        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function

        def my_generator():
            vertex_set = (
                set(vertices)
                if self._vertex_to_id is None
                else set(self._vertex_to_id(vertex) for vertex in vertices)
            )

            v_count = len(vertex_set)
            for v in self._generator:
                if v not in vertex_set:
                    continue
                yield v
                v_count -= 1
                if v_count == 0:
                    break
            else:
                if not fail_silently:
                    raise KeyError("Not all of the given vertices have been found")

        return my_generator()

    def go_to(self, vertex: Vertex, fail_silently: bool = False) -> Optional[Vertex]:
        """
        For a started traversal, walk through the graph, stop at *vertex* and
        return it. If the traversal ends (traversal iterator is exhausted) without
        having found *vertex*, raise KeyError, or return None,
        if fail_silently is True.

        When *vertex* is reported, specific attributes of the traversal object
        contain additional data about the state of the traversal (see the API
        documentation of the respective subclass of `Traversal`).
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError("Method go_to can only be called on a Traversal object.")
        for v in self._generator:
            if v != vertex:
                continue
            return vertex
        else:
            if fail_silently:
                return None
            else:
                raise KeyError("Vertex not found, graph exhausted.")

    def _start_from(
        self,
        start_vertex: Optional[Vertex],
        start_vertices: Optional[Iterable[Vertex]],
        build_paths: bool,
        labeled_paths: bool,
        calculation_limit: Optional[int],
    ):
        if start_vertex is not None:
            if start_vertices is not None:
                raise RuntimeError("Both start_vertex and start_vertices provided.")
            self._start_vertices = (start_vertex,)
        else:
            if start_vertices is None:
                raise RuntimeError("Neither start_vertex and start_vertices provided.")
            self._start_vertices = start_vertices

        self._start_vertices = tuple(self._start_vertices)  # copy from iterable
        self._labeled_paths = labeled_paths

        # Note: Detection of wrong option combinations for paths is implemented in
        # _create_paths and _create_no_paths.
        if build_paths:
            self.paths, self._predecessors, self._edge_data = _create_paths(
                labeled_paths, self._labeled_edges, self._vertex_to_id
            )
            self._predecessors.update(
                (vertex, None)
                for vertex in _iter_start_ids(self._start_vertices, self._vertex_to_id)
            )
        else:
            self.paths, self._predecessors, self._edge_data = _create_no_paths(
                labeled_paths)

        self._calculation_limit = calculation_limit

    def _start(self, *args):
        self._generator = self._traverse(
            self._next_edge_or_vertex,
            self._labeled_edges,
            self._is_tree,
            self._vertex_to_id,
            self._calculation_limit,
            self.paths,
            self._predecessors,
            self._edge_data,
            *args,
        )

    @abstractmethod
    def _traverse(self, *args) -> Iterator[Vertex]:
        """Has to be implemented in sub class"""


class _TraversalWithLabels(Traversal, ABC):
    def __init__(
        self,
        next_edges: NextEdges,
        is_tree: bool,
        vertex_to_id: Optional[VertexToID],
    ) -> None:
        super().__init__(next_edges, True, is_tree, vertex_to_id)


CurrentTraversalClass = TypeVar(
    "CurrentTraversalClass", bound="_TraversalWithOrWithoutLabels"
)


class _TraversalWithOrWithoutLabels(Traversal, ABC):
    def __init__(
        self,
        next_vertices: Optional[NextVertices],
        next_edges: Optional[NextEdges],
        is_tree: bool,
        vertex_to_id: Optional[VertexToID],
    ) -> None:
        if next_vertices is not None:
            if next_edges is not None:
                raise RuntimeError("Both next_vertices and next_edges provided.")
            next_edge_or_vertex = next_vertices
            labeled_edges = False
        else:
            if next_edges is None:
                raise RuntimeError("Neither next_vertices nor next_edges provided.")
            next_edge_or_vertex = next_edges
            labeled_edges = True
        super().__init__(next_edge_or_vertex, labeled_edges, is_tree, vertex_to_id)

        self.visited: Optional[set] = None

    def start_from(
        self: CurrentTraversalClass,
        start_vertex: Optional[Vertex] = None,
        *,
        start_vertices: Optional[Iterable[Vertex]] = None,
        build_paths: bool = False,
        labeled_paths: bool = False,
        calculation_limit: Optional[int] = None,
        already_visited: Optional[set] = None,
    ) -> CurrentTraversalClass:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The vertices (iterator) the search should start at. Only
            allowed if start_vertex equals None.

        :param build_paths: If true, build paths from some start vertex to each visited
            vertex.

        :param labeled_paths: If true, integrate edge data in generated paths,
            not only vertices. Has to be false in graphs without labeled edges, i.e.,
            if you have given a next_vertices function and not a next_edges function.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param already_visited: If provided, this set is used instead of an internal
            one to keep vertices (resp. their hashable ids from vertex_to_id),
            that have already been visited. This parameter can be used to get online
            access to the internal bookkeeping of visited vertices, or to pre-load
            vertices that should never be visited, or to provide you own way for
            storing the information that a vertex has already been visited (if you do
            that in your own graph structure instead of a set, visited_vertices needs
            to provide the methods *update* and *__contains__*).

        :return: Traversal, that has been started, e.g., statements like *iter()*,
            *next()*, *for* and the methods "go*" of the Traversal can now be used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            labeled_paths,
            calculation_limit,
        )

        assert isinstance(self._start_vertices, Iterable)  # todo: solution not nice
        self.visited = _define_visited(
            already_visited,
            _iter_start_ids(self._start_vertices, self._vertex_to_id),
            self._is_tree,
        )
        super()._start()
        return self


class TraversalBreadthFirst(_TraversalWithOrWithoutLabels):
    def __init__(
        self,
        next_vertices: Optional[NextVertices] = None,
        *,
        next_edges: Optional[NextEdges] = None,
        is_tree: bool = False,
        vertex_to_id: Optional[VertexToID] = None,
    ):
        """
        :param next_vertices: See `NextVertices` function. If None, provide next_edges.

        :param next_edges: See `NextEdges` function. Only allowed if next_vertex equals
         None.

        :param is_tree: bool: If it is sure, that during each traversal run,
         each vertex can be reached only once, is_tree can be set to True. This
         improves performance, but attribute *visited* of the traversal will not be
         updated during and after the traversal.

        :param vertex_to_id: See `VertexToID` function.

        **Algorithm:** Breadth First Search, non-recursive, based on FIFO queue.

        **Properties:** Visits and reports vertices in breadth first order, i.e.,
        with ascending depth (edge count of the path with least edges from a start
        vertex).

        **Input:** Directed graph. Unlabeled or labeled edges. One ore more start
        vertices. Optional calculation limit.

        **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
        next_edges) or *reported* (an iterator of the traversal returns it),
        the traversal provides the following attributes:

        - **depth:** At this search depth, the reported vertex has been found. It
          equals the length of the created path to the vertex, if path creation is
          demanded. For the special case of TraversalBreadthFirst, it equals the *depth
          of the vertex* (minimal number of edges needed to come to it from a start
          vertex).

        - **paths:** A container object of class Paths. If path creation has been
          demanded, the container provides the found paths for all vertices visited so
          far. If labeled edges were provided, paths contain them instead of just
          vertices, if demanded. For the special case of TraversalBreadthFirst,
          all created paths are *shortest paths*, i.e., paths with minimal number of
          edges from a start vertex to their end vertex.

        - **visited**: A collection that contains the vertices (resp. their hashable ids
          from vertex_to_id) that have been visited so far, and the start vertices.
          When a finite graph has been fully traversed, it contains the
          vertices reachable from the start vertices.

        **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
        `go_for_vertices_in`, `go_to`.
        """

        super().__init__(next_vertices, next_edges, is_tree, vertex_to_id)
        self.depth = None

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edge_or_vertex,
            labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args
        # copy traversal specific attributes (set by from_*) into method scope
        visited = self.visited

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        # two lists used as FIFO queue with just two buckets
        # (using a queue and counting down size of current depth horizon is slower, and
        # creating a new list instead of clear() is also slower)
        to_visit = list(self._start_vertices)
        next_to_visit = list()

        prev_traversal = copy.copy(self)  # copy of self, for keeping previous depth
        self.depth = 1
        prev_traversal.depth = 0

        # Get references of used methods (avoid object resolution)
        visited_add = visited.add
        to_visit_append = to_visit.append
        next_to_visit_append = next_to_visit.append

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        while to_visit:
            for vertex in to_visit:
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, prev_traversal):
                    neighbor = edge_or_vertex[0] if labeled_edges else edge_or_vertex

                    if paths or not is_tree:
                        n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor

                        if not is_tree:
                            if n_id in visited:
                                continue
                            visited_add(n_id)

                        if paths:
                            predecessors[n_id] = vertex
                            if edge_data_exists:
                                edge_data[n_id] = edge_or_vertex[1:]

                    yield neighbor
                    next_to_visit_append(neighbor)

            self.depth += 1
            prev_traversal.depth += 1
            to_visit, next_to_visit, to_visit_append, next_to_visit_append = (
                next_to_visit,
                to_visit,
                next_to_visit_append,
                to_visit_append,
            )
            next_to_visit.clear()

    def go_for_depth_range(self, start: int, stop: int) -> VertexIterator:
        """
        For a started traversal, it return an iterator. During the traversal,
        the iterator skips vertices as long as their depth is lower than *start*.
        From then on, is reports the found vertices. It stops when the reached depth
        is equal to or higher than *stop*.

        Note: The first vertex with a depth equal or higher than *stop* will be
        consumed from the traversal, but will not be reported, so it is lost (compare
        *itertools.takewhile*).
        """
        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method go_for_depth_range can only be called "
                + "on a Traversal object."
            )

        # In order to make the above check work, the following generator functionality
        # needs to be encapsulated in a local function
        def my_generator():
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


class TraversalDepthFirst(_TraversalWithOrWithoutLabels):
    """
    :param next_vertices: See `NextVertices` function. If None, provide next_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertex equals
        None.

    :param is_tree: bool: If it is sure, that during each traversal run, each vertex can
        be reached only once, is_tree can be set to True. This improves performance,
        but attribute *visited* of the traversal will not be updated during and after
        the traversal.

    :param vertex_to_id: See `VertexToID` function.

    **Algorithm:** Depth First Search ("BFS"), non-recursive, based on stack.

    **Properties:** Follows edges to new vertices as long as possible, and goes back
    a step and follows further edges that start at some visited vertex only if
    necessary to come to new vertices.

    **Input:** Directed graph. One ore more start vertices. Vertices must be
    hashable, or hashable id can be provided. Unlabeled or labeled edges. Optional
    calculation limit.

    **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
    next_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides the following attributes:

    - **depth:** At this search depth, the reported vertex has been found. It equals
      the length of the created path to the vertex, if path creation is demanded. Note:
      The search depth does not need to be the depth of the vertex.

    - **paths:** A container object of class Paths. If path creation has been demanded,
      the container provides the found paths for all vertices visited so far. If labeled
      edges were provided, paths contain them instead of just vertices, if demanded.

    - **visited:** A collection that contains the vertices that have been visited so
      far, and the start vertices. When a finite graph has been fully traversed, it
      contains the vertices reachable from the start vertices.

    **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
    `go_for_vertices_in`, `go_to`.
    """

    def __init__(
        self,
        next_vertices: Optional[NextVertices] = None,
        *,
        next_edges: Optional[NextEdges] = None,
        is_tree: bool = False,
        vertex_to_id: Optional[VertexToID] = None,
    ) -> None:
        super().__init__(next_vertices, next_edges, is_tree, vertex_to_id)
        self.depth = None

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edge_or_vertex,
            labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args

        # copy traversal specific attributes (set by from_*) into method scope
        visited = self.visited

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        depth = 0
        to_visit = list(self._start_vertices)  # list used as stack

        # Get references of methods (avoid object resolution)
        to_visit_append = to_visit.append
        visited_add = visited.add

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        while to_visit:
            vertex = to_visit.pop()  # visit first added vertex first

            if (
                not is_tree and vertex is None
            ):  # Reached marker: end of vertices in same depth
                depth -= 1
                continue

            if depth:
                if is_tree:
                    self.depth = depth
                    yield vertex
                else:
                    n_id = vertex_to_id(vertex) if vertex_to_id else vertex
                    if n_id in visited:
                        continue
                    visited_add(n_id)
                    self.depth = depth
                    yield vertex
                    to_visit_append(
                        None
                    )  # Marker: reached by pop means leaving the vertex
            else:  # start vertices
                # can be expanded (but not yielded) although being visited
                self.depth = depth
                if not is_tree:
                    to_visit_append(
                        None
                    )  # Marker: reached by pop means leaving the vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for edge_or_vertex in next_edge_or_vertex(vertex, self):
                neighbor = edge_or_vertex[0] if labeled_edges else edge_or_vertex
                if paths:
                    n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor

                    if not is_tree and n_id in visited:
                        continue

                    # We have to store the predecessor here, because at time of
                    # visit, it is already lost. And we cannot yield here, because
                    # only the first of the neighbors will indeed be visited next.
                    # But since the visiting order is defined by a stack we know that
                    # for each vertex, the predecessor stored last is the edge
                    # visited first, and after that no other predecessor can be
                    # stored for that vertex.
                    predecessors[n_id] = vertex
                    if edge_data_exists:
                        edge_data[n_id] = edge_or_vertex[1:]

                to_visit_append(neighbor)
            depth += 1


class TraversalTopologicalSort(_TraversalWithOrWithoutLabels):
    """
    :param next_vertices: See `NextVertices` function. If None, provide next_edges.

    :param next_edges: See `NextEdges` function. Only allowed if next_vertex equals
       None.

    :param is_tree: bool: If it is sure, that during each traversal run, each vertex can
       be reached only once, is_tree can be set to True. This improves performance,
       but attribute *visited* of the traversal will not be updated during and after
       the traversal.

    :param vertex_to_id: See `VertexToID` function.

    **Algorithm:** Topological Search, non-recursive, based on stack.

    **Properties:** Vertices are reported in topological ordering, i.e. a linear
    ordering of the vertices such that for every directed edge uv from vertex u to
    vertex v ("u depends on v"), v comes before u in the ordering. If the graph
    contains a cycle that can be reached within the sorting process, a RuntimeError
    exception is raised and a cyclic path from a starting vertex is provided.

    **Input:** Directed graph. One ore more start vertices. Vertices must be
    hashable, or hashable id can be provided. Unlabeled or labeled edges. Optional
    calculation limit. Edge from vertex u to vertex v means, u "depends" from v.

    **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
    next_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides the following attributes:

    - **depth:** At this search depth, the reported vertex has been found. It equals
      the length of the created path to the vertex, if path creation is demanded. Note:
      The search depth does not need to be the depth of the vertex.

    - **paths:** A container object of class Paths. If path creation has been demanded,
      the container provides the found paths for all vertices visited so far. If labeled
      edges were provided, paths contain them instead of just vertices, if demanded.

    - **visited:** A collection that contains the vertices that have been visited so
      far, and the start vertices. When a finite graph has been fully traversed, it
      contains the vertices reachable from the start vertices.

      Note: TraversalTopologicalSort often visits vertices long before it reports them.
      Before it can report a vertex, it needs to report all the vertices, that the
      vertex depends on (directly or indirectly).

    If the graph contains a cycle that can be reached within the sorting process,
    a RuntimeError exception is raised, and the traversal provides the following
    additional attribute:

    - **cycle_from_start:** A cyclic path from a starting vertex.

    **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
    `go_for_vertices_in`, `go_to`.
    """

    def __init__(
        self,
        next_vertices: Optional[NextVertices] = None,
        *,
        next_edges: Optional[NextEdges] = None,
        is_tree: bool = False,
        vertex_to_id: Optional[VertexToID] = None,
    ) -> None:
        super().__init__(next_vertices, next_edges, is_tree, vertex_to_id)
        self.depth = None
        self.cycle_from_start = None

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edge_or_vertex,
            labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args

        # Copy traversal specific attributes (set by from_*) into method scope
        visited = self.visited

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        # Initialization
        self.depth = 0

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        # Get references of methods (avoid object resolution)
        visited_add = visited.add

        # Two separate implementations for the cases is_tree and not is_tree that follow
        # different concepts, because a combined approach makes both cases significantly
        # slower
        if is_tree:
            # Initialization
            to_visit = list(
                itertools.chain.from_iterable(
                    itertools.zip_longest(self._start_vertices, [])
                )
            )

            # Get references of methods (avoid object resolution)
            to_visit_extend = to_visit.extend
            to_visit_pop = to_visit.pop

            while to_visit:
                vertex = to_visit_pop()  # visit last added vertex first

                if vertex is not None:  # We "leave" and report the vertex
                    self.depth -= 1
                    yield vertex
                    continue

                # We "expand" the vertex
                vertex = to_visit[-1]

                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if labeled_edges else edge_or_vertex
                    n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor

                    if paths:
                        # We have to store the predecessor here, because at time of
                        # visit, it is already lost. And we cannot yield here,
                        # because only the first of the neighbors will indeed be
                        # visited next.
                        # But since the visiting order is defined by a stack we know
                        # that for each vertex, the predecessor stored last is the
                        # edge visited first, and after that no other predecessor can
                        # be stored for that vertex.
                        predecessors[n_id] = vertex
                        if edge_data_exists:
                            edge_data[n_id] = edge_or_vertex[1:]

                    to_visit_extend(
                        (neighbor, None)
                    )  # Vertex, and marker "not expanded so far"

                self.depth += 1
        else:
            # Initialization
            to_visit = list(self._start_vertices)  # list used as stack of todos
            trace_set = set()  # set of vertices along the current path

            # Get references of methods (avoid object resolution)
            to_visit_append = to_visit.append
            to_visit_pop = to_visit.pop
            trace_set_add = trace_set.add
            trace_set_discard = trace_set.discard

            while to_visit:
                vertex = to_visit[-1]  # visit or report last added vertex first
                v_id = vertex_to_id(vertex) if vertex_to_id else vertex

                if v_id in trace_set:
                    # Back to trace, from visits/reports of further vertices,
                    # that trace vertices depend on: We "leave" and report the head
                    # vertex of the trace.
                    self.depth -= 1
                    to_visit_pop()
                    trace_set_discard(v_id)
                    yield vertex
                    continue

                # Visit vertex, but not when marked as already visited.
                # Ignore this precondition for trees and start vertices.
                if self.depth > 0:
                    if v_id in visited:
                        to_visit_pop()
                        continue
                    visited_add(v_id)

                # Now, vertex belongs to trace from start. As long as this is so,
                # seeing it as neighbor would be a cycle.
                trace_set_add(v_id)

                # We "expand" the vertex
                if calculation_limit and not (
                    calculation_limit := calculation_limit - 1
                ):
                    raise RuntimeError("Number of visited vertices reached limit")

                for edge_or_vertex in next_edge_or_vertex(vertex, self):
                    neighbor = edge_or_vertex[0] if labeled_edges else edge_or_vertex
                    n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor

                    if n_id in trace_set:
                        # We found a dependency (edge) back to a vertex, whose
                        # dependencies we are currently following (trace). We build
                        # and report this trace.
                        trace = list()
                        for vertex in to_visit:
                            v_id = vertex_to_id(vertex) if vertex_to_id else vertex
                            if v_id in trace_set:
                                trace.append(vertex)
                        trace.append(neighbor)
                        self.cycle_from_start = trace
                        raise RuntimeError("Graph contains cycle")

                    if n_id in visited:
                        continue

                    if paths:
                        # We have to store the predecessor here, because at time of
                        # visit, it is already lost. And we cannot yield here,
                        # because only the first of the neighbors will indeed be
                        # visited next.
                        # But since the visiting order is defined by a stack we know
                        # that for each vertex, the predecessor stored last is the
                        # edge visited first, and after that no other predecessor can
                        # be stored for that vertex.
                        predecessors[n_id] = vertex
                        if edge_data_exists:
                            edge_data[n_id] = edge_or_vertex[1:]

                    to_visit_append(neighbor)

                self.depth += 1


# --------------- traversal strategies for weighted graphs -------------


class TraversalShortestPaths(_TraversalWithLabels):
    """
    :param next_edges: See `NextEdges` function.

    :param is_tree: bool: If it is sure, that during each traversal run, each vertex can
       be reached only once, is_tree can be set to True. This improves performance,
       but attribute *distances* of the traversal will not be updated during and after
       the traversal.

    :param vertex_to_id: See `VertexToID` function.

    **Algorithm:** Shortest paths algorithm of Dijkstra, non-recursive, based on heap.

    **Properties:** Vertices are visited and reported ordered by increasing distance
    (minimally necessary sum of edge weights) from a start vertex. Each vertex is
    visited only once.

    **Input:** Directed graph. One ore more start vertices. Vertices must be
    hashable, or hashable id can be provided. Labeled edges, first field (after
    to_vertex) is weight, weight needs to be non-negative. Optional calculation limit.

    **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
    next_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides the following attributes:

    - **distance:** The length of the shortest path (sum of edge weights) from a
      start vertex to the visited vertex

    - **depth:** At this search depth, the reported vertex has been found. It equals
      the edge count of the created path to the vertex, if path creation is demanded.
      Note: The search depth does not need to be the depth of the vertex.

    - **paths:** A container object of class Paths. If path creation has been
      demanded, the container provides a shortest path for all vertices visited so far.
      If labeled edges were provided, paths contain them instead of just vertices,
      if demanded.

    - **distances:** A dictionary. For the vertices that have already been visited,
      it contains their distance.

      Note: Typically, it contains values for some other vertices, too. These
      might not be final and could change until the respective vertex is visited.

      When a finite graph has been fully traversed, it contains the distances of all
      vertices that are reachable from the start vertices.

    **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
    `go_for_vertices_in`, `go_to`.
    """

    def __init__(
        self,
        next_edges: NextEdges,
        *,
        is_tree: bool = False,
        vertex_to_id: Optional[VertexToID] = None,
    ) -> None:
        super().__init__(next_edges, is_tree, vertex_to_id)
        self.distance = None
        self.depth = None
        self.distances: Optional[dict] = None

    def start_from(
        self,
        start_vertex: Optional[Vertex] = None,
        *,
        start_vertices: Optional[Iterable[Vertex]] = None,
        build_paths: bool = False,
        labeled_paths: bool = False,
        calculation_limit: Optional[int] = None,
        known_distances: Optional[dict[Hashable, Real]] = None,
    ) -> TraversalShortestPaths:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices (iterator) the search should start
            at. Only allowed if start_vertex equals None.

        :param build_paths: If true, build paths from start vertices for each visited
            vertex.

        :param labeled_paths: If true, integrate edge data in generated paths,
            not only vertices.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param known_distances: If provided, this dict is used instead of an internal
            one to keep the distances of vertices that have already been visited (resp.
            their hashable ids from vertex_to_id is used as key) from some start vertex.
            For vertices without known distance, it must yield float('infinity'). The
            internal default implementation uses a collections.defaultdict. Typical use
            cases are: 1) pre-loading known distances of vertices, and the vertices
            should not be visited if no smaller distance is found during the traversal,
            or 2) getting online access to the internal bookkeeping of visited vertices
            and their distances, or 3) for providing your own way for storing the
            distance of a vertex that has already been visited (if you do that in your
            own graph structure instead of a dict, visited_vertices needs to provide the
            methods __contains__, __getitem__ and __setitem__).

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            labeled_paths,
            calculation_limit,
        )
        self.distance = None
        self.depth = None
        self.distances = known_distances
        super()._start()
        return self

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edges,
            _labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given.
        if self.distances is None:
            infinity = float("infinity")
            self.distances = collections.defaultdict(lambda: infinity)
        distances = self.distances

        # So far, the start vertices are to be visited. Each has distance 0 from a
        # start vertex (itself), if not defined otherwise, an edge count of 0,
        # and a path, if one is required, consisting of only the vertex itself.
        start_vertices_and_ids = tuple(
            (vertex, vertex_to_id(vertex) if vertex_to_id else vertex)
            for vertex in self._start_vertices
        )

        for vertex, vertex_id in start_vertices_and_ids:
            distances.setdefault(vertex_id, 0)  # set to 0, if not already set

        # Unique number, that prevents heapq from sorting by vertices in case of a
        # tie in the sort field, because vertices do not need to be pairwise
        # comparable. The integers from -5 to 256 are used first, because they are
        # internalized (pre-calculated, and thus fastest). We count downwards like we
        # do in A* search. There, it is preferable, because a LIFO behavior makes A*
        # often faster. Here, we do it simply to do it the same way.
        unique_no = itertools.count(256, -1)
        to_visit = [  # used as collection.heapq of tuples, lowest distance first
            (distances[vertex_id], next(unique_no), vertex, 0)
            for vertex, vertex_id in start_vertices_and_ids
        ]
        heapify(to_visit)

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        while to_visit:
            # Visit path with lowest distance first
            path_weight, _, vertex, path_edge_count = heappop(to_visit)

            # A vertex can get added to the heap multiple times. We want to process
            # it only once, the first time it is removed from the heap, because this
            # is the case with the least distance from start.
            if not is_tree:
                v_id = vertex_to_id(vertex) if vertex_to_id else vertex
                if path_weight > distances[v_id]:
                    continue
                # (Allow garbage collector to free distance value if nowhere else
                # needed any more)
                distances[v_id] = 0

            # Export traversal data to traversal attributes
            self.distance = path_weight
            self.depth = path_edge_count

            # We now know the distance of the vertex, so we report it.
            if path_edge_count > 0:  # do not yield start vertex
                yield vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            n_path_edge_count = path_edge_count + 1
            for edge in next_edges(vertex, self):
                neighbor, weight = edge[0], edge[1]
                n_path_weight = path_weight + weight

                # If, so far, we have not found a shorter path to the neighbor than the
                # new one that ends with the edge, this path is a candidate for a
                # shortest path to the neighbor. We push it to the heap.
                if paths or not is_tree:
                    n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor

                    if not is_tree:
                        if distances[n_id] <= n_path_weight:
                            continue
                        distances[n_id] = n_path_weight

                    # If we are to generate a path, we have to do it here, since the
                    # edge we have to add to the path prefix is not stored on the heap
                    if paths:
                        predecessors[n_id] = vertex
                        if edge_data_exists:
                            edge_data[n_id] = edge[1:]

                heappush(
                    to_visit,
                    (
                        n_path_weight,
                        next(unique_no),
                        neighbor,
                        n_path_edge_count,
                    ),
                )

    def go_for_distance_range(self, start: int, stop: int) -> VertexIterator:
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
        def my_generator():
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


class TraversalAStar(_TraversalWithLabels):
    """
    :param next_edges: See `NextEdges` function.

    :param is_tree: bool: If it is sure, that during each traversal run, each vertex can
       be reached only once, is_tree can be set to True. This improves performance,
       but attribute *path_length_guesses* of the traversal will not be updated during
       the traversal.

    :param vertex_to_id: See `VertexToID` function.

    **Algorithm:** The search algorithm A*, non-recursive, based on heap.

    **Input:** Weighted directed graph. Only non-negative edge weights. One or more
    start vertices. Vertices must be hashable, but need not to be comparable. A
    heuristic function that estimates the cost of the cheapest path from a given
    vertex to the goal (resp. to any of your goal vertices, if you have more than
    one), and never overestimates the actual needed costs ("admissible heuristic
    function"). Optionally, a calculation limit.

    **Properties:** Vertices are visited and reported ordered by increasing path
    length (sum of edge weights) of the shortest path from a start vertex to the
    visited vertex that have been found so far (!).

    When the goal is visited, the reported path is a shortest path from start to goal
    and the reported length is the distance of the goal from start.

    In case the used heuristic function is consistent, i.e. following an edge from
    one vertex to another never reduces the estimated costs to get to the goal by
    more than the weight of the edge, further guarantees hold: Each vertex is only
    visited once. And for each visited vertex, the yielded path length and edge count
    (and optionally, the path) are the data of the shortest existing path from start
    (not only from the shortest path found so far).

    **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
    next_edges) or *reported* (an iterator of the traversal returns it),
    the traversal provides the following attributes:

    - **path_length:** Length of the found path to the vertex (for the goal vertex: a
      shortest path)

    - **depth:** At this search depth, the reported vertex has been found. It equals
      the edge count of the created path to the vertex, if path creation is demanded.
      Note: The search depth does not need to be the depth of the vertex.

    - **paths:** A container object of class Paths.  If path creation has been
      demanded, the container provides the generated paths for all vertices visited so
      far. If labeled edges were provided, paths contain them instead of just vertices,
      if demanded.

    **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
    `go_for_vertices_in`, `go_to`.
    """

    def __init__(
        self,
        next_edges: NextEdges,
        *,
        is_tree: bool = False,
        vertex_to_id: Optional[VertexToID] = None,
    ) -> None:
        super().__init__(next_edges, is_tree, vertex_to_id)
        self.path_length = None
        self.depth = None

        self._heuristic: Optional[Callable] = None
        self._known_distances: Optional[dict] = None
        self._known_path_length_guesses: Optional[dict] = None

    def start_from(
        self,
        heuristic: Callable[[Vertex], Real],
        start_vertex: Optional[Vertex] = None,
        *,
        start_vertices: Optional[Iterable[Vertex]] = None,
        build_paths: bool = False,
        labeled_paths: bool = False,
        calculation_limit: Optional[int] = None,
        known_distances: Optional[dict[Hashable, Real]] = None,
        known_path_length_guesses: Optional[dict[Hashable, Real]] = None,
    ) -> TraversalAStar:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param heuristic: The admissible and consistent heuristic function that
            estimates the cost of the cheapest path from a given vertex to the goal
            (resp. one of the goals).

        :param start_vertex: The vertex the search should start at. Provide either
            start_vertex or start_vertices, but not both.

        :param start_vertices: The set of vertices (iterator) the search should start
            at. Provide either start_vertex or start_vertices, but not both.

        :param build_paths: If true, build paths from start vertices for each visited
            vertex.

        :param labeled_paths: If true, integrate edge data in generated paths, not only
            vertices.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :param known_distances: If provided, this dict is used instead of an internal
            one to keep the distances of vertices that have already been visited (
            resp. their hashable ids from vertex_to_id is used as key) from some
            start vertex. For vertices without known distance, it must yield float(
            'infinity'). The internal default implementation uses a
            collections.defaultdict. Typical use cases are: 1) pre-loading known
            distances of vertices, and the vertices should not be visited if no
            smaller distance is found during the traversal, or 2) getting online
            access to the internal bookkeeping of visited vertices and their
            distances, or 3) for providing your own way for storing the distance of a
            vertex that has already been visited (if you do that in your own graph
            structure instead of a dict, visited_vertices needs to provide the
            methods __contains__, __getitem__ and __setitem__).

        :param known_path_length_guesses: Like known_distances, but for keeping the sum
            distance+heuristic for vertices.

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            labeled_paths,
            calculation_limit,
        )
        self.path_length = None
        self.depth = None
        self._heuristic = heuristic
        self._known_distances = known_distances
        self._known_path_length_guesses = known_path_length_guesses
        super()._start()
        return self

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edges,
            _labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args

        # copy traversal specific attributes from parameters into method scope (faster
        # access)
        heuristic = self._heuristic

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        # At start, most of the distances from a vertex to a start vertex are not
        # known. If accessed for comparison for possibly better distances, infinity
        # is used, if no other value is given.
        distances = self._known_distances
        if distances is None:
            infinity = float("infinity")
            distances = collections.defaultdict(lambda: infinity)

        path_length_guesses = self._known_path_length_guesses
        if path_length_guesses is None:
            infinity = float("infinity")
            path_length_guesses = collections.defaultdict(lambda: infinity)

        # So far, the start vertices are to be visited. Each has distance 0 from a
        # start vertex (itself), if not defined otherwise, an edge count of 0,
        # and a path, if one is required, consisting of only the vertex itself.
        start_vertices_and_ids = tuple(
            (vertex, vertex_to_id(vertex) if vertex_to_id else vertex)
            for vertex in self._start_vertices
        )

        for vertex, vertex_id in start_vertices_and_ids:
            distances.setdefault(vertex_id, 0)  # set to 0, if not already set
            path_length_guesses.setdefault(
                vertex_id, distances[vertex_id] + heuristic(vertex)
            )

        # Unique number, that prevents heapq from sorting by vertices in case of a
        # tie in the sort field, because vertices do not need to be pairwise
        # comparable. The numbers are generated in decreasing order to make the min
        # heap behave like a LIFO queue in case of ties. The integers from -5 to 256
        # are used first, because they are internalized (pre-calculated, and thus
        # fastest).
        unique_no = itertools.count(256, -1)
        to_visit = [  # used as collection.heapq of tuples, lowest distance first
            (path_length_guesses[vertex_id], next(unique_no), vertex, 0)
            for vertex, vertex_id in start_vertices_and_ids
        ]
        heapify(to_visit)

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        while to_visit:
            # Visit path with lowest distance first
            path_length_guess, _, vertex, path_edge_count = heappop(to_visit)

            # A vertex can get added to the heap multiple times.

            # For consistent heuristics: We want to process the vertex only once, the
            # first time it is removed from the heap, because this is the case with the
            # least distance estimation. If the heuristic is not consistent: Only when
            # the new distance estimation is better than the best found so far, we want
            # to process the vertex again.
            v_id = vertex_to_id(vertex) if vertex_to_id else vertex
            if not is_tree and path_length_guess > path_length_guesses[v_id]:
                continue

            path_weight = distances[v_id]

            # Export traversal data to traversal attributes
            self.path_length = path_weight
            self.depth = path_edge_count

            # We now know the distance of the vertex, so we report it.
            if path_edge_count > 0:  # do not yield start vertex
                yield vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            n_path_edge_count = path_edge_count + 1
            for edge in next_edges(vertex, self):
                neighbor, weight = edge[0:2]
                n_path_weight = path_weight + weight

                # If the new found path to the neighbor is longer than the shortest
                # found so far, we can safely ignore the new path. Otherwise, it is a
                # new candidate for a
                # shortest path to the neighbor, and we push it to the heap.
                n_id = vertex_to_id(neighbor) if vertex_to_id else neighbor
                if not is_tree and distances[n_id] <= n_path_weight:
                    continue

                distances[n_id] = n_path_weight

                # If we are to generate a path, we have to do it here, since the edge
                # we have to add to the path prefix is not stored on the heap
                if paths:
                    predecessors[n_id] = vertex
                    if edge_data_exists:
                        edge_data[n_id] = edge[1:]

                n_guess = n_path_weight + heuristic(neighbor)
                if not is_tree:
                    path_length_guesses[n_id] = n_guess
                heappush(
                    to_visit,
                    (n_guess, next(unique_no), neighbor, n_path_edge_count),
                )


class TraversalMinimumSpanningTree(_TraversalWithLabels):
    """
    :param next_edges: See `NextEdges` function.

    :param vertex_to_id: See `VertexToID` function.

    **Algorithm:**  Minimum spanning tree ("MST") algorithm of Jarnik, Prim, Dijkstra.
    Non-recursive, based on heap. A so-called *tie breaker* is implemented, that
    prioritizes edges that have been found more recently about edges that have been
    found earlier. This is a typical choice that often improves search performance.

    **Properties:** Only edges of the MST from start vertices are reported. Each
    vertex is visited only once.

    **Input:** Weighted undirected graph, given as directed edges with the same
    weight in both directions. One or more start vertices (e.g. for components in
    unconnected graphs). Labeled edges, first field (after to_vertex) is weight.
    Optional calculation limit.

    **Attributes:** When a vertex is *expanded* (traversal calls next_vertices or
    next_edges) or an edge is *reported* (an iterator of the traversal returns the
    vertex it leads to), the traversal provides the following attributes:

    - **edge:** Tuple of from_vertex, to_vertex, the weight of the edge,
      and additional data you have provided with the edge

    - **paths:** A container object of class Paths. If path creation has been
      demanded, the container provides a path within the MST from a start vertex to
      each of the vertices visited so far. If labeled edges were provided,
      paths contain them instead of just vertices, if demanded.

    **Inherited methods:** from `Traversal`: `__iter__`, `__next__`,
    `go_for_vertices_in`, `go_to`.
    """

    def __init__(
        self,
        next_edges: NextEdges,
        *,
        vertex_to_id: Optional[VertexToID] = None,
    ) -> None:
        super().__init__(next_edges, False, vertex_to_id)
        self.edge = None

    def start_from(
        self,
        start_vertex: Optional[Vertex] = None,
        *,
        start_vertices: Optional[Iterable[Vertex]] = None,
        build_paths: bool = False,
        labeled_paths: bool = False,
        calculation_limit: Optional[int] = None,
    ) -> TraversalMinimumSpanningTree:
        """
        Start the traversal at a vertex or a set of vertices and set parameters.

        :param start_vertex: The vertex the search should start at. If None, provide
            start_vertices.

        :param start_vertices: The set of vertices (iterator) the search should start
            at. Only allowed if start_vertex equals None. Leads to a result
            consisting of several trees that are only connected if the start vertices
            are connected.

        :param build_paths: If true, build paths from start vertices for each visited
            vertex.

        :param labeled_paths: If true, integrate edge data in generated paths, not only
            vertices.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

        :return: Traversal, that has been started, e.g., the methods go* can now be
            used.
        """

        if not isinstance(type(self), type(Traversal)):
            raise RuntimeError(
                "Method start_from can only be called on a Traversal object."
            )

        self._start_from(
            start_vertex,
            start_vertices,
            build_paths,
            labeled_paths,
            calculation_limit,
        )
        self.edge = None
        super()._start()
        return self

    def _traverse(self, *args):
        # copy general traversal attributes from parameters into method scope (faster
        # access)
        (
            next_edges,
            _labeled_edges,
            is_tree,
            vertex_to_id,
            calculation_limit,
            paths,
            predecessors,
            edge_data,
        ) = args

        # Create booleans (avoid checks with "is")
        edge_data_exists = edge_data is not None

        # At start, only the start vertices are regarded as visited
        visited = set(_iter_start_ids(self._start_vertices, vertex_to_id))

        # Check if we we already go over the calculation limit when we evaluate the
        # edges from start vertices ("expanding the start vertices"). This avoids a
        # step by step check that slows down the to_visit loop for large sets of
        # start vertices. Note: A calculation limit below 0 leads nowhere ever to an
        # exception. Also here.
        if calculation_limit is not None and calculation_limit >= 0:
            if (calculation_limit := calculation_limit - len(self._start_vertices)) < 0:
                raise RuntimeError("Number of visited vertices reached limit")

        # So far, the edges from the start vertices are to be visited as candidates
        # for edges of a MST. (Unique number prevents heapq from sorting by (possibly
        # not comparable) fields)
        unique_no = itertools.count()
        to_visit = [  # used as collection.heapq, lowest edge weight first
            (edge[1], next(unique_no), vertex, edge)
            for vertex in self._start_vertices
            for edge in next_edges(vertex, self)
        ]
        heapify(to_visit)

        # Get references of methods (avoid object resolution)
        visited_add = visited.add

        if calculation_limit is not None:
            calculation_limit += 1  # allows for limit check by zero check

        while to_visit:
            # Visit edge with lowest weight first
            _weight, _, vertex, to_edge = heappop(to_visit)
            to_vertex = to_edge[0]

            # A vertex can get added to the heap multiple times, as end vertex of
            # several edges. We want to process it only once, as end vertex of a MST
            # edge.
            to_id = vertex_to_id(to_vertex) if vertex_to_id else to_vertex
            if to_id in visited:
                continue

            # The shortest edge from a visited vertex that leads to a vertex not
            # visited so far, must be an edge of the MST.
            visited_add(to_id)

            if paths:
                predecessors[to_id] = vertex
                if edge_data_exists:
                    _, *l_edge_data = to_edge
                    edge_data[to_id] = l_edge_data

            # Export traversal data to traversal attribute and report vertex
            self.edge = (vertex,) + to_edge
            yield to_vertex

            if calculation_limit and not (calculation_limit := calculation_limit - 1):
                raise RuntimeError("Number of visited vertices reached limit")

            for n_to_edge in next_edges(to_vertex, self):
                n_to_vertex, n_weight = n_to_edge[0], n_to_edge[1]
                # If the edge leads to a vertex that is, so far, not reached by edges
                # of the MST, it is a candidate for a MST edge. We push it to the heap.
                n_to_id = vertex_to_id(n_to_vertex) if vertex_to_id else n_to_vertex
                if n_to_id not in visited:
                    heappush(
                        to_visit,
                        (n_weight, next(unique_no), to_vertex, n_to_edge),
                    )
