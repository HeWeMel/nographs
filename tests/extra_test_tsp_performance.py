from collections.abc import Mapping, Iterator, MutableMapping
from typing import Any, Iterable
import collections

from nographs import (  # types
    T_vertex,
    T_weight,
    vertex_as_id,
)

from nographs import (  # ._gears
    GearForHashableVertexIDs,
)

from nographs import BSearchShortestPathFlex  # ._bidir_search

# noinspection PyProtectedMember
from nographs._extra_tsp import (
    weight_changes_for_negative_weights,
    weight_changes_for_find_longest,
    undo_weight_changes_in_travel_length,
)
from nographs import (  # ._extras
    traveling_salesman_flex,
    traveling_salesman,
)

from nographs import (  # ._gears
    # GearForHashableVertexIDs,
    GearForIntVertexIDsAndCFloats,
    GearForIntVerticesAndIDsAndCFloats,
    GearForIntVerticesAndIDsAndCInts,
)

from test_extra_tsp import (
    TSP_gr_21,
    ATSP_br17,
    read_tsp_problem,
    solve,
)

"""
Performance comparisons. Results printed to stdout.
Not part of the test suite of the library.

Need to be called manually, if needed.
"""


# --- Local reference implementation (not used and not exported) ---

T_state = tuple[T_vertex, frozenset[T_vertex]]


