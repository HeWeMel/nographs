""" Functionality that ease the use of gear collection VertexSet
in traversals. """

from tpl.make_insert_look_defined import *

# """$$
import re
from collections.abc import Generator

import_from("tpl/base_lib.py")


class MVertexSet:
    """Methods to ease implementing performant access to VertexSet objects."""

    @staticmethod
    def access(name: str, ops: list[str] = ("add",)):
        for op in ops:
            insert(
                f"""\
                {name}_{op} = {name}.{op}
"""
            )
        insert(
            f"""\
                (
                    {name}_uses_sequence,
                    {name}_sequence,
                    {name}_wrapper,
                    {name}_uses_bits,
                    {name}_index_and_bit_method,
                ) = access_to_vertex_set({name})
"""
        )

    @staticmethod
    def combine_access(collection1: str, collection2: str, combined: str):
        insert(
            f"""\
            # Check compatibility of visited and trace_set. It is used for
            # performance optimization later on.
            assert (
                {collection1}_uses_sequence == {collection2}_uses_sequence
                and {collection1}_uses_bits == {collection2}_uses_bits
            ), (
                "Collection {collection1} is incompatible "
                + "with collection {collection2}"
            )
            {combined}_uses_sequence = {collection1}_uses_sequence
            del {collection1}_uses_sequence, {collection2}_uses_sequence
            {combined}_uses_bits = {collection1}_uses_bits
            del {collection1}_uses_bits, {collection2}_uses_bits
            if {combined}_uses_sequence and {combined}_uses_bits:
                assert {collection1}_index_and_bit_method is {collection2}_index_and_bit_method, (
                    "Collection {collection1} is incompatible "
                    + "with collection {collection2}"
                )
            {combined}_index_and_bit_method = {collection1}_index_and_bit_method
            del {collection1}_index_and_bit_method, {collection2}_index_and_bit_method
"""
        )

    @staticmethod
    def if_visited_continue_else_add(visited: str, vertex_id: str, condition: str):
        condition_and = f"{condition} and " if condition else ""
        else_or_elif_condition = f"elif {condition}" if condition else "else"
        insert(
            f"""\
            # (If-nesting optimized for first case)
            if {condition_and}not {visited}_uses_sequence:
                # Standard implementation for "normal" MutableMapping
                if {vertex_id} in {visited}:
                    continue
                {visited}_add({vertex_id})
            elif {condition_and}{visited}_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = {visited}_index_and_bit_method(
                    {vertex_id}, 8)
                bit_mask = 1 << bit_number
                try:
                    value = {visited}_sequence[sequence_key]
                    if value & bit_mask:
                        continue
                    {visited}_sequence[sequence_key] = value | bit_mask
                except IndexError:
                    {visited}_wrapper.extend_and_set(
                        sequence_key, bit_mask
                    )
            {else_or_elif_condition}:
                # Same as above, but with booleans in byte sequence
                try:
                    if {visited}_sequence[{vertex_id}]:
                        continue
                    {visited}_sequence[{vertex_id}] = True
                except IndexError:
                    {visited}_wrapper.extend_and_set({vertex_id}, True)
"""
        )  # noqa: E272

    @staticmethod
    def if_visited_continue(visited: str, vertex_id: str, condition: str):
        condition_and = f"{condition} and " if condition else ""
        else_or_elif_condition = f"elif {condition}" if condition else "else"
        insert(
            f"""\
            if {condition_and}not {visited}_uses_sequence:
                # Standard implementation for "normal" MutableMapping:
                if {vertex_id} in {visited}:
                    continue
            elif {condition_and}{visited}_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = {visited}_index_and_bit_method(
                    {vertex_id}, 8)
                try:
                    if {visited}_sequence[sequence_key] & (1 << bit_number):
                        continue
                except IndexError:
                    pass
            {else_or_elif_condition}:
                # Same as above, but with booleans in byte sequence
                try:
                    if {visited}_sequence[{vertex_id}]:
                        continue
                except IndexError:
                    pass
"""
        )

    @staticmethod
    def add(collection: str, vertex_id: str, index: str = ""):
        """Add vertex_id to collection. If a combined index is given,
        use this."""
        if not index:
            index = collection
        insert(
            f"""\
            # (If-nesting optimized for first case)
            if not {index}_uses_sequence:
                # Standard implementation for "normal" MutableMapping
                {collection}add({vertex_id})
            elif {index}_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = {index}_index_and_bit_method(
                    {vertex_id}, 8)
                try:
                    {collection}_sequence[sequence_key] |= 1 << bit_number
                except IndexError:
                    {collection}_wrapper.extend_and_set(
                        sequence_key, 1 << bit_number
                    )
            else:
                # Same as above, but with booleans in byte sequence
                try:
                    {collection}_sequence[{vertex_id}] = True
                except IndexError:
                    {collection}_wrapper.extend_and_set({vertex_id}, True)
"""
        )  # noqa: E272

    @staticmethod
    def discard(collection: str, vertex_id: str, index: str = ""):
        """Discard vertex_id from collection. If a combined index is given,
        use this."""
        if not index:
            index = collection
        insert(
            f"""\
            # (If-nesting optimized for first case)
            if not {index}_uses_sequence:
                # Standard implementation for "normal" MutableMapping
                {collection}_discard({vertex_id})
            elif {index}_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = {index}_index_and_bit_method(
                    {vertex_id}, 8)
                try:
                    {collection}_sequence[sequence_key] &= ~(1 << bit_number)
                except IndexError:
                    {collection}_wrapper.extend_and_set(
                        sequence_key, 0
                    )
            else:
                # Same as above, but with booleans in byte sequence
                try:
                    {collection}_sequence[{vertex_id}] = False
                except IndexError:
                    {collection}_wrapper.extend_and_set({vertex_id}, False)
"""
        )  # noqa: E272

    @staticmethod
    def remove(collection: str, vertex_id: str, index: str = ""):
        """Remove vertex_id from collection. If a combined index is given,
        use this. The collection need to contain *vertex_id* before the
        operation, otherwise, the behaviour of the method is not specified!
        """
        if not index:
            index = collection
        insert(
            f"""\
            # (If-nesting optimized for first case)
            if not {index}_uses_sequence:
                # Standard implementation for "normal" MutableMapping
                {collection}_discard({vertex_id})
            elif {index}_uses_bits:
                # Same as above, but with bits in byte sequence
                sequence_key, bit_number = {index}_index_and_bit_method(
                    {vertex_id}, 8)
                {collection}_sequence[sequence_key] -= (1 << bit_number)
            else:
                # Same as above, but with booleans in byte sequence
                {collection}_sequence[{vertex_id}] = False
"""
        )  # noqa: E272

    @staticmethod
    def compile_access(
        vertex_id: str,
        condition: str,
        index: str,
        code: str,
        already_indexed: bool = False,
    ):
        """
        Replace set.add(), set.remove(), set.discard(), and set.contains() in *code*
        by the optimized access prepared by method *access* and, optionally,
        *combined_access*.
        If *combines_access* has been used, *index* is the combined access path,
        otherwise, give the name of the used *vertex_set*.
        """
        condition_and = f"{condition} and " if condition else ""
        else_or_elif_condition = f"elif {condition}" if condition else "else"

        def iterate_matches(lines: str) -> Generator[tuple[str, str, str]]:
            """
            Iterate *lines*, match them on the form
               <some spaces>$<set name>.<special method, optionally with double dots>
            and return tuples match, line, given_indent, set_name, operation.
            For lines that do not match, the last three result values are undefined.
            """
            for line in lines.splitlines():
                match = re.fullmatch(r"( *)\$(\w+).(\w+.?)", line)
                if match is None:
                    yield match, line, "", "", ""
                    continue
                given_indent, set_name, operation = match.groups()
                yield match, line, given_indent, set_name, operation

        insert_with_indent(
            "",
            f"""\
            if {condition_and}not {index}_uses_sequence:
                # Standard implementation for "normal" MutableSet
            """,
        )
        indent = "    "
        for match, line, given_indent, set_name, operation in iterate_matches(code):
            if match is None:
                insert(indent + line + "\n")
            elif operation == "add_vertex_id":
                insert(f"{indent}{given_indent}{set_name}_add({vertex_id})\n")
            elif operation == "discard_vertex_id":
                insert(f"{indent}{given_indent}{set_name}_remove({vertex_id})\n")
            elif (
                operation == "if_contains_vertex_id:"
                or operation == "if_contains_vertex_id_prepare_remove_and_elseadd:"
            ):
                insert(f"{indent}{given_indent}if {vertex_id} in {set_name}:\n")
            elif operation == "prepared_remove_vertex_id":
                insert(f"{indent}{given_indent}{set_name}_discard({vertex_id})\n")
            elif operation == "else_prepared_add_endif":
                insert(
                    f"{indent}{given_indent}else:"
                    f"{indent}{given_indent}    {set_name}_add({vertex_id})\n"
                )
            elif operation == "endif":
                pass
            elif operation == "endif_with_vertex_included_in_past":
                pass
            else:
                raise RuntimeError("Operation not supported:" + operation)

        insert_with_indent(
            "",
            f"""\

            elif {condition_and}not {index}_uses_bits:
                # Same as above, but with booleans in byte sequence
            """,
        )
        for match, line, given_indent, set_name, operation in iterate_matches(code):
            if match is None:
                insert(indent + line + "\n")
            elif operation == "add_vertex_id":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    try:
                        {set_name}_sequence[{vertex_id}] = True
                    except IndexError:
                        {set_name}_wrapper.extend_and_set({vertex_id}, True)
                    """,
                )
            elif operation == "discard_vertex_id":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                try:
                    {set_name}_sequence[{vertex_id}] = False
                except IndexError:
                    {set_name}_wrapper.extend_and_set({vertex_id}, False)
                """,
                )
            elif (
                operation == "if_contains_vertex_id:"
                or operation == "if_contains_vertex_id_prepare_remove_and_elseadd:"
            ):
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    try:
                        if {set_name}_sequence[{vertex_id}]:
                    """,
                )
                indent += "    "
            elif operation == "prepared_remove_vertex_id":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    {set_name}_sequence[{vertex_id}] = False
                    """,
                )
            elif operation == "else_prepared_add_endif":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                        else:
                            {set_name}_sequence[{vertex_id}] = True
                    except IndexError:
                        {set_name}_wrapper.extend_and_set({vertex_id}, True)
                    """,
                )
            elif operation == "endif":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    except IndexError:
                        pass
                    """,
                )
            elif operation == "endif_with_vertex_included_in_past":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    except IndexError:  # pragma: no cover
                        raise AssertionError(
                            "Internal error: IndexError "
                            "should never happen"
                        )
                    """,
                )
            else:
                raise RuntimeError("Operation not supported:" + operation)

        insert_with_indent(
            "",
            f"""\

            {else_or_elif_condition}:
                # Same as above, but with bits in byte sequence
            """,
        )
        if not already_indexed:
            insert_with_indent(
                "",
                f"""\
                sequence_key, bit_number = {index}_index_and_bit_method({vertex_id}, 8)
                bit_mask = 1 << bit_number
            """,
            )
        for match, line, given_indent, set_name, operation in iterate_matches(code):
            if match is None:
                insert(indent + line + "\n")
            elif operation == "add_vertex_id":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    try:
                        {set_name}_sequence[sequence_key] |= bit_mask
                    except IndexError:
                        {set_name}_wrapper.extend_and_set(sequence_key, bit_mask)
                    """,
                )
            elif operation == "discard_vertex_id":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                try:
                    {set_name}_sequence[sequence_key] &= ~bit_mask
                except IndexError:
                    {set_name}_wrapper.extend_and_set(sequence_key, bit_mask)
                """,
                )
            elif operation == "if_contains_vertex_id:":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    try:
                        if {set_name}_sequence[sequence_key] & bit_mask:
                    """,
                )
                indent += "    "
            elif operation == "if_contains_vertex_id_prepare_remove_and_elseadd:":
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    try:
                        value = {set_name}_sequence[sequence_key]
                        if value & bit_mask:
                    """,
                )
                indent += "    "
            elif operation == "prepared_remove_vertex_id":
                insert(
                    f"{given_indent}{indent}{set_name}_sequence[sequence_key] = value - bit_mask\n"
                )
            elif operation == "else_prepared_add_endif":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                        else:
                            {set_name}_sequence[sequence_key] = value | bit_mask
                    except IndexError:
                        {set_name}_wrapper.extend_and_set(sequence_key, bit_mask)
                    """,
                )
            elif operation == "endif":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    except IndexError:
                        pass
                    """,
                )
            elif operation == "endif_with_vertex_included_in_past":
                indent = indent.removesuffix("    ")
                insert_with_indent(
                    indent + given_indent,
                    f"""\
                    except IndexError:  # pragma: no cover
                        raise AssertionError(
                            "Internal error: IndexError "
                            "should never happen"
                        )
                    """,
                )
            else:
                raise RuntimeError("Operation not supported:" + operation)


# $$"""
