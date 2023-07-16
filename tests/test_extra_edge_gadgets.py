import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)


class EdgeGadgets:
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
