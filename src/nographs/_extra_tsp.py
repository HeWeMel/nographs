from collections.abc import Iterator, Iterable, Sequence
from typing import Any, Union, Optional, Protocol, TypeVar
from abc import abstractmethod
import functools
import operator

from ._types import (
    T_vertex,
    T_weight,
    vertex_as_id,
)
from ._gears import (
    Gear,
    GearDefault,
)
from ._strategies import BSearchShortestPathFlex

# -- Protocols --
T_key_contra = TypeVar("T_key_contra", contravariant=True)
T_value_co = TypeVar("T_value_co", covariant=True)


class GettableProto(Protocol[T_key_contra, T_value_co]):
    """
    Protocol for a subscriptable readable container.

    Examples:

    - A dict[str, float] is a GettableProto[str, float]
    - A tuple[str, ...] is a GettableProto[int, str]
    """

    @abstractmethod
    def __getitem__(self, item: T_key_contra) -> Optional[T_value_co]:
        """
        Get the value that is stored for key *item*.
        If the Gettable does not contain *item*, a KeyError or an IndexError might
        be raised, or None is returned.
        """
        raise NotImplementedError


# -- Support functions ---
# For dealing with negative weights and/or search for longest travel.
# Exported for use in tests.


def weight_changes_for_negative_weights(
    weights: Iterator[T_weight], zero: T_weight
) -> tuple[bool, T_weight, bool]:
    """
    Return the necessary weight_factor and weight_offset for solving a TSP for
    shortest paths, if the weights are not guaranteed to be non-negative by using a
    TSP algorithm for only non-negative graph

    For avoiding negative weights, add a constant to the weights - we choose the
    positive value of the most negative weight. When using the results, revert that
    change accordingly. Note: For each edge of the resulting path, the constant goes
    into the resulting total distance exactly once.

    :weights: Iterates all non-None weights of the graph
    :one: Neutral element of the multiplication within T_weight
    """
    negate_weights = False
    weight_offset = zero - min(zero, min((weight for weight in weights), default=zero))
    return negate_weights, weight_offset, weight_offset != zero


def weight_changes_for_find_longest(
    weights: Iterator[T_weight], zero: T_weight
) -> tuple[bool, T_weight]:
    """
    Returns the necessary weight_factor and weight_offset for solving a TSP for
    longest path, if the weights are not guaranteed to be non-negative by using a TSP
    algorithm for only non-negative graph

    For finding the longest path, negate the weight. In order to avoid negative
    weights, we do the same correction as in weight_changes_for_negative_weights,
    but for the negated weight.

    :weights: Iterates all non-None weights of the graph
    :one: Neutral element of the multiplication within T_weight
    """
    negate_weights = True
    weight_offset = zero - min(
        zero, min((zero - weight for weight in weights), default=zero)
    )
    return negate_weights, weight_offset


def undo_weight_changes_in_travel_length(
    length: T_weight,
    no_of_edges: int,
    zero: T_weight,
    negate_weights: bool,
    weight_offset: T_weight,
) -> T_weight:
    # Undo the addition of weight_offset, that affects the path length
    # no_of_edges times.
    # (We have no multiplication in T_weight, so we repeat a subtraction. But since we
    # do this only once per vertex in the path, the additional runtime does not matter.)
    for _i in range(no_of_edges):
        length -= weight_offset
    # Undo the negation of the edge weights. We can do this in one step for the whole
    # path length.
    return zero - length if negate_weights else length


# -------- TSP solution with integer-bases sets --------

IntVertex = int


