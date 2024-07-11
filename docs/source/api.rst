API reference - NoGraphs
------------------------

.. currentmodule:: nographs

.. _type_variables:


Type variables for graph adaptation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The algorithms, data structures and extension features of NoGraphs
are able to handle vertices, vertex ids, weights and edge labels of
different data types. In order to specify their capabilities and typing
relationships optimally, the respective
**classes of NoGraphs are generic, and parameterized**
**by the following type variables**.

Example: When you choose bookkeeping collections for a specific use case
(`gears <nographs.Gear>`)
that are limited to specific data types, plugging them into some graph analysis
strategy will transfer these restrictions to the input and output types of the
analysis. The type variables used in the API of NoGraphs document this
relationship, and, optionally, you can use a type checker to check if your application
correctly handles them.


.. data:: T_vertex
   :value: TypeVar("T_vertex")

   You can use anything as vertex, with the exception of None. (This exception
   cannot be expressed as type bound of a TypeVar. The requirement is checked at
   runtime.)

   Please note: The generic classes of NoGraphs, that have T_vertex as parameter,
   might impose further restrictions on the possible types of vertices,
   by using T_vertex as argument for a type parameter of a superclass where
   this parameter has a type bound. See the documentation of the classes you use.

   Examples: See section `vertices <vertices>` of the tutorial.

.. data:: T_vertex_id
   :value: TypeVar("T_vertex_id", bound=Hashable)

   A vertex id is a hashable object that *identifies* a vertex
   (see `VertexToID` function).

   Examples: See the `section about vertex identity <vertex_identity>`
   in the tutorial.

.. data:: T_weight
   :value: TypeVar("T_weight", bound=Weight)

   As type of weights of edges, you can choose any subtype of protocol *Weight*.
   For the current version of NoGraphs, it is defined as follows:

   .. _nographs.Weight:
   .. code-block:: python

      class Weight(Protocol[T]):
          @abstractmethod
          def __add__(self: T, value: T) -> T: ... # self + value
          @abstractmethod
          def __sub__(self: T, value: T) -> T: ... # self - value
          @abstractmethod
          def __lt__(self: T, value: T) -> bool: ...  #  self<value
          @abstractmethod
          def __le__(self: T, value: T) -> bool: ...  #  self<=value

   Please note, that the `gear <nographs.Gear>` (combination of bookkeeping collections)
   you use might have additional requirements w.r.t. edge weights. If you manually
   set a gear, see its documentation for this aspect.
   `Traversal or search strategy classes <strategy_api>`, that do not allow to
   change the gear, use
   `GearDefault <nographs.GearDefault>`. If you use one of them, see the documentation
   of this gear for its restrictions and for examples of typical weight types for it.

   Examples: See section `edge weights <weights>` in the tutorial.

.. data:: T_labels
   :value: TypeVar("T_labels")

   Labels of edges can be provided as any kind of object, e.g., as a dictionary
   holding key/value pairs, as just a number for numbering edges,
   or as a string for naming an edge.

.. tip::

   Tutorial section `typing` gives a first idea of how NoGraphs can be used in
   typed code.


Function signatures for graph adaptation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Based on the `type variables for graph adaptation <type_variables>`,
NoGraphs defines some signatures for callback functions that application code
can provide to NoGraphs for graph adaptation.

Vertex identity
...............

.. data:: VertexToID

   alias of Callable[[`T_vertex`], `T_vertex_id`]

   For a given vertex, return a hashable object that *identifies* the vertex.

   A function with this signature can be used by application code as parameter
   *vertex_to_id* when creating a `Traversal` of one of the "Flex" classes
   (see tutorial section `vertex identity <vertex_identity>`).

   A VertexToID function defines the identity of vertices (or of equivalence
   classes of vertices) in your graph as follows:
   **NoGraphs regards two vertices as the same vertex**
   ("the same", or "equivalent")
   **if and only if the objects returned by the used VertexToID function**
   (the *identifiers*) for the vertices **are equal**
   (in the sense of Python's equality comparison).

   Typical use cases:

   a) You want to use objects, that are not hashable, as you vertices. The
   identifiers will stand in for the vertices when hashes are needed.

   b) You group vertices into equivalence classes and for each class of vertices,
   the `Traversal` algorithm should treat the vertices in the class as being the same
   vertex. Here, you define the function such that it calculates a hashable identifier
   of the equivalence class of the vertex given as parameter.

   The identifiers will not only be used internally by a Traversal,
   but they will also replace your vertices as keys in sets or mappings used as
   externally accessible traversal attributes. In this case, this effect is documented
   for the traversal class.

   Example: See `tutorial <equivalence_class_example>`.

   NoGraphs provides the following default implementation of a VertexToID function:

   .. autofunction:: vertex_as_id


