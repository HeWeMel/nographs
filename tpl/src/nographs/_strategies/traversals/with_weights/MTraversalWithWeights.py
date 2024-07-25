from tpl.make_insert_look_defined import *

# """$$
import_from("$$/../../MStrategy.py")


class MStrategyWithWeights:
    """Methods to implement subclasses of _TraversalWithWeight."""

    @staticmethod
    def init_signature(traversal_type: str) -> None:
        insert(
            f"""\
            vertex_to_id: VertexToID[T_vertex, T_vertex_id],
            gear: Gear[T_vertex, T_vertex_id, T_weight, T_labels],
            next_edges: Optional[
                NextWeightedEdges[
                    T_vertex,
                    {traversal_type}[T_vertex, T_vertex_id, T_weight, T_labels],
                    T_weight,
                ]
            ] = None,
            *,
            next_labeled_edges: Optional[
                NextWeightedLabeledEdges[
                    T_vertex,
                    {traversal_type}[T_vertex, T_vertex_id, T_weight, T_labels],
                    T_weight,
                    T_labels,
                ]
            ] = None,
"""
        )

    @staticmethod
    def init_code(is_tree: str) -> None:
        insert(
            f"""\
            self._next_edges, labeled_edges = _create_unified_next_weighted(
                next_edges, next_labeled_edges
            )
            super().__init__(labeled_edges, {is_tree}, vertex_to_id, gear)
"""
        )

    @staticmethod
    def check_overflow(variable: str) -> None:
        insert(
            f"""\
                # (Distance values equal to or higher than the chosen infinity
                # value of the gear are invalid and cannot be handled further.)
                if infinity <= {variable}:
                    self._gear.raise_distance_infinity_overflow_error({variable})
"""
        )

    @staticmethod
    def standard_for_flex(
        class_name: str, add_parameters: str = "", add_code: str = ""
    ) -> None:
        insert(
            f'''\
            class {class_name} (
                Generic[T_vertex, T_weight, T_labels],
                {class_name}Flex[T_vertex, T_vertex, Union[T_weight, float], T_labels]
            ):
                """
                Eases the use of `{class_name}Flex` for typical cases.
                For documentation of functionality and parameters, see there.

                .. code-block:: python

                   {class_name}[T_vertex, T_weight, T_labels](*args, **keywords)

                is a short form for

                .. code-block:: python

                   {class_name}Flex[
                       T_vertex, T_vertex, Union[T_weight, float], T_labels],
                   ](nog.vertex_as_id, nog.GearDefault(), *args, **keywords)

                Implications:

                - `GearDefault` is used, see there how it and its superclass work
                - The used weights are defined by Union[T_weight, float], see `GearDefault`
                - T_vertex is bound to Hashable (T_vertex is used as `T_vertex_id`, see there)
                """

                def __init__(
                    self,
                    next_edges: Optional[
                        NextWeightedEdges[
                            T_vertex,
                            {class_name}Flex[
                                T_vertex, T_vertex, Union[T_weight, float], T_labels
                            ],
                            T_weight,
                        ]
                    ] = None,
                    *,
                    next_labeled_edges: Optional[
                        NextWeightedLabeledEdges[
                            T_vertex,
                            {class_name}Flex[
                                T_vertex, T_vertex, Union[T_weight, float], T_labels
                            ],
                            T_weight,
                            T_labels,
                        ]
                    ] = None,
'''
        )
        if add_parameters:
            insert(
                f"""\
                {add_parameters}"""
            )
        insert(
            f"""\
                ) -> None:
                    super().__init__(
                        vertex_as_id,
                        GearDefault(),
                        next_edges,
                        next_labeled_edges=next_labeled_edges,
"""
        )
        if add_code:
            insert(
                f"""\
                {add_code}"""
            )
        insert(
            f"""\
                    )
"""
        )


# $$"""
