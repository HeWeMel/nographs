from tpl.make_insert_look_defined import *

# """$$
import_from("$$/../../MStrategy.py")


class MStrategy:
    """Methods to implement subclasses of Traversal."""

    @staticmethod
    def vertex_to_id(vertex_name: str, vertex_id_name: str) -> None:
        insert(
            f"""\
                {vertex_id_name}: T_vertex_id = (
                    maybe_vertex_to_id({vertex_name})  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else {vertex_name}
                )
"""
        )


class MStrategyWithoutWeights:
    """Methods to implement subclasses of _TraversalWithoutWeight."""

    @staticmethod
    def init_signature(traversal_type: str) -> None:
        insert(
            f"""\
            vertex_to_id: VertexToID[T_vertex, T_vertex_id],
            gear: GearWithoutDistances[T_vertex, T_vertex_id, T_labels],
            next_vertices: Optional[
                NextVertices[
                    T_vertex, {traversal_type}[T_vertex, T_vertex_id, T_labels]
                ]
            ] = None,
            *,
            next_edges: Optional[
                NextEdges[
                    T_vertex, {traversal_type}[T_vertex, T_vertex_id, T_labels]
                ]
            ] = None,
            next_labeled_edges: Optional[
                NextLabeledEdges[
                    T_vertex,
                    {traversal_type}[T_vertex, T_vertex_id, T_labels],
                    T_labels,
                ]
            ] = None,
            is_tree: bool = False,
"""
        )

    @staticmethod
    def init_code(
        depth_computation_optional: bool = False,
        search_depth_is_vertex_depth: bool = False,
    ) -> None:
        insert(
            f'''\
            (
                self._next_edge_or_vertex,
                edges_with_data,
                labeled_edges,
            ) = _create_unified_next(next_vertices, next_edges, next_labeled_edges)
            super().__init__(edges_with_data, labeled_edges, is_tree, vertex_to_id, gear)
            self.depth: int = -1  # value not used, initialized during traversal
            """
'''
        )
        if depth_computation_optional:
            insert(
                """\
            If depth computation has been demanded (see option *compute_depth*):
"""
            )
        insert(
            f"""\
            At this *search depth*, the reported (resp. the expanded) vertex has been
            found. It equals the length (number of edges) of the created path to the
            vertex, if path creation is demanded.
"""
        )
        if search_depth_is_vertex_depth:
            insert(
                """\

            For the special case of this traversal, it equals the
            *depth of the vertex* (minimal number of edges needed to come to it
            from a start vertex).
"""
            )
        else:
            insert(
                """\
            Note: The search depth does not need to be the depth of the vertex
            (see `TraversalBreadthFirstFlex`).
"""
            )
        insert(
            f'''\
            When a traversal has been started, but no vertex has been reported or expanded
            so far, the depth is 0 (depth of the start vertices).
            """
'''
        )

    @staticmethod
    def standard_for_flex(class_name: str) -> None:
        insert(
            f'''\
            class {class_name} (
                Generic[T_vertex, T_labels], {class_name}Flex[T_vertex, T_vertex, T_labels]
            ):
                """
                Eases the use of `{class_name}Flex` for typical cases.
                For documentation of functionality and parameters, see there.

                Uses the following standard arguments for the respective parameters of
                the parent class:

                - vertex_to_id = `vertex_as_id`
                - gear = `GearDefault`
                - `T_vertex_id` = `T_vertex`

                Implications:

                - `GearDefault` is used, see there how it and its superclass work
                - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
                """

                def __init__(
                    self,
                    next_vertices: Optional[
                        NextVertices[
                            T_vertex, {class_name}Flex[T_vertex, T_vertex, T_labels]
                        ]
                    ] = None,
                    *,
                    next_edges: Optional[
                        NextEdges[T_vertex, {class_name}Flex[T_vertex, T_vertex, T_labels]]
                    ] = None,
                    next_labeled_edges: Optional[
                        NextLabeledEdges[
                            T_vertex,
                            {class_name}Flex[T_vertex, T_vertex, T_labels],
                            T_labels,
                        ]
                    ] = None,
                    is_tree: bool = False,
                ) -> None:
                    super().__init__(
                        vertex_as_id,
                        GearDefault(),
                        next_vertices,
                        next_edges=next_edges,
                        next_labeled_edges=next_labeled_edges,
                        is_tree=is_tree,
                    )
'''
        )


# $$"""
