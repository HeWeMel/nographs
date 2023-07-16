# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))
# sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------

project = 'NoGraphs'
copyright = '2022 - 2023, Helmut Melcher'
author = 'Helmut Melcher'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_rtd_theme',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"
# html_theme = 'alabaster'

# html_use_index = False
html_theme_options = {
  'collapse_navigation': False,
  'sticky_navigation': True,
  'navigation_depth': 4,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

root_doc = 'index'
html_show_sourcelink = False
default_role = 'any'

# -- Options for autodocs ----------------------------------------------------

autodoc_typehints_format = 'short'
# autodoc_typehints = 'signature'  # default
autodoc_typehints = 'description'
# autodoc_typehints = 'both'

# Prevent the following aliases from being expanded
aliases = ('NextVertices', 'NextEdges', 'VertexToID', 'Vector', 'Limits',
           'UnweightedUnlabeledFullEdge', 'UnweightedLabeledFullEdge',
           'WeightedUnlabeledFullEdge', 'WeightedLabeledFullEdge',
           'WeightedOrLabeledFullEdge', 'AnyFullEdge', 'OutEdge',
           # 'VertexIdSet', 'VertexIdToDistanceMapping',
           # 'VertexIdToVertexMapping', 'VertexIdToPathEdgeDataMapping',
           )

autodoc_type_aliases = {alias: alias for alias in aliases}  # | {
# 'Vectors': 'Sequence[Vector]'}

autoclass_content = "both"
# autodoc_class_signature = "separated"
autodoc_class_signature = "mixed"

autodoc_default_options = {
    'member-order': 'bysource',
    'undoc-members': False,
    'exclude-members': '__weakref__, __new__'
}


# # The following works only in the signature, not in the type docs of parameters
# def correct_generic_tuple(app, what, name:str, obj, options,
#                           signature: str, return_annotation: str):
#     # if what == "method" and name.find("gears") >= 0:
#     #    signature = signature.replace('~T_', 'T_')
#     signature = signature.replace('T_', 'TT')
#     return (signature, return_annotation)
#
#
# def setup(app):
#     app.connect('autodoc-process-signature', correct_generic_tuple)


# # The following works only in the docstrings, not in the type docs of parameters
# def correct_generic_tuples_in_docstring(
#         app, what, name, obj, options, lines
# ):
#     for i in range(len(lines)):
#         lines[i] = lines[i].replace(r'~T', 'T_')
#
#
# def setup(app):
#     app.connect('autodoc-process-docstring',
#                 correct_generic_tuples_in_docstring)


# def setup(app):
#     app.add_css_file('css/custom.css', priority=300)

# 'special-members': '__init__',


# The following is done directly in the docstrings. Explicit is better than implicit.
# def adapt_bases(app, name, obj, options, bases):
#     bases_unweighted = r"`Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]"
#     bases_weighted = (
#         r"Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`], "
#         + bases_unweighted)
#     for i in range(len(bases)):
#         # The following approach to change the bases does not work, because a
#         # bases entry is of type _GenericAlias, and it is not officially documented
#         # how to work with this and replace content. And string processing destroys
#         # the correct post processing for formatting...
#         #
#         # base: str = str(bases[i])
#         # # The following two classes will be replaced if they occur as base
#         # base = base.replace("_TraversalWithoutWeights[", "Traversal[")
#         # base = base.replace("_TraversalWithWeights[", "Traversal[")
#         # bases[i] = base
#         base_str = str(bases[i])
#         if base_str.find("_TraversalWithoutWeights") >= 0:
#             # Fake Traversal as base, skip the hidden intermediate class
#             bases[i] = bases_unweighted
#         elif base_str.find("_TraversalWithWeights") >= 0:
#             # Fake Traversal as base, skip the hidden intermediate class
#             bases[i] = bases_weighted
#
#
# def setup(app):
#     app.connect('autodoc-process-bases', adapt_bases)


# def skip(app, what, name, obj, skip, options):
#     if what == "class" and name == "nographs.matrix_gadgets.Position":
#         return True
#     else:
#         return None
#
#
# def setup(app):
#     app.connect('autodoc-skip-member', skip)
