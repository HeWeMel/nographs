API reference - extras
----------------------

.. currentmodule:: nographs

The functions and classes documented in this section provide extra functionality
that does not belong to the core of NoGraphs. NoGraphs can be fully used without them.


Gadgets for adapting edge data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Examples: See `tutorial <edge_gadgets>`.

.. autofunction:: adapt_edge_index

.. autofunction:: adapt_edge_iterable

Gadgets for adapting array data and positions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Examples: See `tutorial <matrix_gadgets>`.

Common types
............

.. data:: nographs.Vector

   alias of Sequence[int]

   A vector can be used as parameter to methods of class Position and Array.
   In fact, a Position is itself a Vector, but with further functionality.

.. data:: nographs.Limits

   alias of Sequence[tuple[int, int]]

   The lower (inclusive) and upper (exclusive) boundaries of the indices
   of an Array, given per dimension.

Position
........

Examples: See `tutorial <tutorial_position>`.

.. autoclass:: Position(my_vector: Vector)
   :members:
   :special-members: __add__, __sub__, __mul__

Array
.....

Examples: See `tutorial <matrix_gadgets>`.

.. autoclass:: Array
   :members:
   :special-members: __getitem__, __setitem__


Traveling Salesman
~~~~~~~~~~~~~~~~~~

The algorithm behind the functions described below is used in the tutorial
for demonstration purposes.

Examples: See `tutorial <tsp_in_nographs>`.

.. autofunction:: traveling_salesman_flex

.. autofunction:: traveling_salesman

.. autoclass:: nographs.GettableProto(Protocol[T_key_contra, T_value_co]))
   :special-members: __getitem__


Shortest paths in infinitely branching graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The algorithm behind the classes described below is used in the tutorial
for demonstration purposes.

Examples: See `tutorial <infinite_branching_in_nographs>`.

.. data:: State

   alias of tuple[`T_vertex_id`, int]

.. autoclass:: TraversalShortestPathsInfBranchingSortedFlex
   :exclude-members:

   .. autoattribute:: distance

   .. autoattribute:: paths

   .. autoattribute:: distances

   .. automethod:: start_from

   .. automethod:: go_for_distance_range


.. autoclass:: TraversalShortestPathsInfBranchingSorted
   :show-inheritance: yes