from __future__ import annotations

import collections
import itertools
from collections.abc import Sequence, Mapping, Callable, Iterable
from typing import Union, Any, Literal, overload

from ._types import (
    T_vertex,
    T_weight,
    T_labels,
    OutEdge,
    WeightedOrLabeledFullEdge,
    AnyFullEdge,
)


# ---------- functions for handling test data given as some kind of edges -------------


@overload
def adapt_edge_index(
    index: Mapping[T_vertex, Iterable[T_vertex]],
    *,
    add_inverted: bool,
    attributes: Literal[False],
) -> Callable[[T_vertex, Any], Iterable[T_vertex]]: ...


@overload
def adapt_edge_index(
    index: Mapping[T_vertex, Iterable[OutEdge[T_vertex, T_weight, T_labels]]],
    *,
    add_inverted: bool,
    attributes: Literal[True],
) -> Callable[[T_vertex, Any], Iterable[OutEdge[T_vertex, T_weight, T_labels]]]: ...


@overload
def adapt_edge_index(
    index: Sequence[Iterable[T_vertex]],
    *,
    add_inverted: bool,
    attributes: Literal[False],
) -> Callable[[int, Any], Iterable[T_vertex]]: ...


@overload
def adapt_edge_index(
    index: Sequence[Iterable[OutEdge[int, T_weight, T_labels]]],
    *,
    add_inverted: bool,
    attributes: Literal[True],
) -> Callable[[int, Any], Iterable[OutEdge[int, T_weight, T_labels]]]: ...


def adapt_edge_index(
    index: Union[Mapping, Sequence], *, add_inverted: bool, attributes: bool
) -> Callable:
    """
    Read a graph from a Mapping (e.g. a Dict) or from a Sequence (e.g. a tuple
    or list, if integers are used as the vertices) and provide a neighbor function
    (`NextVertices` or `NextEdges`) from that data. Typically only used for test
    purposes.

    :param index: Mapping or Sequence with vertices as key, resp. as index. For each
        vertex, you provide:

        - either an Iterable of adjacent vertices (this defines edges
          without edge attributes)

        - or an Iterable of edges (with edge attributes) that start at this vertex.
          An edge to some neighbor (see `outgoing edge <outgoing_edges>`) needs
          to be a Sequence of the form
          (neighbor, labels) or (neighbor, weight) or (neighbor, weight, labels).

    :param attributes: Give True, if *index* provides labeled or weighted edges.
        In this case, you can use the resulting neighbor function as `NextEdges`
        function.

        Give False, if index provides neighbor vertices for a given vertex.
        In this case, you can use the resulting neighbor function as
        `NextVertices` function.

    :param add_inverted: If False, the resulting neighbor function will yield only the
        edges of *index*. If True, the function will also provide the
        same edges inverted (start and end vertex exchanged).

        Note: when this option is used, a
        copy of your graph will be held by the returned neighbor function.

    :return: Neighbor function that can be used as parameter for one of the traversal
        algorithms.
    """

    if add_inverted:
        if isinstance(index, Mapping):
            if attributes:
                return adapt_edge_iterable(
                    (
                        (v1,) + e_to
                        for v1, edges_to in index.items()
                        for e_to in edges_to
                    ),
                    add_inverted=add_inverted,
                    attributes=True,
                )
            else:
                return adapt_edge_iterable(
                    ((v1, e_to) for v1, edges_to in index.items() for e_to in edges_to),
                    add_inverted=add_inverted,
                    attributes=False,
                )
        if isinstance(index, Sequence):
            if attributes:
                return adapt_edge_iterable(
                    (
                        (v1,) + e_to
                        for edges_to, v1 in zip(index, itertools.count())
                        for e_to in edges_to
                    ),
                    add_inverted=add_inverted,
                    attributes=True,
                )
            else:
                return adapt_edge_iterable(
                    (
                        (v1, e_to)
                        for edges_to, v1 in zip(index, itertools.count())
                        for e_to in edges_to
                    ),
                    add_inverted=add_inverted,
                    attributes=False,
                )
        raise ValueError("graph must be Mapping or Sequence")

    def get(vertex: Any, _: Any) -> Union[Any, Sequence[Any]]:
        try:
            return index[vertex]
        except KeyError:
            return ()
        except IndexError:
            return ()

    return get


@overload
def adapt_edge_iterable(
    edges: Iterable[AnyFullEdge[T_vertex, T_weight, T_labels]],
    *,
    add_inverted: bool,
    attributes: Literal[False],
) -> Callable[[T_vertex, Any], Iterable[T_vertex]]: ...


@overload
def adapt_edge_iterable(
    edges: Iterable[WeightedOrLabeledFullEdge[T_vertex, T_weight, T_labels]],
    *,
    add_inverted: bool,
    attributes: Literal[True],
) -> Callable[[T_vertex, Any], Iterable[OutEdge[T_vertex, T_weight, T_labels]]]: ...


def adapt_edge_iterable(
    edges: Iterable[Sequence], *, add_inverted: bool, attributes: bool
) -> Callable:
    """
    Read a graph from an Iterable of edges and provide a neighbor function
    (`NextVertices` or `NextEdges`) from that data. Typically only used for test
    purposes.

    :param edges: The edges of your graph, each as Sequence (start_vertex, end_vertex,
        optional_attributes...), where edge data can be either a weight, or labels,
        or both (see `WeightedOrLabeledFullEdge`) or none
        (see `AnyFullEdge`).

    :param attributes: If set to True, the resulting neighbor function will yield
        edges with edge attributes for a given vertex and
        can be used as `NextEdges` function, but the edges of the given graph
        need to have attributes (`WeightedOrLabeledFullEdge`, not
        `AnyFullEdge`).

        If set to False, it will yield neighbor vertices, and can be
        used as `NextVertices` function, and edge data that your edges
        may contain will be ignored.

    :param add_inverted: If False, the resulting neighbor function will only yield
        for *edges*. If True, the function will also provide the
        same edges inverted (start and end vertex exchanged).
        Note: when this option is used, a
        copy of your graph will be held by the returned neighbor function.

    :return: Neighbor function that can be used as parameter for one of the traversal
        algorithms. See `OutEdge <outgoing_edges>` for the case of attributes.
    """
    edge_dict: dict[Any, list[Any]] = collections.defaultdict(list)
    if add_inverted:
        if attributes:
            # Labeled edges are provided and all data should be used
            for from_vertex, to_vertex, *data in edges:
                edge_dict[from_vertex].append((to_vertex, *data))
                edge_dict[to_vertex].append((from_vertex, *data))
            return adapt_edge_index(edge_dict, add_inverted=False, attributes=True)
        else:
            # Only start and end vertices of the edge should be used. Optional
            # additional data is ignored.
            for from_vertex, to_vertex, *_data in edges:
                edge_dict[from_vertex].append(to_vertex)
                edge_dict[to_vertex].append(from_vertex)
            return adapt_edge_index(edge_dict, add_inverted=False, attributes=False)
    else:
        if attributes:
            for edge in edges:
                from_vertex, rest = edge[0], edge[1:]
                edge_dict[from_vertex].append(rest)
            return adapt_edge_index(edge_dict, add_inverted=False, attributes=True)
        else:
            for edge in edges:
                from_vertex, to_vertex = edge[0], edge[1]
                edge_dict[from_vertex].append(to_vertex)
            return adapt_edge_index(edge_dict, add_inverted=False, attributes=False)
