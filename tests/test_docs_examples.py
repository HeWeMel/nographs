from collections.abc import Iterable
from typing import Callable, Any

import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)
from nographs import T, T_vertex


# --- Utility functions ---
def edges(
    next_edges_or_vertices: Callable[[T_vertex, Any], T],
    vertices: Iterable[T_vertex],
) -> dict[T_vertex, T]:
    # Test functionality of a next_edges or next_vertices function by calling
    # it for all vertices and return the relationship between inputs and
    # outputs in a dict.
    return dict((vertex, next_edges_or_vertices(vertex, None)) for vertex in vertices)


class SomeExamplesFromDocs:
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