.. _outgoing_edges:

Outgoing edges
..............

For a given vertex, the edges that start at this vertex can be described
as tuples. The building rules of NoGraphs for such *outedge* tuple structures
are:

- The **first element is always the vertex the edge leads to**.
- Then, **in some cases, a weight value follows**.
- Then, **in some cases, an object that represents edge labels follows**.
- The **vertex is not the only element** of the edge (because otherwise, we
  just use the vertex itself instead of a tuple).

This leads to the following structures that are used in the signatures of
NoGraphs:

.. data:: UnweightedLabeledOutEdge

   alias of tuple[`T_vertex`, `T_labels`]

.. data:: WeightedUnlabeledOutEdge

   alias of tuple[`T_vertex`, `T_weight`]

.. data:: WeightedLabeledOutEdge

   alias of tuple[`T_vertex`, `T_weight`, `T_labels`]

Next vertices and next edges functions
......................................

Application code can use a function ("adjacency function") to inform NoGraphs
about the outgoing edges that start at some vertex. The signature of such a
function needs to have a special structure:

- The **first argument is always the current vertex** (outgoing edges
  from this vertex will be reported to NoGraphs)
- The **second argument is always the current strategy object**
  (see tutorial section about `search-aware graphs <search_aware_graphs>`)

  In the following, type variable *T_strategy* is used as placeholder for
  the type of the `strategy <nographs.Strategy>` object (traversal strategy, resp.
  search strategy).

  .. data:: T_strategy
     :value: TypeVar("T_strategy", bound=Strategy)

- The **result needs to be iterable**.

  - Either it iterates **just the vertices** the edges lead to.
  - Or it iterates **the edges described by tuples** (see
    section `outgoing edges <outgoing_edges>`).

    **Application code might need to provide a weight**
    (because the used traversal or search strategy requires it) or an
    **edge label object** (because it guarantees this to the strategy so that
    this data is included in results of the traversal or search). In these cases,
    the weight, resp. the edge label object, needs to be **of the proper types**
    (as needed by the strategy or as declared in typed code).

    **If such data is provided without such need, it can be of arbitrary types.**

These building rules lead to the following combinations of signature elements:

**Adjacency functions for strategies that accept edges with and without weights:**

.. data:: NextVertices

   alias of Callable[[`T_vertex`, `T_strategy`], Iterable[`T_vertex`]]

   For a given vertex and a `Traversal`, report
   (positively) connected neighbor vertices.

.. data:: NextEdges

   | alias of Callable[[`T_vertex`, `T_strategy`], Iterable[Union[
   |     `WeightedUnlabeledOutEdge` [`T_vertex`, Any],
   |     `UnweightedLabeledOutEdge` [`T_vertex`, Any],
   |     `WeightedLabeledOutEdge` [`T_vertex`, Any, Any]]]]

   Like NextVertices, but instead of connected vertices, **return outgoing**
   **edges with or without weights and with or without labels**, and
   the weight and labels can be of arbitrary type (not need to match the
   types used to instantiate the strategy), because the strategy will ignore
   weights and labels.