def _traveling_salesman_basic(
    graph: Mapping[T_vertex, Mapping[T_vertex, T_weight]],
    zero: T_weight,
    inf: T_weight,
    find_longest: bool = False,
) -> tuple[T_weight, Iterator[T_vertex]]:
    """
    TSP solver without integer-based sets (not used and not exported)

    The following is a basic implementation of a TSP solver. It is not used
    in the library or the documentation. It is solely used to compare the
    performance of the official implementations against it.

    ---

    Traveling salesmen problem: Find the path with shortest (resp. longest) length
    (sum of edge graph) through all vertices, where each vertex is visited exactly
    once, in the form of a loop.

    _traveling_salesman_basic is a variant of the algorithm shown in the tutorial.
    It is based on the bidirectional search of shortest path.

    The *graph* needs to contain at least one outgoing edge for each of the vertices
    that occur in some edge.

    An edge weight can be positive, negative or zero. If two vertices are connected by
    two edges in opposite directions, the edges can have different graph.

    The graph does not need to be total (total means: from each vertex, there is an
    edge to all other vertices), and the algorithms profits if it is not.

    THIS VERSION IS NOT EXPORTED AND NOT USED FOR EXPORTED FUNCTIONALITY. It is
    only there as reference for the version that is based on integers and for
    the unidirectional version shown in the docs.

    :param graph: For each vertex *v* that occurs in the graph, mapping *graph*
        returns a mapping, that contains elements {w: weight} for each
        edge (v, w, weight) of the graph.
    :param zero: Neutral element of weights type w.r.t. addition
       (e.g., 1.0 for float)
    :param inf: Infinite element of weights type w.r.t. comparison
       (e.g., float("infinity") for float)
    :param find_longest: True means, find path with longest instead of shortest total
        distance
    :return: Length of the shortest path of the traveling salesman problem, and
        Iterable that yields the vertices of this path. Both are None if no
        path have been found at all (problem in graph data).
    """

    # Solve TSPs with negative weights or with search for longest travels by using
    # TSP solution for positive weights, where the weights are manipulated in a
    # specific way, and the found travel length is corrected for that afterwards
    iter_weights = (
        weight
        for edges_from_vertex in graph.values()
        for weight in edges_from_vertex.values()
        if weight is not None
    )
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

    """
    Solve TSP for non-negative weights. A dynamic programming approach, typically
    faster than brute-force, but still with exponential running time.

    The algorithm has similarities to the Held–Karp algorithm: It calculates
    intermediate results D(S, c), the minimum distance of travels starting in city 1,
    visiting all cities in S and finishing at city c (to be exact: it uses Nodes - S
    instead of S). But it uses the bidirectional Dijkstra algorithm with minimum heaps
    of  distances to steer the search: It goes from smaller D's to larger ones and thus
    can stop if the first (the smallest) total travel is found. That often avoids
    some computation work.

    Concept of the solution for the base case:
    Create problem specific search graph for doing the search with the
    traverse_shortest_paths algorithm:
    - Search graph vertex: tuple (current base graph vertex, base graph vertices
      remaining for rest of travel)
    - Search graph start vertex: tuple (arbitrary base graph vertex, all base graph
      vertices)
    - Edge in search graph: From a base graph vertex to one of the remaining vertices,
      the vertex taken out of the  remaining vertices for the search graph end vertex,
      and with the weight between the two vertices.
    - Return of Dijkstra: length of shortest travel, and path
    - Return of end result: the same, but with the base graph vertices instead of the
      complete search graph vertices
    """

    # --- Compute data about given graph ---

    no_of_vertices = len(graph)
    if no_of_vertices < 2:
        # A TSP solution for a graph with just one vertex could be defined as being
        # a self-loop (is present in the graph), because "TSP-solutions for n-vertex
        # graphs have n edges", or as being an empty path (because "the salesman
        # does not need to travel). We do not decide here and exclude this case.
        # And it is also unclear, what a TSP solution in an empty graph should be
        # (also the empty path?).
        raise KeyError("A TSP needs to have at least two vertices.")

    # Determine edge weights for incoming (!) edges of some vertex
    transposed_graph: MutableMapping[T_vertex, MutableMapping[T_vertex, T_weight]]
    transposed_graph = collections.defaultdict(dict)
    for vertex, edges_from_vertex in graph.items():
        for to_vertex, weight in edges_from_vertex.items():
            transposed_graph[to_vertex][vertex] = weight

    # Vertex to start (and end) paths with: arbitrary vertex
    start_vertex = next(iter(graph))

    # --- Define start and goal state of search graph ---

    # Vertices to visit when at start: all vertices, without start vertex
    set_of_all_vertices = frozenset(graph)
    set_of_start_vertex = frozenset((start_vertex,))
    vertices_to_visit_at_start = set_of_all_vertices.difference(set_of_start_vertex)

    # Start states: Vertex to start at, vertices still to visit afterwards
    start_state = (start_vertex, vertices_to_visit_at_start)
    goal_state = (start_vertex, frozenset[T_vertex]())

    # --- Define edges of search graph, by functions (both directions) ---

    def next_edges_forwards(
        state: T_state[T_vertex], _: Any
    ) -> Iterable[tuple[T_state[T_vertex], T_weight]]:
        vertex, to_visit_forwards = state
        edges_from_here = graph[vertex]
        # At the last step forwards, the start vertex can be visited
        to_visit_next = to_visit_forwards if to_visit_forwards else set_of_start_vertex
        if len(edges_from_here) != no_of_vertices:
            to_visit_next = to_visit_next.intersection(edges_from_here.keys())
        for to_vertex in to_visit_next:
            weight = edges_from_here[to_vertex]
            yield (
                to_vertex,
                to_visit_forwards.difference((to_vertex,)),
            ), (zero - weight if negate_weights else weight) + weight_offset

    def next_edges_backwards(
        state: T_state[T_vertex], _: Any
    ) -> Iterable[tuple[T_state[T_vertex], T_weight]]:
        vertex, to_visit_forwards = state
        edges_to_here = transposed_graph[vertex]
        to_visit_next = set_of_all_vertices - to_visit_forwards
        if len(to_visit_next) != 1:
            # Only at last step backwards, the start vertex can be visited
            to_visit_next -= set_of_start_vertex
        if len(edges_to_here) != no_of_vertices:
            to_visit_next = to_visit_next.intersection(edges_to_here.keys())
        vertices_to_visit_one_step_before = (
            to_visit_forwards
            if vertex == start_vertex
            else to_visit_forwards.union((vertex,))
        )
        for from_vertex in to_visit_next:
            weight = edges_to_here[from_vertex]
            yield (
                from_vertex,
                vertices_to_visit_one_step_before,
            ), (zero - weight if negate_weights else weight) + weight_offset

    gear = GearForHashableVertexIDs[
        T_state[T_vertex], T_state[T_vertex], T_weight, Any
    ](zero, inf)
    try:
        t = BSearchShortestPathFlex[
            T_state[T_vertex], T_state[T_vertex], T_weight, Any
        ](vertex_as_id, gear, (next_edges_forwards, next_edges_backwards))
    except KeyError:
        raise KeyError("No solution for the TSP exists.")

    length, path = t.start_from((start_state, goal_state), build_path=True)
    it = path.iter_vertices_from_start()
    vertex_path = (vertex for vertex, vertices_to_visit in it)

    if weights_changed:
        # correct the found travel length
        length = undo_weight_changes_in_travel_length(
            length, no_of_vertices, zero, negate_weights, weight_offset
        )
    return length, vertex_path


