""" Macros that ease implementing strategies """

from tpl.make_insert_look_defined import *

# """$$

import_from("tpl/base_lib.py")
import_from("$$/MCalculationLimit.py")
import_from("$$/MVertexSet.py")
import_from("$$/MVertexMapping.py")
import_from("$$/MVertexMappingExpectNone.py")


class MStrategy:
    """Methods that ease implementing subclasses of Strategy."""

    @staticmethod
    def vertex_to_id(vertex_name: str, vertex_id_name: str) -> None:
        insert(
            f"""\
                {vertex_id_name}: T_vertex_id = (
                    maybe_vertex_to_id(
                        {vertex_name}
                    )  # type: ignore[assignment]
                    if maybe_vertex_to_id
                    else {vertex_name}
                )
"""
        )


# $$"""
