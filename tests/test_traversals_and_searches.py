import collections
import textwrap
import sys
from abc import abstractmethod, ABC
from collections.abc import Callable, Hashable, Iterator
from typing import Any, Iterable, Union, TypeVar, Optional, Protocol, Generic

import nographs as nog
from nographs import T, Strategy, T_vertex, T_vertex_id, T_labels, T_weight

# noinspection PyProtectedMember
from nographs._compatibility import pairwise

# noinspection PyProtectedMember
from nographs._strategies import StrRepr  # NOQA F401 (import needed by doc tests)

# ----- Utilities: Printing test results -----


def eprint(*args: Any, **kwargs: Any) -> None:
    """Print to stderr. For typing see print.
    Untyped, because type is overly complex."""
    print(*args, file=sys.stderr, **kwargs)


def print_filled(s: str) -> None:
    """Wrap output to a length that fits into a doubly indented block"""
    print(textwrap.fill(s, 88 - 8, subsequent_indent="  "))


# ----- Utilities: Test procedures printing traversal and search results -----

T_bound_comparable = TypeVar("T_bound_comparable", bound="Comparable")


class Comparable(Protocol):
    @abstractmethod
    def __lt__(self: T_bound_comparable, other: T_bound_comparable) -> bool:
        ...


class HashableComparable(Hashable, Comparable, Protocol):
    pass


T_sortable_vertex = TypeVar("T_sortable_vertex", bound=HashableComparable)

TraversalWithDepthAndVisited = Union[
    nog.TraversalBreadthFirstFlex[T_sortable_vertex, T_vertex_id, T_labels],
    nog.TraversalDepthFirstFlex[T_sortable_vertex, T_vertex_id, T_labels],
    nog.TraversalNeighborsThenDepthFlex[T_sortable_vertex, T_vertex_id, T_labels],
    nog.TraversalTopologicalSortFlex[T_sortable_vertex, T_vertex_id, T_labels],
]


def _results_of_traversal(
    traversal: nog.Traversal[T_sortable_vertex, T_vertex_id, T_labels],
    start_vertices: Iterable[T_sortable_vertex],
) -> dict[str, Any]:
    """Completely traverse graph and print each state, collect vertices, check
    that path container remains the same object, print all paths, return
    original content of __dict__ of traversal object (caller can use this
    for further checks)."""
    vertices = set(start_vertices)
    # get traversal attributes before iterator starts, for comparison
    org_dict = dict(traversal.__dict__)
    print_filled(f"After start: {traversal.state_to_str(vertices)}")
    for vertex in traversal:
        vertices.add(vertex)
        print_filled(f"-> {vertex}: {traversal.state_to_str([vertex])}")
        if org_dict["paths"] is not traversal.paths:
            print("traversal.paths before and while traversal differ!")
    # noinspection PyProtectedMember
    if traversal._build_paths:
        print("All paths:", [traversal.paths[vertex] for vertex in sorted(vertices)])
    return org_dict


def results_standard(
    traversal: nog.Traversal[T_sortable_vertex, T_vertex_id, T_labels],
    start_vertices: Iterable[T_sortable_vertex],
) -> None:
    """Completely traverse graph and print each state, collect vertices, check
    that path container remains the same object, print all paths.
    """
    _ = _results_of_traversal(traversal, start_vertices)


def results_with_visited(
    traversal: TraversalWithDepthAndVisited[T_sortable_vertex, T_vertex_id, T_labels],
    start_vertices: Iterable[T_sortable_vertex],
) -> None:
    """Completely traverse graph and print each state, collect vertices, check
    that path container remains the same object, print all paths.
    Additionally, print visited container and check that it remained the same object
    during traversal.
    """
    org_dict = _results_of_traversal(traversal, start_vertices)
    if org_dict["visited"] is not traversal.visited:
        print("traversal.visited before and while traversal differ!")
    visited = list(traversal.visited)
    visited.sort()
    print("All visited:", visited)


def results_with_distances(
    traversal: nog.TraversalShortestPathsFlex[
        T_sortable_vertex, T_vertex_id, T_weight, T_labels
    ],
    start_vertices: Iterable[T_sortable_vertex],
) -> None:
    """Completely traverse graph and print each state, collect vertices, check
    that path container remains the same object, print all paths.
    Additionally, print distances container and check that it remained the same object
    during traversal.
    """
    org_dict = _results_of_traversal(traversal, start_vertices)
    if org_dict["distances"] is not traversal.distances:
        print("traversal.distances before and while traversal differ!")
    print("All distances:", str(dict(traversal.distances)))


def print_partial_results(
    traversal: nog.Traversal[T_sortable_vertex, T_vertex_id, T_labels],
    paths_to: Optional[T_sortable_vertex] = None,
) -> None:
    """Completely traverse graph, collect reported vertices, and print the
    fist 5 and the last 5. Print path prefixes and suffixes for vertices given
    as parameter.
    """
    vertices = []
    for vertex in traversal:
        vertices.append(vertex)
    print(vertices[:5], vertices[-6:])
    if paths_to is not None:
        path = traversal.paths[paths_to]
        print(tuple(path[:2]), tuple(path[-2:]))


# ----- Utilities: Tesult checking -----


def check_path(
    vertex_iterable: Iterable[T_vertex],
    next_edges: Callable[[T_vertex, Any], Iterable[tuple]],
) -> None:
    """Check if each edge in the path described by the vertex_iterable is
    allowed according to the given next_edges function.
    """
    for v, w in pairwise(vertex_iterable):
        if w not in (w for w, *more in next_edges(v, None)):
            print("path invalid from", v, "to", w)
            return


# ----- Utilities: Creation of adjacency functions that report the search states -----


def adj_funcs_bi_from_list(
    edge_list: Iterable,
    edge_data: bool,
    report_steps: bool = True,
    vertex_to_key: Callable = nog.vertex_as_id,
) -> tuple[
    Callable[[T_vertex, Strategy], Iterable], Callable[[T_vertex, Strategy], Iterable]
]:
    """Create NextEdges function for forward and for backward direction, based
    on an Iterable of edges. When a vertex is expanded, this is printed to std out,
    if demanded.

    If options edge_data is given, weights and/or labels provided in an edge are also
    given by the generated NextEdges functions. Otherwise, NextVertices functions are
    generated.

    If the vertices in the edge_list are not hashable, the argument to parameter
    vertex_to_key need to be a function that returns a hashable key for a vertex,
    where no two vertices have the same key.
    """
    edge_dict_forwards = collections.defaultdict(list)
    edge_dict_backwards = collections.defaultdict(list)
    if edge_data:
        for edge in edge_list:
            v, w, *others = edge
            edge_dict_forwards[vertex_to_key(v)].append((w, *others))
            edge_dict_backwards[vertex_to_key(w)].append((v, *others))
    else:
        for edge in edge_list:
            v, w, *others = edge
            edge_dict_forwards[vertex_to_key(v)].append(w)
            edge_dict_backwards[vertex_to_key(w)].append(v)

    if report_steps:

        def next_edges_forwards(vertex: T_vertex, strategy: Strategy) -> Iterable:
            print_filled(f"? {vertex}: {strategy.state_to_str([vertex])}")
            return edge_dict_forwards.get(vertex_to_key(vertex), [])

        def next_edges_backwards(vertex: T_vertex, strategy: Strategy) -> Iterable:
            print_filled(f"?<{vertex}: {strategy.state_to_str([vertex])}")
            return edge_dict_backwards.get(vertex_to_key(vertex), [])

    else:

        def next_edges_forwards(vertex: T_vertex, strategy: Strategy) -> Iterable:
            return edge_dict_forwards.get(vertex_to_key(vertex), [])

        def next_edges_backwards(vertex: T_vertex, strategy: Strategy) -> Iterable:
            return edge_dict_backwards.get(vertex_to_key(vertex), [])

    return next_edges_forwards, next_edges_backwards


# ----- Test fixtures (here: graphs and special vertices -----


def first_of(lst: list[T]) -> T:
    """VertexToID function for test graphs that use [v] as vertices and v
    as vertex id.
    """
    return lst[0]


infinity = float("infinity")

V = TypeVar("V")
E = TypeVar("E", bound=tuple)


class Fixture(ABC, Generic[V, E]):
    """Basic test fixture. Provides adjacency function next_vertices and
    a start vertex.
    """

    def __init__(self, start: V):
        self.start = start

    next_edges: Callable[[V, Strategy], Iterable[E]]


class FixtureFull(Fixture[V, E]):
    """Test fixture. Provides adjacency functions next_vertices,
    next_vertices_bi, next_edges, and next_edges_bi for some given edges.
    Optionally, these functions report their state. Optionally, a vertex_to_key
    function can be used, e.g., if vertices are not hashable.
    Additionally, a start vertex, goal vertex and a heuristic function for
    A* traversals are set.
    """

    def __init__(
        self,
        edges: Iterable[E],
        start: V,
        goal: V,
        heuristic: Callable[[V], Union[int, float]],
        report: bool = False,
        vertex_to_key: Callable = nog.vertex_as_id,
    ):
        super().__init__(start)
        self.edges = edges
        self.goal = goal
        self.heuristic = heuristic

        self.start_bi = (start, goal)

        self.next_vertices_bi = adj_funcs_bi_from_list(
            edges, edge_data=False, report_steps=report, vertex_to_key=vertex_to_key
        )
        self.next_vertices = self.next_vertices_bi[0]

        self.next_edges_bi = adj_funcs_bi_from_list(
            edges, edge_data=True, report_steps=report, vertex_to_key=vertex_to_key
        )
        self.next_edges = self.next_edges_bi[0]


class FNoEdgesGoalUnreachable(FixtureFull[int, tuple]):
    """Zero edges graph, goal not reachable"""

    def __init__(self) -> None:
        super().__init__([], 0, 1, lambda v: 0, report=True)


class FNoEdgesGoalIsStart(FixtureFull[int, tuple]):
    """Zero edges graph, start equals goal"""

    def __init__(self) -> None:
        super().__init__([], 0, 0, lambda v: 0, report=True)


class FOneEdgeNoData(FixtureFull[int, tuple[int, int]]):
    """One-edge graph with edge from start to goal, no weights, no labels"""

    def __init__(self) -> None:
        super().__init__([(0, 1)], 0, 1, lambda v: 1 if v == 0 else 0)


class FOneEdgeWeighted(FixtureFull[int, tuple[int, int, int]]):
    """One-edge graph with edge from start to goal, weight 1, no labels"""

    def __init__(self) -> None:
        super().__init__([(0, 1, 1)], 0, 1, lambda v: 1 if v == 0 else 0)


class FOneEdgeLabeled(FixtureFull[int, tuple[int, int, int]]):
    """One-edge graph with edge from start to goal, no weights, label 2"""

    def __init__(self) -> None:
        super().__init__([(0, 1, 2)], 0, 1, lambda v: 1 if v == 0 else 0)


class FOneEdgeWeightedLabeled(FixtureFull[int, tuple[int, int, int, int]]):
    """One-edge graph with edge from start to goal, weight 1, label 2"""

    def __init__(self) -> None:
        super().__init__([(0, 1, 1, 2)], 0, 1, lambda v: 1 if v == 0 else 0)


class FOneEdgeUnhashable(FixtureFull[list[int], tuple[list[int], list[int], int, int]]):
    """One-edge graph - vertices are list[int]"""

    def __init__(self) -> None:
        super().__init__(
            [([0], [1], 1, 2)],
            [0],
            [1],
            lambda v: 1 if v == [0] else 0,
            vertex_to_key=first_of,
        )


class FSequenceUnhashable(
    FixtureFull[list[int], tuple[list[int], list[int], int, int]]
):
    """Linear graph of fixed size - vertices are list[int]"""

    def __init__(self) -> None:
        super().__init__(
            [([i], [i + 1], 1, i + 1) for i in range(4)],
            [0],
            [3],
            lambda v: 1 if v == [0] else 0,  # very rough heuristic
            vertex_to_key=first_of,
        )
        self.goals = ([1], [3])
        self.goal_impossible = [5]
        self.goals_impossible = (self.goal_impossible,)
        self.start_impossible_bi = (self.start, self.goal_impossible)


class FDiamond(FixtureFull[int, tuple[int, int, int]]):
    """Diamond-shaped graph of fixed size. Variant with weight 2 from vertices 1 and
    2 to 3 (useful foo TraversalShortestPaths). Edges can be interpreted as being
    labeled instead of weighed. Additionally, a vertex for a test with this vertex
    as already visited vertex is given.
    """

    def __init__(self) -> None:
        super().__init__(
            [(0, 1, 2), (0, 2, 1), (1, 3, 2), (2, 3, 2)],
            0,
            3,
            lambda v: 1 if v == 0 else 0,
            report=True,
        )
        self.vertex_for_already_visited = 1
        self.values_for_known_distances = ((0, 2), (1, 0))


class FDiamondSorted(FixtureFull[int, tuple[int, int, int]]):
    """Diamond-shaped graph of fixed size. Variant with sorted edges (as needed by
    TraversalShortestPathsInfBranchingSorted). No heuristic is given, since it is
    not used for this strategy.
    """

    def __init__(self) -> None:
        super().__init__(
            [(0, 2, 1), (0, 1, 2), (1, 3, 2), (2, 3, 2)], 0, 3, lambda v: 0, report=True
        )


class FDiamond2(FixtureFull[int, tuple[int, int, int]]):
    """Diamond-shaped graph of fixed size. Variant with weight 3 from vertices 1 and
    2 to 3 (used for MST). No heuristic is given, since it is not used for A*.
    """

    def __init__(self) -> None:
        super().__init__(
            [(0, 1, 2), (0, 2, 1), (1, 3, 3), (2, 3, 3)], 0, 3, lambda v: 0, report=True
        )


class FAStar(FixtureFull[int, tuple[int, int, int]]):
    """A* test graph."""

    def __init__(self) -> None:
        super().__init__(
            [(0, 1, 3), (0, 2, 3), (0, 4, 1), (1, 3, 3), (2, 3, 2)],
            0,
            3,
            lambda v: {0: 6, 1: 1, 2: 2, 3: 0, 4: infinity}[v],
            report=True,
        )
        self.values_for_known_distances = ((0, 2), (1, 0))


