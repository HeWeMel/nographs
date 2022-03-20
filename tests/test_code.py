import collections
import nographs as nog


# --- Utility functions ---
def edges(next_edges_or_vertices, vertices):
    # Test functionality of a next_edges or next_vertices function by calling
    # it for all vertices and return the relationship between inputs and
    # outputs in a dict.
    return dict((vertex, next_edges_or_vertices(vertex, None))
                for vertex in vertices)


# --- Tests ---


class ExamplesFromDocs:
    """
    >>> def spiral_graph(i, _):
    ...     j = (i + i // 6) % 6
    ...     yield i + 1, j * 2 + 1
    ...
    ...     if i % 2 == 0:
    ...         yield i + 6, 7 - j
    ...
    ...     else:
    ...         if i > 5:
    ...             yield i - 6, 1
    >>> traversal = nog.TraversalShortestPaths(spiral_graph).start_from(0, build_paths=True)
    >>> traversal.go_to(5)
    5
    >>> traversal.distance
    24
    >>> traversal.paths[5]
    (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)

    -- next_from_edge_dict for weighted edges given as dict --
    >>> edges_weighted_dict = {
    ...    'A': (('B', 1), ('C', 2)),
    ...    'B': (('C', 5), ('D', 5)),
    ...    'C': (('D', 2), ('E', 1), ('F', 5)),
    ...    'D': (('F', 2), ('G', 5)),
    ...    'E': (('F', 5), ('B', 1)),
    ...    'F': (('G', 2),)
    ... }

    >>> next_vertices = nog.adapt_edge_index(edges_weighted_dict,add_inverted=False,labeled=True)
    >>> edges(next_vertices, edges_weighted_dict.keys()) == edges_weighted_dict
    True

    >>> next_vertices = nog.adapt_edge_index(edges_weighted_dict,add_inverted=True,labeled=True)
    >>> edges(next_vertices, edges_weighted_dict.keys())  # doctest: +NORMALIZE_WHITESPACE
    {'A': [('B', 1), ('C', 2)], 'B': [('A', 1), ('C', 5), ('D', 5), ('E', 1)],
     'C': [('A', 2), ('B', 5), ('D', 2), ('E', 1), ('F', 5)],
     'D': [('B', 5), ('C', 2), ('F', 2), ('G', 5)],
     'E': [('C', 1), ('F', 5), ('B', 1)],
     'F': [('C', 5), ('D', 2), ('E', 5), ('G', 2)]}


    -- next_from_edge_dict for weighted edges given as sequence --
    >>> edges_weighted_sequence = (
    ...     ((1, 1), (2, 2)),
    ...     ((2, 5), (3, 5)),
    ...     ((3, 2), (4, 1), (5, 5)),
    ...     ((5, 2), (6, 5)),
    ...     ((5, 5), (1, 1)),
    ...     ((6, 2),)
    ...  )

    >>> next_vertices = nog.adapt_edge_index(edges_weighted_sequence,
    ...     add_inverted=False, labeled=True)
    >>> tuple(edges(next_vertices, range(len(edges_weighted_sequence))).values()
    ...      ) == edges_weighted_sequence
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_weighted_sequence,add_inverted=True,labeled=True)
    >>> edges(next_vertices, range(len(edges_weighted_sequence)))  # doctest: +NORMALIZE_WHITESPACE
    {0: [(1, 1), (2, 2)], 1: [(0, 1), (2, 5), (3, 5), (4, 1)],
     2: [(0, 2), (1, 5), (3, 2), (4, 1), (5, 5)], 3: [(1, 5), (2, 2), (5, 2), (6, 5)],
     4: [(2, 1), (5, 5), (1, 1)], 5: [(2, 5), (3, 2), (4, 5), (6, 2)]}


    -- next_from_edge_dict for unweighted edges given as dict --
    >>> edges_unweighted_dict = {
    ...    'A': ('B', 'C'),
    ...    'B': ('C', 'D'),
    ...    'C': ('D', 'E', 'F'),
    ...    'D': ('F', 'G'),
    ...    'E': ('F', 'B'),
    ...    'F': ('G', )
    ... }

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_dict,add_inverted=False,labeled=False)
    >>> edges(next_vertices, edges_weighted_dict.keys()) == edges_unweighted_dict
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_dict,add_inverted=True,labeled=False)
    >>> edges(next_vertices, edges_weighted_dict.keys())  # doctest: +NORMALIZE_WHITESPACE
    {'A': ['B', 'C'], 'B': ['A', 'C', 'D', 'E'], 'C': ['A', 'B', 'D', 'E', 'F'],
     'D': ['B', 'C', 'F', 'G'], 'E': ['C', 'F', 'B'], 'F': ['C', 'D', 'E', 'G']}


    -- next_from_edge_dict for unweighted edges given as sequence --
    >>> edges_unweighted_sequence = (
    ...     (1, 2),
    ...     (2, 3),
    ...     (3, 4, 5),
    ...     (5, 6),
    ...     (5, 1),
    ...     (6,)
    ... )

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_sequence,add_inverted=False,labeled=False)
    >>> tuple(edges(next_vertices, range(len(edges_weighted_sequence))).values()) \
        == edges_unweighted_sequence
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_sequence,add_inverted=True,labeled=False)
    >>> edges(next_vertices, range(len(edges_weighted_sequence)))  # doctest: +NORMALIZE_WHITESPACE
    {0: [1, 2], 1: [0, 2, 3, 4], 2: [0, 1, 3, 4, 5], 3: [1, 2, 5, 6],
     4: [2, 5, 1], 5: [2, 3, 4, 6]}
    """


# --------- Tests for all traversals -----------