# --- Run the comparison ---


if __name__ == "__main__":
    # First, we do the doc tests for the reference implementation
    import doctest

    doctest.testmod()

    # Then, we do the performance tests
    for tsp, shortest_and_longest in (
        (TSP_gr_21, (2707, 10680)),
        (ATSP_br17, (39, 445)),
    ):
        header_info, graph = read_tsp_problem(tsp)
        tsp_name = header_info["NAME"]
        tsp_type = header_info["TYPE"]
        tsp_is_symmetric = tsp_type != "ATSP"
        tsp_text = "{} ({}sym.), ".format(tsp_name, "" if tsp_is_symmetric else "a")

        for correct_result, find_longest in zip(shortest_and_longest, (False, True)):
            mode_text = "longest" if find_longest else "shortest"

            if find_longest and tsp_is_symmetric:
                print("Skipped:", tsp_text + "_traveling_salesman_basic,", mode_text)
                print()
            else:
                solve(
                    tsp_text + "_traveling_salesman_basic, " + mode_text,
                    lambda: _traveling_salesman_basic(
                        graph,  # noqa: B023
                        0,
                        float("inf"),
                        find_longest=find_longest,  # noqa: B023
                    ),
                    correct_length=correct_result,
                    graph=graph,
                    time_stats=True,
                    mem_stats=True,
                )

            solve(
                tsp_text + "traveling_salesman, " + mode_text,
                lambda: traveling_salesman(
                    range(len(graph)), graph,  # noqa: B023  # fmt: skip
                    find_longest=find_longest  # noqa: B023  # fmt: skip
                ),
                correct_length=correct_result,
                graph=graph,
                time_stats=True,
                mem_stats=True,
            )

            solve(
                tsp_text + "traveling_salesman_flex IntVertexIDs, " + mode_text,
                lambda: traveling_salesman_flex(
                    range(len(graph)), graph,  # noqa: B023  # fmt: skip
                    GearForIntVertexIDsAndCFloats[int, Any](),
                    find_longest=find_longest,  # noqa: B023  # fmt: skip
                ),
                correct_length=correct_result,
                graph=graph,
                time_stats=True,
                mem_stats=True,
            )

            solve(
                tsp_text + "traveling_salesman_flex IntVerticesAndIDs, " + mode_text,
                lambda: traveling_salesman_flex(
                    # fmt: off
                    range(len(graph)), graph,  # noqa: B023  # fmt: skip
                    GearForIntVerticesAndIDsAndCFloats[Any](),
                    find_longest=find_longest,  # noqa: B023  # fmt: skip
                ),
                correct_length=correct_result,
                graph=graph,  # noqa: B023
                time_stats=True,
                mem_stats=True,
            )

            solve(
                tsp_text
                + "traveling_salesman_flex IntVerticesAndIDsAndCInt, "
                + mode_text,
                lambda: traveling_salesman_flex(
                    range(len(graph)), graph,  # noqa: B023  # fmt: skip
                    GearForIntVerticesAndIDsAndCInts[Any](),
                    find_longest=find_longest,  # noqa: B023  # fmt: skip
                ),
                correct_length=correct_result,
                graph=graph,
                time_stats=True,
                mem_stats=True,
            )
            solve(
                tsp_text
                + "traveling_salesman_flex IntVerticesAndIDsAndCInt I, "
                + mode_text,
                lambda: traveling_salesman_flex(
                    range(len(graph)), graph,  # noqa: B023  # fmt: skip
                    GearForIntVerticesAndIDsAndCInts[Any](distance_type_code="I"),
                    find_longest=find_longest,  # noqa: B023  # fmt: skip
                ),
                correct_length=correct_result,
                graph=graph,  # noqa: B023
                time_stats=True,
                mem_stats=True,
            )

            print()
        print()