class FBSearchShortestPath(FixtureFull[int, tuple[int, int, int]]):
    """Additional test graph for BSearchShortestPath"""

    def __init__(self) -> None:
        super().__init__(
            [(0, 1, 50), (1, 4, 50), (0, 2, 30), (2, 3, 30), (3, 4, 30)],
            0,
            4,
            lambda v: 0,
            report=True,
        )


class FSmallBinaryTree(FixtureFull[int, tuple[int, int, int]]):
    """Graphs forming a binary tree with just 6 vertices. Outgoing edges are sorted
    by ascending weight."""

    def __init__(self) -> None:
        super().__init__(
            [(1, 2, 2), (1, 3, 3), (2, 4, 4), (2, 5, 5), (3, 6, 6), (3, 7, 7)],
            1,
            4,
            lambda v: {6: 0, 3: 3}.get(v, 11),
            report=True,
        )


class FMultiStart(FixtureFull[int, tuple[int, int, int]]):
    """Graph for testing multiple start vertices. Used for all strategies
    except of A* and the bidirectional search strategies. Outgoing edges
    are sorted by ascending weight, since all weights are equal."""

    def __init__(self) -> None:
        super().__init__(
            [
                (0, 1, 1),
                (1, 2, 1),
                (5, 6, 1),
                (6, 3, 1),
                (2, 3, 1),
                (2, 4, 1),
                (3, 4, 1),
            ],
            -1,
            4,
            lambda v: {6: 0, 3: 3}.get(v, 11),
            report=True,
        )
        self.start_vertices = (0, 5)
        self.goal_vertices = (4,)


class FMultiStartAStar(FixtureFull[int, tuple[int, int, int]]):
    """Graph for testing multiple start vertices. Used for all strategies
    except of A* and the bidirectional search strategies."""

    def __init__(self) -> None:
        super().__init__(
            [(0, 2, 1), (1, 3, 1), (1, 4, 1), (2, 3, 1), (3, 5, 1)],
            -1,
            -1,
            lambda v: {0: 3, 1: 2, 2: 2, 3: 1, 4: 9, 5: 0}[v],
            report=True,
        )
        self.start_vertices = (0, 1)


class FMultiStartB(FixtureFull[int, tuple[int, int, int]]):
    """Graph for testing multiple start vertices. Used for bidirectional
    search strategies."""

    def __init__(self) -> None:
        super().__init__(
            [
                (0, 1, 1),
                (1, 2, 1),
                (5, 6, 1),
                (6, 3, 2),
                (2, 3, 1),
                (2, 4, 2),
                (3, 4, 1),
            ],
            -1,
            4,
            lambda v: {6: 0, 3: 3}.get(v, 11),
            report=True,
        )
        self.start_vertices = (0, 5)
        self.goal_vertices = (4,)
        self.start_vertices_bi = (self.start_vertices, self.goal_vertices)


