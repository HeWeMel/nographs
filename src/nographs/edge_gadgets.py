from __future__ import annotations

import collections
import itertools
from collections.abc import Sequence, Mapping, Callable, Iterable
from typing import Union, Any


# ---------- functions for handling test data given as some kind of edges -------------


def adapt_edge_index(
    index: Union[Mapping, Sequence], *, add_inverted: bool, labeled: bool
) -> Callable:
    """
    Reads a test graph from a Mapping (e.g. a Dict) or from a Sequence (e.g. a tuple
    or list, if you use integers as your vertices) and provide a neighbor function
    from that data. Typically only used for test purposes.

    :param index: Mapping or Sequence with vertices as key resp. index. For each
        vertex, you provide an Iterable of adjacent vertices (this defines unlabeled
        edges) or an Iterable of the labeled edges that start at this vertex. A labeled
        edge to some neighbor need to be a Sequence of the form (neighbor, additional
        data...).

    :param add_inverted: The resulting neighbor function will yield the edges of m.
        Additionally, if add_inverted_edges is True, it will provide the same edges
        inverted (start end end vertex exchanged).

    :param labeled: Give True, if *index* provides labeled edges. In this case, you can
        use the resulting neighbor function as next_edges function. Give False, if m
        provides neighbor vertices for a given vertex. In this case, you can use the
        resulting neighbor function as next_vertices function.

    :return: Neighbor function that can be used as parameter for one of the traversal
        algorithms.
    """

    if add_inverted:
        if isinstance(index, Mapping):
            return adapt_edge_iterable(
                (
                    (v1,) + e_to if labeled else (v1, e_to)
                    for v1, edges_to in index.items()
                    for e_to in edges_to
                ),
                add_inverted=add_inverted,
                labeled=labeled,
            )
        if isinstance(index, Sequence):
            return adapt_edge_iterable(
                (
                    (v1,) + e_to if labeled else (v1, e_to)
                    for edges_to, v1 in zip(index, itertools.count())
                    for e_to in edges_to
                ),
                add_inverted=add_inverted,
                labeled=labeled,
            )
        raise ValueError("graph must be Mapping or Sequence")

    def get(vertex, _):
        try:
            return index[vertex]
        except KeyError:
            return ()
        except IndexError:
            return ()

    return get


def adapt_edge_iterable(
    edges: Iterable[Sequence], *, add_inverted: bool, labeled: bool
) -> Callable:
    """
    Reads a graph from an Iterable of edges and provide a neighbor function from that
    data. Typically used only for test purposes.

    :param edges: The edges of your graph, each as Sequence (start_vertex, end_vertex,
        optional_more_data...)

    :param add_inverted: The resulting neighbor function will yield your edges.
        Additionally, if add_inverted_edges is True, it will provide the same edges
        inverted (start and end vertices exchanged). Note: when this option is used, a
        copy of your graph will be held by the returned neighbor function.

    :param labeled: If set to True, the resulting neighbor function will yield labeled
        edges ( to_vertex, additional data ...) for a given vertex and can be used as
        next_edges function. If set to False, it will yield neighbor vertices, can be
        used as next_vertices function, and additional data that your edges may contain
        will be ignored.

    :return: Neighbor function that can be used as parameter for one of the traversal
        algorithms.
    """
    edge_dict: dict[Any, list[Any]] = collections.defaultdict(list)
    if add_inverted:
        if labeled:
            # Labeled edges are provided and all data should be used
            for from_vertex, to_vertex, *data in edges:
                edge_dict[from_vertex].append((to_vertex, *data))
                edge_dict[to_vertex].append((from_vertex, *data))
        else:
            # Only start and end vertices of the edge should be used. Optional
            # additional data is ignored.
            for from_vertex, to_vertex, *data in edges:
                edge_dict[from_vertex].append(to_vertex)
                edge_dict[to_vertex].append(from_vertex)
    else:
        for edge in edges:
            if labeled:
                from_vertex, rest = edge[0], edge[1:]
                edge_dict[from_vertex].append(rest)
            else:
                from_vertex, to_vertex = edge[0], edge[1]
                edge_dict[from_vertex].append(to_vertex)
    return adapt_edge_index(edge_dict, add_inverted=False, labeled=labeled)
