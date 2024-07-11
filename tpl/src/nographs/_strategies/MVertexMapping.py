""" Functionality that ease the use of gear collection VertexMapping
in traversals. """

from tpl.make_insert_look_defined import *

# """$$
import_from("tpl/base_lib.py")


class MVertexMapping:
    """Methods to ease implementing performant access to VertexMapping objects."""

    @staticmethod
    def access(name: str):
        insert(
            f"""\
            _, {name}_sequence, {name}_wrapper = access_to_vertex_mapping({name})
"""
        )

    @staticmethod
    def get_included(collection: str, key: str):
        """Reference to value for *key*, and we are sure that *key* exists."""
        insert(f"""{collection}_sequence[{key}]""")

    @staticmethod
    def set_included(collection: str, key: str, value: str):
        """Reference to value for *key*, and we are sure that *key* exists."""
        insert(f"""{collection}_sequence[{key}] = {value}\n""")

    @staticmethod
    def get_with_default(collection: str, key: str, value: str, variable: str):
        """
        Roughly equivalent to:
          variable = collection[key] if key in collection else value.
        There is no guarantee whether the default *value* is set in *collection*
        in the else case (like a defaultdict does is) or not.
        """
        insert(
            f"""\
                try:
                    {variable} = {collection}_sequence[{key}]
                except IndexError:
                    {variable} = {value}
"""
        )

    @staticmethod
    def set(collection: str, key: str, value: str):
        """collection[key] = value."""
        insert(
            f"""\
                try:
                    {collection}_sequence[{key}] = {value}
                except IndexError:
                    {collection}_wrapper.extend_and_set({key}, {value})
"""
        )

    @staticmethod
    def if_value_smaller_set_else_continue(collection: str, key: str, value: str):
        """If value < collection[key] then collection[key] = value else continue."""
        insert(
            f"""\
                try:
                    if {collection}_sequence[{key}] <= {value}:
                        continue
                    {collection}_sequence[{key}] = {value}
                except IndexError:
                    {collection}_wrapper.extend_and_set({key}, {value})
"""
        )

    @staticmethod
    def if_value_smaller_or_condition_set_else_continue(
        collection: str, key: str, value: str, condition: str
    ):
        """
        If condition or value < collection[key]:
            collection[key] = value
        else:
            continue
        """
        insert(
            f"""\
                try:
                    if not {condition} and {collection}_sequence[{key}] <= {value}:
                        continue
                    {collection}_sequence[{key}] = {value}
                except IndexError:
                    # n_id not in distances_collection. To be regarded as value
                    # infinity, i.e., n_path_weight is smaller.
                    {collection}_wrapper.extend_and_set({key}, {value})
"""
        )


# $$"""