class PathHandling:
    # noinspection PyShadowingNames
    """-- Error handling in Paths --
     Path detects illegal calls with None as vertex and with non-existing vertices.
     Iteration works for both types of paths both with vertices and with edges.

    -- Unlabeled paths --

    >>> path_unlabeled = nog.PathsOfUnlabeledEdges(dict(), None)
    >>> path_unlabeled[None]  # Calls p.iter_vertices_to_start
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_unlabeled.iter_vertices_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_unlabeled.iter_edges_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.

    >>> tuple(path_unlabeled.iter_edges_to_start(2))
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.

    >>> path_unlabeled.append_edge(0, 1, None)
    >>> path_unlabeled[1]  # Calls p.iter_vertices_from_start and p.iter_vertices_to_start
    (0, 1)
    >>> tuple(path_unlabeled.iter_edges_from_start(1))  # Also calls p.iter_edges_to_start
    ((0, 1),)

    >>> path_unlabeled.append_edge(1, 2, None)
    >>> path_unlabeled[2]
    (0, 1, 2)
    >>> tuple(path_unlabeled.iter_edges_from_start(2))
    ((0, 1), (1, 2))

    -- Labeled paths --

    >>> path_labeled = nog.PathsOfLabeledEdges(dict(), dict(), None)
    >>> path_labeled[None]
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_labeled.iter_vertices_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_labeled.iter_edges_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.

    >>> tuple(path_labeled.iter_edges_to_start(2))
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.

    >>> path_labeled.append_edge(0, 1, (0, "labeled"))
    >>> path_labeled[1]  # Calls p.iter_edges_from_start and p.iter_edges_to_start
    ((0, 1, 'labeled'),)
    >>> tuple(path_labeled.iter_vertices_from_start(1))  # Also calls p.iter_vertices_to_start
    (0, 1)

    >>> path_labeled.append_edge(1, 2, (0, "labeled"))
    >>> path_labeled[2]
    ((0, 1, 'labeled'), (1, 2, 'labeled'))
    >>> tuple(path_labeled.iter_vertices_from_start(2))
    (0, 1, 2)
    """


class GraphWithoutEdges:
    # noinspection PyShadowingNames
    """-- Graph without edges --
     No vertices are reported. Exception: topological sorting reports it.
     Strategies detect if labeled paths are demanded, but not the generation of paths.

    >>> def no_next(v, _):
    ...     return ()
    >>> def heuristic(v):
    ...    return 0  # Graph has just une vertex and no edges. So, no heuristic needed.

    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalShortestPaths, nog.TraversalMinimumSpanningTree,
    ...                  nog.TraversalTopologicalSort):
    ...     list(strategy(no_next).start_from(0))
    []
    []
    []
    []
    [0]
    >>> list(nog.TraversalAStar(no_next).start_from(heuristic, 0))
    []

    >>> traversal = nog.TraversalBreadthFirst(no_next)
    >>> traversal.start_from(0).go_to(1, fail_silently=True) is None
    True
    >>> traversal.start_from(0).go_to(1)
    Traceback (most recent call last):
    KeyError: 'Vertex not found, graph exhausted.'
    >>> list(traversal.start_from(0).go_for_vertices_in((1,), fail_silently=True))
    []
    >>> list(traversal.start_from(0).go_for_vertices_in((1,)))
    Traceback (most recent call last):
    KeyError: 'Not all of the given vertices have been found'


    >>> traversal = nog.TraversalBreadthFirst(no_next)
    >>> traversal = traversal.start_from(0, build_paths=False, labeled_paths=True)
    Traceback (most recent call last):
    RuntimeError: Option labeled_paths without option build_paths.
    >>> traversal = traversal.start_from(start_vertex=0, start_vertices=(0,))
    Traceback (most recent call last):
    RuntimeError: Both start_vertex and start_vertices provided.
    >>> traversal = traversal.start_from()
    Traceback (most recent call last):
    RuntimeError: Neither start_vertex and start_vertices provided.
    >>> traversal = nog.TraversalBreadthFirst()
    Traceback (most recent call last):
    RuntimeError: Neither next_vertices nor next_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_edges=no_next, next_vertices=no_next)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_edges provided.
    """


class GraphWithOneEdgeAndPathVariants:
    # noinspection PyShadowingNames
    """-- Graph with one edge --
    Start vertex not reported (exception: topological sorting). First edge followed.
    Paths not build if not demanded, and build if demanded.
    Labeled paths not allowed for unlabeled edges, and build for labeled edges, if demanded.
    Calculation limit raises Exception at exactly correct number of visited vertices.

    >>> def test(traversal, with_is_labeled):
    ...     print(list(traversal.start_from(0)))
    ...     print(traversal.paths is None)
    ...     print(next(traversal.start_from(0)))
    ...     _ = traversal.start_from(0, build_paths=True).go_to(1)
    ...     print(traversal.paths[1])
    ...     if with_is_labeled:
    ...        _ = traversal.start_from(0, build_paths=True, labeled_paths=True).go_to(1)
    ...        print(traversal.paths[1])

    # -- Unlabeled graph --
    >>> def next_vertices(v, _):
    ...     return (1,) if v == 0 else ()

    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> test(traversal, with_is_labeled=False)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> test(traversal, with_is_labeled=False)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(next_vertices)
    >>> test(traversal, with_is_labeled=False)
    [1, 0]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(next_vertices, is_tree=True)
    >>> test(traversal, with_is_labeled=False)
    [1, 0]
    True
    1
    (0, 1)

    >>> nog.TraversalBreadthFirst(next_vertices).start_from(0, build_paths=True, labeled_paths=True)
    Traceback (most recent call last):
    RuntimeError: A labeled path can only be computed from labeled edges.
    >>> nog.TraversalDepthFirst(next_vertices).start_from(0, build_paths=True, labeled_paths=True)
    Traceback (most recent call last):
    RuntimeError: A labeled path can only be computed from labeled edges.
    >>> nog.TraversalTopologicalSort(next_vertices).start_from(
    ...     0, build_paths=True, labeled_paths=True)
    Traceback (most recent call last):
    RuntimeError: A labeled path can only be computed from labeled edges.


    # -- Labeled graph --
    >>> def next_edges(v, _):
    ...     return ((1, 1),) if v == 0 else ()

    >>> traversal = nog.TraversalBreadthFirst(next_edges=next_edges)
    >>> test(traversal, with_is_labeled=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalDepthFirst(next_edges=next_edges)
    >>> test(traversal, with_is_labeled=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> test(traversal, with_is_labeled=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> test(traversal, with_is_labeled=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_edges)
    >>> test(traversal, with_is_labeled=True)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_edges, is_tree=True)
    >>> test(traversal, with_is_labeled=True)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 1),)


    >>> traversal = nog.TraversalBreadthFirst(next_edges=next_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalDepthFirst(next_edges=next_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_edges, is_tree=True)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> # Test early exceeded limit, during traversal of edges from start vertex in MST
    >>> _ = list(traversal.start_from(0, calculation_limit=0))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit


    >>> def heuristic(v):
    ...    return 1 if v == 0 else 0  # heuristic with perfect estimation
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> list(traversal.start_from(heuristic, 0))
    [1]
    >>> traversal.paths is None
    True
    >>> _ = traversal.start_from(heuristic, 0, build_paths=True).go_to(1)
    >>> traversal.paths[1]
    (0, 1)
    >>> _ = traversal.start_from(heuristic, 0, build_paths=True, labeled_paths=True).go_to(1)
    >>> traversal.paths[1]
    ((0, 1, 1),)

    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> _ = list(traversal.start_from(heuristic, 0, calculation_limit=2))
    >>> _ = list(traversal.start_from(heuristic, 0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    """


