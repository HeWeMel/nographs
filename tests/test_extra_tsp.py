from collections.abc import Mapping, Iterator
from typing import Callable, Union, Iterable
import re
import textwrap

from nographs import T_vertex, T_weight  # types
from nographs import traveling_salesman  # ._tsp
from nographs import GearDefault  # NOQA F401 (import needed by doc tests)  # ._gears

# noinspection PyProtectedMember
from nographs._extra_tsp import (  # NOQA F401 (import needed by doc tests)
    _traveling_salesman_int_vertices,
    GettableProto,
)


class GettableProtoTest:
    """
    >>> GettableProto.__getitem__(None, None)
    Traceback (most recent call last):
    NotImplementedError
    """


class TspTestsGeneral:
    """
    Unit tests for TSP

    >>> def test(edges, longest=False, vertices=None):
    ...    if vertices is None:
    ...        vertices=range(len(edges))
    ...    l, p = traveling_salesman(vertices, edges, longest)
    ...    print(l, list(p))

    -- TSP problem is not well-defined --

    Graph has no vertices and no edges
    >>> test(dict(), False)
    Traceback (most recent call last):
    RuntimeError: A TSP needs to have at least two vertices.

    Graph has one vertex and no edges
    >>> test({0: dict()}, False)
    Traceback (most recent call last):
    RuntimeError: A TSP needs to have at least two vertices.

    Graph has two vertices and one edge, but the relevant vertices are less than two
    >>> test({0: {1:1}, 1: {0:1}}, False, ())
    Traceback (most recent call last):
    RuntimeError: A TSP needs to have at least two vertices.
    >>> test({0: {1:1}, 1: {0:1}}, False, (1,))
    Traceback (most recent call last):
    RuntimeError: A TSP needs to have at least two vertices.

    -- TSP problem has no solution --

    A vertex has no outgoing edges
    >>> test({0: {1:1}}, False, (0, 1))
    Traceback (most recent call last):
    KeyError: 'No solution for the TSP exists: Some vertices have no outgoing edges.'

    A vertex has no incoming edges
    >>> test({0: {2:1}, 1: {2:1}, 2: {1:1}})
    Traceback (most recent call last):
    KeyError: 'No solution for the TSP exists: Some vertices have no incoming edges.'

    One of the vertices has only a self loop - but this will be ignored
    >>> test({0: {1:1}, 1: {0:1}, 2: {2:1},}, False)
    Traceback (most recent call last):
    KeyError: 'No solution for the TSP exists: Some vertices have no outgoing edges.'

    Graph has two vertices and one edge, but the relevant vertices are others
    >>> test({0: {1:1}, 1: {0:1}}, False, (0, 3))
    Traceback (most recent call last):
    KeyError: 'No solution for the TSP exists: Some vertices have no outgoing edges.'

    Graph has two isolated loops -> Unsolvable
    >>> test({0: {1:1}, 1: {0:1}, 2: {3:1}, 3: {2:1}}, False)
    Traceback (most recent call last):
    KeyError: 'No solution for the TSP exists.'

    Graph has two vertices and two suitable edges -> return result
    >>> test({0: {1:1}, 1: {0:1}}, False)
    2 [0, 1, 0]
    >>> test({0: {1:1}, 1: {0:1}}, True)
    2 [0, 1, 0]

    Three vertices, all connected, one edge direction shorter -> take this edge
    >>> test({0: {1:0, 2:1}, 1: {0:1, 2:1}, 2: {0:1, 1:1}}, False)
    2 [0, 1, 2, 0]
    >>> test({0: {1:1, 2:0}, 1: {0:1, 2:1}, 2: {0:1, 1:1}}, False)
    2 [0, 2, 1, 0]

    Three vertices, all connected, one edge direction longer, longest -> take this edge
    >>> test({0: {1:5, 2:1}, 1: {0:1, 2:1}, 2: {0:1, 1:1}}, True)
    7 [0, 1, 2, 0]
    >>> test({0: {1:1, 2:5}, 1: {0:1, 2:1}, 2: {0:1, 1:1}}, True)
    7 [0, 2, 1, 0]

    Four vertices, all connected, two consecutive edges shorter, shortest -> take this
    >>> test({0: {1:1, 2:0, 3:1}, 1: {0:1, 2:1, 3:1},
    ...       2: {0:1, 1:0, 3:1}, 3: {0:1, 1:1, 2:1}}, False)
    2 [0, 2, 1, 3, 0]

    Four vertices, all connected, two consecutive edges longer, longest -> take this
    >>> test({0: {1:1, 2:5, 3:1}, 1: {0:1, 2:1, 3:1},
    ...       2: {0:1, 1:5, 3:1}, 3: {0:1, 1:1, 2:1}}, True)
    12 [0, 2, 1, 3, 0]

    Four vertices, all connected, two relevant vertices -> solve this
    >>> test({0: {1:1, 2:1, 3:1}, 1: {0:1, 2:1, 3:1},
    ...       2: {0:1, 1:1, 3:1}, 3: {0:1, 1:1, 2:1}}, False, (1, 2))
    2 [1, 2, 1]
    """