def _traveling_salesman_int_vertices(
    graph: Sequence[Sequence[Optional[T_weight]]],
    gear: Gear[int, int, T_weight, Any],
    find_longest: bool = False,
) -> tuple[T_weight, Iterator[IntVertex]]:
    """
    Like traveling_salesman_flex, but the implementation is optimized for the
    case of integer vertices, and a graph needs to be a sequence of sequences of
    weights that forms a quadratic matrix:

    - Nested mappings are not allowed.
    - The matrix needs to be quadratic (vertices cannot be "left out", neither
      as source vertex of edges nor as target vertex of edges).
    - It is not possible to define a subset of vertices that the TSP tour need
      to use - automatically, all vertices will be visited.
    - If there is no edge between two vertices v and w, graph[v][w] needs to return
      None.

    :param graph: For each pair of vertices *v* and *w*, *graph* [*v*][*w*] is the
        weight of the edge from *v* to *w*.
    :param gear: The `gear` to be used internally (where vertices and vertex ids are
        represented by integers).
    :param find_longest: True means, find path with longest instead of shortest
        total distance.
    :return: Length of the found travel, and an iterator for the path of vertices
    :rtype: tuple[T_weight, Iterator[IntVertex]]
    """
    # Above, the rtype is documented manually because Sphinx autodocs with
    # option autodoc_typehints = 'description' cannot correctly
    # evaluate the type parameters of tuple (whilst typing.Tuple works).

    zero = gear.zero()

    # Solve TSPs with negative weights or with search for longest travels by using
    # TSP solution for positive weights, where the weights are manipulated in a
    # specific way, and the found travel length is corrected for that afterwards
    iter_weights = (weight for edges in graph for weight in edges if weight is not None)
    if find_longest:
        negate_weights, weight_offset = weight_changes_for_find_longest(
            iter_weights, zero
        )
        weights_changed = True
    else:
        (
            negate_weights,
            weight_offset,
            weights_changed,
        ) = weight_changes_for_negative_weights(iter_weights, zero)

    """ Solve TSP for non-negative weights
    See example in the tutorial that explains the concept of the algorithms.

    Implementation notes for the following optimized implementation:
    For memory and runtime efficiency, a search graph vertex is represented just
    by an integer. This is done as follows:
    - Sets of base graph vertices, e.g. the set of remaining vertices, are represented
      by the bits of an integer
    - The search graph vertex (a tuple) is encoded as:
      vertex_id + set_of_remaining_vertices * no_of_vertices
    """

    # --- Compute data about given graph and check if graph is well-formed ---
    # Size
    no_of_vertices = len(graph)
    if no_of_vertices < 2:
        # A TSP solution for a graph with just one vertex could be defined as being
        # a self-loop (is present in the graph), because "TSP-solutions for n-vertex
        # graphs have n edges", or as being an empty path (because "the salesman
        # does not need to travel). We do not decide here and exclude this case.
        # And it is also unclear, what a TSP solution in an empty graph should be
        # (also the empty path?).
        raise RuntimeError("A TSP needs to have at least two vertices.")

    # Is matrix quadratic?
    for v, edges in enumerate(graph):
        if len(edges) != no_of_vertices:
            raise RuntimeError(
                f"For vertex {v}, {len(edges)} edges instead of "
                + f"{no_of_vertices} edges are given."
            )

    # Pack transformed edge weights in nested tuples
    graph_forwards = tuple(
        tuple(
            (
                None
                if (weight := graph[v][w]) is None
                else (zero - weight if negate_weights else weight) + weight_offset
            )
            for w in range(no_of_vertices)
        )
        for v in range(no_of_vertices)
    )

    # The same, but for for incoming (!) edges of some vertex
    graph_backwards = tuple(
        tuple(
            (
                None
                if (weight := graph[w][v]) is None
                else (zero - weight if negate_weights else weight) + weight_offset
            )
            for w in range(no_of_vertices)
        )
        for v in range(no_of_vertices)
    )

    # arbitrary vertex to start (and end) paths with:
    start_vertex = 0

    # --- Define start and goal state of search graph ---

    # Vertices to visit when at start: all vertices, without start vertex
    # (vertex set containing only start vertex, as bitmask)
    start_vertices = 1 << start_vertex
    all_vertices = (1 << no_of_vertices) - 1  # set (bit mask) of all vertices
    vertices_to_visit = all_vertices - start_vertices

    # Start and goal states
    # Each as tuple (Current vertex, vertices still to visit afterwards)
    # Each tuple is encoded as a single integer as follows.
    start_state = start_vertex + vertices_to_visit * no_of_vertices
    goal_state = start_vertex + 0 * no_of_vertices

    # --- Define edges of search graph, by functions (both directions) ---

    # Precompiled adjacency matrix: For each vertex, the set of adjacent vertices (as
    # bit mask) (Typically, the adjacency matrix of a TSP is a full matrix. But in
    # order to get a better performance for sparse adjacency, the adjacency matrix is
    # precompiled from the graph, to avoid unnecessary failing dict lookups.)
    adjacent_vertices_forwards = tuple(
        functools.reduce(
            operator.or_,
            (
                (
                    1 << to_vertex
                    if from_vertex != to_vertex
                    and edges_from_vertex[to_vertex] is not None
                    else 0
                )
                for to_vertex in range(no_of_vertices)
            ),
            0,
        )
        for from_vertex, edges_from_vertex in enumerate(graph_forwards)
    )
    if not all(adjacent_vertices_forwards):
        raise KeyError(
            "No solution for the TSP exists: " + "Some vertices have no outgoing edges."
        )
    adjacent_vertices_backwards = tuple(
        functools.reduce(
            operator.or_,
            (
                (
                    1 << to_vertex
                    if from_vertex != to_vertex
                    and edges_from_vertex[to_vertex] is not None
                    else 0
                )
                for to_vertex in range(no_of_vertices)
            ),
            0,
        )
        for from_vertex, edges_from_vertex in enumerate(graph_backwards)
    )
    if not all(adjacent_vertices_backwards):
        raise KeyError(
            "No solution for the TSP exists: " + "Some vertices have no incoming edges."
        )

    def next_edges_forwards(state: int, _: Any) -> Iterable[tuple[int, T_weight]]:
        # 1. Interpret search graph vertex in terms of original graph
        to_visit_forwards, vertex = divmod(state, no_of_vertices)

        # 2. Yield edges in the search graph based on all existing edges in the base
        # graph from the current vertex to one of the vertices not visited in the
        # current travel so far. When all vertices are visited in the travel,
        # go to start vertex.
        if to_visit_forwards == 0:
            # At the last step forwards, the start vertex can be visited
            to_visit_forwards = start_vertices
        to_visit_next = to_visit_forwards & adjacent_vertices_forwards[vertex]
        edges_from_here = graph_forwards[vertex]
        while to_visit_next:
            to_vertex = to_visit_next.bit_length() - 1  # highest vertex in set
            to_vertex_set = 1 << to_vertex  # vertex (bit)set with just that vertex
            # weight of the edge (from_vertex, to_vertex):
            # (cannot be None, since we only iterate the non-None weights)
            weight: T_weight = edges_from_here[to_vertex]  # type: ignore[assignment]
            vertices_remaining_to_visit = to_visit_forwards - to_vertex_set
            yield (to_vertex + vertices_remaining_to_visit * no_of_vertices, weight)
            to_visit_next -= to_vertex_set  # to_vertex has been done

    def next_edges_backwards(state: int, _: Any) -> Iterable[tuple[int, T_weight]]:
        # 1. Interpret search graph vertex in terms of original graph
        to_visit_forwards, vertex = divmod(state, no_of_vertices)

        # 2. Yield edges in the search graph based on all existing edges in the base
        # graph to the current vertex from one of the vertices not visited in the
        # current travel so far. When all vertices are visited in the travel,
        # go to start vertex.
        to_visit_next = all_vertices - to_visit_forwards
        if to_visit_next != start_vertices:
            # Only at last step backwards, the start vertex can be visited
            to_visit_next -= start_vertices
        to_visit_next &= adjacent_vertices_backwards[vertex]
        edges_to_here = graph_backwards[vertex]
        vertices_remaining_to_visit = (
            to_visit_forwards
            if vertex == start_vertex
            else to_visit_forwards + (1 << vertex)
        )
        while to_visit_next:
            from_vertex = to_visit_next.bit_length() - 1  # highest vertex in set
            from_vertex_set = 1 << from_vertex  # vertex (bit)set with just that vertex
            # weight of the edge (from_vertex, to_vertex):
            # (cannot be None, since we only iterate the non-None weights)
            weight: T_weight = edges_to_here[from_vertex]  # type: ignore[assignment]
            yield (from_vertex + vertices_remaining_to_visit * no_of_vertices, weight)
            to_visit_next -= from_vertex_set  # from_vertex has been done

    s = BSearchShortestPathFlex[int, int, T_weight, Any](
        vertex_as_id, gear, (next_edges_forwards, next_edges_backwards)
    )

    try:
        length, state_path = s.start_from((start_state, goal_state), build_path=True)
    except KeyError:
        raise KeyError("No solution for the TSP exists.")

    # for the found path, return weight sum and vertices
    # (remove sets of remaining vertices)
    vertex_path = (v1 % no_of_vertices for v1 in state_path.iter_vertices_from_start())
    if weights_changed:
        # correct the found travel length
        length = undo_weight_changes_in_travel_length(
            length, no_of_vertices, zero, negate_weights, weight_offset
        )
    return length, vertex_path


