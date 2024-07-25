""" Basis functionality easing the use of the template library """

from tpl.make_insert_look_defined import *


# """$$
# Above, the leading comment character is just to hide the macro start mark
# from the syntax analysis of the used IDE. This makes the IDE check
# the syntax within the macro code after this macro start mark.


def insert_with_indent(indent: str, code: str) -> None:
    """Change each line of code as follows, and call function *insert*
    on each result: Remove the indentation string given by the last line
    of *code*. Prepend the given indentation string *indent*.
    """
    lines = code.splitlines(keepends=True)
    ignore_indent = lines[-1]
    for line in lines[:-1]:
        insert(indent + line.removeprefix(ignore_indent))


# $$"""