class TspTestsOnlyForIntVertices:
    """
    >>> g = ((1, 1), (1,))
    >>> l, p = _traveling_salesman_int_vertices(g, GearDefault(), False)
    Traceback (most recent call last):
    RuntimeError: For vertex 1, 1 edges instead of 2 edges are given.
    """


# Source:
# TSPLIB – Sammlung von Benchmark-Instanzen des TSP und verschiedener Varianten
# http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/

ATSP_br17 = """
NAME:  br17
TYPE: ATSP
COMMENT: 17 city problem (Repetto)
DIMENSION:  17
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: FULL_MATRIX
EDGE_WEIGHT_SECTION
9999    3    5   48   48    8    8    5    5    3    3    0    3    5    8    8    5
3 9999    3   48   48    8    8    5    5    0    0    3    0    3    8    8    5
5    3 9999   72   72   48   48   24   24    3    3    5    3    0   48   48   24
48   48   74 9999    0    6    6   12   12   48   48   48   48   74    6    6   12
48   48   74    0 9999    6    6   12   12   48   48   48   48   74    6    6   12
8    8   50    6    6 9999    0    8    8    8    8    8    8   50    0    0    8
8    8   50    6    6    0 9999    8    8    8    8    8    8   50    0    0    8
5    5   26   12   12    8    8 9999    0    5    5    5    5   26    8    8    0
5    5   26   12   12    8    8    0 9999    5    5    5    5   26    8    8    0
3    0    3   48   48    8    8    5    5 9999    0    3    0    3    8    8    5
3    0    3   48   48    8    8    5    5    0 9999    3    0    3    8    8    5
0    3    5   48   48    8    8    5    5    3    3 9999    3    5    8    8    5
3    0    3   48   48    8    8    5    5    0    0    3 9999    3    8    8    5
5    3    0   72   72   48   48   24   24    3    3    5    3 9999   48   48   24
8    8   50    6    6    0    0    8    8    8    8    8    8   50 9999    0    8
8    8   50    6    6    0    0    8    8    8    8    8    8   50    0 9999    8
5    5   26   12   12    8    8    0    0    5    5    5    5   26    8    8 9999
EOF
"""

TSP_gr_21 = """
NAME: gr21
TYPE: TSP
COMMENT: 21-city problem (Groetschel)
DIMENSION: 21
EDGE_WEIGHT_TYPE: EXPLICIT
EDGE_WEIGHT_FORMAT: LOWER_DIAG_ROW
EDGE_WEIGHT_SECTION
  0   510     0   635   355     0    91   415   605     0
385   585   390   350     0   155   475   495   120   240
  0   110   480   570    78   320    96     0   130   500
540    97   285    36    29     0   490   605   295   460
120   350   425   390     0   370   320   700   280   590
365   350   370   625     0   155   380   640    63   430
200   160   175   535   240     0    68   440   575    27
320    91    48    67   430   300    90     0   610   360
705   520   835   605   590   610   865   250   480   545
  0   655   235   585   555   750   615   625   645   775
285   515   585   190     0   480    81   435   380   575
440   455   465   600   245   345   415   295   170     0
265   480   420   235   125   125   200   165   230   475
310   205   715   650   475     0   255   440   755   235
650   370   320   350   680   150   175   265   400   435
385   485     0   450   270   625   345   660   430   420
440   690    77   310   380   180   215   190   545   225
  0   170   445   750   160   495   265   220   240   600
235   125   170   485   525   405   375    87   315     0
240   290   590   140   480   255   205   220   515   150
100   170   390   425   255   395   205   220   155     0
380   140   495   280   480   340   350   370   505   185
240   310   345   280   105   380   280   165   305   150
  0
EOF
"""