class GraphWithOneEdgeAndVertexToId:
    # noinspection PyShadowingNames
    """-- Graph with one edge, parameter vertex_to_id used --
    For the test, vertices are given as list [int] to have something that is not hashable.
    Start vertex not reported (exception: topological sorting). First edge followed.
    Paths not build if not demanded, and build if demanded.
    Labeled paths not allowed for unlabeled edges, and build for labeled edges, if demanded.
    Calculation limit raises Exception at exactly correct number of visited vertices.

    >>> def next_vertices(v, _):
    ...     return ([1],) if v == [0] else ()
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalTopologicalSort):
    ...     print(strategy.__name__)
    ...     traversal = strategy(next_vertices, vertex_to_id=lambda l: l[0])
    ...     list(traversal.start_from([0]))
    ...     traversal.paths is None
    ...     _ = traversal.start_from([0], build_paths=True).go_to([1])
    ...     traversal.paths[[1]]
    TraversalBreadthFirst
    [[1]]
    True
    ([0], [1])
    TraversalDepthFirst
    [[1]]
    True
    ([0], [1])
    TraversalTopologicalSort
    [[1], [0]]
    True
    ([0], [1])


    >>> def next_edges(v, _):
    ...     return (([1], 1),) if v == [0] else ()
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalShortestPaths, nog.TraversalMinimumSpanningTree,
    ...                  nog.TraversalTopologicalSort):
    ...     print(strategy.__name__)
    ...     traversal = strategy(next_edges=next_edges, vertex_to_id=lambda l: l[0])
    ...     list(traversal.start_from([0]))
    ...     traversal.paths is None
    ...     _ = traversal.start_from([0], build_paths=True).go_to([1])
    ...     traversal.paths[[1]]
    ...     _ = traversal.start_from([0], build_paths=True, labeled_paths=True).go_to([1])
    ...     traversal.paths[[1]]
    TraversalBreadthFirst
    [[1]]
    True
    ([0], [1])
    (([0], [1], 1),)
    TraversalDepthFirst
    [[1]]
    True
    ([0], [1])
    (([0], [1], 1),)
    TraversalShortestPaths
    [[1]]
    True
    ([0], [1])
    (([0], [1], 1),)
    TraversalMinimumSpanningTree
    [[1]]
    True
    ([0], [1])
    (([0], [1], 1),)
    TraversalTopologicalSort
    [[1], [0]]
    True
    ([0], [1])
    (([0], [1], 1),)


    >>> def heuristic(v):
    ...    return 1 if v == [0] else 0  # heuristic with perfect estimation
    >>> traversal = nog.TraversalAStar(next_edges=next_edges, vertex_to_id=lambda l: l[0])
    >>> list(traversal.start_from(heuristic, [0]))
    [[1]]
    >>> traversal.paths is None
    True
    >>> _ = traversal.start_from(heuristic, [0], build_paths=True).go_to([1])
    >>> traversal.paths[[1]]
    ([0], [1])
    >>> _ = traversal.start_from(heuristic, [0], build_paths=True, labeled_paths=True).go_to([1])
    >>> traversal.paths[[1]]
    (([0], [1], 1),)
    """


