""" Functionality that ease the use of gear collection VertexMapping
in traversals. """

from tpl.make_insert_look_defined import *

# """$$
import_from("tpl/base_lib.py")


class MVertexMappingExpectNone:
    """Methods to ease implementing performant access to VertexMappingExpectNone
    objects.
    """

    @staticmethod
    def access(name: str):
        insert(
            f"""\
            (
                _,
                {name}_sequence,
                {name}_wrapper,
            ) = access_to_vertex_mapping_expect_none({name})
"""
        )

    @staticmethod
    def store_vertex(predecessors: str, predecessor: str, vertex_id: str):
        insert(
            f"""\
            # Store the predecessor ({predecessor}) of {vertex_id}
            try:
                {predecessors}_sequence[{vertex_id}] = {predecessor}
            except IndexError:
                {predecessors}_wrapper.extend_and_set({vertex_id}, {predecessor})
"""
        )

    @staticmethod
    def store_vertex_if_empty(predecessors: str, predecessor: str, vertex_id: str):
        insert(
            f"""\
            # Store the predecessor ({predecessor}) of {vertex_id}, if there
            # is none so far. In this case, a MutableMapping raises a
            # KeyError, and a Sequence contains None or raises an
            # IndexError.
            try:
                if {predecessors}_sequence[{vertex_id}] is None:
                    {predecessors}_sequence[{vertex_id}] = {predecessor}
            except KeyError:
                {predecessors}_sequence[{vertex_id}] = {predecessor}
            except IndexError:
                {predecessors}_wrapper.extend_and_set({vertex_id}, {predecessor})
"""
        )

    @staticmethod
    def store_vertex_and_edge_data(
        predecessors: str,
        attributes: str,
        predecessor: str,
        vertex_id: str,
        edge_data_expr: str,
        from_edge: bool = False,
    ):
        insert(
            f"""\
            # Store the predecessor ({predecessor}) of the neighbor
            try:
                {predecessors}_sequence[{vertex_id}] = {predecessor}
            except IndexError:
                {predecessors}_wrapper.extend_and_set({vertex_id}, {predecessor})
            # Store the labels of the edge to the neighbor
            if labeled_edges:
"""
        )
        if from_edge:
            insert(
                f"""\
                # Proof for correctness of the type hole:
                # self._labeled_edges -> next_edges (a NextWeightedEdges)
                # is a NextWeightedLabeledEdges -> {edge_data_expr} is a T_labels
                data_of_edge: T_labels = (
                    {edge_data_expr}
                )  # type: ignore[assignment]
"""
            )
        else:
            insert(
                f"""\
                data_of_edge = {edge_data_expr}
"""
            )
        insert(
            f"""\
                try:
                    {attributes}_sequence[{vertex_id}] = data_of_edge
                except IndexError:
                    {attributes}_wrapper.extend_and_set({vertex_id}, data_of_edge)
"""
        )


# $$"""