def read_tsp_problem(s: str) -> tuple[dict[str, str], dict[int, dict[int, int]]]:
    # generator that yields s line by line, each line without leading and trailing
    # spaces, first and last line are left out
    lines = (line.strip() for line in s[1:-1].split("\n"))

    # read header of TSP, extract size
    header_info = dict()
    while (line := next(lines)) != "EDGE_WEIGHT_SECTION":
        key, value = re.split(r": *", line)
        header_info[key] = value
    size = int(header_info["DIMENSION"])
    tsp_type = header_info["TYPE"]
    edge_weight_format = header_info["EDGE_WEIGHT_FORMAT"]

    numbers: Iterator[str]
    numbers = (word for line in lines for word in re.split(r"\W+", line))
    if edge_weight_format == "FULL_MATRIX":
        graph = {
            row: {column: int(next(numbers)) for column in range(size)}
            for row in range(size)
        }
    elif tsp_type == "TSP" and edge_weight_format == "LOWER_DIAG_ROW":
        numbers_tuple = tuple(numbers)
        # edges in forward direction
        numbers_iterator = iter(numbers_tuple)
        graph = {
            row: {column: int(next(numbers_iterator)) for column in range(row + 1)}
            for row in range(size)
        }
        # edges in backward direction
        numbers_iterator = iter(numbers_tuple)
        for row in range(size):
            for column in range(row + 1):
                graph[column][row] = int(next(numbers_iterator))
        numbers = numbers_iterator
    else:
        raise RuntimeError()

    if (line := next(numbers).strip()) != "EOF":
        raise RuntimeError(
            "TSP not correctly read: EOF not found where expected, instead found: "
            + line
        )

    return header_info, graph


def solve(
    test_name: str,
    function: Callable[[], Union[tuple[int, Iterable], tuple[float, Iterable]]],
    correct_length: T_weight,
    graph: Mapping[T_vertex, Mapping[T_vertex, T_weight]],
    time_stats: bool = False,
    mem_stats: bool = False,
    print_only_on_error: bool = False,
) -> bool:
    if not print_only_on_error and len(test_name) > 0:
        print()
        print("Running test:", test_name)

    if mem_stats and time_stats:
        correct = solve(
            "",
            function,
            correct_length,
            graph,
            time_stats=True,
            print_only_on_error=print_only_on_error,
        )
        correct = correct and solve(
            "",
            function,
            correct_length,
            graph,
            mem_stats=True,
            print_only_on_error=print_only_on_error,
        )
        return correct

    if mem_stats:
        import tracemalloc

        tracemalloc.start()
        tracemalloc.reset_peak()  # reset peak of previous execution parts

    if time_stats:
        import gc
        import timeit

        gc.collect()
        start = timeit.default_timer()

    try:
        length, path_iter = function()
    except OverflowError as e:
        if print_only_on_error:
            print("Running test:", test_name)
        if time_stats:
            print("Time: None. Test aborted. Exception caught:")
        if mem_stats:
            print("Memory peak: None. Test aborted. Exception caught:")
        print("\n  ".join(textwrap.wrap(str(e), 64)))
        return True

    if time_stats:
        stop = timeit.default_timer()
        print("Time: ", stop - start)

    if mem_stats:
        mem_size, mem_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"Memory peak: {int(mem_peak):,}")

    path = tuple(path_iter)
    path_is_correct = path[0] == path[-1]
    zero = correct_length - correct_length
    path_length = zero
    for v, w in zip(path, path[1:]):
        if w not in graph[v].keys():
            path_is_correct = False
            path_length = zero
            break
        path_length += graph[v][w]

    if length != correct_length or length != path_length or not path_is_correct:
        if print_only_on_error:
            print("Running test:", test_name)
        print("Got vertex sequence", path)
        print("This is " + ("" if path_is_correct else "not ") + "a valid path.")
        print(
            f"Got nominal length {length}, real length is {path_length}. "
            + f"Expected path with length {correct_length}."
        )
        return False
    return True


if __name__ == "__main__":
    """Additional unit tests for TSP: One of the standard TSPLIB problems."""
    for tsp, shortest, longest in (
        # Excluded the first tsp problem here. It is not necessary for QS, and
        # only used for the separate performance analysis.
        # (TSP_gr_21, 2707, 10680),
        (ATSP_br17, 39, 445),
    ):
        header_info, graph = read_tsp_problem(tsp)
        tsp_name = header_info["NAME"]
        tsp_type = header_info["TYPE"]
        tsp_is_symmetric = tsp_type != "ATSP"
        tsp_text = "{} ({}sym.), ".format(tsp_name, "" if tsp_is_symmetric else "a")

        solve(
            tsp_text + "traveling_salesman, shortest",
            lambda: traveling_salesman(
                range(len(graph)), graph),  # noqa: B023  # fmt: skip
            shortest,
            graph,  # noqa: B023
            print_only_on_error=True,
        )

        solve(
            tsp_text + "traveling_salesman, longest",
            lambda: traveling_salesman(
                range(len(graph)), graph, find_longest=True),  # noqa: B023  # fmt: skip
            longest,
            graph,
            print_only_on_error=True,
        )
