# These definitions are just to silence the QA of the used IDE for
# calls of *insert* and similar functions in macro code.
# Usage in a text section (!) of a template, that will be
# imported (!) in another template:
#   from tpl.make_insert_look_defined import *
# Since text sections are not evaluated and the text is ignored by
# *import_from()*, it has no effect. But the IDE thinks, the functions
# are really defined here.


def insert(*args, **kwargs):
    pass


def import_from(*args, **kwargs):
    pass


def insert_from(*args, **kwargs):
    pass