class NormalGraphTraversalsWithOrWithoutLabels:
    # noinspection PyShadowingNames
    """-- Small example graph, 3 Traversal strategies that can work with and wihout labels --
    Correct traversal of TraversalBreadthFirst, TraversalDepthFirst, TraversalTopologicalSort.
    For: graph without labels and graph with labeles.
    Without and with vertices defined as already visited (only tested for graph without labels).
    (Uses implementation descisions:
    - TraversalBreadthFirst traverses edges in given order
    - TraversalDepthFirst and TraversalTopologicalSort traverse edges in reversed order)

    1. Unlabeled edges

    >>> def next_vertices(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...     return (1, 2) if vertex == 0 else ((3,) if vertex in (1, 2) else ())

    >>> def this_test(strategy):
    ...     traversal = strategy(next_vertices).start_from(0, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...         print(f"  traversal.paths[vertex]={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    ...     print()
    ...     already_visited = {1}  # vertex 1 already visited
    ...     traversal = strategy(next_vertices).start_from(0, build_paths=True,
    ...         already_visited=already_visited)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=}")
    ...         print(f"  traversal.paths[vertex]={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(4) if vertex!=1])
    ...     print("Already visited:", already_visited)
    ...     return traversal

    >>> traversal = this_test(nog.TraversalBreadthFirst)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1}
      traversal.paths[vertex]=(0, 1)
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1, 3)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 1), (0, 2), (0, 1, 3)]
    <BLANKLINE>
    Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
    Reported: vertex=2 traversal.depth=1
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
    Reported: vertex=3 traversal.depth=2
      traversal.paths[vertex]=(0, 2, 3)
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 2), (0, 2, 3)]
    Already visited: {0, 1, 2, 3}
    >>> traversal.paths[1]
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.

    >>> traversal = this_test(nog.TraversalDepthFirst)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 2}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 2}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2, 3)
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    <BLANKLINE>
    Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
    Reported: vertex=2 traversal.depth=1
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
    Reported: vertex=3 traversal.depth=2
      traversal.paths[vertex]=(0, 2, 3)
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 2), (0, 2, 3)]
    Already visited: {0, 1, 2, 3}
    >>> traversal.paths[1]
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.

    >>> traversal = this_test(nog.TraversalTopologicalSort)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 2}
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2, 3)
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1)
    Reported: vertex=0 traversal.depth=0 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0,)
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    <BLANKLINE>
    Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
    Reported: vertex=3 traversal.depth=2
      traversal.paths[vertex]=(0, 2, 3)
    Reported: vertex=2 traversal.depth=1
      traversal.paths[vertex]=(0, 2)
    Reported: vertex=0 traversal.depth=0
      traversal.paths[vertex]=(0,)
    All paths: [(0,), (0, 2), (0, 2, 3)]
    Already visited: {0, 1, 2, 3}
    >>> traversal.paths[1]
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.


    2. Labeled edges

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...     return ((1, 2), (2, 1)) if vertex == 0 else (((3, 2),) if vertex in (1, 2) else ())

    >>> def this_test(strategy):
    ...     traversal = strategy(next_edges=next_edges).start_from(0, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...         print(f"  traversal.paths[vertex]={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(4)])

    >>> this_test(nog.TraversalBreadthFirst)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1}
      traversal.paths[vertex]=(0, 1)
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1, 3)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 1), (0, 2), (0, 1, 3)]

    >>> this_test(nog.TraversalDepthFirst)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 2}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 2}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2, 3)
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]

    >>> this_test(nog.TraversalTopologicalSort)
    Next called: vertex=0 traversal.depth=0 traversal.visited={0}
    Next called: vertex=2 traversal.depth=1 traversal.visited={0, 2}
    Next called: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
    Reported: vertex=3 traversal.depth=2 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2, 3)
    Reported: vertex=2 traversal.depth=1 traversal.visited={0, 2, 3}
      traversal.paths[vertex]=(0, 2)
    Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
    Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0, 1)
    Reported: vertex=0 traversal.depth=0 traversal.visited={0, 1, 2, 3}
      traversal.paths[vertex]=(0,)
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


    3. is_tree

    >>> def next_vertices(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...     return (2*vertex, 2*vertex+1) if 1 <= vertex <= 3 else ()

    >>> def this_test(strategy):
    ...     traversal = strategy(next_vertices, is_tree=True).start_from(1, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} {traversal.visited=}")
    ...         print(f"  traversal.paths[vertex]={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(1,8)])

    >>> this_test(nog.TraversalBreadthFirst)
    Next called: vertex=1 traversal.depth=0 traversal.visited=set()
    Reported: vertex=2 traversal.depth=1 traversal.visited=set()
      traversal.paths[vertex]=(1, 2)
    Reported: vertex=3 traversal.depth=1 traversal.visited=set()
      traversal.paths[vertex]=(1, 3)
    Next called: vertex=2 traversal.depth=1 traversal.visited=set()
    Reported: vertex=4 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 4)
    Reported: vertex=5 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 5)
    Next called: vertex=3 traversal.depth=1 traversal.visited=set()
    Reported: vertex=6 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 6)
    Reported: vertex=7 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 7)
    Next called: vertex=4 traversal.depth=2 traversal.visited=set()
    Next called: vertex=5 traversal.depth=2 traversal.visited=set()
    Next called: vertex=6 traversal.depth=2 traversal.visited=set()
    Next called: vertex=7 traversal.depth=2 traversal.visited=set()
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]

    >>> this_test(nog.TraversalDepthFirst)
    Next called: vertex=1 traversal.depth=0 traversal.visited=set()
    Reported: vertex=3 traversal.depth=1 traversal.visited=set()
      traversal.paths[vertex]=(1, 3)
    Next called: vertex=3 traversal.depth=1 traversal.visited=set()
    Reported: vertex=7 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 7)
    Next called: vertex=7 traversal.depth=2 traversal.visited=set()
    Reported: vertex=6 traversal.depth=3 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 6)
    Next called: vertex=6 traversal.depth=3 traversal.visited=set()
    Reported: vertex=2 traversal.depth=4 traversal.visited=set()
      traversal.paths[vertex]=(1, 2)
    Next called: vertex=2 traversal.depth=4 traversal.visited=set()
    Reported: vertex=5 traversal.depth=5 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 5)
    Next called: vertex=5 traversal.depth=5 traversal.visited=set()
    Reported: vertex=4 traversal.depth=6 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 4)
    Next called: vertex=4 traversal.depth=6 traversal.visited=set()
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]

    >>> this_test(nog.TraversalTopologicalSort)
    Next called: vertex=1 traversal.depth=0 traversal.visited=set()
    Next called: vertex=3 traversal.depth=1 traversal.visited=set()
    Next called: vertex=7 traversal.depth=2 traversal.visited=set()
    Reported: vertex=7 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 7)
    Next called: vertex=6 traversal.depth=2 traversal.visited=set()
    Reported: vertex=6 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 3, 6)
    Reported: vertex=3 traversal.depth=1 traversal.visited=set()
      traversal.paths[vertex]=(1, 3)
    Next called: vertex=2 traversal.depth=1 traversal.visited=set()
    Next called: vertex=5 traversal.depth=2 traversal.visited=set()
    Reported: vertex=5 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 5)
    Next called: vertex=4 traversal.depth=2 traversal.visited=set()
    Reported: vertex=4 traversal.depth=2 traversal.visited=set()
      traversal.paths[vertex]=(1, 2, 4)
    Reported: vertex=2 traversal.depth=1 traversal.visited=set()
      traversal.paths[vertex]=(1, 2)
    Reported: vertex=1 traversal.depth=0 traversal.visited=set()
      traversal.paths[vertex]=(1,)
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
    """


class NormalGraphTraversalsWithLabels:
    # noinspection PyShadowingNames
    """-- Small example graph. The three strategies that need edge weights. --
    For TraversalShortestPaths, test option known_distances, too.

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     return ((1, 2), (2, 1)) if vertex == 0 else (((3, 2),) if vertex in (1, 2) else ())

    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> traversal = traversal.start_from(0, build_paths=True)
    >>> reported = []
    >>> for vertex in traversal:
    ...     reported.append(vertex)
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     print("distances for reported vertices: " +
    ...           f"{str({vertex: traversal.distances[vertex] for vertex in reported})} " +
    ...           f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.distance=0 traversal.depth=0
    Reported: vertex=2 traversal.distance=1 traversal.depth=1
    distances for reported vertices: {2: 0} traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=1 traversal.depth=1
    Reported: vertex=1 traversal.distance=2 traversal.depth=1
    distances for reported vertices: {2: 0, 1: 0} traversal.paths=(0, 1)
    Next called: vertex=1 traversal.distance=2 traversal.depth=1
    Reported: vertex=3 traversal.distance=3 traversal.depth=2
    distances for reported vertices: {2: 0, 1: 0, 3: 0} traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.distance=3 traversal.depth=2
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]

    Start vertex starts with distance 2, and we pretend to have a path to 1 with distance 0.
    Effect: All reported distances are 2 higher than in the test before, because the traversal
    starts at distance 2, and vertex 1 is not visited and reported at all, because no path
    can be found that beats this "already found" low distance.
    >>> infinity = float('infinity')
    >>> known_distances = collections.defaultdict(lambda: infinity, ((0, 2), (1, 0)))
    >>> traversal = traversal.start_from(0, build_paths=True, known_distances=known_distances)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.distance=2 traversal.depth=0
    Reported: vertex=2 traversal.distance=3 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=3 traversal.depth=1
    Reported: vertex=3 traversal.distance=5 traversal.depth=2 traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.distance=5 traversal.depth=2
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(4) if vertex != 1])
    All paths: [(0,), (0, 2), (0, 2, 3)]
    >>> print("Known distances:", dict(known_distances))
    Known distances: {0: 0, 1: 0, 2: 0, 3: 0}


    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.edge=}")
    ...     return ((1, 2), (2, 1)) if vertex == 0 else (((3, 3),) if vertex in (1, 2) else ())
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> traversal = traversal.start_from(0, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.edge=}"
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.edge=None
    Reported: vertex=2 traversal.edge=(0, 2, 1)traversal.paths=(0, 2)
    Next called: vertex=2 traversal.edge=(0, 2, 1)
    Reported: vertex=1 traversal.edge=(0, 1, 2)traversal.paths=(0, 1)
    Next called: vertex=1 traversal.edge=(0, 1, 2)
    Reported: vertex=3 traversal.edge=(2, 3, 3)traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.edge=(2, 3, 3)
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


    Test TraversaAStar. Typically, one would use go_to(3) for our goal vertex 3, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> def heuristic(v):
    ...    return {0:6, 1:1, 2:2, 3:0, 4:infinity}[v]  # makes 2nd best path visited first
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.path_length=} {traversal.depth=}")
    ...     return {0: ((1, 3), (2, 3), (4, 1)), 1: ((3, 3),), 2: ((3, 2),), 3:(), 4:()}[vertex]
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> traversal = traversal.start_from(heuristic, 0, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.path_length=0 traversal.depth=0
    Reported: vertex=1 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 1)
    Next called: vertex=1 traversal.path_length=3 traversal.depth=1
    Reported: vertex=2 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.path_length=3 traversal.depth=1
    Reported: vertex=3 traversal.path_length=5 traversal.depth=2 traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.path_length=5 traversal.depth=2
    Reported: vertex=4 traversal.path_length=1 traversal.depth=1 traversal.paths=(0, 4)
    Next called: vertex=4 traversal.path_length=1 traversal.depth=1
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3), (0, 4)]

    Variant of the test with option known_distances.
    For the start vertex, we define a start distance. Effect: All distances are now 2 higher.
    For vertex 1, we define an artificial and low distance of 0. Effect: it is not visited.
    >>> known_distances = collections.defaultdict(lambda: infinity, ((0, 2),(1, 0)))
    >>> known_path_length_guesses = collections.defaultdict(lambda: infinity)
    >>> traversal = traversal.start_from(heuristic, 0, build_paths=True,
    ...     known_distances=known_distances, known_path_length_guesses=known_path_length_guesses)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.path_length=2 traversal.depth=0
    Reported: vertex=2 traversal.path_length=5 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.path_length=5 traversal.depth=1
    Reported: vertex=3 traversal.path_length=7 traversal.depth=2 traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.path_length=7 traversal.depth=2
    Reported: vertex=4 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 4)
    Next called: vertex=4 traversal.path_length=3 traversal.depth=1
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(5) if vertex!=1])
    All paths: [(0,), (0, 2), (0, 2, 3), (0, 4)]
    >>> print("Distance at goal:", known_distances[3])
    Distance at goal: 7
    >>> print("Best distances found so far:", dict(known_distances))
    Best distances found so far: {0: 2, 1: 0, 2: 5, 4: 3, 3: 7}
    >>> print("Best path len guesses found so far):", dict(known_path_length_guesses))
    Best path len guesses found so far): {0: 8, 2: 7, 4: inf, 3: 7}


    All algorithms, with option is_tree:

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.distance=}")
    ...     return ((2*vertex, 2*vertex), (2*vertex+1, 2*vertex+1)) if 1 <= vertex <= 3 else ()
    >>> def this_test(strategy):
    ...     traversal = strategy(next_edges, is_tree=True).start_from(1, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} {traversal.distance=} " +
    ...             f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(1,8)])
    ...     print("All distances:", dict(traversal.distances))
    >>> this_test(nog.TraversalShortestPaths)
    Next called: vertex=1 traversal.depth=0 traversal.distance=0
    Reported: vertex=2 traversal.depth=1 traversal.distance=2 traversal.paths=(1, 2)
    Next called: vertex=2 traversal.depth=1 traversal.distance=2
    Reported: vertex=3 traversal.depth=1 traversal.distance=3 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.depth=1 traversal.distance=3
    Reported: vertex=4 traversal.depth=2 traversal.distance=6 traversal.paths=(1, 2, 4)
    Next called: vertex=4 traversal.depth=2 traversal.distance=6
    Reported: vertex=5 traversal.depth=2 traversal.distance=7 traversal.paths=(1, 2, 5)
    Next called: vertex=5 traversal.depth=2 traversal.distance=7
    Reported: vertex=6 traversal.depth=2 traversal.distance=9 traversal.paths=(1, 3, 6)
    Next called: vertex=6 traversal.depth=2 traversal.distance=9
    Reported: vertex=7 traversal.depth=2 traversal.distance=10 traversal.paths=(1, 3, 7)
    Next called: vertex=7 traversal.depth=2 traversal.distance=10
    All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]
    All distances: {1: 0}

    >>> this_test(nog.TraversalMinimumSpanningTree)
    Traceback (most recent call last):
    TypeError: TraversalMinimumSpanningTree.__init__() got an unexpected keyword argument 'is_tree'

    Test TraversaAStar. Typically, one would use go_to(6) for our goal vertex 6, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.path_length=}")
    ...     return ((2*vertex, 2*vertex), (2*vertex+1, 2*vertex+1)) if 1 <= vertex <= 3 else ()
    >>> def heuristic(v):
    ...    return {6:0, 3:3}.get(v, 11)
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> traversal = traversal.start_from(heuristic, 1, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.depth=} {traversal.path_length=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=1 traversal.depth=0 traversal.path_length=0
    Reported: vertex=3 traversal.depth=1 traversal.path_length=3 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.depth=1 traversal.path_length=3
    Reported: vertex=6 traversal.depth=2 traversal.path_length=9 traversal.paths=(1, 3, 6)
    Next called: vertex=6 traversal.depth=2 traversal.path_length=9
    Reported: vertex=2 traversal.depth=1 traversal.path_length=2 traversal.paths=(1, 2)
    Next called: vertex=2 traversal.depth=1 traversal.path_length=2
    Reported: vertex=4 traversal.depth=2 traversal.path_length=6 traversal.paths=(1, 2, 4)
    Next called: vertex=4 traversal.depth=2 traversal.path_length=6
    Reported: vertex=5 traversal.depth=2 traversal.path_length=7 traversal.paths=(1, 2, 5)
    Next called: vertex=5 traversal.depth=2 traversal.path_length=7
    Reported: vertex=7 traversal.depth=2 traversal.path_length=10 traversal.paths=(1, 3, 7)
    Next called: vertex=7 traversal.depth=2 traversal.path_length=10
    """


class SpecialCases:
    # noinspection PyShadowingNames
    """ TraversalDepthFirst, vertex seams to be not visited at first,
    but becomes visited before it is got from the stack"
    >>> edges = {0: (1, 2), 2: (1,)}
    >>> def next_vertices(vertex, _):
    ...     return edges.get(vertex, ())
    >>> list(nog.TraversalDepthFirst(next_vertices).start_from(0))
    [2, 1]
    """
    # inspection PyShadowingNames


class MultipleStartVerticesTraversalsWithOrWithoutLabels:
    # noinspection PyShadowingNames
    """-- Traversal with multiple start vertices, first 3 traversal strategies --
    Correct traversal of TraversalBreadthFirst, TraversalDepthFirst, TraversalTopologicalSort
    in case of multiple start vertices. No traversal in case of no start vertex.
    (Uses implementation descisions:
    - All strategies travers start vertices in given order
    - TraversalBreadthFirst traverses edges in given order
    - TraversalDepthFirst and TraversalTopologicalSort traverse edges in reversed order)

    1. Unlabeled edges
    >>> def next_vertices(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=}")
    ...     return {0: (2,), 1: (3,), 2: (3, 4), 3: (4,), 4: ()}[vertex]
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalTopologicalSort):
    ...     print("- Strategy:", strategy.__name__, "-")
    ...     sv = iter((0,1))  # an iterator (can be iterated only once) should be enough for lib
    ...     traversal = strategy(next_vertices).start_from(start_vertices=sv, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} "
    ...             + f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    ...     traversal = strategy(next_vertices).start_from(start_vertices=(), build_paths=True)
    ...     list(traversal)
    ...     print()
    - Strategy: TraversalBreadthFirst -
    Next called: vertex=0 traversal.depth=0
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=1 traversal.depth=0
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=2 traversal.depth=1
    Reported: vertex=4 traversal.depth=2 traversal.paths=(0, 2, 4)
    Next called: vertex=3 traversal.depth=1
    Next called: vertex=4 traversal.depth=2
    All paths: [(0,), (1,), (0, 2), (1, 3), (0, 2, 4)]
    []
    <BLANKLINE>
    - Strategy: TraversalDepthFirst -
    Next called: vertex=1 traversal.depth=0
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.depth=1
    Reported: vertex=4 traversal.depth=2 traversal.paths=(1, 3, 4)
    Next called: vertex=4 traversal.depth=2
    Next called: vertex=0 traversal.depth=0
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.depth=1
    All paths: [(0,), (1,), (0, 2), (1, 3), (1, 3, 4)]
    []
    <BLANKLINE>
    - Strategy: TraversalTopologicalSort -
    Next called: vertex=1 traversal.depth=0
    Next called: vertex=3 traversal.depth=1
    Next called: vertex=4 traversal.depth=2
    Reported: vertex=4 traversal.depth=2 traversal.paths=(1, 3, 4)
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Reported: vertex=1 traversal.depth=0 traversal.paths=(1,)
    Next called: vertex=0 traversal.depth=0
    Next called: vertex=2 traversal.depth=1
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Reported: vertex=0 traversal.depth=0 traversal.paths=(0,)
    All paths: [(0,), (1,), (0, 2), (1, 3), (1, 3, 4)]
    []
    <BLANKLINE>

    1. Labeled edges
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=}")
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()}[vertex]
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalTopologicalSort):
    ...     print("- Strategy:", strategy.__name__, "-")
    ...     traversal = strategy(next_edges=next_edges)
    ...     sv = iter((0,1))  # an iterator (can be iterated only once) should be enough for lib
    ...     traversal = traversal.start_from(start_vertices=sv, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} "
    ...             + f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    ...     traversal = strategy(next_vertices).start_from(start_vertices=(), build_paths=True)
    ...     list(traversal)
    ...     print()
    - Strategy: TraversalBreadthFirst -
    Next called: vertex=0 traversal.depth=0
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=1 traversal.depth=0
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=2 traversal.depth=1
    Reported: vertex=4 traversal.depth=2 traversal.paths=(0, 2, 4)
    Next called: vertex=3 traversal.depth=1
    Next called: vertex=4 traversal.depth=2
    All paths: [(0,), (1,), (0, 2), (1, 3)]
    []
    <BLANKLINE>
    - Strategy: TraversalDepthFirst -
    Next called: vertex=1 traversal.depth=0
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.depth=1
    Reported: vertex=4 traversal.depth=2 traversal.paths=(1, 3, 4)
    Next called: vertex=4 traversal.depth=2
    Next called: vertex=0 traversal.depth=0
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.depth=1
    All paths: [(0,), (1,), (0, 2), (1, 3)]
    []
    <BLANKLINE>
    - Strategy: TraversalTopologicalSort -
    Next called: vertex=1 traversal.depth=0
    Next called: vertex=3 traversal.depth=1
    Next called: vertex=4 traversal.depth=2
    Reported: vertex=4 traversal.depth=2 traversal.paths=(1, 3, 4)
    Reported: vertex=3 traversal.depth=1 traversal.paths=(1, 3)
    Reported: vertex=1 traversal.depth=0 traversal.paths=(1,)
    Next called: vertex=0 traversal.depth=0
    Next called: vertex=2 traversal.depth=1
    Reported: vertex=2 traversal.depth=1 traversal.paths=(0, 2)
    Reported: vertex=0 traversal.depth=0 traversal.paths=(0,)
    All paths: [(0,), (1,), (0, 2), (1, 3)]
    []
    <BLANKLINE>
    """


class MultipleStartVerticesTraversalsWithLabels:
    # noinspection PyShadowingNames
    """-- Traversal with multiple start vertex, last 3 traversal strategies --
    Correct traversal in case of multiple start vertices. No traversal in case of no start vertex.

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()}[vertex]
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> sv = iter((0,1))  # an iterator (can be iterated only once) should be enough for lib
    >>> traversal = traversal.start_from(start_vertices=sv, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=1 traversal.distance=0 traversal.depth=0
    Next called: vertex=0 traversal.distance=0 traversal.depth=0
    Reported: vertex=2 traversal.distance=1 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=1 traversal.depth=1
    Reported: vertex=3 traversal.distance=1 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.distance=1 traversal.depth=1
    Reported: vertex=4 traversal.distance=2 traversal.depth=2 traversal.paths=(0, 2, 4)
    Next called: vertex=4 traversal.distance=2 traversal.depth=2
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    All paths: [(0,), (1,), (0, 2), (1, 3), (0, 2, 4)]
    >>> traversal = traversal.start_from(start_vertices=(), build_paths=True)
    >>> list(traversal)
    []

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.edge=}")
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()}[vertex]
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> sv = iter((0,1))  # an iterator (can be iterated only once) should be enough for lib
    >>> traversal = traversal.start_from(start_vertices=sv, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.edge=}"
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.edge=None
    Next called: vertex=1 traversal.edge=None
    Reported: vertex=2 traversal.edge=(0, 2, 1)traversal.paths=(0, 2)
    Next called: vertex=2 traversal.edge=(0, 2, 1)
    Reported: vertex=3 traversal.edge=(1, 3, 1)traversal.paths=(1, 3)
    Next called: vertex=3 traversal.edge=(1, 3, 1)
    Reported: vertex=4 traversal.edge=(2, 4, 1)traversal.paths=(0, 2, 4)
    Next called: vertex=4 traversal.edge=(2, 4, 1)
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    All paths: [(0,), (1,), (0, 2), (1, 3), (0, 2, 4)]
    >>> traversal = traversal.start_from(start_vertices=(), build_paths=True)
    >>> list(traversal)
    []

    >>> def heuristic(vertex):
    ...    return {0:3, 1:2, 2:2, 3:1, 4:9, 5:0}[vertex] # heuristic with perfect estimation
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.path_length=} {traversal.depth=}")
    ...     return {0: ((2, 1),), 1: ((3, 1), (4, 1)), 2: ((3, 1),), 3: ((5, 1),), 4: (), 5:()
    ...         }[vertex]
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> sv = iter((0,1))  # an iterator (can be iterated only once) should be enough for lib
    >>> traversal = traversal.start_from(heuristic, start_vertices=sv, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=1 traversal.path_length=0 traversal.depth=0
    Reported: vertex=3 traversal.path_length=1 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.path_length=1 traversal.depth=1
    Reported: vertex=5 traversal.path_length=2 traversal.depth=2 traversal.paths=(1, 3, 5)
    Next called: vertex=5 traversal.path_length=2 traversal.depth=2
    Next called: vertex=0 traversal.path_length=0 traversal.depth=0
    Reported: vertex=2 traversal.path_length=1 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.path_length=1 traversal.depth=1
    Reported: vertex=4 traversal.path_length=1 traversal.depth=1 traversal.paths=(1, 4)
    Next called: vertex=4 traversal.path_length=1 traversal.depth=1
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(6)])
    All paths: [(0,), (1,), (0, 2), (1, 3), (1, 4), (1, 3, 5)]
    >>> traversal = traversal.start_from(heuristic, start_vertices=(), build_paths=True)
    >>> list(traversal)
    []
    """


class InitiationForgotten:
    # noinspection PyTypeChecker
    """Check if the library detects the mistake that start_from or one of the go_... methods are
    called on a traversal class instead of an object, i.e., the round brackets after the class name
    have been forgotten.

    In the following test code, such calls are intentionally made, an since these are typing
    errors, that code inspection is disabled for them in the line on top of the class.

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
    """
    # inspection PyTypeChecker


class EdgeGadgets:
    # noinspection PyShadowingNames
    """
    # ------------ adapt_edge_index -------------
    >>> # Weighted directed edges given as mapping:
    >>> edges = {
    ...    'A': (('B', 1), ('C', 2)),
    ...    'B': (('C', 5), ('D', 5)),
    ...    'C': (('D', 2), ('E', 1), ('F', 5)),
    ...    'D': (('F', 2), ('G', 5)),
    ...    'E': (('F', 5), ('B', 1)),
    ...    'F': (('G', 2),)
    ... }
    >>> import nographs as nog
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=False,labeled=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from("A", build_paths=True).go_to("G")
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: G distance: 8 path edge count: 4 path: ('A', 'C', 'D', 'F', 'G')
    >>>
    >>> # The generated next_vertices function returns the empty list if no edges where given
    >>> # for it in the dict.
    >>> next_vertices("G", None)
    ()

    >>> # Same edges, given in a sequence, node id is integer index of the sequence
    >>> edges = (
    ...     ((1, 1), (2, 2)),
    ...     ((2, 5), (3, 5)),
    ...     ((3, 2), (4, 1), (5, 5)),
    ...     ((5, 2), (6, 5)),
    ...     ((5, 5), (1, 1)),
    ...     ((6, 2),)
    ... )
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=False,labeled=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from(0, build_paths=True).go_to(6)
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: 6 distance: 8 path edge count: 4 path: (0, 2, 3, 5, 6)
    >>>
    >>> # The generated next_vertices function returns the empty list if the index is out of range
    >>> next_vertices(7, None)
    ()

    >>> # Access testing data, where weighted undirected edges are given as dict
    >>> edges = {
    ...     'A': (('B', 1), ('C', 2)),
    ...     'B': (('E', 1), ('D', 4), ('F', 1)),
    ...     'C': (('D', 1),),
    ...     'D': (('E', 1),),
    ...     'E': (('F', 2),),
    ...     'F': (('G', 2),)
    ... }
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=True,labeled=True)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from("A")]
    [('A', 'B', 1), ('B', 'E', 1), ('B', 'F', 1), ('E', 'D', 1), ('D', 'C', 1), ('F', 'G', 2)]
    >>> # Note, that the minimum spanning tree contains edge ('D', 'C') in the direction not
    >>> # directly listed in the input.

    >>> # Access same testing graph, but the weighted undirected edges are given as list, vertices
    >>> # are int
    >>> edges = [
    ...     ((1, 1), (2, 2)),
    ...     ((4, 1), (3, 4), (5, 1)),
    ...     ((3, 1),),
    ...     ((4, 1),),
    ...     ((5, 2),),
    ...     ((6, 2),)
    ... ]
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=True,labeled=True)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from(0)]
    [(0, 1, 1), (1, 4, 1), (1, 5, 1), (4, 3, 1), (3, 2, 1), (5, 6, 2)]
    >>> # Note, that the minimum spanning tree contains edge (3, 2) in the direction not
    >>> # directly listed in the input.
    >>> next_vertices = nog.adapt_edge_index(set(),add_inverted=True,labeled=False)
    Traceback (most recent call last):
    ValueError: graph must be Mapping or Sequence

    # ------------ adapt_edge_iterable -------------
    >>> # Access testing data, where weighted directed edges are given as flat unsorted edge list
    >>> edges = [
    ...     ('A', 'B', 1), ('A', 'C', 2),
    ...     ('B', 'C', 5), ('B', 'D', 5),
    ...     ('C', 'D', 2), ('C', 'E', 1), ('C', 'F', 5),
    ...     ('D', 'F', 2), ('D', 'G', 5),
    ...     ('E', 'F', 5), ('E', 'B', 1),
    ...     ('F', 'G', 2)
    ... ]
    >>> import nographs as nog
    >>> next_vertices = nog.adapt_edge_iterable(edges,add_inverted=False,labeled=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from("A", build_paths=True).go_to("G")
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: G distance: 8 path edge count: 4 path: ('A', 'C', 'D', 'F', 'G')
    >>>
    >>> # Access testing data, where weighted undirected edges are given as flat edge list
    >>> edges = [
    ...     ('A', 'B', 1), ('A', 'C', 2),
    ...     ('B', 'E', 1), ('B', 'D', 4), ('B', 'F', 1),
    ...     ('C', 'D', 1),
    ...     ('D', 'E', 1),
    ...     ('E', 'F', 2),
    ...     ('F', 'G', 2)
    ... ]
    >>> next_vertices = nog.adapt_edge_iterable(edges,add_inverted=True,labeled=True)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from("A")]
    [('A', 'B', 1), ('B', 'E', 1), ('B', 'F', 1), ('E', 'D', 1), ('D', 'C', 1), ('F', 'G', 2)]
    >>> # Note, that the minimum spanning tree contains edge ('D', 'C') in the direction not
    >>> # directly listed in the input.

    """
    # inspection PyShadowingNames


# --------- Tests for the gadgets --------
# (Only test cases that are not covered by examples in the documentation)

class ArrayTests:
    """
    Array positions should wrap at the position limits of each dimension:

    >>> array = nog.Array('''
    ... S..#.
    ... .#.#G
    ... #G...
    ... '''.strip().splitlines(), 2)
    >>> starts, goals = (array.findall(c) for c in "SG")
    >>> next_vertices = array.next_vertices_from_forbidden("#", wrap=True)
    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> for found in traversal.start_from(start_vertices=starts, build_paths=True
    ...     ).go_for_vertices_in(goals):
    ...         traversal.depth, traversal.paths[found]
    (2, ((0, 0), (0, 4), (1, 4)))
    (2, ((0, 0), (0, 1), (2, 1)))

    "Diagonal" moves (edges) in the array positions should be allowed:
    >>> array = nog.Array('''
    ... S....
    ... ##...
    ... .G...
    ... '''.strip().splitlines(), 2)
    >>> start, goal = (array.findall(c)[0] for c in "SG")
    >>> next_vertices = array.next_vertices_from_forbidden("#", diagonals=True)
    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> found = traversal.start_from(start, build_paths=True).go_to(goal)
    >>> traversal.depth, traversal.paths[found]
    (3, ((0, 0), (0, 1), (1, 2), (2, 1)))
    """

# if __name__ == "__main__":
#     import doctest
#
#     doctest.testmod()