def traveling_salesman_flex(
    vertices: Iterable[T_vertex],
    weights: GettableProto[T_vertex, GettableProto[T_vertex, T_weight]],
    gear: Gear[int, int, T_weight, Any],
    find_longest: bool = False,
) -> tuple[T_weight, Iterator[T_vertex]]:
    """
    Solve the traveling salesmen problem in directed graphs, in a slightly
    more general and flexible form than that of typical implementations. Performance
    has been a design goal.

    Find the path with the shortest, resp. the longest,
    length (sum of edge weights) through the relevant vertices (at least two), where
    each of these vertices is visited exactly once, in the form of a loop.

    If no solution can be found, raise a KeyError. If the problem is not well-defined,
    raise a RuntimeError.

    Flexibility:

    - Vertices can be any object except for None.

    - Edge weights can be positive, negative or zero.

    - The graph does not need to be symmetric (symmetric means: for each edge
      (i, j, weight), an edge (j, i, weight) exists).

    - The graph does not need to be complete (complete means: from each vertex there
      is an edge to all other vertices) and the algorithms profits
      if the graph is not complete.

    - Self-loops (i.e., an edge from a vertex to itself) are allowed (and will be
      ignored)

    - Optionally, a longest path is searched, instead of a shortest.

    - Edges from and to irrelevant vertices are allowed (and will be ignored)

    The function is an implementation of the algorithm shown in the
    `tutorial <reduction_of_other_problems>`,
    but it is based on the bidirectional search `BSearchShortestPathFlex`
    instead of the unidirectional traversal `TraversalShortestPaths`. And internally,
    it works with bit arrays instead of vertex sets.

    Recipes for solving other, but similar problems:

    - Your graph has multi-edges (i.e., from two vertices v and w, there are
      several edges from v to w): Give only the edge with the lowest edge
      weight between such vertices v and w.

    - Your graph is undirected: Give each edge in both directions.

    - Vertices can be visited multiple times: Build the distance graph
      and give it as input instead of your original graph.
      The distance graph can be computed by applying the traversal strategy
      `TraversalShortestPaths` for each of the vertices. Then, each tuple
      (start_vertex, reached_vertex, distance) is an edge of the distance
      graph. Save these edges, and the respective paths. When the TSP
      is solved on the distance graph, replace each edge in the result
      by the respective path of the original graph.

    :param vertices: The computed circle need to go through each of them exactly
        once. See `T_vertex`.
    :param weights: For each pair of vertices *v* and *w*, *weights* [*v*][*w*] is the
        weight of the edge from *v* to *w*, if the edge exists. Otherwise, a
        KeyError or an IndexError is raised, or None is returned. This allows
        for providing weights in nested tuples, lists or Mappings.
    :param gear: The `Gear` to be used internally (where vertices and vertex ids are
        represented by integers).
    :param find_longest: True means, find path with the longest instead of the
        shortest total distance
    :return: Length of the found travel, and an iterator for the path of vertices.
    :rtype: tuple[T_weight, Iterator[T_vertex]]
    """
    # See above why the rtype is documented manually

    vertex_tuple = tuple(vertices)
    no_of_vertices = len(vertex_tuple)

    # Generate quadratic matrix of weights
    int_graph = list[list[Optional[T_weight]]](
        [None] * no_of_vertices for v in range(no_of_vertices)
    )
    edge_to_vertex = [False] * no_of_vertices
    for v_int, v in enumerate(vertex_tuple):
        try:
            edges_from_v = weights[v]
        except (IndexError, KeyError):
            continue
        if edges_from_v is not None:
            for w_int, w in enumerate(vertex_tuple):
                try:
                    weight = edges_from_v[w]
                except (IndexError, KeyError):
                    continue
                if weight is not None:
                    int_graph[v_int][w_int] = weight
                    edge_to_vertex[w_int] = True

    # Solve TSP by using TSP solution for graphs with integer vertices
    length, path_raw = _traveling_salesman_int_vertices(int_graph, gear, find_longest)

    # Undo replacement of vertices by integers in the found path
    path = (vertex_tuple[v] for v in path_raw)

    return length, path


