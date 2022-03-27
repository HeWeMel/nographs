API reference
-------------

.. currentmodule:: nographs

Basic types
~~~~~~~~~~~

.. data:: nographs.Vertex

   alias of Any

   You can use anything as `Vertex <vertices>`, with the exception of None.

   If your vertices are not Hashable, you need to provide a `VertexToID` function
   as parameter *vertex_to_id* when creating a `Traversal`.

.. data:: nographs.Edge

   alias of Sequence

   Structure: *start_vertex, end_vertex, additional_data_elements...*

   In case of a weighted edge, the weight will be given as first element
   of the additional data elements.

   Used in analysis results of the library.

.. data:: nographs.NextVertices

   alias of Callable[[Vertex, Traversal], Iterable[Vertex]]

   For a given `Vertex` and a `Traversal`, your NextVertices function reports
   (positively) connected neighbor vertices.

   Used for `adapting graphs with unlabeled edges <unlabeled_graphs>`.

.. data:: nographs.NextEdges

   alias of Callable[[Vertex, Traversal], Iterable[Sequence]]

   For a given `Vertex` and a `Traversal`, your NextEdges function reports
   *outgoing edges*, each in the form of a sequence with the following
   elements:

   - *end_vertex* of the edge
   - optionally, a *weight*
   - optionally, further elements with *additional data*.

   Note: Since each outgoing edge starts at the given vertex, this information
   is not repeated here (compare `edges <nographs.Edge>`).

   Used for `adapting graphs with labeled edges <labeled_graphs>`.

   Your additional data will be included in traversal results, if you demand
   this by using option *labeled_paths* of method *start_from* of the `Traversal`.

.. data:: nographs.VertexToID

   alias of Callable[[Vertex], Hashable]

   For a given `Vertex`, a VertexToID function returns a hashable object that
   *identifies* the vertex. This means: For two given vertices, the respectively
   returned objects ("*identifiers*") have to be equal (in the sense of Python's
   equality comparison) if and only if the two vertices are to be regarded as
   the same vertex in the sense of your graph.

   Used as parameter *vertex_to_id* when creating a `Traversal`.

   Typical use cases:

   a) You want to use objects, that are not hashable, as you vertices. The
   identifiers will stand in for the vertices when hashes are needed.

   b) You group vertices into equivalence classes and for each class of vertices,
   the `Traversal` algorithm should treat the vertices in the class as being the same
   vertex. Here, you define the function such that it calculates a hashable identifier
   of the equivalence class of the vertex given as parameter.

   Please note, that the identifiers will not only be used internally by a Traversal,
   but they will also replace your vertices as keys in sets or mappings used as
   externally accessible traversal attributes.

   Examples: For identifying vertices that are singletons, the build-in function
   *id* can be used, because every other object stored somewhere else is not the
   same vertex. For a mutable collection like a *list*, an immutable counterpart like
   a *tuple* could be returned (provided, the elements are hashable). Or you number
   your vertices and return the numbers as identifiers.


.. _traversal_api:

Traversal strategies
~~~~~~~~~~~~~~~~~~~~

Common methods
..............

.. autoclass:: Traversal()
   :members:
   :special-members: __iter__, __next__
..
  Note: Signature suppressed here (manually overridden by "()") - is abstract class


.. _traversal-classes-api:

Traversal classes for all graphs
................................

TraversalBreadthFirst
+++++++++++++++++++++

Examples: See `example-traversal-breadth-first-in-maze`,
`example-traversal-breadth-first-towers-hanoi`,
the comparing examples `here <examples_weighted_graphs>`, and
`an example for method go_for_depth_range <example_go_for_depth_range>`.

.. autoclass:: TraversalBreadthFirst
   :member-order: bysource
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to
..
  Note: Method start_from is inherited from _TraversalWithOrWithoutLabels. The
  inheritance is not explained, and the method is shown as method of the current class.
  Reason: The inheritance from _TraversalWithOrWithoutLabels is code inheritance.
  This inheritance structure is not guaranteed for the future.

TraversalDepthFirst
+++++++++++++++++++

Examples: See `example-traversal-depth-first-integers` and
the comparing examples `here <examples_weighted_graphs>`.

.. autoclass:: TraversalDepthFirst
   :members: __init__
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to

TraversalTopologicalSort
++++++++++++++++++++++++++

Examples: See `example-topological_sorting_processes` and
the comparing examples `here <examples_weighted_graphs>`.

.. autoclass:: TraversalTopologicalSort
   :members: __init__
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to


Traversal classes for weighted graphs
.....................................

TraversalShortestPaths
++++++++++++++++++++++

Examples: See `example-shortest-paths-in-maze`,
the comparing examples `here <examples_weighted_graphs>` and
`an example for method go_for_distance_range <example_go_for_distance_range>`.

.. autoclass:: TraversalShortestPaths
   :members: __init__
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to

TraversalAStar
++++++++++++++

Examples: See `example-shortest-paths-with-heuristic`
and the comparing examples `here <examples_weighted_graphs>`.

.. autoclass:: TraversalAStar
   :members: __init__
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to

TraversalMinimumSpanningTree
++++++++++++++++++++++++++++

Examples: See `the comparing examples here <examples_weighted_graphs>`.

.. autoclass:: TraversalMinimumSpanningTree
   :members: __init__
   :inherited-members:
   :exclude-members: go_for_vertices_in, go_to

.. _paths_api:

Paths
~~~~~

.. autoclass:: Paths()
   :members:
   :exclude-members: append_edge, __init__
   :special-members: __contains__, __getitem__

Gadgets
~~~~~~~

Gadgets for adapting edge data
..............................

Examples: See `tutorial <edge_gadgets>`.

.. autofunction:: adapt_edge_index

.. autofunction:: adapt_edge_iterable

Gadgets for adapting array data and positions
.............................................

Examples: See `tutorial <matrix_gadgets>`.

Common types
++++++++++++

.. data:: nographs.Vector

   alias of Sequence[int]

   A vector can be used as parameter to methods of class Position and Array.
   In fact, a Position is itself a Vector, but with further functionality.

.. data:: nographs.Limits

   alias of Sequence[tuple[int, int]]

   The lower (inclusive) and upper (exclusive) boundaries of the indices
   of an Array, given per dimension.

Array
+++++

Examples: See `tutorial <matrix_gadgets>`.

.. autoclass:: Array
   :members:
   :special-members: __getitem__, __setitem__
   :exclude-members: items, findall

   .. automethod:: items() -> Generator[tuple[Position, Any]]
   .. automethod:: findall(content: Container[Any]) -> tuple[Position]

Position
++++++++

Examples: See `tutorial <tutorial_position>`.

.. autoclass:: Position(my_vector: Vector)
   :members:
