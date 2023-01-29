import collections  # noqa: F401
import itertools  # noqa: F401
import nographs as nog  # noqa: F401


# --- Utility functions ---
def edges(next_edges_or_vertices, vertices):
    # Test functionality of a next_edges or next_vertices function by calling
    # it for all vertices and return the relationship between inputs and
    # outputs in a dict.
    return dict((vertex, next_edges_or_vertices(vertex, None)) for vertex in vertices)


def print_results(traversal, start_vertices_for_path: set, no_paths=False):
    has_path = start_vertices_for_path
    for vertex in traversal:
        has_path.add(vertex)
        print(f"Reported: {vertex=} {traversal.depth=} {traversal.visited=}")
        if not no_paths:
            print(f"  traversal.paths[vertex]={traversal.paths[vertex]}")
    if not no_paths:
        print("All paths:", [traversal.paths[vertex] for vertex in sorted(has_path)])


def print_partial_results(traversal, paths_to=None):
    vertices = []
    for vertex in traversal:
        vertices.append(vertex)
    print(vertices[:5], vertices[-6:])
    if paths_to is not None:
        path = traversal.paths[paths_to]
        print(tuple(path[:2]), tuple(path[-2:]))


def graph_report_next(edges):
    def graph(vertex, traversal):
        print(f"Next called: {vertex=} {traversal.depth=} {traversal.visited=}")
        return edges.get(vertex, ())

    return graph


# --- Test graphs ---
edges_diamond_unlabeled = {0: (1, 2), 1: (3,), 2: (3,)}
graph_diamond_unlabeled = graph_report_next(edges_diamond_unlabeled)
edges_diamond_labeled = {0: ((1, 2), (2, 1)), 1: ((3, 2),), 2: ((3, 2),)}
graph_diamond_labeled = graph_report_next(edges_diamond_labeled)


def graph_small_binary_tree_report_next(vertex, traversal):
    print(f"Next called: {vertex=} {traversal.depth=} {traversal.visited=}")
    return (2 * vertex, 2 * vertex + 1) if 1 <= vertex <= 3 else ()


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
    >>> traversal = nog.TraversalShortestPaths(spiral_graph).start_from(
    ...    0, build_paths=True)
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

    >>> next_vertices = nog.adapt_edge_index(
    ...     edges_weighted_dict,add_inverted=False,attributes=True)
    >>> edges(next_vertices, edges_weighted_dict.keys()) == edges_weighted_dict
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...     edges_weighted_dict,add_inverted=True,attributes=True)
    >>> edges(next_vertices, edges_weighted_dict.keys()
    ...      )  # doctest: +NORMALIZE_WHITESPACE
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
    ...     add_inverted=False, attributes=True)
    >>> tuple(edges(next_vertices, range(len(edges_weighted_sequence))).values()
    ...      ) == edges_weighted_sequence
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_weighted_sequence,add_inverted=True,attributes=True)
    >>> edges(next_vertices, range(len(edges_weighted_sequence))
    ...     )  # doctest: +NORMALIZE_WHITESPACE
    {0: [(1, 1), (2, 2)], 1: [(0, 1), (2, 5), (3, 5), (4, 1)],
     2: [(0, 2), (1, 5), (3, 2), (4, 1), (5, 5)], 3: [(1, 5), (2, 2), (5, 2),
     (6, 5)],
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
    ...    edges_unweighted_dict,add_inverted=False,attributes=False)
    >>> edges(next_vertices, edges_weighted_dict.keys()) == edges_unweighted_dict
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_dict,add_inverted=True,attributes=False)
    >>> edges(next_vertices, edges_weighted_dict.keys()
    ...      )  # doctest: +NORMALIZE_WHITESPACE
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
    ...    edges_unweighted_sequence,add_inverted=False,attributes=False)
    >>> tuple(edges(next_vertices, range(len(edges_weighted_sequence))).values()
    ...     ) == edges_unweighted_sequence
    True

    >>> next_vertices = nog.adapt_edge_index(
    ...    edges_unweighted_sequence,add_inverted=True,attributes=False)
    >>> edges(next_vertices, range(len(edges_weighted_sequence))
    ...      )  # doctest: +NORMALIZE_WHITESPACE
    {0: [1, 2], 1: [0, 2, 3, 4], 2: [0, 1, 3, 4, 5], 3: [1, 2, 5, 6],
     4: [2, 5, 1], 5: [2, 3, 4, 6]}
    """


# --------- Types -----------


class Types:
    """Test function vertex_as_id. Test needed here, since this
    function is not intended to be really called anywhere in NoGraphs.

    >>> nog.vertex_as_id(0)
    0
    """


# --------- Tests for protocols and ABCs -----------


class ProtocolAndABCNotImplementedErrors:
    """-- Abstract methods of protocols and ABCs.
    Check, if exception raised when called.

    Note: All calls are illegal w.r.t. typing (only the number of parameters
    is correct): Instance methods are called like a classmethod would,
    the given argument for parameter self has the wrong type, and other
    arguments may be illegal, too, and the generic parameters are missing.
    But all this does not matter here, since the methods are to raise
    NotImplementedError directly and in all cases.

    -- Module types--

    >>> nog.Weight.__add__(0, 0)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Weight.__lt__(0, 0)
    Traceback (most recent call last):
    NotImplementedError
    >>> nog.Weight.__le__(0, 0)
    Traceback (most recent call last):
    NotImplementedError

    -- Module gear_collections --

    >>> nog.GettableSettableForGearProto.__getitem__(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GettableSettableForGearProto.__setitem__(None, None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.SequenceForGearProto.__len__(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.SequenceForGearProto.append(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.SequenceForGearProto.extend(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.SequenceForGearProto.__iter__(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto.sequence(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto.default(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto.extend_and_set(None, None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto.update_from_keys(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto.index_and_bit_method(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForSetProto._from_iterable(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForMappingProto.sequence(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForMappingProto.default(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForMappingProto.extend_and_set(None, None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForMappingProto.update_from_keys_values(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSequenceWrapperForMappingProto.update_default(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSetWrappingSequence.__iter__(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSetWrappingSequence.__len__(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSetWrappingSequence.update_from_keys(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSetWrappingSequence._from_iterable(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.VertexSetWrappingSequence.index_and_bit_method(None)
    Traceback (most recent call last):
    NotImplementedError


    -- Module gear --

    >>> nog.GearWithoutDistances.vertex_id_set(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.vertex_id_to_vertex_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.vertex_id_to_path_attributes_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.GearWithoutDistances.sequence_of_vertices(None, None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.zero(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.infinity(None)
    Traceback (most recent call last):
    NotImplementedError

    >>> nog.Gear.vertex_id_to_distance_mapping(None, None)
    Traceback (most recent call last):
    NotImplementedError


    -- Module gear_collections --

    >>> nog._GettableSettableForGearAssertNoCall.__getitem__(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._GettableSettableForGearAssertNoCall.__setitem__(None, None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.sequence(None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.default(None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.extend_and_set(None, None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.update_from_keys(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.index_and_bit_method(None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.update_from_keys_values(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall.update_default(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> nog._VertexSequenceWrapperAssertNoCall._from_iterable(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen
    """


# --------- Paths -----------


class PathHandling:
    # noinspection PyShadowingNames
    """
    - Error handling in Paths
      (Path detects illegal calls with None as vertex and with non-existing vertices.)
    - Iteration works for both types of paths both with vertices and with edges.

    -- Unlabeled paths --

    >>> gear = nog.GearDefault()
    >>> path_unlabeled = nog.PathsOfUnlabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path_unlabeled[None]  # Calls p.iter_vertices_to_start
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> None in path_unlabeled
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
    >>> path_unlabeled.append_edge(0, 0, None)
    >>> path_unlabeled.append_edge(0, 1, None)
    >>> # Calls p.iter_vertices_from_start and p.iter_vertices_to_start
    >>> path_unlabeled[1]
    (0, 1)
    >>> # Also calls p.iter_edges_to_start
    >>> tuple(path_unlabeled.iter_edges_from_start(1))
    ((0, 1),)
    >>> path_unlabeled.append_edge(1, 2, None)
    >>> path_unlabeled[2]
    (0, 1, 2)
    >>> tuple(path_unlabeled.iter_edges_from_start(2))
    ((0, 1), (1, 2))

    -- Paths (and not overridden in PathsOfUNlabeledEdges) --
    >>> path_unlabeled.iter_labeled_edges_from_start(2)
    Traceback (most recent call last):
    RuntimeError: Edges with labels needed, and Traversal needs to know about them
    >>> path_unlabeled.iter_labeled_edges_to_start(2)
    Traceback (most recent call last):
    RuntimeError: Edges with labels needed, and Traversal needs to know about them

    -- Labeled paths --

    >>> path_labeled = nog.PathsOfLabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path_labeled[None]
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> None in path_labeled
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

    >>> path_labeled.append_edge(0, 0, (None, None))
    >>> path_labeled.append_edge(0, 1, (None, "labeled"))
    >>> tuple(path_labeled.iter_vertices_from_start(1))
    (0, 1)
    >>> tuple(path_labeled.iter_edges_from_start(1))
    ((0, 1),)
    >>> tuple(path_labeled[1])  # Calls iter_labeled_edges_from_start
    ((0, 1, 'labeled'),)

    >>> path_labeled.append_edge(1, 2, (None, "labeled"))
    >>> tuple(path_labeled.iter_vertices_from_start(2))
    (0, 1, 2)
    >>> tuple(path_labeled.iter_edges_from_start(2))
    ((0, 1), (1, 2))
    >>> path_labeled[2]  # Calls iter_labeled_edges_from_start
    ((0, 1, 'labeled'), (1, 2, 'labeled'))
    >>> tuple(path_labeled.iter_labeled_edges_to_start(2))
    ((1, 2, 'labeled'), (0, 1, 'labeled'))

    -- Any Path --
    >>> 2 in path_labeled
    True


    -- Unlabeled Path with sequence based predecessor--
    >>> gear = nog.GearForIntVertexIDsAndCFloats()
    >>> path = nog.PathsOfUnlabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path.append_edge(0, 0, [0])
    >>> path.append_edge(0, 1, [1])
    >>> path[1]
    (0, 1)

    -- Labeled Path with sequence based predecessor--
    >>> gear = nog.GearForIntVertexIDsAndCFloats()
    >>> path = nog.PathsOfLabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    gear.vertex_id_to_path_attributes_mapping(()),
    ...    None
    ... )
    >>> path.append_edge(0, 0, [0])
    >>> path.append_edge(0, 1, [1])
    >>> path[1]
    ((0, 1, 1),)


    -- Dummy paths --

    >>> paths_dummy = nog._PathsDummy()  # noinspection PyProtectedMember
    >>> paths_dummy._check_vertex(None)  # noinspection PyProtectedMember
    Traceback (most recent call last):
    RuntimeError: No paths available: Traversal not started or no paths requested.
    >>> paths_dummy.__getitem__(None)  # noinspection PyProtectedMember
    Traceback (most recent call last):
    RuntimeError: No paths available: Traversal not started or no paths requested.
    >>> predecessor = paths_dummy._predecessor
    >>> predecessor[None]
    Traceback (most recent call last):
    KeyError
    >>> del predecessor[None]
    Traceback (most recent call last):
    KeyError
    >>> predecessor[None] = None
    Traceback (most recent call last):
    RuntimeError: Cannot add a path, traversal not started or no paths requested.
    >>> tuple(iter(predecessor)), len(predecessor), None in predecessor
    ((), 0, False)
    """


# --------- Tests for all traversals -----------


class GraphWithoutEdges:
    # noinspection PyShadowingNames
    """-- Graph without edges --
    -- 1) No vertices are reported. Exception: topological sorting reports it.

    >>> def no_next(v, _):
    ...     return ()
    >>> def heuristic(v):
    ...    return 0  # Graph has just une vertex and no edges. So, no heuristic needed.

    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalNeighborsThenDepth,
    ...                  nog.TraversalShortestPaths, nog.TraversalMinimumSpanningTree,
    ...                  nog.TraversalTopologicalSort):
    ...     list(strategy(no_next).start_from(0))
    []
    []
    []
    []
    []
    [0]
    >>> list(nog.TraversalAStar(no_next).start_from(heuristic, 0))
    []

    -- 2) go_to and go_for_vertices_in find nothing and correctly report this
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

    -- 3) __init__ and start_from of the strategies w/o weights detect parameter errors
    >>> traversal = nog.TraversalBreadthFirst(no_next)
    >>> traversal = traversal.start_from(start_vertex=0, start_vertices=(0,))
    Traceback (most recent call last):
    RuntimeError: Both start_vertex and start_vertices provided.
    >>> traversal = traversal.start_from()
    Traceback (most recent call last):
    RuntimeError: Neither start_vertex nor start_vertices provided.

    >>> traversal = nog.TraversalBreadthFirst()
    Traceback (most recent call last):
    RuntimeError: Neither next_vertices nor next_edges nor next_labeled_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_vertices=no_next, next_edges=no_next)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_vertices=no_next,
    ...                                       next_labeled_edges=no_next)
    Traceback (most recent call last):
    RuntimeError: Both next_vertices and next_labeled_edges provided.
    >>> traversal = nog.TraversalBreadthFirst(next_edges=no_next,
    ...                                       next_labeled_edges=no_next)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.

    -- 3) __init__ and start_from of the strategies with weights detect parameter errors
    >>> traversal = nog.TraversalShortestPaths()
    Traceback (most recent call last):
    RuntimeError: Neither next_edges and next_labeled_edges provided.
    >>> traversal = nog.TraversalShortestPaths(next_edges=no_next,
    ...                                       next_labeled_edges=no_next)
    Traceback (most recent call last):
    RuntimeError: Both next_edges and next_labeled_edges provided.
    """


class GraphWithOneEdgeAndPathVariants:
    # noinspection PyShadowingNames
    """-- Graph with one edge --
    Start vertex not reported (exception: topological sorting). First edge followed.
    Paths not build if not demanded, and build if demanded.
    Labeled paths not allowed for unlabeled edges, and build for labeled edges, if
    demanded. Calculation limit raises Exception at exactly correct number of visited
    vertices.

    >>> def test(traversal, labeled_paths, **start_args):
    ...     print(list(traversal.start_from(0, **start_args)))
    ...     print(traversal.paths is None)
    ...     print(next(traversal.start_from(0, **start_args)))
    ...     _ = traversal.start_from(0, build_paths=True, **start_args).go_to(1)
    ...     if labeled_paths:
    ...        print(tuple(traversal.paths.iter_vertices_from_start(1)))
    ...     print(traversal.paths[1])

    # -- Unlabeled graph --
    >>> def next_vertices(v, _):
    ...     return (1,) if v == 0 else ()

    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> test(traversal, labeled_paths=False)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> test(traversal, labeled_paths=False)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalNeighborsThenDepth(next_vertices)
    >>> test(traversal, labeled_paths=False)
    [1]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(next_vertices)
    >>> test(traversal, labeled_paths=False)
    [1, 0]
    True
    1
    (0, 1)
    >>> traversal = nog.TraversalTopologicalSort(next_vertices, is_tree=True)
    >>> test(traversal, labeled_paths=False)
    [1, 0]
    True
    1
    (0, 1)


    # -- Labeled graph (changed for v3: next_labeled_edges instead of labeled_paths) --
    >>> def next_labeled_edges(v, _):
    ...     return ((1, 1),) if v == 0 else ()
    >>> def next_weighted_labeled_edges(v, _):
    ...     return ((1, 1, 1),) if v == 0 else ()

    >>> traversal = nog.TraversalBreadthFirst(next_labeled_edges=next_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalDepthFirst(next_labeled_edges=next_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalNeighborsThenDepth(
    ...     next_labeled_edges=next_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalShortestPaths(
    ...     next_labeled_edges=next_weighted_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalMinimumSpanningTree(
    ...     next_labeled_edges=next_weighted_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalTopologicalSort(
    ...     next_labeled_edges=next_weighted_labeled_edges)
    >>> test(traversal, labeled_paths=True)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 1),)
    >>> traversal = nog.TraversalTopologicalSort(
    ...     next_labeled_edges=next_weighted_labeled_edges, is_tree=True)
    >>> test(traversal, labeled_paths=True)
    [1, 0]
    True
    1
    (0, 1)
    ((0, 1, 1),)


    >>> def next_weighted_edges(v, _):
    ...     return ((1, 1),) if v == 0 else ()

    >>> traversal = nog.TraversalBreadthFirst(next_edges=next_weighted_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalDepthFirst(next_edges=next_weighted_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalNeighborsThenDepth(next_edges=next_weighted_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_weighted_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalTopologicalSort(next_edges=next_weighted_edges,
    ...     is_tree=True)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_weighted_edges)
    >>> _ = list(traversal.start_from(0, calculation_limit=2))
    >>> _ = list(traversal.start_from(0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_weighted_edges)
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
    >>> traversal = nog.TraversalAStar(next_edges=next_weighted_labeled_edges)
    >>> list(traversal.start_from(heuristic, 0))
    [1]
    >>> traversal.paths is None
    True
    >>> _ = traversal.start_from(heuristic, 0, build_paths=True).go_to(1)
    >>> traversal.paths[1]
    (0, 1)
    >>> traversal = nog.TraversalAStar(next_labeled_edges=next_weighted_labeled_edges)
    >>> _ = traversal.start_from(heuristic, 0, build_paths=True).go_to(1)
    >>> tuple(traversal.paths.iter_labeled_edges_from_start(1))
    ((0, 1, 1),)

    >>> traversal = nog.TraversalAStar(next_edges=next_weighted_labeled_edges)
    >>> _ = list(traversal.start_from(heuristic, 0, calculation_limit=2))
    >>> _ = list(traversal.start_from(heuristic, 0, calculation_limit=1))
    Traceback (most recent call last):
    RuntimeError: Number of visited vertices reached limit
    """


class GraphWithOneEdgeAndVertexToId:
    # noinspection PyShadowingNames
    """-- Graph with one edge, parameter vertex_to_id used --
    For the test, vertices are given as list [int] to have something that is not
    hashable. Start vertex not reported (exception: topological sorting). First edge
    followed. Paths not build if not demanded, and build if demanded. Labeled paths
    not allowed for unlabeled edges, and build for labeled edges, if demanded.
    Calculation limit raises Exception at exactly correct number of visited vertices.

    >>> def test(traversal, start, goal, labeled_paths, **start_args):
    ...     print(list(traversal.start_from(start_vertex=start, **start_args)))
    ...     print(traversal.paths is None)
    ...     print(next(traversal.start_from(start_vertex=start, **start_args)))
    ...     _ = traversal.start_from(start_vertex=start, build_paths=True,
    ...                              **start_args).go_to(goal)
    ...     if labeled_paths:
    ...        print(tuple(traversal.paths.iter_vertices_from_start(goal)))
    ...     print(traversal.paths[goal])

    >>> def next_vertices(v, _):
    ...     return ([1],) if v == [0] else ()

    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_vertices)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalDepthFirstFlex(
    ...    lambda l: l[0], nog.GearDefault(), next_vertices)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...    lambda l: l[0], nog.GearDefault(), next_vertices)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...    lambda l: l[0], nog.GearDefault(), next_vertices)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1], [0]]
    True
    [1]
    ([0], [1])




    >>> def next_labeled_edges(v, _):
    ...     return (([1], 1, 1),) if v == [0] else ()

    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)

    >>> traversal = nog.TraversalDepthFirstFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalDepthFirstFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)

    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalNeighborsThenDepthFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)

    >>> traversal = nog.TraversalShortestPathsFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalShortestPathsFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)

    >>> traversal = nog.TraversalMinimumSpanningTreeFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalMinimumSpanningTreeFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)

    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False)
    [[1], [0]]
    True
    [1]
    ([0], [1])
    >>> traversal = nog.TraversalTopologicalSortFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True)
    [[1], [0]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)



    >>> def heuristic(v):
    ...    return 1 if v == [0] else 0  # heuristic with perfect estimation

    >>> traversal = nog.TraversalAStarFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=False, heuristic=heuristic)
    [[1]]
    True
    [1]
    ([0], [1])

    >>> traversal = nog.TraversalAStarFlex(
    ...     lambda l: l[0], nog.GearDefault(), next_labeled_edges=next_labeled_edges)
    >>> test(traversal, [0], [1], labeled_paths=True, heuristic=heuristic)
    [[1]]
    True
    [1]
    ([0], [1])
    (([0], [1], 1),)
    """


class VertexToIdWithGoForVerticesInAndGoTo:
    """
    >>> def next_labeled_edges(v, _):
    ...     i = v[0]
    ...     return (([i+1], 1, i+1),) if i < 4 else ()
    >>> goal_vertices = ([1], [3])
    >>> impossible_goals = ([5],)
    >>> for strategy in (
    ...     nog.TraversalBreadthFirstFlex, nog.TraversalDepthFirstFlex,
    ...     nog.TraversalNeighborsThenDepthFlex,
    ...     nog.TraversalShortestPathsFlex, nog.TraversalMinimumSpanningTreeFlex,
    ...     nog.TraversalTopologicalSortFlex
    ... ):
    ...     print(strategy.__name__)
    ...     traversal = strategy(lambda l: l[0], nog.GearDefault(),
    ...         next_edges=next_labeled_edges)
    ...     list(traversal.start_from([0]))
    ...     list(traversal.start_from([0]).go_for_vertices_in(goal_vertices))
    TraversalBreadthFirstFlex
    [[1], [2], [3], [4]]
    [[1], [3]]
    TraversalDepthFirstFlex
    [[1], [2], [3], [4]]
    [[1], [3]]
    TraversalNeighborsThenDepthFlex
    [[1], [2], [3], [4]]
    [[1], [3]]
    TraversalShortestPathsFlex
    [[1], [2], [3], [4]]
    [[1], [3]]
    TraversalMinimumSpanningTreeFlex
    [[1], [2], [3], [4]]
    [[1], [3]]
    TraversalTopologicalSortFlex
    [[4], [3], [2], [1], [0]]
    [[3], [1]]

    >>> def heuristic(v):
    ...    return 1 if v == [0] else 0  # heuristic with perfect estimation
    >>> traversal = nog.TraversalAStarFlex(lambda l: l[0], nog.GearDefault(),
    ...     next_labeled_edges)
    >>> list(traversal.start_from(heuristic, [0]))
    [[1], [2], [3], [4]]
    >>> list(traversal.start_from(heuristic, [0]).go_for_vertices_in(goal_vertices))
    [[1], [3]]

    For one of the traversals, test the case "not all goals reachable":
    >>> list(traversal.start_from(heuristic, [0]).go_for_vertices_in(impossible_goals))
    Traceback (most recent call last):
    KeyError: 'Not all of the given vertices have been found'

    For one of the traversals, test for go_to_vertex: Not immediatetly found and
    then not found at all, and not found with fail_simlently:
    >>> traversal = nog.TraversalBreadthFirstFlex(lambda l: l[0], nog.GearDefault(),
    ...     next_edges=next_labeled_edges)
    >>> traversal.start_from([0]).go_to([5])
    Traceback (most recent call last):
    KeyError: 'Vertex not found, graph exhausted.'
    >>> traversal.start_from([0]).go_to([5], fail_silently=True) is None
    True
    """


class NormalGraphTraversalsWithOrWithoutLabels:
    # noinspection PyShadowingNames
    """
    -- Small example graph, 3 Traversal strategies that can work with and wihout
    labels -- Correct traversal of TraversalBreadthFirst, TraversalDepthFirst,
    TraversalTopologicalSort. For: graph without labels and graph with labels.
    Without and with vertices defined as already visited (only tested for graph
    without labels). (Uses implementation decisions:
    - TraversalBreadthFirst traverses edges in given order
    - TraversalDepthFirst and TraversalTopologicalSort traverse edges in reversed order)
    """

    @staticmethod
    def unlabeled_edges():
        """
        >>> traversal = nog.TraversalBreadthFirst(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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


        >>> traversal = nog.TraversalDepthFirst(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
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

        >>> traversal = nog.TraversalDepthFirst(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=-1 traversal.visited={0}
        Reported: vertex=2 traversal.depth=-1 traversal.visited={0, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=-1 traversal.visited={0, 2}
        Reported: vertex=3 traversal.depth=-1 traversal.visited={0, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=-1 traversal.visited={0, 2, 3}
        Reported: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 1)
        Next called: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


        >>> traversal = nog.TraversalNeighborsThenDepth(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0}
        Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1}
          traversal.paths[vertex]=(0, 1)
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]

        >>> traversal = nog.TraversalNeighborsThenDepth(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=-1 traversal.visited={0}
        Reported: vertex=1 traversal.depth=-1 traversal.visited={0, 1}
          traversal.paths[vertex]=(0, 1)
        Reported: vertex=2 traversal.depth=-1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=-1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        Next called: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


        >>> traversal = nog.TraversalTopologicalSort(graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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
        """
        pass

    @staticmethod
    def unlabeled_edges_and_int_id_gear():
        """
        >>> gear = nog.GearForIntVertexIDsAndCFloats()

        >>> traversal = nog.TraversalBreadthFirstFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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


        >>> traversal = nog.TraversalDepthFirstFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
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

        >>> traversal = nog.TraversalDepthFirstFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=-1 traversal.visited={0}
        Reported: vertex=2 traversal.depth=-1 traversal.visited={0, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=-1 traversal.visited={0, 2}
        Reported: vertex=3 traversal.depth=-1 traversal.visited={0, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=-1 traversal.visited={0, 2, 3}
        Reported: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 1)
        Next called: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


        >>> traversal = nog.TraversalNeighborsThenDepthFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0}
        Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1}
          traversal.paths[vertex]=(0, 1)
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]

        >>> traversal = nog.TraversalNeighborsThenDepthFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=-1 traversal.visited={0}
        Reported: vertex=1 traversal.depth=-1 traversal.visited={0, 1}
          traversal.paths[vertex]=(0, 1)
        Reported: vertex=2 traversal.depth=-1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=-1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        Next called: vertex=1 traversal.depth=-1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]


        >>> traversal = nog.TraversalTopologicalSortFlex(
        ...     nog.vertex_as_id, gear, graph_diamond_unlabeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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
        """
        pass

    @staticmethod
    def unlabeled_edges_and_already_visited():
        """
        1b. Unlabeled edges and already_visited

        >>> traversal = nog.TraversalBreadthFirst(graph_diamond_unlabeled)
        >>> already_visited={1}
        >>> traversal = traversal.start_from(
        ...     0, build_paths=True, already_visited=already_visited)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[1]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalDepthFirst(graph_diamond_unlabeled)
        >>> already_visited={1}
        >>> traversal = traversal.start_from(
        ...     0, build_paths=True, compute_depth=True,
        ...     already_visited=already_visited)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[1]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalNeighborsThenDepth(graph_diamond_unlabeled)
        >>> already_visited={1}
        >>> traversal = traversal.start_from(
        ...     0, build_paths=True, compute_depth=True,
        ...     already_visited=already_visited)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[1]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.

        >>> traversal = nog.TraversalTopologicalSort(graph_diamond_unlabeled)
        >>> already_visited={1}
        >>> traversal = traversal.start_from(
        ...     0, build_paths=True, already_visited=already_visited)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2)
        Reported: vertex=0 traversal.depth=0 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0,)
        All paths: [(0,), (0, 2), (0, 2, 3)]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[1]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.
        """
        pass

    @staticmethod
    def unlabeled_edges_and_seq_based_already_visited():
        """
        >>> traversal = nog.TraversalBreadthFirst(graph_diamond_unlabeled)
        >>> already_visited = nog.GearForIntVertexIDsAndCFloats().vertex_id_set(())
        >>> already_visited.add(1)
        >>> traversal = traversal.start_from(
        ...     0, build_paths=True, already_visited=already_visited)

        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0, 1}
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 2), (0, 2, 3)]
        >>> print("Already visited:", already_visited)
        Already visited: {0, 1, 2, 3}
        >>> traversal.paths[1]
        Traceback (most recent call last):
        RuntimeError: Paths: No path for given vertex.
        """
        pass

    @staticmethod
    def labeled_edges():
        """
        >>> traversal = nog.TraversalBreadthFirst(next_edges=graph_diamond_labeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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

        >>> traversal = nog.TraversalDepthFirst(next_edges=graph_diamond_labeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
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

        >>> traversal = nog.TraversalNeighborsThenDepth(
        ...     next_edges=graph_diamond_labeled)
        >>> traversal = traversal.start_from(0, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {0})
        Next called: vertex=0 traversal.depth=0 traversal.visited={0}
        Reported: vertex=1 traversal.depth=1 traversal.visited={0, 1}
          traversal.paths[vertex]=(0, 1)
        Reported: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
          traversal.paths[vertex]=(0, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited={0, 1, 2}
        Reported: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
          traversal.paths[vertex]=(0, 2, 3)
        Next called: vertex=3 traversal.depth=2 traversal.visited={0, 1, 2, 3}
        Next called: vertex=1 traversal.depth=1 traversal.visited={0, 1, 2, 3}
        All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]

        >>> traversal = nog.TraversalTopologicalSort(next_edges=graph_diamond_labeled)
        >>> traversal = traversal.start_from(0, build_paths=True)
        >>> print_results(traversal, {0})
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
        """
        pass

    @staticmethod
    def is_tree():
        """
        >>> next_vertices = graph_small_binary_tree_report_next

        >>> traversal = nog.TraversalBreadthFirst(next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(1, build_paths=True)
        >>> print_results(traversal, {1})
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

        >>> traversal = nog.TraversalDepthFirst(next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(1, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {1})
        Next called: vertex=1 traversal.depth=0 traversal.visited=set()
        Reported: vertex=3 traversal.depth=1 traversal.visited=set()
          traversal.paths[vertex]=(1, 3)
        Next called: vertex=3 traversal.depth=1 traversal.visited=set()
        Reported: vertex=7 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 3, 7)
        Next called: vertex=7 traversal.depth=2 traversal.visited=set()
        Reported: vertex=6 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 3, 6)
        Next called: vertex=6 traversal.depth=2 traversal.visited=set()
        Reported: vertex=2 traversal.depth=1 traversal.visited=set()
          traversal.paths[vertex]=(1, 2)
        Next called: vertex=2 traversal.depth=1 traversal.visited=set()
        Reported: vertex=5 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 2, 5)
        Next called: vertex=5 traversal.depth=2 traversal.visited=set()
        Reported: vertex=4 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 2, 4)
        Next called: vertex=4 traversal.depth=2 traversal.visited=set()
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]

        >>> traversal = nog.TraversalNeighborsThenDepth(next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(1, build_paths=True, compute_depth=True)
        >>> print_results(traversal, {1})
        Next called: vertex=1 traversal.depth=0 traversal.visited=set()
        Reported: vertex=2 traversal.depth=1 traversal.visited=set()
          traversal.paths[vertex]=(1, 2)
        Reported: vertex=3 traversal.depth=1 traversal.visited=set()
          traversal.paths[vertex]=(1, 3)
        Next called: vertex=3 traversal.depth=1 traversal.visited=set()
        Reported: vertex=6 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 3, 6)
        Reported: vertex=7 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 3, 7)
        Next called: vertex=7 traversal.depth=2 traversal.visited=set()
        Next called: vertex=6 traversal.depth=2 traversal.visited=set()
        Next called: vertex=2 traversal.depth=1 traversal.visited=set()
        Reported: vertex=4 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 2, 4)
        Reported: vertex=5 traversal.depth=2 traversal.visited=set()
          traversal.paths[vertex]=(1, 2, 5)
        Next called: vertex=5 traversal.depth=2 traversal.visited=set()
        Next called: vertex=4 traversal.depth=2 traversal.visited=set()
        All paths: [(1,), (1, 2), (1, 3), (1, 2, 4), (1, 2, 5), (1, 3, 6), (1, 3, 7)]

        >>> traversal = nog.TraversalTopologicalSort(next_vertices, is_tree=True)
        >>> traversal = traversal.start_from(1, build_paths=True)
        >>> print_results(traversal, {1})
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
        pass


class NormalGraphTraversalsWithLabels:
    # noinspection PyShadowingNames
    """-- Small example graph. The three strategies that need edge weights. --
    For TraversalShortestPaths, test option known_distances, too.

    -- TraversalShortestPaths --
    First we test without know_distances, and with option keep_distances.
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     return ((1, 2), (2, 1)) if vertex == 0 else (
    ...            ((3, 2),) if vertex in (1, 2) else ())

    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> traversal = traversal.start_from(0, build_paths=True, keep_distances=True)
    >>> reported = []
    >>> for vertex in traversal:
    ...     reported.append(vertex)
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     print("distances for reported vertices: " +
    ...        f"{str({vertex: traversal.distances[vertex] for vertex in reported})} " +
    ...        f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.distance=0 traversal.depth=0
    Reported: vertex=2 traversal.distance=1 traversal.depth=1
    distances for reported vertices: {2: 1} traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=1 traversal.depth=1
    Reported: vertex=1 traversal.distance=2 traversal.depth=1
    distances for reported vertices: {2: 1, 1: 2} traversal.paths=(0, 1)
    Next called: vertex=1 traversal.distance=2 traversal.depth=1
    Reported: vertex=3 traversal.distance=3 traversal.depth=2
    distances for reported vertices: {2: 1, 1: 2, 3: 3} traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.distance=3 traversal.depth=2
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3)]
    >>> print("All distances:", str(traversal.distances))
    All distances: {0: 0, 1: 2, 2: 1, 3: 3}

    Now we test with known_distances, but without option keep_distances.
    Start vertex starts with distance 2, and we pretend to have a path to 1 with
    distance 0. Effect: All reported distances are 2 higher than in the test before,
    because the traversal starts at distance 2, and vertex 1 is not visited and
    reported at all, because no path can be found that beats this "already found" low
    distance.
    >>> infinity = float('infinity')
    >>> known_distances = collections.defaultdict(lambda: infinity, ((0, 2), (1, 0)))
    >>> traversal = traversal.start_from(
    ...     0, build_paths=True, known_distances=known_distances)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.distance=2 traversal.depth=0
    Reported: vertex=2 traversal.distance=3 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=3 traversal.depth=1
    Reported: vertex=3 traversal.distance=5 traversal.depth=2 traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.distance=5 traversal.depth=2
    >>> print("All paths:", [traversal.paths[vertex]
    ...                     for vertex in range(4) if vertex != 1])
    All paths: [(0,), (0, 2), (0, 2, 3)]
    >>> print("Known distances:", dict(known_distances))
    Known distances: {0: 0, 1: 0, 2: 0, 3: 0}

    The same again, but with a sequence-based known_distances
    >>> gear = nog.GearForIntVertexIDsAndIntsMaybeFloats()
    >>> known_distances = gear.vertex_id_to_distance_mapping(())
    >>> known_distances.update([(0, 2), (1, 0)])
    >>> traversal = traversal.start_from(
    ...     0, build_paths=True, known_distances=known_distances)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.distance=} {traversal.depth=} "
    ...         + f"traversal.paths={traversal.paths[vertex]}")
    Next called: vertex=0 traversal.distance=2 traversal.depth=0
    Reported: vertex=2 traversal.distance=3 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.distance=3 traversal.depth=1
    Reported: vertex=3 traversal.distance=5 traversal.depth=2 traversal.paths=(0, 2, 3)
    Next called: vertex=3 traversal.distance=5 traversal.depth=2


    -- TraversalMinimumSpanningTree --
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.edge=}")
    ...     return ((1, 2), (2, 1)) if vertex == 0 else (
    ...            ((3, 3),) if vertex in (1, 2) else ())
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


    -- TraversaAStar --
    Typically, one would use go_to(3) for our goal vertex 3, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> def heuristic(v):
    ...    # makes 2nd best path visited first
    ...    return {0:6, 1:1, 2:2, 3:0, 4:infinity}[v]
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.path_length=} {traversal.depth=}")
    ...     return {0: ((1, 3), (2, 3), (4, 1)), 1: ((3, 3),), 2: ((3, 2),), 3:(), 4:()
    ...            }[vertex]
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> traversal = traversal.start_from(heuristic, 0, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...           + f"traversal.paths={traversal.paths[vertex]}"
    ...          )  # doctest: +NORMALIZE_WHITESPACE
    Next called: vertex=0 traversal.path_length=0 traversal.depth=0
    Reported: vertex=1 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 1)
    Next called: vertex=1 traversal.path_length=3 traversal.depth=1
    Reported: vertex=2 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.path_length=3 traversal.depth=1
    Reported: vertex=3 traversal.path_length=5 traversal.depth=2 traversal.paths=(0,
    2, 3)
    Next called: vertex=3 traversal.path_length=5 traversal.depth=2
    Reported: vertex=4 traversal.path_length=1 traversal.depth=1 traversal.paths=(0, 4)
    Next called: vertex=4 traversal.path_length=1 traversal.depth=1
    >>> print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    All paths: [(0,), (0, 1), (0, 2), (0, 2, 3), (0, 4)]


    Variant of the test with option known_distances.
    For the start vertex, we define a start distance. Effect: All distances are now 2
    higher. For vertex 1, we define an artificial and low distance of 0. Effect: it is
    not visited.
    >>> known_distances = collections.defaultdict(lambda: infinity, ((0, 2),(1, 0)))
    >>> known_path_length_guesses = collections.defaultdict(lambda: infinity)
    >>> traversal = traversal.start_from(heuristic, 0, build_paths=True,
    ...     known_distances=known_distances,
    ...     known_path_length_guesses=known_path_length_guesses)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...           + f"traversal.paths={traversal.paths[vertex]}"
    ...           )  # doctest: +NORMALIZE_WHITESPACE
    Next called: vertex=0 traversal.path_length=2 traversal.depth=0
    Reported: vertex=2 traversal.path_length=5 traversal.depth=1 traversal.paths=(0, 2)
    Next called: vertex=2 traversal.path_length=5 traversal.depth=1
    Reported: vertex=3 traversal.path_length=7 traversal.depth=2 traversal.paths=(0, 2,
    3)
    Next called: vertex=3 traversal.path_length=7 traversal.depth=2
    Reported: vertex=4 traversal.path_length=3 traversal.depth=1 traversal.paths=(0, 4)
    Next called: vertex=4 traversal.path_length=3 traversal.depth=1
    >>> print("All paths:",
    ...       [traversal.paths[vertex] for vertex in range(5) if vertex!=1])
    All paths: [(0,), (0, 2), (0, 2, 3), (0, 4)]
    >>> print("Distance at goal:", known_distances[3])
    Distance at goal: 7
    >>> print("Best distances found so far:", dict(known_distances))
    Best distances found so far: {0: 2, 1: 0, 2: 5, 4: 3, 3: 7}
    >>> print("Best path len guesses found so far):", dict(known_path_length_guesses))
    Best path len guesses found so far): {0: 8, 2: 7, 3: 7, 4: inf}


    All algorithms, with option is_tree (except for MST, it does not have the option):

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.distance=}")
    ...     return (((2*vertex, 2*vertex), (2*vertex+1, 2*vertex+1)) if 1 <= vertex <= 3
    ...             else ())
    >>> def this_test(strategy):
    ...     traversal = strategy(next_edges, is_tree=True).start_from(
    ...         1, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} {traversal.distance=} " +
    ...             f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(1,8)])
    ...     print("All distances:", traversal.distances)
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

    Test TraversaAStar. Typically, one would use go_to(6) for our goal vertex 6, but for
    the test purposes we continue to iterate the rest of the graph.
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=} {traversal.path_length=}")
    ...     return (((2*vertex, 2*vertex), (2*vertex+1, 2*vertex+1)) if 1 <= vertex <= 3
    ...             else ())
    >>> def heuristic(v):
    ...    return {6:0, 3:3}.get(v, 11)
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> traversal = traversal.start_from(heuristic, 1, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.depth=} {traversal.path_length=} "
    ...           + f"traversal.paths={traversal.paths[vertex]}"
    ...          )  # doctest: +NORMALIZE_WHITESPACE
    Next called: vertex=1 traversal.depth=0 traversal.path_length=0
    Reported: vertex=3 traversal.depth=1 traversal.path_length=3 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.depth=1 traversal.path_length=3
    Reported: vertex=6 traversal.depth=2 traversal.path_length=9 traversal.paths=(1, 3,
    6)
    Next called: vertex=6 traversal.depth=2 traversal.path_length=9
    Reported: vertex=2 traversal.depth=1 traversal.path_length=2 traversal.paths=(1, 2)
    Next called: vertex=2 traversal.depth=1 traversal.path_length=2
    Reported: vertex=4 traversal.depth=2 traversal.path_length=6 traversal.paths=(1, 2,
    4)
    Next called: vertex=4 traversal.depth=2 traversal.path_length=6
    Reported: vertex=5 traversal.depth=2 traversal.path_length=7 traversal.paths=(1, 2,
    5)
    Next called: vertex=5 traversal.depth=2 traversal.path_length=7
    Reported: vertex=7 traversal.depth=2 traversal.path_length=10 traversal.paths=(1, 3,
    7)
    Next called: vertex=7 traversal.depth=2 traversal.path_length=10
    """


class SpecialCases:
    # noinspection PyShadowingNames
    """TraversalDepthFirst, vertex seams to be not visited at first,
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
    Correct traversal of TraversalBreadthFirst, TraversalDepthFirst,
    TraversalTopologicalSort in case of multiple start vertices. No traversal in case
    of no start vertex.
    (Uses implementation descisions:
    - All strategies travers start vertices in given order
    - TraversalBreadthFirst traverses edges in given order
    - TraversalDepthFirst and TraversalTopologicalSort traverse edges in reversed order)

    1. Unlabeled edges
    >>> def next_vertices(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.depth=}")
    ...     return {0: (2,), 1: (3,), 2: (3, 4), 3: (4,), 4: ()}[vertex]
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalNeighborsThenDepth, nog.TraversalTopologicalSort):
    ...     print("- Strategy:", strategy.__name__, "-")
    ...     # an iterator (can be iterated only once) should be enough for lib
    ...     sv = iter((0,1))
    ...     if (strategy is nog.TraversalDepthFirst
    ...         or strategy is nog.TraversalNeighborsThenDepth
    ...        ):
    ...         traversal = strategy(next_vertices).start_from(
    ...             start_vertices=sv, build_paths=True, compute_depth=True)
    ...     else:
    ...         traversal = strategy(next_vertices).start_from(
    ...             start_vertices=sv, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} "
    ...             + f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(5)])
    ...     traversal = strategy(next_vertices).start_from(
    ...         start_vertices=(), build_paths=True)
    ...     list(traversal)
    ...     sv = iter((0,1))
    ...     if (strategy is nog.TraversalDepthFirst
    ...         or strategy is nog.TraversalNeighborsThenDepth
    ...        ):
    ...         # give results without paths and depth)
    ...         traversal = strategy(next_vertices).start_from(start_vertices=sv)
    ...         for vertex in traversal:
    ...             print(f"Reported: {vertex=}")
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
    Next called: vertex=1 traversal.depth=-1
    Reported: vertex=3
    Next called: vertex=3 traversal.depth=-1
    Reported: vertex=4
    Next called: vertex=4 traversal.depth=-1
    Next called: vertex=0 traversal.depth=-1
    Reported: vertex=2
    Next called: vertex=2 traversal.depth=-1
    <BLANKLINE>
    - Strategy: TraversalNeighborsThenDepth -
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
    Next called: vertex=1 traversal.depth=-1
    Reported: vertex=3
    Next called: vertex=3 traversal.depth=-1
    Reported: vertex=4
    Next called: vertex=4 traversal.depth=-1
    Next called: vertex=0 traversal.depth=-1
    Reported: vertex=2
    Next called: vertex=2 traversal.depth=-1
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
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()
    ...            }[vertex]
    >>> for strategy in (nog.TraversalBreadthFirst, nog.TraversalDepthFirst,
    ...                  nog.TraversalNeighborsThenDepth, nog.TraversalTopologicalSort):
    ...     print("- Strategy:", strategy.__name__, "-")
    ...     traversal = strategy(next_edges=next_edges)
    ...     # an iterator (can be iterated only once) should be enough for lib
    ...     sv = iter((0,1))
    ...     if (strategy is nog.TraversalDepthFirst
    ...         or strategy is nog.TraversalNeighborsThenDepth
    ...        ):
    ...         traversal = traversal.start_from(start_vertices=sv, build_paths=True,
    ...              compute_depth=True)
    ...     else:
    ...         traversal = traversal.start_from(start_vertices=sv, build_paths=True)
    ...     for vertex in traversal:
    ...         print(f"Reported: {vertex=} {traversal.depth=} "
    ...             + f"traversal.paths={traversal.paths[vertex]}")
    ...     print("All paths:", [traversal.paths[vertex] for vertex in range(4)])
    ...     traversal = strategy(next_vertices).start_from(
    ...         start_vertices=(), build_paths=True)
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
    - Strategy: TraversalNeighborsThenDepth -
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
    Correct traversal in case of multiple start vertices. No traversal in case of no
    start vertex.

    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.distance=} {traversal.depth=}")
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()
    ...            }[vertex]
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    ... # an iterator (can be iterated only once) should be enough for lib
    >>> sv = iter((0,1))
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
    ...     return {0: ((2, 1),), 1: ((3, 1),), 2: ((3, 1), (4, 1)), 3: ((4, 1),), 4: ()
    ...            }[vertex]
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> # an iterator (can be iterated only once) should be enough for lib
    >>> sv = iter((0,1))
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
    ...    # heuristic with perfect estimation
    ...    return {0:3, 1:2, 2:2, 3:1, 4:9, 5:0}[vertex]
    >>> def next_edges(vertex, traversal):
    ...     print(f"Next called: {vertex=} {traversal.path_length=} {traversal.depth=}"
    ...          )
    ...     return {0: ((2, 1),), 1: ((3, 1), (4, 1)), 2: ((3, 1),), 3: ((5, 1),),
    ...             4: (), 5:()}[vertex]
    >>> traversal = nog.TraversalAStar(next_edges=next_edges)
    >>> # an iterator (can be iterated only once) should be enough for lib
    >>> sv = iter((0,1))
    >>> traversal = traversal.start_from(heuristic, start_vertices=sv, build_paths=True)
    >>> for vertex in traversal:
    ...     print(f"Reported: {vertex=} {traversal.path_length=} {traversal.depth=} "
    ...           + f"traversal.paths={traversal.paths[vertex]}"
    ...          )  # doctest: +NORMALIZE_WHITESPACE
    Next called: vertex=1 traversal.path_length=0 traversal.depth=0
    Reported: vertex=3 traversal.path_length=1 traversal.depth=1 traversal.paths=(1, 3)
    Next called: vertex=3 traversal.path_length=1 traversal.depth=1
    Reported: vertex=5 traversal.path_length=2 traversal.depth=2 traversal.paths=(1, 3,
    5)
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
    """Check if the library detects the mistake that start_from or one of the
    go_... methods are called on a traversal class instead of an object, i.e., the
    round brackets after the class name have been forgotten.

    In the following test code, such calls are intentionally made, an since these are
    typing errors, that code inspection is disabled for them in the line on top of the
    class.

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


class RandomExample:
    # noinspection PyShadowingNames
    """
    -- Pseudo ramdom example graph. Check number of reachable vertices.

    For each vertex: 3 pseudo-random edges in range(100)
    >>> def next_edges(v, *_):
    ...     for i in range(3):
    ...        yield hash(1/(v*10+i+1)) % 100, 1

    >>> traversal = nog.TraversalBreadthFirst(next_edges=next_edges)
    >>> sum(1 for v in traversal.start_from(0))
    82
    >>> traversal = nog.TraversalDepthFirst(next_edges=next_edges)
    >>> sum(1 for v in traversal.start_from(0))
    82
    >>> traversal = nog.TraversalNeighborsThenDepth(next_edges=next_edges)
    >>> sum(1 for v in traversal.start_from(0))
    82
    >>> traversal = nog.TraversalShortestPaths(next_edges=next_edges)
    >>> sum(1 for v in traversal.start_from(0))
    82
    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges=next_edges)
    >>> sum(1 for v in traversal.start_from(0))
    82
    """


# --------- Tests for gear collections -----------


class GearCollectionFunctionalityMainlyOnlyForAppCode:
    """
    Test the functionality, that NoGraphs inlines, does not use itself,
    and that is mainly there for application code only.
    Exception: see documentation of VertexSequenceWrapperForSetAndMapping.

    >>> list_factory = lambda: list()
    >>> ws = nog.VertexSetWrappingSequenceNoBitPacking(
    ...     list_factory, 1024, [1, 3])
    >>> ws
    {1, 3}
    >>> len(ws.sequence())
    1026
    >>> "a" in ws  # Case "is not instance(key, int)"
    False
    >>> 1026 in ws  # Case "IndexError"
    False
    >>> 1 in ws  # Case "return True"
    True
    >>> 2 in ws  # Case "return False"
    False
    >>> len(ws)
    2
    >>> ws.add(2)
    >>> ws
    {1, 2, 3}
    >>> ws.discard(3)
    >>> ws
    {1, 2}
    >>> ws.discard(3)
    >>> ws.add(1026)  # Case "IndexError"
    >>> ws
    {1, 2, 1026}
    >>> len(ws.sequence())
    2051
    >>> ws.discard(2051)   # Case "IndexError"
    >>> ws | ({4})  # Calls _from_iterable(iterable) to create new set
    {1, 2, 4, 1026}

    >>> list_factory = lambda: list()
    >>> ws = nog.VertexSetWrappingSequenceBitPacking(
    ...     list_factory, 128, [1, 3])
    >>> ws
    {1, 3}
    >>> len(ws.sequence())
    129
    >>> "a" in ws  # Case "is not instance(key, int)"
    False
    >>> 129*8 in ws  # Case "IndexError"
    False
    >>> 1 in ws  # Case "return True"
    True
    >>> 2 in ws  # Case "return False"
    False
    >>> len(ws)
    2
    >>> ws.add(2)
    >>> ws
    {1, 2, 3}
    >>> ws.discard(3)
    >>> ws
    {1, 2}
    >>> ws.discard(3)
    >>> ws.add(129*8)  # Case "IndexError"
    >>> ws
    {1, 2, 1032}
    >>> len(ws.sequence())
    258
    >>> ws.discard(258*8)   # Case "IndexError"
    >>> ws | ({4})  # Calls _from_iterable(iterable) to create new set
    {1, 2, 4, 1032}

    >>> list_factory = lambda: list[float]()
    >>> ws = nog.VertexMappingWrappingSequence(
    ...     list_factory, float("infinity"), 1024, [(0, 0), (2, 2)])
    >>> ws.default()  # Gap marker / default value of the mapping emulation
    inf
    >>> ws.sequence()[:5]  # Given values are set, others are gap-marker / default
    [0, inf, 2, inf, inf]
    >>> len(ws.sequence())
    1025
    >>> ws
    {0: 0, 2: 2}
    >>> ws.update_default([(1, 1), (2, 2.5), (3, 3)])  # key 2 has value ->ignore change
    >>> ws
    {0: 0, 1: 1, 2: 2, 3: 3}
    >>> ws.update_default([(1025, 1025)])  # Gives IndexError -> extend_and_set
    >>> ws
    {0: 0, 1: 1, 2: 2, 3: 3, 1025: 1025}
    >>> ws[0]
    0
    >>> ws[4]  # Gives KeyError because gap marker
    Traceback (most recent call last):
    KeyError
    >>> ws[2048]  # Gives KeyError because outside
    Traceback (most recent call last):
    KeyError
    >>> "hallo" in ws  # str is outside key type int
    False
    >>> len(ws)
    5
    >>> del ws[1]
    >>> ws
    {0: 0, 2: 2, 3: 3, 1025: 1025}
    >>> len(ws.sequence())
    2050
    >>> ws[2050] = 2050
    >>> ws
    {0: 0, 2: 2, 3: 3, 1025: 1025, 2050: 2050}
    """


class GearCollectionTestRemainingCasesForUseByLibrary:
    """
    An example that uses VertexMappingWrappingSequenceWithNone
    (and calls methods of VertexMappingWrappingSequenceWithNone) with distances is
    already given in the docs.
    Missing, and given here, is an example that uses VertexSetWrappingSequence
    (calls methods of VertexSetByWrapper)
    and VertexMappingWrappingSequenceWithoutNone
    (calls methods of VertexMappingByWrapper with case without None).

    Fehlt: Aufruf von access_paths_to_vertex_mapping_expect_none, wobei unter dem
    Mapping keine VertexMappingByWrapperWithNone sondern eine VertexMappingByWrapper
    liegt. Ich dachte, predecessor von Paths nutzt ...expect_none, und wenn ein
    Array darunter liegt, wird von GearArrays... dann VertexMappingByWrapper und nicht
    VertexMappingByWrapperWithNone genutzt...

    >>> def next_vertices(i, _):
    ...     yield i+1
    >>> t = nog.TraversalDepthFirstFlex(
    ...     nog.vertex_as_id, nog.GearForIntVerticesAndIDsAndCFloats(), next_vertices
    ... )
    >>> t.paths.debug = True
    >>> v = t.start_from(0, build_paths=True, compute_depth = True).go_to(5)
    >>> t.paths[5]
    (0, 1, 2, 3, 4, 5)
    >>> t.depth
    5
    """


class GearCollectionTestsForDoNotCallCases:
    """
    A "real" set has no wrapper. So, the index_and_bit_method returned by
    nog.access_to_vertex_set is not intended to be called.
    >>> c = set()
    >>> res = nog.access_to_vertex_set(c)
    >>> is_wrapper, gettable_settable, wrapper, uses_bits, index_and_bit_method = res
    >>> index_and_bit_method(None, None)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen
    """


# --------- Tests for gears  -----------


class GearTestsTraversalsWithOrWithoutLabels:
    # noinspection PyShadowingNames
    """
    -- TraversalShortestPathsFlex with different gears --
    >>> def next_edges(i, _):
    ...     j = (i + i // 6) % 6
    ...     yield i + 1, j * 2 + 1, j * 2 + 1
    ...     if i % 2 == 0:
    ...         yield i + 6, 7 - j, 7 - j
    ...     elif i % 1200000 > 5:
    ...         yield i - 6, 1, 1
    >>> def gear_test(gear):
    ...    traversal = nog.TraversalShortestPathsFlex(nog.vertex_as_id,
    ...        gear, next_labeled_edges=next_edges)
    ...    vertex = traversal.start_from(0, build_paths=True).go_to(5)
    ...    path = traversal.paths[vertex]
    ...    print([traversal.distance, tuple(path[:2]), tuple(path[-2:])])
    ...    traversal = nog.TraversalBreadthFirstFlex(nog.vertex_as_id, gear,
    ...        next_labeled_edges=next_edges)
    ...    vertex = traversal.start_from(0, build_paths=True).go_to(5)
    ...    path = traversal.paths[vertex]
    ...    print([traversal.depth, tuple(path[:2]), tuple(path[-2:])])

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


    Three main gear types, one also without bit_packing, used for each of the
    traversals, graph is no tree. For traversals dealing with distances, we
    need to test this gear functionality additionally.

    >>> enough_for_index_error = (1+128)*8  # index error even for seq of bits
    >>> path_goal = 2 * enough_for_index_error
    >>> limit = 3 * enough_for_index_error
    >>> def next_edges(i, _):
    ...     if i < limit:
    ...         if i % 2 == 0:
    ...             yield i + 1, 1, 1
    ...             yield i + 3, 1, 3
    ...         else:
    ...             yield i + 3, 1, 1
    ...             yield i + 1, 1, 3

    >>> test_gears = [nog.GearForHashableVertexIDsAndIntsMaybeFloats(),
    ...               nog.GearForIntVertexIDsAndCFloats(),
    ...               nog.GearForIntVerticesAndIDsAndCFloats(),
    ...               nog.GearForIntVerticesAndIDsAndCFloats(no_bit_packing=True),
    ...              ]
    >>> def gear_test_traversals(traversal_class, *args, **nargs):
    ...     for gear in test_gears:
    ...         yield traversal_class(nog.vertex_as_id, gear,
    ...                               next_labeled_edges=next_edges, *args, **nargs)


    >>> for t in gear_test_traversals(nog.TraversalBreadthFirstFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    For DFS, we also test without paths, because this changes the process
    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex):
    ...    print_partial_results(t.start_from(0, build_paths=False))
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]
    [3, 4, 7, 8, 11] [9, 10, 5, 6, 1, 2]

    >>> for t in gear_test_traversals(nog.TraversalNeighborsThenDepthFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [1, 3, 6, 4, 5] [3093, 3095, 3098, 3096, 3097, 2]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    >>> for t in gear_test_traversals(nog.TraversalTopologicalSortFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))
    [3096, 3098, 3095, 3097, 3094] [5, 4, 3, 2, 1, 0]
    ((0, 3, 3), (3, 4, 3)) ((2060, 2063, 3), (2063, 2064, 3))

    >>> for t in gear_test_traversals(nog.TraversalShortestPathsFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
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
    ...     next_labeled_edges=next_edges)
    >>> print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalShortestPathsFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=next_edges)
    >>> print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than
    the infinity value 255 used by the chosen gear and its configuration


    >>> for t in gear_test_traversals(nog.TraversalMinimumSpanningTreeFlex):
    ...    print_partial_results(t.start_from(0, build_paths=True), paths_to=path_goal)
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    [1, 3, 4, 2, 6] [3092, 3094, 3096, 3095, 3097, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))



    >>> def heuristic(vertex):
    ...    return 0
    >>> for t in gear_test_traversals(nog.TraversalAStarFlex):
    ...    print_partial_results(t.start_from(heuristic, 0, build_paths=True),
    ...                           paths_to=path_goal)
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
    ...     next_labeled_edges=next_edges)
    >>> print_partial_results(t.start_from(heuristic, 0, build_paths=True),
    ...                       paths_to=path_goal)
    [3, 1, 2, 4, 6] [3092, 3094, 3096, 3097, 3095, 3098]
    ((0, 3, 3), (3, 6, 1)) ((2058, 2061, 3), (2061, 2064, 1))
    >>> t = nog.TraversalAStarFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=next_edges)
    >>> print_partial_results(t.start_from(heuristic, 0, build_paths=True),
    ...                       paths_to=path_goal
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than
    the infinity value 255 used by the chosen gear and its configuration

    >>> def heuristic2(vertex):
    ...     return 255 - vertex  # Create infinity overflow of guessed distance
    >>> def next_edges2(vertex, _):
    ...     return [(vertex + 1, 1)]
    >>> t = nog.TraversalAStarFlex(
    ...     nog.vertex_as_id,
    ...     nog.GearForIntVerticesAndIDsAndCInts(distance_type_code="B"),
    ...     next_labeled_edges=next_edges2)
    >>> print_partial_results(t.start_from(heuristic2, 0), paths_to=255
    ... )  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    OverflowError: Distance 255 is equal or larger than
    the infinity value 255 used by the chosen gear and its configuration


    Three main gear types, one also without bit_packing,
    used for each of the traversals, graph is tree
    (TraversalMinimumSpanningTreeFlex omitted, because it has no option is_tree):
    >>> enough_for_index_error = (1+128)*8  # index error even for seq of bits
    >>> path_goal = 2 * enough_for_index_error
    >>> limit = 3 * path_goal
    >>> def next_edges(i, _):
    ...     if i < limit:
    ...         yield 2*i + 0, 1, 1
    ...         yield 2*i + 1, 1, 3

    >>> for t in gear_test_traversals(nog.TraversalBreadthFirstFlex, is_tree=True):
    ...    print_partial_results(t.start_from(1, build_paths=True), paths_to=path_goal)
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 4, 5, 6] [12378, 12379, 12380, 12381, 12382, 12383]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex, is_tree=True):
    ...    print_partial_results(t.start_from(1, build_paths=True), paths_to=path_goal)
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    For DFS, we also test without paths, because this changes the process
    >>> for t in gear_test_traversals(nog.TraversalDepthFirstFlex, is_tree=True):
    ...    print_partial_results(t.start_from(1, build_paths=False))
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]
    [3, 7, 15, 31, 63] [4097, 8195, 8194, 4096, 8193, 8192]

    >>> for t in gear_test_traversals(nog.TraversalNeighborsThenDepthFlex,
    ...     is_tree=True
    ... ):
    ...     print_partial_results(t.start_from(1, build_paths=True), paths_to=path_goal)
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [2, 3, 6, 7, 14] [4096, 4097, 8194, 8195, 8192, 8193]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalTopologicalSortFlex, is_tree=True):
    ...    print_partial_results(t.start_from(1, build_paths=True), paths_to=path_goal)
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [8191, 8190, 4095, 8189, 8188] [32, 16, 8, 4, 2, 1]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    >>> for t in gear_test_traversals(nog.TraversalShortestPathsFlex, is_tree=True):
    ...    print_partial_results(t.start_from(1, build_paths=True), paths_to=path_goal)
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))
    [3, 2, 5, 4, 7] [10927, 10926, 10921, 10920, 10923, 10922]
    ((1, 2, 1), (2, 4, 1)) ((516, 1032, 1), (1032, 2064, 1))

    Here is no call to TraversalMinimumSpanningTreeFlex, because this
    traversal does not support option is_tree.

    >>> def heuristic(vertex):
    ...    return 0
    >>> for t in gear_test_traversals(nog.TraversalAStarFlex,
    ...                               is_tree=True):
    ...    print_partial_results(t.start_from(heuristic, 1, build_paths=True),
    ...                          paths_to=path_goal)
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


# --------- Tests for the edge gadgets -----------


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
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=False,attributes=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from("A", build_paths=True).go_to("G")
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: G distance: 8 path edge count: 4 path: ('A', 'C', 'D', 'F', 'G')
    >>>
    >>> # The generated next_vertices function returns the empty list if no edges where
    >>> # given for it in the dict.
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
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=False,attributes=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from(0, build_paths=True).go_to(6)
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: 6 distance: 8 path edge count: 4 path: (0, 2, 3, 5, 6)
    >>>
    >>> # The generated next_vertices function returns the empty list if the index is
    >>> # out of range
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
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=True,attributes=True)
    >>> print({v: next_vertices(v, None) for v in "ABCDEF"}
    ... )  # doctest: +NORMALIZE_WHITESPACE
    {'A': [('B', 1), ('C', 2)], 'B': [('A', 1), ('E', 1), ('D', 4), ('F', 1)],
     'C': [('A', 2), ('D', 1)], 'D': [('B', 4), ('C', 1), ('E', 1)],
     'E': [('B', 1), ('D', 1), ('F', 2)], 'F': [('B', 1), ('E', 2), ('G', 2)]}

    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from("A")
    ... ]  # doctest: +NORMALIZE_WHITESPACE
    [('A', 'B', 1), ('B', 'E', 1), ('B', 'F', 1), ('E', 'D', 1), ('D', 'C', 1),
    ('F', 'G', 2)]
    >>> # Note, that the minimum spanning tree contains edge ('D', 'C') in the direction
    >>> # not directly listed in the input.

    >>> # Access same testing graph, but the weighted undirected edges are given as
    >>> # list, vertices are int
    >>> edges = [
    ...     ((1, 1), (2, 2)),
    ...     ((4, 1), (3, 4), (5, 1)),
    ...     ((3, 1),),
    ...     ((4, 1),),
    ...     ((5, 2),),
    ...     ((6, 2),)
    ... ]
    >>> next_vertices = nog.adapt_edge_index(edges,add_inverted=True,attributes=True)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from(0)]
    [(0, 1, 1), (1, 4, 1), (1, 5, 1), (4, 3, 1), (3, 2, 1), (5, 6, 2)]
    >>> # Note, that the minimum spanning tree contains edge (3, 2) in the direction
    >>> # not directly listed in the input.
    >>> next_vertices = nog.adapt_edge_index(set(),add_inverted=True,attributes=False)
    Traceback (most recent call last):
    ValueError: graph must be Mapping or Sequence

    # ------------ adapt_edge_iterable -------------
    >>> # Access testing data, where weighted directed edges are given as flat unsorted
    >>> # edge list
    >>> edges = [
    ...     ('A', 'B', 1), ('A', 'C', 2),
    ...     ('B', 'C', 5), ('B', 'D', 5),
    ...     ('C', 'D', 2), ('C', 'E', 1), ('C', 'F', 5),
    ...     ('D', 'F', 2), ('D', 'G', 5),
    ...     ('E', 'F', 5), ('E', 'B', 1),
    ...     ('F', 'G', 2)
    ... ]
    >>> import nographs as nog
    >>> next_vertices = nog.adapt_edge_iterable(
    ...     edges, add_inverted=False, attributes=True)
    >>> traversal = nog.TraversalShortestPaths(next_vertices)
    >>> vertex = traversal.start_from("A", build_paths=True).go_to("G")
    >>> print("vertex:", vertex, "distance:", traversal.distance,
    ...       "path edge count:", traversal.depth, "path:", traversal.paths[vertex])
    vertex: G distance: 8 path edge count: 4 path: ('A', 'C', 'D', 'F', 'G')
    >>>
    >>> # Access testing data, where weighted undirected edges are given as flat edge
    >>> # list
    >>> edges = [
    ...     ('A', 'B', 1), ('A', 'C', 2),
    ...     ('B', 'E', 1), ('B', 'D', 4), ('B', 'F', 1),
    ...     ('C', 'D', 1),
    ...     ('D', 'E', 1),
    ...     ('E', 'F', 2),
    ...     ('F', 'G', 2)
    ... ]
    >>> next_vertices = nog.adapt_edge_iterable(edges,add_inverted=True,attributes=True)
    >>> traversal = nog.TraversalMinimumSpanningTree(next_vertices)
    >>> [traversal.edge for vertex in traversal.start_from("A")
    ... ]  # doctest: +NORMALIZE_WHITESPACE
    [('A', 'B', 1), ('B', 'E', 1), ('B', 'F', 1), ('E', 'D', 1), ('D', 'C', 1),
    ('F', 'G', 2)]
    >>> # Note, that the minimum spanning tree contains edge ('D', 'C') in the
    >>> # direction not directly listed in the input.

    """
    # inspection PyShadowingNames


# --------- Tests for the array gadgets --------


class ArrayTests:
    """
    Only test cases that are not covered by examples in the documentation

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

    Incompatible options of move
    >>> nog.Position.moves(diagonals = True, non_zero_counts=range(1, 2))
    Traceback (most recent call last):
    RuntimeError: Incompatible options
    >>> nog.Position.moves(zero_move = True, non_zero_counts=range(1, 2))
    Traceback (most recent call last):
    RuntimeError: Incompatible options

    Ascending order
    >>> moves = nog.Position.moves(3, True, True)
    >>> moves == sorted(moves)
    True
    """
