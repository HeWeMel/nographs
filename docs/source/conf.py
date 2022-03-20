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
copyright = '2022, Helmut Melcher'
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

# Prevent the following aliases from being expanded
# (Note: VertexIterator is only needed due to an error in sphinx autodocs: With Vertex
# in aliases, Iterator[Vertex] leads to WARNING "Failed to get a method signature for.."
# with reason "unhashable type: 'TypeAliasForwardRef'". So, it was necessary
# to encapsulate this in a artificial TypeAlias "VertexIterator = Iterator[Vertex]"
# and to add the resolved typing manually in the autodoc_type_aliases.)
aliases = ('Vertex', 'NextVertices', 'NextEdges', 'VertexToID', 'Vector', 'Limits')
autodoc_type_aliases = {alias: alias for alias in aliases} | {
  'VertexIterator': 'Iterator[Vertex]'} | {
  'Vectors': 'Sequence[Vector]'}

autoclass_content = "both"
# autodoc_class_signature = "separated"
autodoc_class_signature = "mixed"

autodoc_default_options = {
    'member-order': 'bysource',
    'undoc-members': False,
    'exclude-members': '__weakref__, __new__'
}

# 'special-members': '__init__',


# def skip(app, what, name, obj, skip, options):
#     if what == "class" and name == "nographs.matrix_gadgets.Position":
#         return True
#     else:
#         return None
#
#
# def setup(app):
#     app.connect('autodoc-skip-member', skip)
