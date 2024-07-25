from __future__ import annotations

import itertools
from typing import Optional, Iterable, Generic

from nographs._types import (
    T_vertex,
    T_vertex_id,
    T_labels,
    VertexToID,
    vertex_as_id,
)
from nographs._gears import (
    GearWithoutDistances,
    GearDefault,
)
from nographs._path import (
    Path,
    PathOfLabeledEdges,
    PathOfUnlabeledEdges,
)
from nographs._gear_collections import access_to_vertex_set

from ..type_aliases import (
    Strategy,
    BNextVertices,
    BNextEdges,
    BNextLabeledEdges,
)
from ..utils import iter_start_vertices_and_ids

from ..traversals.without_weights.breadth_first import (
    TraversalBreadthFirstFlex,
)
from .base import (
    _create_unified_next_bidirectional,
    _search_needs_search_object,
)


class BSearchBreadthFirstFlex(Strategy[T_vertex, T_vertex_id, T_labels]):
    """
    Bases: `Strategy` [`T_vertex`, `T_vertex_id`, `T_labels`]

    :param vertex_to_id: See `VertexToID` function.

    :param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

    :param next_vertices: Tuple `BNextVertices` of two NextVertices function.
      If None, provide next_edges or next_labeled_edges.

    :param next_edges: Tuple `BNextEdges` of two NextEdges functions.
      See paragraph *input* below for details. Only allowed if next_vertices equals
      None. If both are None, provide next_labeled_edges.

    :param next_labeled_edges: Tuple `BNextLabeledEdges` of two NextEdges
      functions. See paragraph *input* below for details. The parameter is only
      allowed if next_vertices and next_edges equal None. If given, paths will record
      the given labels.

    **Algorithm:** Bidirectional version of the Breadth First Search algorithm,
    non-recursive, based on FIFO queues.

    **Properties:** In both directions, vertices are visited by increasing depth
    from a start (resp. a goal) vertex (minimal number of edges), till a shortest
    path (minimal number of edges) from a start to a goal vertex is found. Each
    vertex is visited only once.

    **Input:** Directed graph. Unlabeled or labeled edges. One or more start vertices,
    and one or more goal vertices. NextVertices (resp. NextEdges) functions both for
    the outgoing edges from a vertex and the incoming edges to a vertex have to be
    provided, and they need to describe the same graph. Optional calculation limit.

    Note: A shortest path from a vertex *v* to itself always exists, has an edge count
    of 0, and will be found by the class, whilst TraversalBreadthFirst does not report
    start vertices and thus,
    TraversalBreadthFirst(<something>).start_at(v).go_to(v) fails.
    """

    def __init__(
        self,
        vertex_to_id: VertexToID[T_vertex, T_vertex_id],
        gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
        next_vertices: Optional[
            BNextVertices[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            BNextEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels],
            ],
        ] = None,
        next_labeled_edges: Optional[
            BNextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels],
                T_labels,
            ],
        ] = None,
    ) -> None:
        self._vertex_to_id = vertex_to_id
        self._gear = gear

        (
            _,
            self._edges_with_data,
            self._labeled_edges,
        ) = _create_unified_next_bidirectional(
            next_vertices, next_edges, next_labeled_edges
        )

        self._traversal_bi = tuple(
            TraversalBreadthFirstFlex[T_vertex, T_vertex_id, T_labels](
                vertex_to_id,
                gear,
                next_vertices=None if next_vertices is None else next_vertices[i],
                next_edges=None if next_edges is None else next_edges[i],
                next_labeled_edges=(
                    None if next_labeled_edges is None else next_labeled_edges[i]
                ),
            )
            for i in range(2)
        )

    def start_from(
        self,
        start_and_goal_vertex: Optional[tuple[T_vertex, T_vertex]] = None,
        *,
        start_and_goal_vertices: Optional[
            tuple[Iterable[T_vertex], Iterable[T_vertex]]
        ] = None,
        build_path: bool = False,
        calculation_limit: Optional[int] = None,
        fail_silently: bool = False,
    ) -> tuple[int, Path[T_vertex, T_vertex_id, T_labels]]:
        """
        Start the search both from a start vertex and a goal vertex, resp. both
        from a set of start vertices and a set of goal vertices. Return the
        length of a shortest (sum of edge weights) path between the/a start vertex
        and the/a goal vertex. If building a path was requested, also return the path,
        and otherwise, return a dummy path object.

        If the search ends without having found a path, raise KeyError,
        or, if a silent fail is demanded, return -1 and a dummy path object.
        Here, infinity means the value for infinite distance that is defined by the
        used `Gear` (as provided by a call of gear.infinity()).

        NoGraphs gives no guarantees about a dummy path. Do not use it for anything.

        :param start_and_goal_vertex: The start vertex and the goal vertex of the
            search. If None, provide start_and_goal_vertices.

        :param start_and_goal_vertices: The start vertices and the
            goal vertices of the search. Only allowed if start_and_goal_vertex
            equals None.

        :param build_path: If true, build and return a path of the minimum possible
            length.

        :param calculation_limit: If provided, maximal number of vertices to process
            (read in) from your graph in each of the searches in one of the two
            directions. If it is exceeded, a RuntimeError will be raised.

        :param fail_silently: If no path can be found, fail silently (see above)
            instead of raising an exception.
        """
        # steps that other strategies do in start_from

        _search_needs_search_object(self, BSearchBreadthFirstFlex)

        start_vertices: Iterable[T_vertex]
        goal_vertices: Iterable[T_vertex]
        if start_and_goal_vertex is not None:
            if start_and_goal_vertices is not None:
                raise RuntimeError(
                    "Both start_and_goal_vertex and "
                    + "start_and_goal_vertices provided."
                )
            start_vertex, goal_vertex = start_and_goal_vertex
            start_vertices, goal_vertices = (start_vertex,), (goal_vertex,)
        else:
            if start_and_goal_vertices is None:
                raise RuntimeError(
                    "Neither start_and_goal_vertex nor "
                    + "start_and_goal_vertices provided."
                )
            start_vertices, goal_vertices = start_and_goal_vertices

        for t, vertices in zip(self._traversal_bi, (start_vertices, goal_vertices)):
            t.start_from(
                start_vertices=vertices,
                build_paths=build_path,
                calculation_limit=calculation_limit,
                _report_depth_increase=True,
            )

        visited_bi = tuple(t.visited for t in self._traversal_bi)

        # Copy Traversal attributes into method scope (faster access)
        # labeled_edges = self._labeled_edges
        maybe_vertex_to_id = (
            None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
        )  # Case vertex_as_id: not apply; T_vertex_id > T_vertex

        # Get references of used gear objects and methods (avoid attribute resolution)
        (
            visited_forwards_uses_sequence,
            visited_forwards_sequence,
            visited_forwards_wrapper,
            visited_forwards_uses_bits,
            visited_forwards_index_and_bit_method,
        ) = access_to_vertex_set(visited_bi[0])
        (
            visited_backwards_uses_sequence,
            visited_backwards_sequence,
            visited_backwards_wrapper,
            visited_backwards_uses_bits,
            visited_backwards_index_and_bit_method,
        ) = access_to_vertex_set(visited_bi[1])

        # ----- Initialize method specific bookkeeping -----

        # Get the right class for storing a path (labeled or not)
        path_cls: type[Path]
        if self._labeled_edges:
            path_cls = PathOfLabeledEdges[T_vertex, T_vertex_id, T_labels]
        else:
            path_cls = PathOfUnlabeledEdges[T_vertex, T_vertex_id, T_labels]

        # Detect if a start vertex is also goal vertex, and report result manually.
        # (Without this manual handling, a non-self loop from such a start vertex back
        #  to itself with a length > 0 would be reported as smallest distance. This
        #  would be unexpected for users, since they expect that the distance from a
        #  vertex to itself is always 0.)
        common_vertex_ids = set(
            v_id
            for v, v_id in iter_start_vertices_and_ids(
                start_vertices, self._vertex_to_id
            )
        ).intersection(
            v_id
            for v, v_id in iter_start_vertices_and_ids(
                goal_vertices, self._vertex_to_id
            )
        )
        if common_vertex_ids:
            for c_vertex, cv_id in iter_start_vertices_and_ids(
                start_vertices, self._vertex_to_id
            ):
                if cv_id in common_vertex_ids:
                    p = path_cls.from_vertex(c_vertex)
                    return 0, p

        # ----- Inner loop -----

        for (
            traversal_iter,
            visited_other,
            visited_other_uses_sequence,
            visited_other_sequence,
            visited_other_uses_bits,
            visited_other_index_and_bit_method,
        ) in itertools.cycle(
            (
                (
                    iter(self._traversal_bi[0]),
                    visited_bi[1],
                    visited_backwards_uses_sequence,
                    visited_backwards_sequence,
                    visited_backwards_uses_bits,
                    visited_backwards_index_and_bit_method,
                ),
                (
                    iter(self._traversal_bi[1]),
                    visited_bi[0],
                    visited_forwards_uses_sequence,
                    visited_forwards_sequence,
                    visited_forwards_uses_bits,
                    visited_forwards_index_and_bit_method,
                ),
            )
        ):
            prev_vertex: Optional[T_vertex] = None
            for vertex in traversal_iter:
                # If we get the same vertex twice, directly after each other,
                # this signals, that the depth will increase with the next reported
                # vertex. So we leave the loop here.
                if prev_vertex == vertex:
                    break
                prev_vertex = vertex

                # If vertex is not in visited vertices of other traversal: continue
                v_id: T_vertex_id = (
                    maybe_vertex_to_id(vertex)  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else vertex
                )

                if not visited_other_uses_sequence:
                    # Standard implementation for "normal" MutableMapping
                    if v_id not in visited_other:
                        continue
                elif visited_other_uses_bits:
                    # Same as above, but with bits in byte sequence
                    sequence_key, bit_number = visited_other_index_and_bit_method(
                        v_id, 8
                    )
                    bit_mask = 1 << bit_number
                    try:
                        value = visited_other_sequence[sequence_key]
                        if not (value & bit_mask):
                            continue
                    except IndexError:
                        continue
                else:
                    # Same as above, but with booleans in byte sequence
                    try:
                        if not visited_other_sequence[v_id]:
                            continue
                    except IndexError:
                        continue

                # We found a vertex from both directions
                path = (
                    path_cls.from_bidirectional_search(
                        self._traversal_bi[0].paths, self._traversal_bi[1].paths, vertex
                    )
                    if build_path
                    else path_cls.of_nothing()
                )
                return sum(t.depth for t in self._traversal_bi), path
            else:
                # No new vertices reported by traversal in this direction and depth:
                # Whole search is over.
                break

        if fail_silently:
            return -1, path_cls.of_nothing()
        else:
            raise KeyError("No path to (a) goal vertex found")


class BSearchBreadthFirst(
    Generic[T_vertex, T_labels], BSearchBreadthFirstFlex[T_vertex, T_vertex, T_labels]
):
    """
    Eases the use of `BSearchBreadthFirstFlex` for typical cases.
    For documentation of functionality and parameters, see there.

    .. code-block:: python

       BSearchBreadthFirst[T_vertex, T_labels](*args, **keywords)

    is a short form for

    .. code-block:: python

       BSearchBreadthFirstFlex[
           T_vertex, T_vertex, T_labels],
      ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

    Implication:

    - `GearDefault` is used, see there how it and its superclass work
    - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
    """

    def __init__(
        self,
        next_vertices: Optional[
            BNextVertices[
                T_vertex, TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels]
            ]
        ] = None,
        *,
        next_edges: Optional[
            BNextEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels],
            ],
        ] = None,
        next_labeled_edges: Optional[
            BNextLabeledEdges[
                T_vertex,
                TraversalBreadthFirstFlex[T_vertex, T_vertex, T_labels],
                T_labels,
            ],
        ] = None,
    ) -> None:
        super().__init__(
            vertex_as_id,
            GearDefault(),
            next_vertices,
            next_edges=next_edges,
            next_labeled_edges=next_labeled_edges,
        )