""" --------------- results of performance comparison ---------------
Running test: gr21 (sym.), _traveling_salesman_basic, shortest
Time:  27.631008600001223
Memory peak: 2,980,343,232

Running test: gr21 (sym.), traveling_salesman, shortest
Time:  11.9508657999977
Memory peak: 1,178,960,960

Running test: gr21 (sym.), traveling_salesman_flex IntVertexIDs, shortest
Time:  13.009757099993294
Memory peak: 1,746,319,440

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDs, shortest
Time:  13.50954910001019
Memory peak: 1,302,542,952

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDsAndCInt, shortest
Time:  14.237763200013433
Memory peak: 1,331,388,184

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDsAndCInt I, shortest
Time:  12.5570251000172
Memory peak: 1,331,387,800

Skipped: gr21 (sym.), _traveling_salesman_basic, longest


Running test: gr21 (sym.), traveling_salesman, longest
Time:  136.87711160001345
Memory peak: 3,638,079,744

Running test: gr21 (sym.), traveling_salesman_flex IntVertexIDs, longest
Time:  108.13367139999173
Memory peak: 2,903,916,544

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDs, longest
Time:  104.6956693000102
Memory peak: 2,330,797,808

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDsAndCInt, longest
Time:  108.24468939998769
Memory peak: 2,409,590,976

Running test: gr21 (sym.), traveling_salesman_flex IntVerticesAndIDsAndCInt I, longest
Time:  105.12879269997939
Memory peak: 2,409,590,936



Running test: br17 (asym.), _traveling_salesman_basic, shortest
Time:  0.839628999994602
Memory peak: 149,823,104

Running test: br17 (asym.), traveling_salesman, shortest
Time:  0.38522150000790134
Memory peak: 38,416,072

Running test: br17 (asym.), traveling_salesman_flex IntVertexIDs, shortest
Time:  0.534208299999591
Memory peak: 80,866,420

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDs, shortest
Time:  0.5972311000223272
Memory peak: 59,789,080

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDsAndCInt, shortest
Time:  0.6129723000049125
Memory peak: 56,039,056

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDsAndCInt I, shortest
Time:  0.5280643000151031
Memory peak: 56,039,160


Running test: br17 (asym.), _traveling_salesman_basic, longest
Time:  9.076881199987838
Memory peak: 617,979,224

Running test: br17 (asym.), traveling_salesman, longest
Time:  4.059841299982509
Memory peak: 183,759,808

Running test: br17 (asym.), traveling_salesman_flex IntVertexIDs, longest
Time:  3.371155100001488
Memory peak: 119,636,392

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDs, longest
Time:  3.379681400023401
Memory peak: 92,437,696

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDsAndCInt, longest
Time:  3.5230599000060465
Memory peak: 95,265,928

Running test: br17 (asym.), traveling_salesman_flex IntVerticesAndIDsAndCInt I, longest
Time: None. Test aborted. Exception caught:
Distance 69648 is equal or larger than the infinity value 65535
  used by the chosen gear and its configuration
Memory peak: None. Test aborted. Exception caught:
Distance 69648 is equal or larger than the infinity value 65535
  used by the chosen gear and its configuration
"""