def traveling_salesman(
    vertices: Iterable[T_vertex],
    weights: GettableProto[T_vertex, GettableProto[T_vertex, T_weight]],
    find_longest: bool = False,
) -> tuple[Union[T_weight, float], Iterator[T_vertex]]:
    """
    Like `traveling_salesman_flex`, see there,
    but the gear is `GearDefault`, see also there.

    Note: As usual with GearDefault, the type for weight results (here: the path
    length) is extended by float. In case of `traveling_salesman`, a float will
    never be returned, if your graph does not contain float edge weights and the
    arithmetic operations on edge weights that are used (see `T_weight`) do not
    return floats. The reason is, that unsolvable TSP problems raise a KeyError,
    instead of returning a infinite path length.
    Use `traveling_salesman_flex` and choose another `Gear` if you like to have
    a stricter type specification (see also tutorial section `typing`).

    :param vertices: The computed circle need to go through each of them exactly
        once. See `T_vertex`.
    :param weights: For each pair of vertices *v* and *w*, *weights* [*v*][*w*] is the
        weight of the edge from *v* to *w*, if the edge exists. Otherwise, a
        KeyError or an IndexError is raised, or None is returned. This allows
        for providing weights in nested tuples, lists or Mappings.
    :param find_longest: True means, find path with the longest instead of the
        shortest total distance
    :return: Length of the found travel, and an iterator for the path of vertices.
    :rtype: tuple[Union[T_weight, float], Iterator[T_vertex]]
    """
    # See above why the rtype is documented manually

    # The following is a Gear[int, int, Union[T_weight, float], Any]
    gear = GearDefault[int, int, T_weight, Any]()
    return traveling_salesman_flex(vertices, weights, gear, find_longest=find_longest)