.. data:: NextLabeledEdges

    | alias of Callable[[`T_vertex`, `T_strategy`], Iterable[Union[
    |     `WeightedLabeledOutEdge` [`T_vertex`, Any, `T_labels`],
    |     `UnweightedLabeledOutEdge` [`T_vertex`, `T_labels`]]

    Here, **a labels object must be given**, and it needs to match the edge
    data type used to instantiate the strategy in order to ensure correct
    functioning of NoGraphs.

**Adjacency functions for strategies that accept only edges with weights:**

.. data:: NextWeightedEdges

   | alias of Callable[[`T_vertex`, `T_strategy`], Iterable[Union[
   |     `WeightedUnlabeledOutEdge` [`T_vertex`, `T_weight`],
   |     `WeightedLabeledOutEdge` [`T_vertex`, `T_weight`, Any]]]]

    Here, **a weight must be given**, and it needs to match the weight type
    used to instantiate the strategy in order to ensure correct
    functioning of NoGraphs. Labels are not necessary, and if given,
    can have arbitrary type.

.. data:: NextWeightedLabeledEdges

   | alias of callable[[`T_vertex`, `T_strategy`], Iterable[
   |     `WeightedLabeledOutEdge` [`T_vertex`, `T_weight`, `T_labels`]]]

   Here, **both a weight and labels must be given**, and they need to match
   the weight and labels types used to instantiate the strategy in order
   to ensure correct functioning of NoGraphs.

**Adjacency functions for bidirectional search strategies:**

Here, two adjacency functions of the same type are needed, one for reporting
outedges from a given vertex, and one for reporting inedges leading to a given
vertex.

.. data:: BNextVertices

   | alias of tuple[
   |     `NextVertices` [`T_vertex`, `T_strategy`],
   |     `NextVertices` [`T_vertex`, `T_strategy`],
   | ]

.. data:: BNextEdges

   | alias of tuple[
   |     `NextEdges` [`T_vertex`, `T_strategy`],
   |     `NextEdges` [`T_vertex`, `T_strategy`],
   | ]

.. data:: BNextLabeledEdges

   | alias of tuple[
   |     `NextLabeledEdges` [`T_vertex`, `T_strategy`, `T_labels`],
   |     `NextLabeledEdges` [`T_vertex`, `T_strategy`, `T_labels`],
   | ]

.. data:: BNextWeightedEdges

   | alias of tuple[
   |     `NextWeightedEdges` [`T_vertex`, `T_strategy`, `T_weight`],
   |     `NextWeightedEdges` [`T_vertex`, `T_strategy`, `T_weight`],
   | ]

.. data:: BNextWeightedLabeledEdges

   | alias of tuple[
   |     `NextWeightedLabeledEdges` [`T_vertex`, `T_strategy`, `T_weight`, `T_labels`],
   |     `NextWeightedLabeledEdges` [`T_vertex`, `T_strategy`, `T_weight`, `T_labels`],
   | ]


Edges as part of trees or paths
...............................

NoGraphs computes trees and paths consisting of edges and returns them
with the data you request. Accordingly, such edges can have weights,
labels, both, or none of these:

.. data:: UnweightedUnlabeledFullEdge

   alias of tuple[`T_vertex`, `T_vertex`]

.. data:: UnweightedLabeledFullEdge

   alias of tuple[`T_vertex`, `T_vertex`, `T_labels`]

.. data:: WeightedUnlabeledFullEdge

   alias of tuple[`T_vertex`, `T_vertex`, `T_weight`]

.. data:: WeightedLabeledFullEdge

   alias of tuple[`T_vertex`, `T_vertex`, `T_weight`, `T_labels`]

Sometimes, it is optional whether you provide labels for an edges or not, and
NoGraphs returns the edges as part of computed results with our without labels:

.. data:: WeightedFullEdge

   | alias of Union[
   |     `WeightedUnlabeledFullEdge` [`T_vertex`, `T_weight`],
   |     `WeightedLabeledFullEdge` [`T_vertex`, `T_weight`, `T_labels`]]


.. data:: WeightedOrLabeledFullEdge

   | alias of Union[
   |    `UnweightedLabeledFullEdge` [`T_vertex`, `T_labels`],
   |    `WeightedUnlabeledFullEdge` [`T_vertex`, `T_weight`],
   |    `WeightedLabeledFullEdge` [`T_vertex`, `T_weight`, `T_labels`]]


.. data:: AnyFullEdge

   | alias of Union[
   | `UnweightedUnlabeledFullEdge` [`T_vertex`],
   | `WeightedUnlabeledFullEdge` [`T_vertex`, `T_weight`],
   | `UnweightedLabeledFullEdge` [`T_vertex`, `T_labels`],
   | `WeightedLabeledFullEdge` [`T_vertex`, `T_weight`, `T_labels`],


.. _strategy_api:

Traversal and search strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Strategy
      :members:


See `traversal strategies <traversal_api>` and `search strategies <search_api>`.

.. _traversal_api:

Traversal strategies
~~~~~~~~~~~~~~~~~~~~

Common methods
..............

.. class:: Traversal

  Abstract Class. Its subclasses provide methods to iterate through vertices
  and edges using some specific traversal strategies.

  Bases: `Strategy <nographs.Strategy>` [`T_vertex`, `T_vertex_id`, `T_labels`]

  .. automethod:: __iter__

  .. automethod:: __next__

  .. automethod:: go_for_vertices_in

  .. automethod:: go_to

..
    .. autoclass:: Traversal()
      :show-inheritance: yes
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
the comparing examples `here <examples_all_graphs>`, and
`an example for method go_for_depth_range <example_go_for_depth_range>`.

.. autoclass:: TraversalBreadthFirstFlex
   :exclude-members:

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. autoattribute:: visited

   .. automethod:: start_from

   .. automethod:: go_for_depth_range

..
  Note: Method start_from is inherited from _TraversalWithoutWeights. The
  inheritance is not explained, and the method is shown as method of the current class.
  Reason: The inheritance from _TraversalWithoutWeights is code inheritance.
  This inheritance structure is not guaranteed for the future.

.. autoclass:: TraversalBreadthFirst
   :show-inheritance: yes

TraversalDepthFirst
+++++++++++++++++++

**Enumerations used in the definition of parameters:**

.. autoclass:: DFSEvent

.. autoclass:: DFSMode

**About the class:**

Examples: See `example-traversal-depth-first-integers` and
the comparing examples `here <examples_all_graphs>`.

.. autoclass:: TraversalDepthFirstFlex
   :exclude-members:

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. autoattribute:: visited

   .. autoattribute:: event

   .. autoattribute:: trace

   .. autoattribute:: trace_labels

   .. autoattribute:: on_trace

   .. autoattribute:: index

   .. automethod:: start_from

   .. automethod:: __iter__

   .. automethod:: skip_expanding_entered_vertex

.. autoclass:: TraversalDepthFirst
   :show-inheritance: yes

TraversalNeighborsThenDepthFlex
+++++++++++++++++++++++++++++++

Examples: See `example-traversal-depth-first-integers` and
the comparing examples `here <examples_all_graphs>`.

.. autoclass:: TraversalNeighborsThenDepthFlex
   :exclude-members:

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. autoattribute:: visited

   .. automethod:: start_from

.. autoclass:: TraversalNeighborsThenDepth
   :show-inheritance: yes

TraversalTopologicalSort
++++++++++++++++++++++++++

Examples: See `example-topological_sorting_processes` and
the comparing examples `here <examples_all_graphs>`.

.. autoclass:: TraversalTopologicalSortFlex
   :exclude-members:

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. autoattribute:: visited

   .. autoattribute:: cycle_from_start

   .. automethod:: start_from

.. autoclass:: TraversalTopologicalSort
   :show-inheritance: yes


Traversal classes for weighted graphs
.....................................

TraversalShortestPaths
++++++++++++++++++++++

Examples: See `example-shortest-paths-in-maze`,
the comparing examples `here <examples_weighted_graphs>` and
`an example for method go_for_distance_range <example_go_for_distance_range>`.

.. autoclass:: TraversalShortestPathsFlex
   :exclude-members:

   .. autoattribute:: distance

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. autoattribute:: distances

   .. automethod:: start_from

   .. automethod:: go_for_distance_range

.. autoclass:: TraversalShortestPaths
   :show-inheritance: yes

TraversalAStar
++++++++++++++

Examples: See `example-shortest-paths-with-heuristic`
and the comparing examples `here <examples_weighted_graphs>`.

.. autoclass:: TraversalAStarFlex
   :exclude-members:

   .. autoattribute:: path_length

   .. autoattribute:: depth

   .. autoattribute:: paths

   .. automethod:: start_from

.. autoclass:: TraversalAStar
   :show-inheritance: yes

TraversalMinimumSpanningTree
++++++++++++++++++++++++++++

Examples: See `the comparing examples here <examples_weighted_graphs>`.

.. autoclass:: TraversalMinimumSpanningTreeFlex
   :exclude-members:

   .. autoattribute:: edge

   .. autoattribute:: paths

   .. automethod:: start_from

.. autoclass:: TraversalMinimumSpanningTree
   :show-inheritance: yes


.. _search_api:

Bidirectional search strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BSearchBreadthFirstFlex
.......................

Example: See `here <example-bsearch-breadth-first>`.

.. autoclass:: BSearchBreadthFirstFlex

.. autoclass:: BSearchBreadthFirst
   :show-inheritance: yes

BSearchShortestPathFlex
.......................

Example: See `here <example-bsearch-shortest-path>`.

.. autoclass:: BSearchShortestPathFlex

.. autoclass:: BSearchShortestPath
   :show-inheritance: yes


.. _paths_api:

Paths containers and paths
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Paths
   :members:
   :exclude-members: append_edge
   :special-members: __contains__, __getitem__

.. autoclass:: Path
   :members:
   :exclude-members: from_bidirectional_search, of_nothing, from_vertex
   :special-members: __contains__, __getitem__

..
   Notes:

   - The other two classes of the module are internal and thus not documented here
   - Even if __init__ were listed in exclude-members, its parameters would be displayed
     as part of the class documentation.

.. _gears_api:

Gears
~~~~~

In NoGraphs, a *gear* provides a **complete set of bookkeeping data structures,**
**that are optimized for a specific usage scenario** of NoGraphs.
Application code can:

- choose the optimal gear for a given situation,

- and define new gears that are derived from existing ones and that
  replace some collections by other set- oder mapping-like collections (e.g.,
  collections from external libraries) that better suite the use case.

Side note: If you like to define a new gear based on a new list- or array-like
collection (e.g., one of an external library) and you also aim at high runtime
efficiency (comparable to the predefined gears for integer vertex ids, that
use lists and arrays of the standard library in a special and fast way), please
inform the author, that the documentation should also cover this aspect.

The protocols
.............

Syntactically, a gear is an implementation of one of the protocols
`nographs.GearWithoutDistances` and `nographs.Gear`. Each
of its methods is a factory that creates one of the kinds of data structures
that NoGraphs needs for its algorithms.

.. autoclass:: GearWithoutDistances()
   :show-inheritance: yes
   :members:

.. autoclass:: Gear()
   :show-inheritance: yes
   :members:
   :exclude-members: raise_distance_infinity_overflow_error

Gears for hashable vertex ids
.............................

.. autoclass:: GearForHashableVertexIDs
   :show-inheritance: yes

Subclasses:

.. autoclass:: GearDefault
   :show-inheritance: yes

.. autoclass:: GearForHashableVertexIDsAndIntsMaybeFloats
   :show-inheritance: yes

.. autoclass:: GearForHashableVertexIDsAndDecimals
   :show-inheritance: yes

.. autoclass:: GearForHashableVertexIDsAndFloats
   :show-inheritance: yes

..
  Option :members: is not given here, since the methods are just overloaded
  by appropriate implementations, but the documentation is unchanged.

Gears for integer vertex ids
............................

.. autoclass:: GearForIntVertexIDs
   :show-inheritance: yes

Subclasses:

.. autoclass:: GearForIntVertexIDsAndIntsMaybeFloats
   :show-inheritance: yes

.. autoclass:: GearForIntVertexIDsAndDecimals
   :show-inheritance: yes

.. autoclass:: GearForIntVertexIDsAndCFloats
   :show-inheritance: yes

.. autoclass:: GearForIntVertexIDsAndCInts
   :show-inheritance: yes

Gears for integer vertices and ids
..................................

.. autoclass:: GearForIntVerticesAndIDs
   :show-inheritance: yes

Subclasses:

.. autoclass:: GearForIntVerticesAndIDsAndIntsMaybeFloats
   :show-inheritance: yes

.. autoclass:: GearForIntVerticesAndIDsAndDecimals
   :show-inheritance: yes

.. autoclass:: GearForIntVerticesAndIDsAndCFloats
   :show-inheritance: yes

.. autoclass:: GearForIntVerticesAndIDsAndCInts
   :show-inheritance: yes

..
  Option :members: is not given here, since the methods are just overloaded
  by appropriate implementations, but the documentation is unchanged.