class FSpiral(Fixture[int, tuple[int, int, int]]):
    """Graph for testing TraversalShortestPathsFlex with all gears.
    Outgoing edges are sorted by ascending weight.
    """

    @staticmethod
    def next_edges(i: int, _: Any) -> Iterable[tuple[int, int, int]]:
        j = (i + i // 6) % 6
        yield i + 1, j * 2 + 1, j * 2 + 1
        if i % 2 == 0:
            yield i + 6, 7 - j, 7 - j
        elif i % 1200000 > 5:
            yield i - 6, 1, 1

    def __init__(self) -> None:
        super().__init__(0)
        self.goal = 5
        self.focus = 2  # number of vertices at path start and end to print


class FSpiralSorted(FSpiral):
    """A variant of FSpiral where outgoing edges are sorted by ascending weight."""

    @staticmethod
    def next_edges(i: int, _: Any) -> Iterable[tuple[int, int, int]]:
        out_edges = list(super(FSpiralSorted, FSpiralSorted).next_edges(i, None))
        out_edges.sort(key=lambda e: e[1])
        return out_edges


class FOvertaking(FixtureFull[int, tuple[int, int, int, int]]):
    """Graph for testing all strategies with different gears. It can be used
    to create a distance overflow for distance values stored in an array of
    byte."""

    def __init__(self) -> None:
        _enough_for_index_error = (1 + 128) * 8  # index error even for seq of bits
        goal = 2 * _enough_for_index_error
        limit = 3 * _enough_for_index_error
        self.last_vertex = limit + 2  # todo: Goal? Remove?

        edges = []
        for v in range(0, limit, 2):
            edges.append((v, v + 1, 1, 1))
            edges.append((v, v + 3, 1, 3))
        for v in range(1, limit, 2):
            edges.append((v, v + 3, 1, 1))
            edges.append((v, v + 1, 1, 3))

        super().__init__(edges, 0, goal, lambda v: 0, report=False)


class FSequenceTo255(Fixture[int, tuple[int, int]]):
    """Graph with vertices from 0 to 255, edges from i to i+1, and 255 as goal.
    It can be used to create an infinity overflow of guessed distance (guess >= 255)
    for distance guess values stored in an array of byte.
    """

    @staticmethod
    def next_edges(vertex: int, _: Any) -> Iterable[tuple[int, int]]:
        return [(vertex + 1, 1)] if vertex < 255 else []

    def __init__(self) -> None:
        super().__init__(0)
        self.goal = 255

    @staticmethod
    def heuristic(vertex: int) -> int:
        return 255 - vertex  # Create infinity overflow of guessed distance


class FBinaryTreeFixedWeights(Fixture[int, tuple[int, int, int]]):
    """Graph for testing strategies with is_tree and different gears."""

    def __init__(self) -> None:
        _enough_for_index_error = (1 + 128) * 8  # index error even for seq of bits
        self.goal = 2 * _enough_for_index_error
        _limit = 3 * self.goal

        def next_edges(i: int, _: Any) -> Iterator[tuple[int, int, int]]:
            if i < _limit:
                yield 2 * i + 0, 1, 1
                yield 2 * i + 1, 1, 3

        self.next_edges = next_edges
        super().__init__(1)

    @staticmethod
    def heuristic(vertex: int) -> int:
        return 0


# --------- Tests of traversal functionality -----------


class GraphWithoutEdges:
    """-- Graph without edges --
    -- 1) No vertices are reported. Exceptions: topological sorting reports it,
    and BidirectionalSearchShortestPath finds a path from v to v in empty paths.
    >>> f = FNoEdgesGoalIsStart()

    >>> list(nog.TraversalBreadthFirst(f.next_vertices).start_from(f.start))
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    []
    >>> list(nog.TraversalDepthFirst(f.next_vertices).start_from(f.start,
    ...     compute_depth=True))
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    []
    >>> list(nog.TraversalNeighborsThenDepth(f.next_vertices).start_from(f.start,
    ...     compute_depth=True))
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    []
    >>> list(nog.TraversalTopologicalSort(f.next_vertices).start_from(f.start))
    ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {}}
    [0]
    >>> list(nog.TraversalShortestPaths(f.next_edges).start_from(f.start))
    ? 0: {'distance': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {}}
    []
    >>> list(nog.TraversalShortestPathsInfBranchingSorted(f.next_edges).
    ...      start_from(f.start))
    ? 0: {'distance': 0, 'distances': {0: inf}, 'paths': {}}
    []
    >>> list(nog.TraversalMinimumSpanningTree(f.next_edges).start_from(f.start))
    ? 0: {'edge': None, 'paths': {}}
    []
    >>> list(nog.TraversalAStar(f.next_edges).start_from(f.heuristic, f.start))
    ? 0: {'path_length': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {}}
    []
    >>> d, p = nog.BSearchBreadthFirst(f.next_vertices_bi).start_from(f.start_bi)
    >>> print(d, list(p))
    0 [0]
    >>> l, p = nog.BSearchShortestPath(f.next_edges_bi).start_from(f.start_bi)
    >>> print(l, list(p))
    0 [0]

    -- 2a) go_to and go_for_vertices_in find nothing and correctly report this
    >>> f = FNoEdgesGoalUnreachable()

    >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
    >>> traversal.start_from(f.start).go_to(f.goal, fail_silently=True) is None
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    True
    >>> traversal.start_from(f.start).go_to(f.goal)
    Traceback (most recent call last):
    KeyError: 'Vertex not found, graph exhausted.'
    >>> list(traversal.start_from(f.start).go_for_vertices_in(
    ...    (f.goal,), fail_silently=True)
    ... )
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    []
    >>> list(traversal.start_from(f.start).go_for_vertices_in((f.goal,)))
    Traceback (most recent call last):
    KeyError: 'Not all of the given vertices have been found'

    -- 2b) start_at of bidirectional searches find nothing and correctly report this
    >>> search = nog.BSearchBreadthFirst(next_edges=f.next_vertices_bi)
    >>> _ = search.start_from(f.start_bi)
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> length, path = search.start_from(f.start_bi, fail_silently=True)
    ? 0: {'depth': 0, 'visited': {0}, 'paths': {}}
    >>> print(length, type(path))
    -1 <class 'nographs._path.PathOfUnlabeledEdges'>

    >>> search = nog.BSearchShortestPath(f.next_edges_bi)
    >>> _ = search.start_from(f.start_bi)
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> length, path = search.start_from(f.start_bi, fail_silently=True)
    ? 0: {}
    ?<1: {}
    >>> print(length, type(path))
    inf <class 'nographs._path.PathOfUnlabeledEdges'>

    -- 3) __init__ and start_from of the strategies w/o weights detect parameter errors
    >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
    >>> _ = traversal.start_from(start_vertex=f.start, start_vertices=(f.start,))
    Traceback (most recent call last):
    RuntimeError: Both start_vertex and start_vertices provided.
    >>> traversal = traversal.start_from()
    Traceback (most recent call last):
    RuntimeError: Neither start_vertex nor start_vertices provided.

    >>> traversal = nog.TraversalBreadthFirst()
    Traceback (most recent call last):
    RuntimeError: Neither next_vertices nor next_edges nor next_labeled_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_vertices=f.next_vertices,
    ...                                       next_edges=f.next_edges)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_vertices=f.next_vertices,
    ...                                       next_labeled_edges=f.next_edges)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_labeled_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_edges=f.next_edges,
    ...                                       next_labeled_edges=f.next_edges)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.

    -- 3) __init__ and start_from of the strategies with weights detect parameter errors
    >>> traversal = nog.TraversalShortestPaths()
    Traceback (most recent call last):
    RuntimeError: Neither next_edges and next_labeled_edges provided.
    >>> traversal = nog.TraversalShortestPaths(next_edges=f.next_edges,
    ...                                        next_labeled_edges=f.next_edges)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.

    -- 4) __init__ and start_from of the bidirectional searches detect parameter errors
    >>> search = nog.BSearchBreadthFirst(f.next_vertices_bi)
    >>> _ = search.start_from()
    Traceback (most recent call last):
    RuntimeError: Neither start_and_goal_vertex nor start_and_goal_vertices provided.
    >>> _ = search.start_from(start_and_goal_vertex=f.start_bi,
    ...                       start_and_goal_vertices=([],[]))
    Traceback (most recent call last):
    RuntimeError: Both start_and_goal_vertex and start_and_goal_vertices provided.
    >>> _ = nog.BSearchBreadthFirst()
    Traceback (most recent call last):
    RuntimeError: Neither next_vertices nor next_edges nor next_labeled_edges provided.
    >>> _ = nog.BSearchBreadthFirst(next_vertices=f.next_vertices_bi,
    ...                             next_edges=f.next_edges_bi)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_edges provided.
    >>> _ = nog.BSearchBreadthFirst(next_vertices=f.next_vertices_bi,
    ...                             next_labeled_edges=f.next_edges_bi)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_labeled_edges provided.
    >>> _ = nog.BSearchBreadthFirst(next_edges=f.next_edges_bi,
    ...                             next_labeled_edges=f.next_edges_bi)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.

    >>> search = nog.BSearchShortestPath(f.next_edges_bi)
    >>> _ = search.start_from()
    Traceback (most recent call last):
    RuntimeError: Neither start_and_goal_vertex nor start_and_goal_vertices provided.
    >>> _ = search.start_from(start_and_goal_vertex=f.start_bi,
    ...                       start_and_goal_vertices=([],[]))
    Traceback (most recent call last):
    RuntimeError: Both start_and_goal_vertex and start_and_goal_vertices provided.
    >>> _ = nog.BSearchShortestPath()
    Traceback (most recent call last):
    RuntimeError: Neither next_edges and next_labeled_edges provided.
    >>> _ = nog.BSearchShortestPath(next_edges=f.next_edges_bi,
    ...                             next_labeled_edges=f.next_edges_bi)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.
    """


class GraphWithOneEdgeAndPathVariants:
    """-- Graph with one edge --
    Start vertex not reported (exception: topological sorting). First edge followed.
    Paths not build if not demanded, and build if demanded.
    Labeled paths not allowed for unlabeled edges, and build for labeled edges, if
    demanded. Calculation limit raises Exception at exactly correct number of visited
    vertices.

    >>> def test(traversal, goal, labeled_paths, *start_args):
    ...     print(list(traversal.start_from(*start_args)))  # reported vertices
    ...     print(goal not in traversal.paths)  # no path build if not requested
    ...     print(next(traversal.start_from(*start_args)))  # first reported vertex
    ...     _ = traversal.start_from(*start_args, build_paths=True).go_to(goal)
    ...     if labeled_paths:  # also print just vertices (edges are default here)
    ...        print(tuple(traversal.paths.iter_vertices_from_start(1)))
    ...     print(traversal.paths[goal])
    >>> def test_bidirectional(search, goal, labeled_path, *args):
    ...     p_length, p = search.start_from(*args)
    ...     print(goal not in p)  # no path build if not requested
    ...     print(p_length)  # path length (edge count resp. sum of weights)
    ...     p_length, p = search.start_from(*args, build_path=True)
    ...     if labeled_path:  # compare with test... edges are so far not default...
    ...        print(tuple(p.iter_vertices_from_start()))
    ...        print(tuple(p.iter_labeled_edges_from_start()))
    ...     else:
    ...        print(tuple(p))

    # -- Unlabeled graph (if possible: with vertices or edges), functionality tests --
    >>> f = FOneEdgeNoData()
    >>> fw = FOneEdgeWeighted()

    >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalBreadthFirst(next_edges=f.next_edges)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalDepthFirst(f.next_vertices)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalDepthFirst(next_edges=f.next_edges)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalNeighborsThenDepth(f.next_vertices)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalNeighborsThenDepth(
    ...    next_edges=f.next_edges)
    >>> test(traversal, f.goal, False, f.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(f.next_vertices)
    >>> test(traversal, f.goal, False, f.start)
    [1, 0]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(f.next_vertices, is_tree=True)
    >>> test(traversal, f.goal, False, f.start)
    [1, 0]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(next_edges=f.next_edges)
    >>> test(traversal, f.goal, False, f.start)
    [1, 0]
    True
    1
    (0, 1)
    >>> search = nog.BSearchBreadthFirst(f.next_vertices_bi)
    >>> test_bidirectional(search, f.goal, False, f.start_bi)
    True
    1
    (0, 1)
    >>> search = nog.BSearchBreadthFirst(next_edges=f.next_edges_bi)
    >>> test_bidirectional(search, f.goal, False, f.start_bi)
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalShortestPaths(next_edges=fw.next_edges)
    >>> test(traversal, fw.goal, False, fw.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalShortestPathsInfBranchingSorted(
    ...     next_edges=fw.next_edges)
    >>> test(traversal, fw.goal, False, fw.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=fw.next_edges)
    >>> test(traversal, fw.goal, False, fw.start)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalAStar(next_edges=fw.next_edges)
    >>> test(traversal, fw.goal, False, fw.heuristic, fw.start)
    [1]
    True
    1
    (0, 1)


    # -- Unlabeled graph, calculations limit tests --
    >>> traversal = nog.TraversalBreadthFirst(next_edges=f.next_edges)
    >>> list(traversal.start_from(f.start, calculation_limit=2))
    [1]
    >>> _ = list(traversal.start_from(f.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalDepthFirst(next_edges=f.next_edges)
    >>> list(traversal.start_from(f.start, calculation_limit=2))
    [1]
    >>> _ = list(traversal.start_from(f.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalNeighborsThenDepth(next_edges=f.next_edges)
    >>> list(traversal.start_from(f.start, calculation_limit=2))
    [1]
    >>> _ = list(traversal.start_from(f.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=f.next_edges)
    >>> list(traversal.start_from(f.start, calculation_limit=2))
    [1, 0]
    >>> _ = list(traversal.start_from(f.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=f.next_edges, is_tree=True)
    >>> list(traversal.start_from(f.start, calculation_limit=2))
    [1, 0]
    >>> _ = list(traversal.start_from(f.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalShortestPaths(next_edges=fw.next_edges)
    >>> list(traversal.start_from(fw.start, calculation_limit=2))
    [1]
    >>> _ = list(traversal.start_from(fw.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalShortestPathsInfBranchingSorted(fw.next_edges)
    >>> list(traversal.start_from(fw.start, combined_calculation_limit=3))
    [1]
    >>> _ = list(traversal.start_from(fw.start, combined_calculation_limit=2))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=fw.next_edges)
    >>> list(traversal.start_from(fw.start, calculation_limit=2))
    [1]
    >>> _ = list(traversal.start_from(fw.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> # Test early exceeded limit, during traversal of edges from start vertex in MST
    >>> _ = list(traversal.start_from(fw.start, calculation_limit=0))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalAStar(
    ...    next_edges=fw.next_edges)
    >>> _ = list(traversal.start_from(fw.heuristic, fw.start, calculation_limit=2))
    >>> _ = list(traversal.start_from(fw.heuristic, fw.start, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit

    # With the BSearch strategies, we cannot use "traversing the whole graph"
    # to check the calculation_limit functionality. So, on our 1-edge-graph,
    # we search the way from one to the other vertex. Here, it is necessary
    # "to read in one vertex". So, we compare against this.
    >>> search = nog.BSearchBreadthFirst(next_edges=f.next_edges_bi)
    >>> length, path = search.start_from(f.start_bi, calculation_limit=1)
    >>> length, tuple(path)
    (1, ())
    >>> search.start_from(f.start_bi, calculation_limit=0)
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> search = nog.BSearchShortestPath(fw.next_edges_bi)
    >>> length, path = search.start_from(fw.start_bi, calculation_limit=1)
    >>> length, tuple(path)
    (1, ())
    >>> search.start_from(fw.start_bi, calculation_limit=0)
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit


    # -- Labeled graph (changed for v3: next_labeled_edges instead of labeled_paths) --
    >>> f = FOneEdgeLabeled()
    >>> fw = FOneEdgeWeightedLabeled()

    >>> traversal = nog.TraversalBreadthFirst(next_labeled_edges=f.next_edges)
    >>> test(traversal, f.goal, True, f.start)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalDepthFirst(next_labeled_edges=f.next_edges)
    >>> test(traversal, f.goal, True, f.start)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalNeighborsThenDepth(next_labeled_edges=f.next_edges)
    >>> test(traversal, f.goal, True, f.start)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalTopologicalSort(next_labeled_edges=f.next_edges)
    >>> test(traversal, f.goal, True, f.start)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalTopologicalSort(next_labeled_edges=f.next_edges,
    ...                                          is_tree=True)
    >>> test(traversal, f.goal, True, f.start)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalShortestPaths(next_labeled_edges=f.next_edges)
    >>> test(traversal, f.goal, True, f.start)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_labeled_edges=fw.next_edges)
    >>> test(traversal, fw.goal, True, fw.start)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> search = nog.BSearchBreadthFirst(next_labeled_edges=f.next_edges_bi)
    >>> test_bidirectional(search, f.goal, True, f.start_bi)
    True
    1
    (0, 1)
    ((0, 1, 2),)
    >>> search = nog.BSearchShortestPath(next_labeled_edges=fw.next_edges_bi)
    >>> test_bidirectional(search, fw.goal, True, fw.start_bi)
    True
    1
    (0, 1)
    ((0, 1, 2),)
    """


class GraphWithOneEdgeAndVertexToId:
    """-- Graph with one edge, parameter vertex_to_id used --
    For the test, vertices are given as list [int] to have something that is not
    hashable. Start vertex not reported (exception: topological sorting). First edge
    followed. Paths not build if not demanded, and build if demanded. Labeled paths
    not allowed for unlabeled edges, and build for labeled edges, if demanded.
    Calculation limit raises Exception at exactly correct number of visited vertices.

    >>> def test(traversal, start, goal, labeled_paths, **start_args):
    ...     print(list(traversal.start_from(start_vertex=start, **start_args)))
    ...     print(goal not in traversal.paths)
    ...     print(next(traversal.start_from(start_vertex=start, **start_args)))
    ...     _ = traversal.start_from(start_vertex=start, build_paths=True,
    ...                              **start_args).go_to(goal)
    ...     if labeled_paths:
    ...        print(tuple(traversal.paths.iter_vertices_from_start(goal)))
    ...     print(traversal.paths[goal])
    ...     print_filled(traversal.state_to_str([goal]))
    >>> def test_bidirectional(search, start, goal, labeled_paths, **args):
    ...     p_length, p = search.start_from((start, goal), **args)
    ...     print(p_length, list(p) == [])
    ...     p_length, p = search.start_from((start, goal), build_path=True, **args)
    ...     print(p_length, list(p))
    >>> f = FOneEdgeUnhashable()

    # Unlabeled edges
    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), f.next_vertices)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': 1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalDepthFirstFlex(
    ...    first_of, nog.GearDefault(), f.next_vertices)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...    first_of, nog.GearDefault(), f.next_vertices)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...    first_of, nog.GearDefault(), f.next_vertices)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1], [0]]
    True
    [1]
    ([0], [1])
    {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1}, 'paths': {[1]: ([0],
      [1])}}
    >>> search = nog.BSearchBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), f.next_vertices_bi)
    >>> test_bidirectional(search, f.start, f.goal, labeled_paths=False)
    1 True
    1 [[0], [1]]


    # Labeled / weighted edges
    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': 1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'depth': 1, 'visited': {0, 1}, 'paths': {[1]: (([0], [1], 2),)}}

    >>> traversal = nog.TraversalDepthFirstFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}

    >>> traversal = nog.TraversalDepthFirstFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: (([0], [1], 2),)}}

    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: ([0], [1])}}

    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'depth': -1, 'visited': {0, 1}, 'paths': {[1]: (([0], [1], 2),)}}

    >>> traversal = nog.TraversalShortestPathsFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'distance': 1, 'depth': 1, 'distances': {1: 0}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalShortestPathsFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'distance': 1, 'depth': 1, 'distances': {1: 0}, 'paths': {[1]: (([0], [1],
      2),)}}

    >>> traversal = nog.TraversalMinimumSpanningTreeFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    {'edge': ([0], [1], 1, 2), 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalMinimumSpanningTreeFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'edge': ([0], [1], 1, 2), 'paths': {[1]: (([0], [1], 2),)}}

    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False)
    [[1], [0]]
    True
    [1]
    ([0], [1])
    {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1}, 'paths': {[1]: ([0],
      [1])}}
    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True)
    [[1], [0]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1}, 'paths': {[1]: (([0],
      [1], 2),)}}

    >>> traversal = nog.TraversalAStarFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=False,
    ...     heuristic=f.heuristic)
    [[1]]
    True
    [1]
    ([0], [1])
    {'path_length': 1, 'depth': 1, 'distances': {1: 1}, 'paths': {[1]: ([0], [1])}}
    >>> traversal = nog.TraversalAStarFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges)
    >>> test(traversal, f.start, f.goal, labeled_paths=True,
    ...     heuristic=f.heuristic)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 2),)
    {'path_length': 1, 'depth': 1, 'distances': {1: 1}, 'paths': {[1]: (([0], [1],
      2),)}}

    >>> search = nog.BSearchBreadthFirstFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges_bi)
    >>> test_bidirectional(search, f.start, f.goal, labeled_paths=True)
    1 True
    1 [([0], [1], 2)]

    >>> search = nog.BSearchShortestPathFlex(
    ...     first_of, nog.GearDefault(),
    ...     next_labeled_edges=f.next_edges_bi)
    >>> test_bidirectional(search, f.start, f.goal, labeled_paths=True)
    1 True
    1 [([0], [1], 2)]
    """


class VertexToIdWithGoForVerticesInAndGoTo:
    """
    >>> f = FSequenceUnhashable()
    >>> def test_traversal(traversal, *vargs):
    ...     print(list(traversal.start_from(*vargs, f.start)))
    ...     _ = traversal.start_from(*vargs, f.start)
    ...     print(list(traversal.go_for_vertices_in(f.goals)))
    ...     _ = traversal.start_from(*vargs, f.start, build_paths=True)
    ...     print(list(traversal.go_to(f.goal)))
    ...     print(traversal.paths[f.goal])
    ...     print_filled(traversal.state_to_str([f.goal]))
    >>> def test_bsearch(search, *vargs):
    ...     l, p = search.start_from(*vargs, f.start_bi)
    ...     print(l, list(p))
    ...     l, p = search.start_from(*vargs, f.start_bi, build_path=True)
    ...     print(l, list(p))

    >>> test_traversal(nog.TraversalBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'depth': 3, 'visited': {0, 1, 2, 3}, 'paths': {[3]: ([0], [1], [2], [3])}}
    >>> test_traversal(nog.TraversalDepthFirstFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {[3]: ([0], [1], [2], [3])}}
    >>> test_traversal(nog.TraversalNeighborsThenDepthFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {[3]: ([0], [1], [2], [3])}}
    >>> test_traversal(nog.TraversalShortestPathsFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'distance': 3, 'depth': 3, 'distances': {3: 0}, 'paths': {[3]: ([0], [1], [2],
      [3])}}
    >>> test_traversal(nog.TraversalMinimumSpanningTreeFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'edge': ([2], [3], 1, 3), 'paths': {[3]: ([0], [1], [2], [3])}}
    >>> test_traversal(nog.TraversalTopologicalSortFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges))
    [[4], [3], [2], [1], [0]]
    [[3], [1]]
    [3]
    ([0], [1], [2], [3])
    {'depth': 3, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4}, 'paths': {[3]:
      ([0], [1], [2], [3])}}
    >>> test_traversal(nog.TraversalAStarFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges), f.heuristic)
    [[1], [2], [3], [4]]
    [[1], [3]]
    [3]
    ([0], [1], [2], [3])
    {'path_length': 3, 'depth': 3, 'distances': {3: 3}, 'paths': {[3]: ([0], [1],
      [2], [3])}}
    >>> test_bsearch(nog.BSearchBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), next_labeled_edges=f.next_edges_bi))
    3 []
    3 [([0], [1], 1), ([1], [2], 2), ([2], [3], 3)]
    >>> test_bsearch(nog.BSearchShortestPathFlex(
    ...     first_of, nog.GearDefault(), next_labeled_edges=f.next_edges_bi))
    3 []
    3 [([0], [1], 1), ([1], [2], 2), ([2], [3], 3)]

    For one of the traversals, test the case "not all goals reachable":
    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> list(traversal.start_from(f.start).go_for_vertices_in(f.goals_impossible))
    Traceback (most recent call last):
    KeyError: 'Not all of the given vertices have been found'

    For one of the traversals, test for go_to_vertex: Not immediatetly found and
    then not found at all, and not found with fail_simlently:
    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), next_edges=f.next_edges)
    >>> traversal.start_from(f.start).go_to(f.goal_impossible)
    Traceback (most recent call last):
    KeyError: 'Vertex not found, graph exhausted.'
    >>> (traversal.start_from(f.start).go_to(f.goal_impossible, fail_silently=True)
    ... ) is None
    True

    For both searches, test the case "not all goals reachable":
    >>> search = nog.BSearchBreadthFirstFlex(
    ...     first_of, nog.GearDefault(), next_labeled_edges=f.next_edges_bi)
    >>> _ = search.start_from(f.start_impossible_bi)
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(f.start_impossible_bi, fail_silently=True)
    >>> print(l, list(p))
    -1 []
    >>> search = nog.BSearchShortestPathFlex(
    ...     first_of, nog.GearDefault(), next_labeled_edges=f.next_edges_bi)
    >>> _ = search.start_from(f.start_impossible_bi)
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(f.start_impossible_bi, fail_silently=True)
    >>> print(l, list(p))
    inf []
    """


class NormalGraphTraversalsWithOrWithoutLabels:
    """
    -- Small example graph, 3 Traversal strategies that can work with and without
    labels -- Correct traversal of TraversalBreadthFirst, TraversalDepthFirst,
    TraversalTopologicalSort. For: graph without labels and graph with labels.
    Without and with vertices defined as already visited (only tested for graph
    without labels). (Uses implementation decisions:
    - TraversalBreadthFirst traverses edges in given order
    - TraversalDepthFirst and TraversalTopologicalSort traverse edges in reversed order)
    """

    @staticmethod
    def unattributed_edges() -> None:
        """
        >>> f = FDiamond()
        >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {1: (0, 1)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {2: (0, 2)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 1, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalDepthFirst(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        -> 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalDepthFirst(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': -1, 'visited': {0}, 'paths': {0: (0,)}}
        -> 2: {'depth': -1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': -1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': -1, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': -1, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        -> 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        ? 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalNeighborsThenDepth(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalNeighborsThenDepth(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': -1, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': -1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': -1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': -1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalTopologicalSort(f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0:
          (0,)}}
        ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0: (0,)}}
        ? 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2}, 'paths': {2: (0,
          2)}}
        ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3: (0,
          2, 3)}}
        -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3:
          (0, 2, 3)}}
        -> 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {2:
          (0, 2)}}
        ? 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {0:
          (0,)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> search = nog.BSearchBreadthFirst(f.next_vertices_bi)
        >>> l, p = search.start_from(f.start_bi, build_path=True)
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ?<3: {'depth': 0, 'visited': {3}, 'paths': {3: (3,)}}
        >>> print(l, list(p))
        2 [0, 1, 3]
        """
        pass

    @staticmethod
    def unattributed_edges_and_int_id_gear() -> None:
        """
        >>> f = FDiamond()
        >>> gear = nog.GearForIntVertexIDsAndCFloats()

        >>> traversal = nog.TraversalBreadthFirstFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {1: (0, 1)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {2: (0, 2)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 1, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalDepthFirstFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        -> 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalDepthFirstFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': -1, 'visited': {0}, 'paths': {0: (0,)}}
        -> 2: {'depth': -1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': -1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': -1, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': -1, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        -> 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        ? 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalNeighborsThenDepthFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalNeighborsThenDepthFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': -1, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': -1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': -1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': -1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 1: {'depth': -1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalTopologicalSortFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0:
          (0,)}}
        ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0: (0,)}}
        ? 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2}, 'paths': {2: (0,
          2)}}
        ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3: (0,
          2, 3)}}
        -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3:
          (0, 2, 3)}}
        -> 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {2:
          (0, 2)}}
        ? 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {0:
          (0,)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> search = nog.BSearchBreadthFirstFlex(
        ...     nog.vertex_as_id, gear, f.next_vertices_bi)
        >>> l, p = search.start_from(f.start_bi, build_path=True)
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ?<3: {'depth': 0, 'visited': {3}, 'paths': {3: (3,)}}
        >>> print(l, list(p))
        2 [0, 1, 3]
        """
        pass

    @staticmethod
    def unlabeled_edges_and_already_visited() -> None:
        """
        1b. Unlabeled edges and already_visited
        >>> f = FDiamond()

        >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
        >>> already_visited={f.vertex_for_already_visited}
        >>> traversal = traversal.start_from(
        ...     f.start, build_paths=True, already_visited=already_visited)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]
        >>> print("Already visited:", StrRepr.from_set(already_visited))
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[f.vertex_for_already_visited]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalDepthFirst(f.next_vertices)
        >>> already_visited={f.vertex_for_already_visited}
        >>> traversal = traversal.start_from(
        ...     f.start, build_paths=True, compute_depth=True,
        ...     already_visited=already_visited)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]
        >>> print("Already visited:", StrRepr.from_set(already_visited))
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[f.vertex_for_already_visited]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalNeighborsThenDepth(f.next_vertices)
        >>> already_visited={f.vertex_for_already_visited}
        >>> traversal = traversal.start_from(
        ...     f.start, build_paths=True, compute_depth=True,
        ...     already_visited=already_visited)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]
        >>> print("Already visited:", StrRepr.from_set(already_visited))
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[f.vertex_for_already_visited]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalTopologicalSort(f.next_vertices)
        >>> already_visited={f.vertex_for_already_visited}
        >>> traversal = traversal.start_from(
        ...     f.start, build_paths=True, already_visited=already_visited)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1}, 'paths':
          {0: (0,)}}
        ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1}, 'paths': {0: (0,)}}
        ? 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2}, 'paths': {2: (0,
          2)}}
        ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {3:
          (0, 2, 3)}}
        -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {3:
          (0, 2, 3)}}
        -> 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {2:
          (0, 2)}}
        -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {0:
          (0,)}}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]
        >>> print("Already visited:", StrRepr.from_set(already_visited))
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[f.vertex_for_already_visited]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.
        """
        pass

    @staticmethod
    def unattributed_edges_and_seq_based_already_visited() -> None:
        """
        >>> f = FDiamond()
        >>> traversal = nog.TraversalBreadthFirst(f.next_vertices)
        >>> already_visited = nog.GearForIntVertexIDsAndCFloats().vertex_id_set(())
        >>> already_visited.add(f.vertex_for_already_visited)
        >>> traversal = traversal.start_from(
        ...     f.start, build_paths=True, already_visited=already_visited)

        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0, 1}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[f.vertex_for_already_visited]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.
        """
        pass

    @staticmethod
    def labeled_edges() -> None:
        """
        >>> f = FDiamond()
        >>> traversal = nog.TraversalBreadthFirst(
        ...     next_edges=f.next_edges)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {1: (0, 1)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {2: (0, 2)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 1, 3)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 1, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalDepthFirst(
        ...     next_edges=f.next_edges)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 2, 3}, 'paths': {3: (0, 2, 3)}}
        -> 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalNeighborsThenDepth(
        ...     next_edges=f.next_edges)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        -> 1: {'depth': 1, 'visited': {0, 1}, 'paths': {1: (0, 1)}}
        -> 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        ? 2: {'depth': 1, 'visited': {0, 1, 2}, 'paths': {2: (0, 2)}}
        -> 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 3: {'depth': 2, 'visited': {0, 1, 2, 3}, 'paths': {3: (0, 2, 3)}}
        ? 1: {'depth': 1, 'visited': {0, 1, 2, 3}, 'paths': {1: (0, 1)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> traversal = nog.TraversalTopologicalSort(
        ...     next_edges=f.next_edges)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0:
          (0,)}}
        ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0}, 'paths': {0: (0,)}}
        ? 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2}, 'paths': {2: (0,
          2)}}
        ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3: (0,
          2, 3)}}
        -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {3:
          (0, 2, 3)}}
        -> 2: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 2, 3}, 'paths': {2:
          (0, 2)}}
        ? 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {1:
          (0, 1)}}
        -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3}, 'paths': {0:
          (0,)}}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
        All visited: [0, 1, 2, 3]

        >>> search = nog.BSearchBreadthFirst(next_edges=f.next_edges_bi)
        >>> l, p = search.start_from(f.start_bi, build_path=True)
        ? 0: {'depth': 0, 'visited': {0}, 'paths': {0: (0,)}}
        ?<3: {'depth': 0, 'visited': {3}, 'paths': {3: (3,)}}
        >>> print(l, list(p))
        2 [0, 1, 3]
        """
        pass

    @staticmethod
    def is_tree() -> None:
        """
        >>> f = FSmallBinaryTree()
        >>> traversal = nog.TraversalBreadthFirst(f.next_vertices,is_tree=True)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        ? 1: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        -> 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        -> 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        ? 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        -> 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        -> 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        ? 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        -> 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        -> 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        ? 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        ? 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        ? 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        ? 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
        All visited: []

        >>> traversal = nog.TraversalDepthFirst(f.next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        ? 1: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        -> 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        ? 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        -> 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        ? 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        -> 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        ? 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        -> 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        ? 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        -> 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        ? 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        -> 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        ? 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
        All visited: []

        >>> traversal = nog.TraversalNeighborsThenDepth(f.next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(f.start, build_paths=True,
        ...                                  compute_depth=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        ? 1: {'depth': 0, 'visited': {}, 'paths': {1: (1,)}}
        -> 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        -> 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        ? 3: {'depth': 1, 'visited': {}, 'paths': {3: (1, 3)}}
        -> 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        -> 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        ? 7: {'depth': 2, 'visited': {}, 'paths': {7: (1, 3, 7)}}
        ? 6: {'depth': 2, 'visited': {}, 'paths': {6: (1, 3, 6)}}
        ? 2: {'depth': 1, 'visited': {}, 'paths': {2: (1, 2)}}
        -> 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        -> 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        ? 5: {'depth': 2, 'visited': {}, 'paths': {5: (1, 2, 5)}}
        ? 4: {'depth': 2, 'visited': {}, 'paths': {4: (1, 2, 4)}}
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
        All visited: []

        >>> traversal = nog.TraversalTopologicalSort(f.next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(f.start, build_paths=True)
        >>> results_with_visited(traversal, {f.start})
        After start: {'depth': 0, 'cycle_from_start': [], 'visited': {}, 'paths': {1:
          (1,)}}
        ? 1: {'depth': 0, 'cycle_from_start': [], 'visited': {}, 'paths': {1: (1,)}}
        ? 3: {'depth': 1, 'cycle_from_start': [], 'visited': {}, 'paths': {3: (1, 3)}}
        ? 7: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {7: (1, 3,
          7)}}
        -> 7: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {7: (1, 3,
          7)}}
        ? 6: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {6: (1, 3,
          6)}}
        -> 6: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {6: (1, 3,
          6)}}
        -> 3: {'depth': 1, 'cycle_from_start': [], 'visited': {}, 'paths': {3: (1, 3)}}
        ? 2: {'depth': 1, 'cycle_from_start': [], 'visited': {}, 'paths': {2: (1, 2)}}
        ? 5: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {5: (1, 2,
          5)}}
        -> 5: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {5: (1, 2,
          5)}}
        ? 4: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {4: (1, 2,
          4)}}
        -> 4: {'depth': 2, 'cycle_from_start': [], 'visited': {}, 'paths': {4: (1, 2,
          4)}}
        -> 2: {'depth': 1, 'cycle_from_start': [], 'visited': {}, 'paths': {2: (1, 2)}}
        -> 1: {'depth': 0, 'cycle_from_start': [], 'visited': {}, 'paths': {1: (1,)}}
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
        All visited: []
        """
        pass


class NormalGraphTraversalsWithWeights:
    """-- Small example graph. The three strategies that need edge weights. --
    For TraversalShortestPaths, test option known_distances, too.

    -- TraversalShortestPaths --
    First we test without know_distances, and with option keep_distances.
    We also check here, whether distances and paths stay the same from
    start_from till traversal.
    >>> f = FDiamond()
    >>> traversal = nog.TraversalShortestPaths(next_edges=f.next_edges)
    >>> traversal = traversal.start_from(f.start, build_paths=True, keep_distances=True)
    >>> results_with_distances(traversal, {f.start})
    After start: {'distance': inf, 'depth': 0, 'distances': {0: 0}, 'paths': {0:
      (0,)}}
    ? 0: {'distance': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 2: {'distance': 1, 'depth': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    ? 2: {'distance': 1, 'depth': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    -> 1: {'distance': 2, 'depth': 1, 'distances': {1: 2}, 'paths': {1: (0, 1)}}
    ? 1: {'distance': 2, 'depth': 1, 'distances': {1: 2}, 'paths': {1: (0, 1)}}
    -> 3: {'distance': 3, 'depth': 2, 'distances': {3: 3}, 'paths': {3: (0, 2, 3)}}
    ? 3: {'distance': 3, 'depth': 2, 'distances': {3: 3}, 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    All distances: {0: 0, 1: 2, 2: 1, 3: 3}


    Now we test with known_distances, but without option keep_distances.
    Start vertex starts with distance 2, and we pretend to have a path to 1 with
    distance 0. Effect: All reported distances are 2 higher than in the test before,
    because the traversal starts at distance 2, and vertex 1 is not visited and
    reported at all, because no path can be found that beats this "already found" low
    distance. Due to keep_distances==False, the distances to 2 and 3 are deleted.
    >>> known_distances = collections.defaultdict(
    ...     lambda: infinity, f.values_for_known_distances)
    >>> traversal = traversal.start_from(
    ...     f.start, build_paths=True, known_distances=known_distances)
    >>> results_with_distances(traversal, {f.start})
    After start: {'distance': inf, 'depth': 0, 'distances': {0: 2}, 'paths': {0:
      (0,)}}
    ? 0: {'distance': 2, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 2: {'distance': 3, 'depth': 1, 'distances': {2: 0}, 'paths': {2: (0, 2)}}
    ? 2: {'distance': 3, 'depth': 1, 'distances': {2: 0}, 'paths': {2: (0, 2)}}
    -> 3: {'distance': 5, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (0, 2, 3)}}
    ? 3: {'distance': 5, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 2), (0, 2, 3)]
    All distances: {0: 0, 1: 0, 2: 0, 3: 0}
    >>> traversal.distances is known_distances
    True

    The same again, but with a sequence-based known_distances
    >>> gear = nog.GearForIntVertexIDsAndIntsMaybeFloats()
    >>> known_distances = gear.vertex_id_to_distance_mapping(())
    >>> known_distances.update(f.values_for_known_distances)
    >>> traversal = traversal.start_from(
    ...     f.start, build_paths=True, known_distances=known_distances)
    >>> results_with_distances(traversal, {f.start})
    After start: {'distance': inf, 'depth': 0, 'distances': {0: 2}, 'paths': {0:
      (0,)}}
    ? 0: {'distance': 2, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 2: {'distance': 3, 'depth': 1, 'distances': {2: 0}, 'paths': {2: (0, 2)}}
    ? 2: {'distance': 3, 'depth': 1, 'distances': {2: 0}, 'paths': {2: (0, 2)}}
    -> 3: {'distance': 5, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (0, 2, 3)}}
    ? 3: {'distance': 5, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 2), (0, 2, 3)]
    All distances: {0: 0, 1: 0, 2: 0, 3: 0}
    >>> traversal.distances is known_distances
    True


    -- TraversalShortestPathsInfBranchingSorted --
    First we test with option store_distances.
    We also check here, whether distances and paths stay the same from
    start_from till traversal.
    Note: Distances are stored (and thus: printed) in order of reporting, whilst
    TraversalShortestPaths results in an other order
    >>> f = FDiamondSorted()
    >>> traversal = nog.TraversalShortestPathsInfBranchingSorted(f.next_edges)
    >>> traversal = traversal.start_from(f.start, build_paths=True,
    ...     store_distances=True)
    >>> results_with_distances(traversal, {f.start})
    After start: {'distance': inf, 'distances': {0: 0}, 'paths': {0: (0,)}}
    ? 0: {'distance': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 2: {'distance': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    ? 2: {'distance': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    -> 1: {'distance': 2, 'distances': {1: 2}, 'paths': {1: (0, 1)}}
    ? 1: {'distance': 2, 'distances': {1: 2}, 'paths': {1: (0, 1)}}
    -> 3: {'distance': 3, 'distances': {3: 3}, 'paths': {3: (0, 2, 3)}}
    ? 3: {'distance': 3, 'distances': {3: 3}, 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    All distances: {0: 0, 2: 1, 1: 2, 3: 3}

    Now we test without option store_distances.
    >>> f = FDiamondSorted()
    >>> traversal = nog.TraversalShortestPathsInfBranchingSorted(f.next_edges)
    >>> traversal = traversal.start_from(f.start, build_paths=True)
    >>> results_with_distances(traversal, {f.start})
    After start: {'distance': inf, 'distances': {0: inf}, 'paths': {0: (0,)}}
    ? 0: {'distance': 0, 'distances': {0: inf}, 'paths': {0: (0,)}}
    -> 2: {'distance': 1, 'distances': {2: inf}, 'paths': {2: (0, 2)}}
    ? 2: {'distance': 1, 'distances': {2: inf}, 'paths': {2: (0, 2)}}
    -> 1: {'distance': 2, 'distances': {1: inf}, 'paths': {1: (0, 1)}}
    ? 1: {'distance': 2, 'distances': {1: inf}, 'paths': {1: (0, 1)}}
    -> 3: {'distance': 3, 'distances': {3: inf}, 'paths': {3: (0, 2, 3)}}
    ? 3: {'distance': 3, 'distances': {3: inf}, 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    All distances: {0: inf, 2: inf, 1: inf, 3: inf}


    -- TraversalMinimumSpanningTree --
    >>> fmst = FDiamond2()
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=fmst.next_edges)
    >>> traversal = traversal.start_from(fmst.start, build_paths=True)
    >>> results_standard(traversal, {fmst.start})
    After start: {'edge': None, 'paths': {0: (0,)}}
    ? 0: {'edge': None, 'paths': {0: (0,)}}
    -> 2: {'edge': (0, 2, 1), 'paths': {2: (0, 2)}}
    ? 2: {'edge': (0, 2, 1), 'paths': {2: (0, 2)}}
    -> 1: {'edge': (0, 1, 2), 'paths': {1: (0, 1)}}
    ? 1: {'edge': (0, 1, 2), 'paths': {1: (0, 1)}}
    -> 3: {'edge': (2, 3, 3), 'paths': {3: (0, 2, 3)}}
    ? 3: {'edge': (2, 3, 3), 'paths': {3: (0, 2, 3)}}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


    -- TraversaAStar --
    Typically, one would use go_to(3) for our goal vertex 3, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> fa = FAStar()
    >>> traversal = nog.TraversalAStar(next_edges=fa.next_edges)
    >>> traversal = traversal.start_from(fa.heuristic, fa.start, build_paths=True)
    >>> results_standard(traversal, {fa.start})
    After start: {'path_length': inf, 'depth': 0, 'distances': {0: 0}, 'paths': {0:
      (0,)}}
    ? 0: {'path_length': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 1: {'path_length': 3, 'depth': 1, 'distances': {1: 3}, 'paths': {1: (0, 1)}}
    ? 1: {'path_length': 3, 'depth': 1, 'distances': {1: 3}, 'paths': {1: (0, 1)}}
    -> 2: {'path_length': 3, 'depth': 1, 'distances': {2: 3}, 'paths': {2: (0, 2)}}
    ? 2: {'path_length': 3, 'depth': 1, 'distances': {2: 3}, 'paths': {2: (0, 2)}}
    -> 3: {'path_length': 5, 'depth': 2, 'distances': {3: 5}, 'paths': {3: (0, 2,
      3)}}
    ? 3: {'path_length': 5, 'depth': 2, 'distances': {3: 5}, 'paths': {3: (0, 2,
      3)}}
    -> 4: {'path_length': 1, 'depth': 1, 'distances': {4: 1}, 'paths': {4: (0, 4)}}
    ? 4: {'path_length': 1, 'depth': 1, 'distances': {4: 1}, 'paths': {4: (0, 4)}}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3), (0, 4)]


    Variant of the test with option known_distances.
    For the start vertex, we define a start distance. Effect: All distances are now 2
    higher. For vertex 1, we define an artificial and low distance of 0. Effect: it is
    not visited.
    >>> known_distances = collections.defaultdict(
    ...     lambda: infinity, fa.values_for_known_distances)
    >>> known_path_length_guesses = collections.defaultdict(lambda: infinity)
    >>> traversal = traversal.start_from(fa.heuristic, fa.start, build_paths=True,
    ...     known_distances=known_distances,
    ...     known_path_length_guesses=known_path_length_guesses)
    >>> results_standard(traversal, {fa.start})
    After start: {'path_length': inf, 'depth': 0, 'distances': {0: 2}, 'paths': {0:
      (0,)}}
    ? 0: {'path_length': 2, 'depth': 0, 'distances': {0: 2}, 'paths': {0: (0,)}}
    -> 2: {'path_length': 5, 'depth': 1, 'distances': {2: 5}, 'paths': {2: (0, 2)}}
    ? 2: {'path_length': 5, 'depth': 1, 'distances': {2: 5}, 'paths': {2: (0, 2)}}
    -> 3: {'path_length': 7, 'depth': 2, 'distances': {3: 7}, 'paths': {3: (0, 2,
      3)}}
    ? 3: {'path_length': 7, 'depth': 2, 'distances': {3: 7}, 'paths': {3: (0, 2,
      3)}}
    -> 4: {'path_length': 3, 'depth': 1, 'distances': {4: 3}, 'paths': {4: (0, 4)}}
    ? 4: {'path_length': 3, 'depth': 1, 'distances': {4: 3}, 'paths': {4: (0, 4)}}
    All paths: [(0,), (0, 2), (0, 2, 3), (0, 4)]
    >>> print("Distance at goal:", known_distances[fa.goal])
    Distance at goal: 7
    >>> print("Best distances found so far:", dict(known_distances))
    Best distances found so far: {0: 2, 1: 0, 2: 5, 4: 3, 3: 7}
    >>> print("Best path len guesses found so far):", dict(known_path_length_guesses))
    Best path len guesses found so far): {0: 8, 2: 7, 4: inf, 3: 7}


    -- BidirectionalSearchShortestPath --
    >>> search = nog.BSearchShortestPath(f.next_edges_bi)
    >>> l, p = search.start_from(f.start_bi)
    ? 0: {}
    ?<3: {}
    ? 2: {}
    >>> print(l, f.goal in p)
    3 False


    >>> fsp = FBSearchShortestPath()
    >>> search = nog.BSearchShortestPath(fsp.next_edges_bi)
    >>> l, p = search.start_from(fsp.start_bi)
    ? 0: {}
    ?<4: {}
    ? 2: {}
    ?<3: {}
    ? 1: {}
    >>> print(l, fsp.goal in p)
    90 False



    All traversals, with option is_tree (except for MST, BSearchShortestPath,
    and TraversalShortestPathsInfBranchingSorted, since they do not have the option):
    >>> fsb = FSmallBinaryTree()
    >>> traversal = nog.TraversalShortestPaths(fsb.next_edges, is_tree=True)
    >>> traversal = traversal.start_from(fsb.start, build_paths=True)
    >>> results_with_distances(traversal, {fsb.start})
    After start: {'distance': inf, 'depth': 0, 'distances': {1: 0}, 'paths': {1:
      (1,)}}
    ? 1: {'distance': 0, 'depth': 0, 'distances': {1: 0}, 'paths': {1: (1,)}}
    -> 2: {'distance': 2, 'depth': 1, 'distances': {2: inf}, 'paths': {2: (1, 2)}}
    ? 2: {'distance': 2, 'depth': 1, 'distances': {2: inf}, 'paths': {2: (1, 2)}}
    -> 3: {'distance': 3, 'depth': 1, 'distances': {3: inf}, 'paths': {3: (1, 3)}}
    ? 3: {'distance': 3, 'depth': 1, 'distances': {3: inf}, 'paths': {3: (1, 3)}}
    -> 4: {'distance': 6, 'depth': 2, 'distances': {4: inf}, 'paths': {4: (1, 2,
      4)}}
    ? 4: {'distance': 6, 'depth': 2, 'distances': {4: inf}, 'paths': {4: (1, 2, 4)}}
    -> 5: {'distance': 7, 'depth': 2, 'distances': {5: inf}, 'paths': {5: (1, 2,
      5)}}
    ? 5: {'distance': 7, 'depth': 2, 'distances': {5: inf}, 'paths': {5: (1, 2, 5)}}
    -> 6: {'distance': 9, 'depth': 2, 'distances': {6: inf}, 'paths': {6: (1, 3,
      6)}}
    ? 6: {'distance': 9, 'depth': 2, 'distances': {6: inf}, 'paths': {6: (1, 3, 6)}}
    -> 7: {'distance': 10, 'depth': 2, 'distances': {7: inf}, 'paths': {7: (1, 3,
      7)}}
    ? 7: {'distance': 10, 'depth': 2, 'distances': {7: inf}, 'paths': {7: (1, 3,
      7)}}
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
    All distances: {1: 0, 2: inf, 3: inf, 4: inf, 5: inf, 6: inf, 7: inf}

    Test TraversaAStar. Typically, one would use go_to(6) for our goal vertex 6, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> traversal = nog.TraversalAStar(next_edges=fsb.next_edges)
    >>> traversal = traversal.start_from(fsb.heuristic, fsb.start, build_paths=True)
    >>> results_standard(traversal, {fsb.start})
    After start: {'path_length': inf, 'depth': 0, 'distances': {1: 0}, 'paths': {1:
      (1,)}}
    ? 1: {'path_length': 0, 'depth': 0, 'distances': {1: 0}, 'paths': {1: (1,)}}
    -> 3: {'path_length': 3, 'depth': 1, 'distances': {3: 3}, 'paths': {3: (1, 3)}}
    ? 3: {'path_length': 3, 'depth': 1, 'distances': {3: 3}, 'paths': {3: (1, 3)}}
    -> 6: {'path_length': 9, 'depth': 2, 'distances': {6: 9}, 'paths': {6: (1, 3,
      6)}}
    ? 6: {'path_length': 9, 'depth': 2, 'distances': {6: 9}, 'paths': {6: (1, 3,
      6)}}
    -> 2: {'path_length': 2, 'depth': 1, 'distances': {2: 2}, 'paths': {2: (1, 2)}}
    ? 2: {'path_length': 2, 'depth': 1, 'distances': {2: 2}, 'paths': {2: (1, 2)}}
    -> 4: {'path_length': 6, 'depth': 2, 'distances': {4: 6}, 'paths': {4: (1, 2,
      4)}}
    ? 4: {'path_length': 6, 'depth': 2, 'distances': {4: 6}, 'paths': {4: (1, 2,
      4)}}
    -> 5: {'path_length': 7, 'depth': 2, 'distances': {5: 7}, 'paths': {5: (1, 2,
      5)}}
    ? 5: {'path_length': 7, 'depth': 2, 'distances': {5: 7}, 'paths': {5: (1, 2,
      5)}}
    -> 7: {'path_length': 10, 'depth': 2, 'distances': {7: 10}, 'paths': {7: (1, 3,
      7)}}
    ? 7: {'path_length': 10, 'depth': 2, 'distances': {7: 10}, 'paths': {7: (1, 3,
      7)}}
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
    """


class MultipleOrNoneStartVerticesTraversalsWithOrWithoutLabels:
    """-- Traversal with none or multiple start vertices, first 3 traversal strategies
    Checks: Correct traversal of TraversalBreadthFirst, TraversalDepthFirst,
    TraversalNeighborsThenDepth, and TraversalTopologicalSort in case of multiple
    start vertices. No traversal in case of no start vertex resp. no goal vertex
    (this is checked only for unlabeled edges).
    Uses implementation descisions:
    - All strategies travers start vertices in given order
    - TraversalBreadthFirst traverses edges in given order, while TraversalDepthFirst
      and TraversalTopologicalSort traverse edges in reversed order.

    1. Unlabeled edges
    >>> f = FMultiStart()
    >>> fb = FMultiStartB()

    >>> t = nog.TraversalBreadthFirst(f.next_vertices).start_from(
    ...      start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 5}, 'paths': {1: (0, 1)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {6: (5, 6)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 6: {'depth': 1, 'visited': {0, 1, 2, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 1, 2, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 5, 6}, 'paths': {2: (0, 1, 2)}}
    -> 4: {'depth': 3, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {4: (0, 1, 2, 4)}}
    ? 3: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 4: {'depth': 3, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {4: (0, 1, 2, 4)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (0, 1, 2, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> list(t.start_from(start_vertices=(), build_paths=True))
    []
    >>> list(t.start_from(start_vertices=f.start_vertices, build_paths=True
    ...     ).go_for_vertices_in([]))
    []

    For TraversalDepthFirst, we need to specify compute_depth to get depth.
    And we need to check the extra execution path for the case without depth and paths.
    >>> t = nog.TraversalDepthFirst(f.next_vertices).start_from(
    ...      start_vertices=f.start_vertices, build_paths=True, compute_depth=True)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'visited': {0, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    ? 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    -> 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 0: {'depth': 0, 'visited': {0, 3, 4, 5, 6}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> _ = t.start_from(start_vertices=f.start_vertices)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {}}
    ? 5: {'depth': -1, 'visited': {0, 5}, 'paths': {}}
    -> 6: {'depth': -1, 'visited': {0, 5, 6}, 'paths': {}}
    ? 6: {'depth': -1, 'visited': {0, 5, 6}, 'paths': {}}
    -> 3: {'depth': -1, 'visited': {0, 3, 5, 6}, 'paths': {}}
    ? 3: {'depth': -1, 'visited': {0, 3, 5, 6}, 'paths': {}}
    -> 4: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    ? 4: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    ? 0: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    -> 1: {'depth': -1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {}}
    ? 1: {'depth': -1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {}}
    -> 2: {'depth': -1, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {}}
    ? 2: {'depth': -1, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {}}
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> list(t.start_from(start_vertices=(), build_paths=True))
    []
    >>> list(t.start_from(start_vertices=f.start_vertices, build_paths=True
    ...     ).go_for_vertices_in([]))
    []

    For TraversalNeighborsThenDepth, we need to specify compute_depth to get depth.
    And we need to check the extra execution path for the case without depth and paths.
    >>> t = nog.TraversalNeighborsThenDepth(f.next_vertices).start_from(
    ...      start_vertices=f.start_vertices, build_paths=True, compute_depth=True)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'visited': {0, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    ? 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    -> 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 0: {'depth': 0, 'visited': {0, 3, 4, 5, 6}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> _ = t.start_from(start_vertices=f.start_vertices)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {}}
    ? 5: {'depth': -1, 'visited': {0, 5}, 'paths': {}}
    -> 6: {'depth': -1, 'visited': {0, 5, 6}, 'paths': {}}
    ? 6: {'depth': -1, 'visited': {0, 5, 6}, 'paths': {}}
    -> 3: {'depth': -1, 'visited': {0, 3, 5, 6}, 'paths': {}}
    ? 3: {'depth': -1, 'visited': {0, 3, 5, 6}, 'paths': {}}
    -> 4: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    ? 4: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    ? 0: {'depth': -1, 'visited': {0, 3, 4, 5, 6}, 'paths': {}}
    -> 1: {'depth': -1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {}}
    ? 1: {'depth': -1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {}}
    -> 2: {'depth': -1, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {}}
    ? 2: {'depth': -1, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {}}
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> list(t.start_from(start_vertices=(), build_paths=True))
    []
    >>> list(t.start_from(start_vertices=f.start_vertices, build_paths=True
    ...     ).go_for_vertices_in([]))
    []

    >>> t = nog.TraversalTopologicalSort(f.next_vertices).start_from(
    ...      start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_visited(t, f.start_vertices)
    After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 5}, 'paths':
      {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 5}, 'paths': {5: (5,)}}
    ? 6: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 5, 6}, 'paths': {6: (5,
      6)}}
    ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 3, 5, 6}, 'paths': {3:
      (5, 6, 3)}}
    ? 4: {'depth': 3, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {4: (5, 6, 3, 4)}}
    -> 4: {'depth': 3, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {4: (5, 6, 3, 4)}}
    -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {3: (5, 6, 3)}}
    -> 6: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {6: (5, 6)}}
    -> 5: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {5: (5,)}}
    ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {0: (0,)}}
    ? 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 3, 4, 5, 6},
      'paths': {1: (0, 1)}}
    ? 2: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {2: (0, 1, 2)}}
    -> 2: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {2: (0, 1, 2)}}
    -> 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {1: (0, 1)}}
    -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {0: (0,)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]
    >>> list(t.start_from(start_vertices=(), build_paths=True))
    []
    >>> list(t.start_from(start_vertices=f.start_vertices, build_paths=True
    ...     ).go_for_vertices_in([]))
    []

    >>> l, p = nog.BSearchBreadthFirst(fb.next_vertices_bi
    ...     ).start_from(start_and_goal_vertices=fb.start_vertices_bi)
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {}}
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {}}
    >>> print(l, f.goal not in p)
    3 True
    >>> l, p = nog.BSearchBreadthFirst(fb.next_vertices_bi
    ...     ).start_from(start_and_goal_vertices=fb.start_vertices_bi, build_path=True)
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {4: (4,)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {1: (0, 1)}}
    >>> print(l, list(p))
    3 [0, 1, 2, 4]

    >>> l, p = nog.BSearchBreadthFirst(fb.next_vertices_bi
    ...     ).start_from(start_and_goal_vertices=((), ()))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = nog.BSearchBreadthFirst(fb.next_vertices_bi
    ...     ).start_from(start_and_goal_vertices=(fb.start_vertices_bi[0], ()))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = nog.BSearchBreadthFirst(fb.next_vertices_bi
    ...     ).start_from(start_and_goal_vertices=((), fb.start_vertices_bi[1]))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'

    Search in graph with reversed edges and with exchanged start and goal vertices.
    Since we exchange the adjacency functions instead of defining new ones with
    correct reporting, the edge directions reported below are to be interpreted in
    reversed directions.
    >>> l, p = nog.BSearchBreadthFirst(tuple(reversed(fb.next_vertices_bi))
    ...     ).start_from(start_and_goal_vertices=tuple(reversed(fb.start_vertices_bi)),
    ...                  build_path=True)
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {4: (4,)}}
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    ?<2: {'depth': 1, 'visited': {2, 3, 4}, 'paths': {2: (4, 2)}}
    >>> print(l, list(p))
    3 [4, 2, 1, 0]

    2. Labeled edges
    >>> traversal = nog.TraversalBreadthFirst(
    ...     next_edges=f.next_edges
    ... ).start_from(start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_visited(traversal, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 5}, 'paths': {1: (0, 1)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {6: (5, 6)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 6: {'depth': 1, 'visited': {0, 1, 2, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 1, 2, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 5, 6}, 'paths': {2: (0, 1, 2)}}
    -> 4: {'depth': 3, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {4: (0, 1, 2, 4)}}
    ? 3: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 4: {'depth': 3, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {4: (0, 1, 2, 4)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (0, 1, 2, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]

    >>> traversal = nog.TraversalDepthFirst(
    ...     next_edges=f.next_edges
    ... ).start_from(
    ...     start_vertices=f.start_vertices, build_paths=True, compute_depth=True)
    >>> results_with_visited(traversal, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'visited': {0, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    ? 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    -> 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 0: {'depth': 0, 'visited': {0, 3, 4, 5, 6}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]

    >>> traversal = nog.TraversalNeighborsThenDepth(
    ...     next_edges=f.next_edges
    ... ).start_from(
    ...     start_vertices=f.start_vertices, build_paths=True, compute_depth=True)
    >>> results_with_visited(traversal, f.start_vertices)
    After start: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'visited': {0, 5}, 'paths': {5: (5,)}}
    -> 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    ? 6: {'depth': 1, 'visited': {0, 5, 6}, 'paths': {6: (5, 6)}}
    -> 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'depth': 2, 'visited': {0, 3, 5, 6}, 'paths': {3: (5, 6, 3)}}
    -> 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 4: {'depth': 3, 'visited': {0, 3, 4, 5, 6}, 'paths': {4: (5, 6, 3, 4)}}
    ? 0: {'depth': 0, 'visited': {0, 3, 4, 5, 6}, 'paths': {0: (0,)}}
    -> 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 3, 4, 5, 6}, 'paths': {1: (0, 1)}}
    -> 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'depth': 2, 'visited': {0, 1, 2, 3, 4, 5, 6}, 'paths': {2: (0, 1, 2)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]

    >>> traversal = nog.TraversalTopologicalSort(
    ...     next_edges=f.next_edges
    ... ).start_from(start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_visited(traversal, f.start_vertices)
    After start: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 5}, 'paths':
      {0: (0,), 5: (5,)}}
    ? 5: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 5}, 'paths': {5: (5,)}}
    ? 6: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 5, 6}, 'paths': {6: (5,
      6)}}
    ? 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 3, 5, 6}, 'paths': {3:
      (5, 6, 3)}}
    ? 4: {'depth': 3, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {4: (5, 6, 3, 4)}}
    -> 4: {'depth': 3, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {4: (5, 6, 3, 4)}}
    -> 3: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {3: (5, 6, 3)}}
    -> 6: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {6: (5, 6)}}
    -> 5: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {5: (5,)}}
    ? 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 3, 4, 5, 6}, 'paths':
      {0: (0,)}}
    ? 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 3, 4, 5, 6},
      'paths': {1: (0, 1)}}
    ? 2: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {2: (0, 1, 2)}}
    -> 2: {'depth': 2, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {2: (0, 1, 2)}}
    -> 1: {'depth': 1, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {1: (0, 1)}}
    -> 0: {'depth': 0, 'cycle_from_start': [], 'visited': {0, 1, 2, 3, 4, 5, 6},
      'paths': {0: (0,)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All visited: [0, 1, 2, 3, 4, 5, 6]

    >>> search =  nog.BSearchBreadthFirst(next_edges=fb.next_edges_bi)
    >>> l, p = search.start_from(start_and_goal_vertices=((), fb.goal_vertices))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(start_and_goal_vertices=(fb.start_vertices, ()))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(start_and_goal_vertices=((), fb.goal_vertices),
    ...                          fail_silently=True)
    >>> print(l, type(p))
    -1 <class 'nographs._path.PathOfUnlabeledEdges'>
    >>> l, p = search.start_from(start_and_goal_vertices=(fb.start_vertices, ()),
    ...                          fail_silently=True)
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {}}
    >>> print(l, type(p))
    -1 <class 'nographs._path.PathOfUnlabeledEdges'>

    >>> l, p = search.start_from(start_and_goal_vertices=fb.start_vertices_bi)
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {}}
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {}}
    >>> print(l, f.goal not in p)
    3 True
    >>> l, p = search.start_from(start_and_goal_vertices=fb.start_vertices_bi,
    ...                          build_path=True)
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {4: (4,)}}
    ? 1: {'depth': 1, 'visited': {0, 1, 5, 6}, 'paths': {1: (0, 1)}}
    >>> print(l, list(p))
    3 [0, 1, 2, 4]

    Search in graph with reversed edges and with exchanged start and goal vertices.
    Since we exchange the adjacency functions instead of defining new ones with
    correct reporting, the edge directions reported below are to be interpreted in
    reversed directions.
    >>> l, p = nog.BSearchBreadthFirst(next_edges=tuple(reversed(fb.next_edges_bi))
    ...     ).start_from(start_and_goal_vertices=tuple(reversed(fb.start_vertices_bi)),
    ...                  build_path=True)
    ?<4: {'depth': 0, 'visited': {4}, 'paths': {4: (4,)}}
    ? 0: {'depth': 0, 'visited': {0, 5}, 'paths': {0: (0,)}}
    ? 5: {'depth': 0, 'visited': {0, 1, 5}, 'paths': {5: (5,)}}
    ?<2: {'depth': 1, 'visited': {2, 3, 4}, 'paths': {2: (4, 2)}}
    >>> print(l, list(p))
    3 [4, 2, 1, 0]
    """


class MultipleStartVerticesTraversalsWithWeights:
    """-- Traversal with multiple start vertex, last 3 traversal strategies --
    Correct traversal in case of multiple start vertices. No traversal in case of no
    start vertex.

    >>> f = FMultiStart()
    >>> fb = FMultiStartB()

    >>> traversal = nog.TraversalShortestPaths(
    ...     next_edges=f.next_edges)
    >>> traversal = traversal.start_from(
    ...     start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_distances(traversal, f.start_vertices)
    After start: {'distance': inf, 'depth': 0, 'distances': {0: 0, 5: 0}, 'paths':
      {0: (0,), 5: (5,)}}
    ? 5: {'distance': 0, 'depth': 0, 'distances': {5: 0}, 'paths': {5: (5,)}}
    ? 0: {'distance': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 1: {'distance': 1, 'depth': 1, 'distances': {1: 0}, 'paths': {1: (0, 1)}}
    ? 1: {'distance': 1, 'depth': 1, 'distances': {1: 0}, 'paths': {1: (0, 1)}}
    -> 6: {'distance': 1, 'depth': 1, 'distances': {6: 0}, 'paths': {6: (5, 6)}}
    ? 6: {'distance': 1, 'depth': 1, 'distances': {6: 0}, 'paths': {6: (5, 6)}}
    -> 3: {'distance': 2, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'distance': 2, 'depth': 2, 'distances': {3: 0}, 'paths': {3: (5, 6, 3)}}
    -> 2: {'distance': 2, 'depth': 2, 'distances': {2: 0}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'distance': 2, 'depth': 2, 'distances': {2: 0}, 'paths': {2: (0, 1, 2)}}
    -> 4: {'distance': 3, 'depth': 3, 'distances': {4: 0}, 'paths': {4: (5, 6, 3,
      4)}}
    ? 4: {'distance': 3, 'depth': 3, 'distances': {4: 0}, 'paths': {4: (5, 6, 3,
      4)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All distances: {0: 0, 5: 0, 6: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    >>> traversal = traversal.start_from(start_vertices=(), build_paths=True)
    >>> list(traversal)
    []

    >>> traversal = nog.TraversalShortestPathsInfBranchingSorted(
    ...     next_edges=f.next_edges)
    >>> traversal = traversal.start_from(
    ...     start_vertices=f.start_vertices, build_paths=True)
    >>> results_with_distances(traversal, f.start_vertices)
    After start: {'distance': inf, 'distances': {0: inf, 5: inf}, 'paths': {0: (0,),
      5: (5,)}}
    ? 5: {'distance': 0, 'distances': {5: inf}, 'paths': {5: (5,)}}
    ? 0: {'distance': 0, 'distances': {0: inf}, 'paths': {0: (0,)}}
    -> 1: {'distance': 1, 'distances': {1: inf}, 'paths': {1: (0, 1)}}
    ? 1: {'distance': 1, 'distances': {1: inf}, 'paths': {1: (0, 1)}}
    -> 6: {'distance': 1, 'distances': {6: inf}, 'paths': {6: (5, 6)}}
    ? 6: {'distance': 1, 'distances': {6: inf}, 'paths': {6: (5, 6)}}
    -> 3: {'distance': 2, 'distances': {3: inf}, 'paths': {3: (5, 6, 3)}}
    ? 3: {'distance': 2, 'distances': {3: inf}, 'paths': {3: (5, 6, 3)}}
    -> 2: {'distance': 2, 'distances': {2: inf}, 'paths': {2: (0, 1, 2)}}
    ? 2: {'distance': 2, 'distances': {2: inf}, 'paths': {2: (0, 1, 2)}}
    -> 4: {'distance': 3, 'distances': {4: inf}, 'paths': {4: (5, 6, 3, 4)}}
    ? 4: {'distance': 3, 'distances': {4: inf}, 'paths': {4: (5, 6, 3, 4)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (5, 6, 3, 4), (5,), (5, 6)]
    All distances: {0: inf, 5: inf, 1: inf, 6: inf, 3: inf, 2: inf, 4: inf}
    >>> traversal = traversal.start_from(start_vertices=(), build_paths=True)
    >>> list(traversal)
    []

    >>> traversal = nog.TraversalMinimumSpanningTree(
    ...     next_edges=f.next_edges)
    >>> traversal = traversal.start_from(
    ...     start_vertices=f.start_vertices, build_paths=True)
    >>> results_standard(traversal, f.start_vertices)
    After start: {'edge': None, 'paths': {0: (0,), 5: (5,)}}
    ? 0: {'edge': None, 'paths': {0: (0,)}}
    ? 5: {'edge': None, 'paths': {5: (5,)}}
    -> 1: {'edge': (0, 1, 1), 'paths': {1: (0, 1)}}
    ? 1: {'edge': (0, 1, 1), 'paths': {1: (0, 1)}}
    -> 6: {'edge': (5, 6, 1), 'paths': {6: (5, 6)}}
    ? 6: {'edge': (5, 6, 1), 'paths': {6: (5, 6)}}
    -> 2: {'edge': (1, 2, 1), 'paths': {2: (0, 1, 2)}}
    ? 2: {'edge': (1, 2, 1), 'paths': {2: (0, 1, 2)}}
    -> 3: {'edge': (6, 3, 1), 'paths': {3: (5, 6, 3)}}
    ? 3: {'edge': (6, 3, 1), 'paths': {3: (5, 6, 3)}}
    -> 4: {'edge': (2, 4, 1), 'paths': {4: (0, 1, 2, 4)}}
    ? 4: {'edge': (2, 4, 1), 'paths': {4: (0, 1, 2, 4)}}
    All paths: [(0,), (0, 1), (0, 1, 2), (5, 6, 3), (0, 1, 2, 4), (5,), (5, 6)]
    >>> traversal = traversal.start_from(start_vertices=(), build_paths=True)
    >>> list(traversal)
    []


    >>> fa = FMultiStartAStar()
    >>> traversal = nog.TraversalAStar(next_edges=fa.next_edges)
    >>> traversal = traversal.start_from(
    ...     fa.heuristic, start_vertices=fa.start_vertices, build_paths=True)
    >>> results_standard(traversal, fa.start_vertices)
    After start: {'path_length': inf, 'depth': 0, 'distances': {0: 0, 1: 0},
      'paths': {0: (0,), 1: (1,)}}
    ? 1: {'path_length': 0, 'depth': 0, 'distances': {1: 0}, 'paths': {1: (1,)}}
    -> 3: {'path_length': 1, 'depth': 1, 'distances': {3: 1}, 'paths': {3: (1, 3)}}
    ? 3: {'path_length': 1, 'depth': 1, 'distances': {3: 1}, 'paths': {3: (1, 3)}}
    -> 5: {'path_length': 2, 'depth': 2, 'distances': {5: 2}, 'paths': {5: (1, 3,
      5)}}
    ? 5: {'path_length': 2, 'depth': 2, 'distances': {5: 2}, 'paths': {5: (1, 3,
      5)}}
    ? 0: {'path_length': 0, 'depth': 0, 'distances': {0: 0}, 'paths': {0: (0,)}}
    -> 2: {'path_length': 1, 'depth': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    ? 2: {'path_length': 1, 'depth': 1, 'distances': {2: 1}, 'paths': {2: (0, 2)}}
    -> 4: {'path_length': 1, 'depth': 1, 'distances': {4: 1}, 'paths': {4: (1, 4)}}
    ? 4: {'path_length': 1, 'depth': 1, 'distances': {4: 1}, 'paths': {4: (1, 4)}}
    All paths: [(0,), (1,), (0, 2), (1, 3), (1, 4), (1, 3, 5)]
    >>> traversal = traversal.start_from(
    ...     fa.heuristic, start_vertices=(), build_paths=True)
    >>> list(traversal)
    []

    >>> search = nog.BSearchShortestPath(fb.next_edges_bi)
    >>> l, p = search.start_from(start_and_goal_vertices = ((), fb.goal_vertices))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(start_and_goal_vertices = (fb.start_vertices, ()))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    >>> l, p = search.start_from(start_and_goal_vertices = ((), fb.goal_vertices),
    ...                          fail_silently=True)
    >>> print(l, type(p))
    inf <class 'nographs._path.PathOfUnlabeledEdges'>
    >>> l, p = search.start_from(start_and_goal_vertices = (fb.start_vertices, ()),
    ...                          fail_silently=True)
    >>> print(l, type(p))
    inf <class 'nographs._path.PathOfUnlabeledEdges'>

    >>> l, p = search.start_from(start_and_goal_vertices = fb.start_vertices_bi)
    ? 5: {}
    ?<4: {}
    ? 0: {}
    ?<3: {}
    ? 1: {}
    ?<2: {}
    ? 6: {}
    >>> print(l, fb.goal not in p)
    4 True
    >>> l, p = search.start_from(
    ...     start_and_goal_vertices = fb.start_vertices_bi, build_path=True)
    ? 5: {}
    ?<4: {}
    ? 0: {}
    ?<3: {}
    ? 1: {}
    ?<2: {}
    ? 6: {}
    >>> print(l, list(p))
    4 [5, 6, 3, 4]

    Search in graph with reversed edges and with exchanged start and goal vertices.
    Since we exchange the adjacency functions instead of defining new ones with
    correct reporting, the edge directions reported below are to be interpreted in
    reversed directions.
    >>> l, p = nog.BSearchShortestPath(tuple(reversed(fb.next_edges_bi))
    ...     ).start_from(start_and_goal_vertices=tuple(reversed(fb.start_vertices_bi)),
    ...                  build_path=True)
    ?<4: {}
    ? 5: {}
    ?<3: {}
    ? 0: {}
    ?<2: {}
    ? 1: {}
    >>> print(l, list(p))
    4 [4, 3, 6, 5]
    """


class InitiationForgotten:
    """Check if the library detects the mistake that start_from or one of the
    go_... methods are called on a traversal class instead of an object, i.e., the
    round brackets after the class name have been forgotten.

    >>> nog.TraversalBreadthFirst.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalBreadthFirst.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalBreadthFirst.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalBreadthFirst.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.
    >>> nog.TraversalBreadthFirst.go_for_depth_range(None, None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_depth_range can only be called on a Traversal object.

    >>> nog.TraversalDepthFirst.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalDepthFirst.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalDepthFirst.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalDepthFirst.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.

    >>> nog.TraversalNeighborsThenDepth.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalNeighborsThenDepth.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalNeighborsThenDepth.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalNeighborsThenDepth.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.

    >>> nog.TraversalShortestPaths.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalShortestPaths.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalShortestPaths.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalShortestPaths.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.
    >>> nog.TraversalShortestPaths.go_for_distance_range(None, None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_distance_range can only be called on a Traversal object.

    >>> nog.TraversalShortestPathsInfBranchingSorted.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalShortestPathsInfBranchingSorted.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalShortestPathsInfBranchingSorted.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalShortestPathsInfBranchingSorted.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.
    >>> nog.TraversalShortestPathsInfBranchingSorted.go_for_distance_range(
    ...     None, None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_distance_range can only be called on a Traversal object.

    >>> nog.TraversalAStar.start_from(None, None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalAStar.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalAStar.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalAStar.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.

    >>> nog.TraversalMinimumSpanningTree.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalMinimumSpanningTree.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalMinimumSpanningTree.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalMinimumSpanningTree.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.

    >>> nog.TraversalTopologicalSort.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a Traversal object.
    >>> nog.TraversalTopologicalSort.__iter__(None)
    Traceback (most recent call last):
    RuntimeError: Method go can only be called on a Traversal object.
    >>> nog.TraversalTopologicalSort.go_to(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_to can only be called on a Traversal object.
    >>> nog.TraversalTopologicalSort.go_for_vertices_in(None, None)
    Traceback (most recent call last):
    RuntimeError: Method go_for_vertices_in can only be called on a Traversal object.

    >>> nog.BSearchBreadthFirst.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a search strategy object.

    >>> nog.BSearchShortestPath.start_from(None)
    Traceback (most recent call last):
    RuntimeError: Method start_from can only be called on a search strategy object.
    """


class RandomExample:
    """
    Checks based on random example graph

    For each vertex: 3 pseudo-random edges in range(100)
    >>> def next_edges(v, *_):
    ...     for i in range(3):
    ...        yield hash(1/(v*10+i+1)) % 100, (v + i) % 3 + 1

    - Check some results of bidirectional searches against unidirectional strategies

    >>> next_forwards, next_backwards = adj_funcs_bi_from_list(
    ...     ((v, w, weight) for v in range(100) for w, weight in next_edges(v)),
    ...     edge_data=True, report_steps=False)

    >>> traversal = nog.TraversalBreadthFirst(next_edges=next_edges)
    >>> search = nog.BSearchBreadthFirst(next_edges=(next_forwards, next_backwards))

    >>> for i in range(0, 1, 10):
    ...     for j in range(50, 51, 10):
    ...         if i == j:
    ...             # Traversals do not report start vertices -> handle case manually
    ...             edge_count_uni = 0
    ...         else:
    ...             v = traversal.start_from(i).go_to(j, fail_silently=True)
    ...             # If the goal is not found, traversal.depth is the highest
    ...             # found depth. We manually return -1, like the search
    ...             # does it in this case.
    ...             edge_count_uni = -1 if v is None else traversal.depth
    ...         edge_count_bi, path = search.start_from((i, j), fail_silently=True)
    ...         if edge_count_uni != edge_count_bi:
    ...             print(f"Difference: {i=} {j=} {edge_count_uni=} {edge_count_bi=}")
    ...             print(tuple(traversal.paths[j]))
    ...             print(tuple(path))

    >>> search.start_from((0, 100))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'

    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> search = nog.BSearchShortestPath((next_forwards, next_backwards))

    >>> for i in range(0, 100, 10):
    ...     for j in range(0, 100, 10):
    ...         if i == j:
    ...             # Traversals do not report start vertices -> handled manually
    ...             distance_uni = 0
    ...         else:
    ...             v = traversal.start_from(i).go_to(j, fail_silently=True)
    ...             # If the goal is not found, traversal.distance is the highest
    ...             # found distance. We manually return infinity, like the search
    ...             # does it in this case.
    ...             distance_uni = float("inf") if v is None else traversal.distance
    ...         distance_bi, paths = search.start_from((i, j), fail_silently=True)
    ...         if distance_uni != distance_bi:
    ...             print(f"Difference: {i=} {j=} {distance_uni=} {distance_bi=}")

    >>> search.start_from((0, 100))
    Traceback (most recent call last):
    KeyError: 'No path to (a) goal vertex found'
    """


# --------- Tests for compatibility with different gears  -----------


class GearTestsTraversalsWithOrWithoutLabels:
    """
    -- TraversalShortestPathsFlex and TraversalBreadthFirstFlex
    with all kinds of gears --

    >>> def gear_test(gear):
    ...    f = FSpiral()
    ...    traversal = nog.TraversalShortestPathsFlex(nog.vertex_as_id,
    ...        gear, next_labeled_edges=f.next_edges)
    ...    vertex = traversal.start_from(f.start, build_paths=True).go_to(f.goal)
    ...    path = traversal.paths[vertex]
    ...    print([traversal.distance, tuple(path[:f.focus]), tuple(path[-f.focus:])])
    ...    traversal = nog.TraversalBreadthFirstFlex(nog.vertex_as_id, gear,
    ...        next_labeled_edges=f.next_edges)
    ...    vertex = traversal.start_from(f.start, build_paths=True).go_to(f.goal)
    ...    path = traversal.paths[vertex]
    ...    print([traversal.depth, tuple(path[:f.focus]), tuple(path[-f.focus:])])

    >>> gear_test(nog.GearForHashableVertexIDs(0, float("infinity")))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearDefault())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForHashableVertexIDsAndIntsMaybeFloats())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForHashableVertexIDsAndDecimals())
    [Decimal('24'), ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForHashableVertexIDsAndFloats())
    [24.0, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]

    >>> gear_test(nog.GearForIntVertexIDs(0, float("infinity")))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVertexIDsAndIntsMaybeFloats())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> # Switch off prefer_arrays
    >>> gear_test(nog.GearForIntVertexIDsAndIntsMaybeFloats(True, False))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> # Switch off use_bit_packing
    >>> gear_test(nog.GearForIntVertexIDsAndIntsMaybeFloats(False, True))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVertexIDsAndDecimals())
    [Decimal('24'), ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats())
    [24.0, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> # Switch off use_bit_packing
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats(True))
    [24.0, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVertexIDsAndCInts())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]

    >>> gear_test(nog.GearForIntVerticesAndIDs(0, float("infinity")))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVerticesAndIDsAndIntsMaybeFloats())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> # Switch off use_bit_packing
    >>> gear_test(nog.GearForIntVerticesAndIDsAndIntsMaybeFloats(False))
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVerticesAndIDsAndDecimals())
    [Decimal('24'), ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVerticesAndIDsAndCFloats())
    [24.0, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> # Switch off use_bit_packing
    >>> gear_test(nog.GearForIntVerticesAndIDsAndCFloats(True))
    [24.0, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]
    >>> gear_test(nog.GearForIntVerticesAndIDsAndCInts())
    [24, ((0, 1, 1), (1, 2, 3)), ((17, 11, 1), (11, 5, 1))]
    [5, ((0, 1, 1), (1, 2, 3)), ((3, 4, 7), (4, 5, 9))]


    -- TraversalShortestPathsInfBranchingSortedFlex with gears for Hashable --
    (output of TraversalShortestPathsFlex also shown, as comparison)

    >>> def gear_test(gear):
    ...    f = FSpiralSorted()
    ...    traversal = nog.TraversalShortestPathsFlex(nog.vertex_as_id,
    ...        gear, next_labeled_edges=f.next_edges)
    ...    vertex = traversal.start_from(f.start, build_paths=True).go_to(f.goal)
    ...    path = traversal.paths.iter_vertices_from_start(vertex)
    ...    print([traversal.distance, tuple(path)])
    ...    traversal = nog.TraversalShortestPathsInfBranchingSortedFlex(
    ...        gear, gear, f.next_edges)
    ...    vertex = traversal.start_from(f.start, build_paths=True).go_to(f.goal)
    ...    path = traversal.paths[vertex]
    ...    print([traversal.distance, tuple(path)])
    ...    # print([traversal.distance, tuple(path[:f.focus]), tuple(path[-f.focus:])])

    >>> gear_test(nog.GearForHashableVertexIDs(0, float("infinity")))
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    >>> gear_test(nog.GearDefault())
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    >>> gear_test(nog.GearForHashableVertexIDsAndIntsMaybeFloats())
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    [24, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    >>> gear_test(nog.GearForHashableVertexIDsAndDecimals())
    [Decimal('24'), (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    [Decimal('24'), (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    >>> gear_test(nog.GearForHashableVertexIDsAndFloats())
    [24.0, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]
    [24.0, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)]


    -- Three main gear types, one also without bit_packing, used for each of the
    traversals, graph is no tree. --

    For traversals dealing with distances, we need to test this gear functionality
    additionally.

    >>> f = FOvertaking()
    >>> test_gears = [nog.GearForHashableVertexIDsAndIntsMaybeFloats(),
    ...               nog.GearForIntVertexIDsAndCFloats(),
    ...               nog.GearForIntVerticesAndIDsAndCFloats(),
    ...               nog.GearForIntVerticesAndIDsAndCFloats(no_bit_packing=True),
    ...              ]
    >>> def gear_test_traversals(traversal_class, next_labeled_edges, *args, **nargs):
    ...     for gear in test_gears:
    ...         yield traversal_class(
    ...             nog.vertex_as_id, gear,
    ...             next_labeled_edges=next_labeled_edges,
    ...             *args, **nargs)

    >>> for t in gear_test_traversals(nog.TraversalBreadthFirstFlex, f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex, f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    For DFS, we also test without paths, because this changes the process
    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex, f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=False))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]

    >>> for t in gear_test_traversals(nog.TraversalNeighborsThenDepthFlex,
    ...                               f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    >>> for t in gear_test_traversals(nog.TraversalTopologicalSortFlex,
    ...                               f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    >>> for t in gear_test_traversals(nog.TraversalShortestPathsFlex,
    ...                               f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalShortestPathsFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(),
    ...     next_labeled_edges=f.next_edges)
    >>> print_partial_results(t.start_from(f.start, build_paths=True),
    ...                       paths_to=f.goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalShortestPathsFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=f.next_edges)
    >>> print_partial_results(t.start_from(f.start, build_paths=True),
    ...                       paths_to=f.goal
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than the infinity value 255 used by
    the chosen gear and its configuration

    >>> for t in gear_test_traversals(nog.TraversalMinimumSpanningTreeFlex,
    ...                               f.next_edges):
    ...    print_partial_results(t.start_from(f.start, build_paths=True),
    ...                          paths_to=f.goal)
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalAStarFlex, f.next_edges):
    ...    print_partial_results(
    ...        t.start_from(f.heuristic, f.start, build_paths=True),
    ...        paths_to=f.goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalAStarFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(),  # infinity overflow in distance
    ...     next_labeled_edges=f.next_edges)
    >>> print_partial_results(
    ...     t.start_from(f.heuristic, f.start, build_paths=True),
    ...     paths_to=f.goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalAStarFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=f.next_edges)
    >>> print_partial_results(
    ...     t.start_from(f.heuristic, f.start, build_paths=True),
    ...     paths_to=f.goal)  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than the infinity value 255 used by
    the chosen gear and its configuration
    >>> # Create infinity overflow of guessed distance (guess >= 255)
    >>> fs255 = FSequenceTo255()
    >>> t = nog.TraversalAStarFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=fs255.next_edges)
    >>> print_partial_results(
    ...     t.start_from(fs255.heuristic, fs255.start), paths_to=fs255.goal
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than the infinity value 255 used by
    the chosen gear and its configuration


    Tests for BSearchBreadthFirst and BSearchShortestPaths:
    >>> def test_for_gear(strategy_class, g):
    ...     s = strategy_class(nog.vertex_as_id, g,
    ...                        next_labeled_edges=f.next_edges_bi)
    ...     value, path = s.start_from((f.start, f.last_vertex), build_path=True)
    ...     path_tuple = tuple(path.iter_vertices_from_start())
    ...     check_path(path_tuple, f.next_edges)
    ...     print("--", str(type(g)).split("'")[1].split(".")[-1], "--")
    ...     print(value, path_tuple[:5], path_tuple[-5:])
    ...     for path_iter in (
    ...         path.iter_vertices_from_start(),
    ...         path.iter_vertices_to_start(),
    ...         path.iter_edges_from_start(),
    ...         path.iter_edges_to_start(),
    ...         path.iter_labeled_edges_from_start(),
    ...         path.iter_labeled_edges_to_start(),
    ...     ):
    ...         path_tuple = tuple(path_iter)
    ...         print(path_tuple[:3], path_tuple[-2:])

    For testing BidirectionalSearchBreadthFirst, we use the distances
    found by TraversalBreadthFirst as reference:
    >>> t = nog.TraversalBreadthFirst(next_edges=f.next_edges)
    >>> v = t.start_from(f.start, build_paths=True).go_to(f.last_vertex)
    >>> path = t.paths[f.last_vertex]
    >>> print(t.depth, path[:5], path[-5:], f.last_vertex)
    1034 (0, 1, 4, 5, 8) (3086, 3089, 3092, 3095, 3098) 3098

    >>> for g in test_gears:
    ...     test_for_gear(nog.BSearchBreadthFirstFlex, g)
    -- GearForHashableVertexIDsAndIntsMaybeFloats --
    1034 (0, 1, 4, 5, 8) (3086, 3089, 3092, 3095, 3098)
    (0, 1, 4) (3095, 3098)
    (3098, 3095, 3092) (1, 0)
    ((0, 1), (1, 4), (4, 5)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((1, 4), (0, 1))
    ((0, 1, 1), (1, 4, 1), (4, 5, 1)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((1, 4, 1), (0, 1, 1))
    -- GearForIntVertexIDsAndCFloats --
    1034 (0, 1, 4, 5, 8) (3086, 3089, 3092, 3095, 3098)
    (0, 1, 4) (3095, 3098)
    (3098, 3095, 3092) (1, 0)
    ((0, 1), (1, 4), (4, 5)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((1, 4), (0, 1))
    ((0, 1, 1), (1, 4, 1), (4, 5, 1)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((1, 4, 1), (0, 1, 1))
    -- GearForIntVerticesAndIDsAndCFloats --
    1034 (0, 1, 4, 5, 8) (3086, 3089, 3092, 3095, 3098)
    (0, 1, 4) (3095, 3098)
    (3098, 3095, 3092) (1, 0)
    ((0, 1), (1, 4), (4, 5)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((1, 4), (0, 1))
    ((0, 1, 1), (1, 4, 1), (4, 5, 1)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((1, 4, 1), (0, 1, 1))
    -- GearForIntVerticesAndIDsAndCFloats --
    1034 (0, 1, 4, 5, 8) (3086, 3089, 3092, 3095, 3098)
    (0, 1, 4) (3095, 3098)
    (3098, 3095, 3092) (1, 0)
    ((0, 1), (1, 4), (4, 5)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((1, 4), (0, 1))
    ((0, 1, 1), (1, 4, 1), (4, 5, 1)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((1, 4, 1), (0, 1, 1))


    For testing BidirectionalSearchShortestPath, we use the length of the
    shortest path found by TraversalShortestPaths as reference:
    >>> t = nog.TraversalShortestPaths(f.next_edges)
    >>> v = t.start_from(f.start, build_paths=True).go_to(f.last_vertex)
    >>> path = t.paths[f.last_vertex]
    >>> print(t.distance, path[:5], path[-5:], f.last_vertex)
    1034 (0, 3, 6, 9, 12) (3088, 3091, 3092, 3095, 3098) 3098

    >>> for g in test_gears:
    ...     test_for_gear(nog.BSearchShortestPathFlex, g)
    -- GearForHashableVertexIDsAndIntsMaybeFloats --
    1034 (0, 3, 6, 9, 12) (3086, 3089, 3092, 3095, 3098)
    (0, 3, 6) (3095, 3098)
    (3098, 3095, 3092) (3, 0)
    ((0, 3), (3, 6), (6, 9)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((3, 6), (0, 3))
    ((0, 3, 3), (3, 6, 1), (6, 9, 3)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((3, 6, 1), (0, 3, 3))
    -- GearForIntVertexIDsAndCFloats --
    1034.0 (0, 3, 6, 9, 12) (3086, 3089, 3092, 3095, 3098)
    (0, 3, 6) (3095, 3098)
    (3098, 3095, 3092) (3, 0)
    ((0, 3), (3, 6), (6, 9)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((3, 6), (0, 3))
    ((0, 3, 3), (3, 6, 1), (6, 9, 3)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((3, 6, 1), (0, 3, 3))
    -- GearForIntVerticesAndIDsAndCFloats --
    1034.0 (0, 3, 6, 9, 12) (3086, 3089, 3092, 3095, 3098)
    (0, 3, 6) (3095, 3098)
    (3098, 3095, 3092) (3, 0)
    ((0, 3), (3, 6), (6, 9)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((3, 6), (0, 3))
    ((0, 3, 3), (3, 6, 1), (6, 9, 3)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((3, 6, 1), (0, 3, 3))
    -- GearForIntVerticesAndIDsAndCFloats --
    1034.0 (0, 3, 6, 9, 12) (3086, 3089, 3092, 3095, 3098)
    (0, 3, 6) (3095, 3098)
    (3098, 3095, 3092) (3, 0)
    ((0, 3), (3, 6), (6, 9)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((3, 6), (0, 3))
    ((0, 3, 3), (3, 6, 1), (6, 9, 3)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((3, 6, 1), (0, 3, 3))

    >>> test_for_gear(nog.BSearchShortestPathFlex,
    ...               nog.GearForIntVerticesAndIDsAndCInts())
    -- GearForIntVerticesAndIDsAndCInts --
    1034 (0, 3, 6, 9, 12) (3086, 3089, 3092, 3095, 3098)
    (0, 3, 6) (3095, 3098)
    (3098, 3095, 3092) (3, 0)
    ((0, 3), (3, 6), (6, 9)) ((3092, 3095), (3095, 3098))
    ((3095, 3098), (3092, 3095), (3089, 3092)) ((3, 6), (0, 3))
    ((0, 3, 3), (3, 6, 1), (6, 9, 3)) ((3092, 3095, 3), (3095, 3098, 1))
    ((3095, 3098, 1), (3092, 3095, 3), (3089, 3092, 1)) ((3, 6, 1), (0, 3, 3))

    >>> test_for_gear(nog.BSearchShortestPathFlex,
    ...               nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B")
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than the infinity value 255 used by
    the chosen gear and its configuration


    Three main gear types, one also without bit_packing,
    used for each of the traversals, graph is tree
    (TraversalMinimumSpanningTreeFlex and the Search* are omitted, because they have
    no option is_tree):

    >>> f = FBinaryTreeFixedWeights()

    >>> for t in gear_test_traversals(nog.TraversalBreadthFirstFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...      print_partial_results(
    ...          t.start_from(f.start, build_paths=True),
    ...          paths_to=f.goal)
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...      print_partial_results(
    ...         t.start_from(f.start, build_paths=True),
    ...         paths_to=f.goal)
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    For DFS, we also test without paths, because this changes the process
    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...     print_partial_results(
    ...         t.start_from(f.start, build_paths=False))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]

    >>> for t in gear_test_traversals(nog.TraversalNeighborsThenDepthFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...     print_partial_results(
    ...         t.start_from(f.start, build_paths=True),
    ...         paths_to=f.goal)
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalTopologicalSortFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...     print_partial_results(
    ...         t.start_from(f.start, build_paths=True),
    ...         paths_to=f.goal)
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalShortestPathsFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...     print_partial_results(
    ...         t.start_from(f.start, build_paths=True),
    ...         paths_to=f.goal)
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    Here is no call to TraversalMinimumSpanningTreeFlex or the Search*, because they
    do not support option is_tree.

    >>> for t in gear_test_traversals(nog.TraversalAStarFlex,
    ...                               f.next_edges,
    ...                               is_tree=True):
    ...     print_partial_results(
    ...         t.start_from(f.heuristic,
    ...                      f.start, build_paths=True),
    ...         paths_to=f.goal)
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))


    Case for TraversTopologicalSorted, without and with cycle.
    Example from concept_and_examples.rst. Here, we number the vertices, so that we
    can use the gears for positive integer vertex ids.
    >>> depends_on = {"drink coffee": ["make coffee"],
    ...               "make coffee": ["stand up", "get water"],
    ...               "get water": ["stand up"]}
    >>> def next_vertices(task, _):
    ...     return depends_on.get(task, ())
    >>> vertex_to_id = dict(
    ...     (v_id, vertex) for vertex, v_id in
    ...     enumerate(("drink coffee", "make coffee", "stand up", "get water"))
    ... ).__getitem__
    >>> def gear_test(gear):
    ...    traversal = nog.TraversalTopologicalSortFlex(
    ...        vertex_to_id, gear, next_vertices)
    ...    print(tuple(traversal.start_from("drink coffee", build_paths=True)))
    >>> gear_test(nog.GearForHashableVertexIDsAndIntsMaybeFloats())
    ('stand up', 'get water', 'make coffee', 'drink coffee')
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats())
    ('stand up', 'get water', 'make coffee', 'drink coffee')
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats(no_bit_packing=True))
    ('stand up', 'get water', 'make coffee', 'drink coffee')

    >>> depends_on["get water"].append("make coffee")
    >>> gear_test(nog.GearForHashableVertexIDsAndIntsMaybeFloats())
    Traceback (most recent call last):
    RuntimeError: Graph contains cycle
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats())
    Traceback (most recent call last):
    RuntimeError: Graph contains cycle
    >>> gear_test(nog.GearForIntVertexIDsAndCFloats(no_bit_packing=True))
    Traceback (most recent call last):
    RuntimeError: Graph contains cycle
    """
