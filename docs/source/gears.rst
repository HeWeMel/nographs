.. _replace-internals:

Choosing and changing internal data structures
----------------------------------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

Depending on your graph, on your search task and especially on
the data types you use to represent the
`vertices <vertices>`,
`vertex ids <vertex_identity>`,
and `edge weights <weights>` of your graph,
you might want to choose specific bookkeeping data structures optimized for
your usage scenario.

NoGraphs offers three ways to choose or change data structures that it
uses internally. In the following sections, we discuss them.


.. _choosing_gear:

Choosing the optimal gear
~~~~~~~~~~~~~~~~~~~~~~~~~

As already said, for each of the classes described in the sections
`traversal algorithms <traversals>` and
`bidirectional search algorithms <bidirectional_search>`,
there is another, more flexible class,
with "Flex" appended to the class name. These classes have two more parameters,
*vertex_to_id* (see `vertex identity <vertex_identity>`) and *gear*. In this section,
we explain the latter parameter.

In NoGraphs, a *gear* provides a **complete set of bookkeeping data structures,**
**that are optimized for a specific usage scenario** of NoGraphs.
Application code can choose the optimal gear for a given situation,
and it can define new gears.

.. versionchanged:: 3.0

   Gears introduced.

Syntactically, a gear is an implementation of protocol `nographs.Gear`
(or, in feature-limited special cases, of protocol `nographs.GearWithoutDistances`).
Each of its methods is a factory that creates one of the kinds of data structures
that NoGraphs needs for its algorithms.

NoGraphs offers the following predefined gears. **The three main classes support**
**different types of vertices and vertex IDs**, and their respective
**subclasses are special cases for specific types of weights/distances**
(and suitable choices of the values representing zero and infinite distance).

.. _gear_for_hashable_vertex_ids:

1. Class `nographs.GearForHashableVertexIDs`

  Supports **hashable vertex IDs** (either, your vertices are hashable, or you
  assign hashable IDs to them, see `vertex identity <vertex_identity>`).


  Creates *set* and *dict* collections for NoGraphs. Such collections are
  quite **flexible, but they store Python objects** by reference. As long as NoGraphs
  keeps vertices, weights and other objects in the bookkeeping, the objects will stay
  in memory. If, for example, your graph has 10 M of vertices
  and each is represented by an integer, about 10 M of integer objects will
  exist in the Python interpreter while the analysis runs, even if your
  application does not need or work with them at this point of time.

  The traversal classes with simplified API as described in section
  `traversal algorithms <traversals>`, that do not allow for choosing a gear,
  use the following subclass of `nographs.GearForHashableVertexIDs` as gear:

.. _gear_default:

  - Class `nographs.GearDefault`

    Uses the **integer 0 for zero distance and float("infinity")**
    **for infinite distance**. Distance results can be one of these values or a value
    of the type the application uses for its edge weights.

    For most of the typical use cases this choice fits well. See the section about
    `weights`.

  For contexts where static types should be defined as narrow as possible, there are
  three **subclasses for the common cases that**
  **integers/floats or Decimal or only floats are used as edge weights**.
  They all readily define zero and infinite distance by values from their respective
  edge weight type, so that no other weight and distance types occur. The first uses
  integer 0 and float("infinity"), see `GearDefault <gear_default>` above, but without
  additional application-specific weight types.

  - Class `nographs.GearForHashableVertexIDsAndIntsMaybeFloats`

  - Class `nographs.GearForHashableVertexIDsAndDecimals`

  - Class `nographs.GearForHashableVertexIDsAndFloats`

.. _gear_for_int_vertex_ids:

2. Class `nographs.GearForIntVertexIDs`

  Supports **vertex IDs that are non-negative integers** (to be exact: they should be
  a dense subset of the natural numbers starting at 0). Either, your vertices are
  such numbers, or you assign such numbers as IDs to them (see section about
  `vertex identity <vertex_identity>`).

  Trades type flexibility and runtime for an (often large) reduction of the memory
  consumption: Uses sequence-based collections (instead of hash-based collections
  like dict and set) for bookkeeping. Arrays are preferred over lists, since there,
  data can be stored as C-native values. Boolean values are packed into integers.

  The memory consumption of the gear is typically much lower than that of
  `nographs.GearForHashableVertexIDs` and its subclasses,
  if the used numbers are *dense* enough. More details about this
  topic can be found in section `Comparison of NoGraphs gears <performance_gears>`.

  There are four **subclasses for the common cases that integers/floats,**
  **Decimal, C-native floats, or C-native integers are used as edge weights**,
  with zero and infinite distance defined accordingly.
  See above for the respective properties. Additionally, the two versions with C-native
  value types save some memory by using arrays instead of lists for storing weights
  and distances.

  - Class `nographs.GearForIntVertexIDsAndIntsMaybeFloats`

  - Class `nographs.GearForIntVertexIDsAndDecimals`

  - Class `nographs.GearForIntVertexIDsAndCFloats`

  - Class `nographs.GearForIntVertexIDsAndCInts`

.. _gear_for_int_vertices_and_ids:

3. Class `nographs.GearForIntVerticesAndIDs`

  A *GearForIntVertexIDs* (see above for its constraints on vertex ids) for
  **vertices that are non-negative integers** and fulfil one of the
  **size constraints** (number of bytes) offered by the class.

  Trades type flexibility and runtime for an (often large) reduction of the memory
  consumption. Here, the effects described for `GearForIntVertexIDs` can be used
  by more kinds of graph traversals and in more situations, since now, the vertices
  are integers, too, and thus can be used as index of sequences. For more details see
  section `Comparison of NoGraphs gears <performance_gears>`.

  Again, there are four **subclasses for common type cases** and
  respective choices of zero and infinity distance. See subclasses
  of `GearForIntVertexIDs <gear_for_int_vertex_ids>` for the respective properties.

  - Class `nographs.GearForIntVerticesAndIDsAndIntsMaybeFloats`

  - Class `nographs.GearForIntVerticesAndIDsAndDecimals`

  - Class `nographs.GearForIntVerticesAndIDsAndCFloats`

  - Class `nographs.GearForIntVerticesAndIDsAndCInts`

**Example:**

..
    >>> def next_edges(i, _):
    ...     j = (i + i // 6) % 6
    ...     yield i + 1, j * 2 + 1
    ...     if i % 2 == 0:
    ...         yield i + 6, 7 - j
    ...     elif i % 1200000 > 5:
    ...         yield i - 6, 1

We use the next_edges function defined in section :doc:`overview <index>`.

Instead of the traversal class `TraversalShortestPaths` used there, now, we use
the more flexible class `TraversalShortestPathsFlex`. We provide the
default value `nog.vertex_as_id <vertex_as_id>` for parameter *vertex_to_id*,
and a gear that can be chosen as parameter *gear* of our test function *gear_test*.

.. code-block:: python

   >>> def gear_test(gear):
   ...    traversal = nog.TraversalShortestPathsFlex(nog.vertex_as_id, gear, next_edges)
   ...    vertex = traversal.start_from(0, build_paths=True).go_to(1200000)
   ...    path = traversal.paths[vertex]
   ...    print([traversal.distance, tuple(path[:5]), tuple(path[-5:])])

1. First, we test
with *GearDefault*:

.. code-block:: python

   >>> gear_test(nog.GearDefault())  #doctest:+SLOW_TEST
   [816674, (0, 1, 2, 8, 14), (1199976, 1199982, 1199988, 1199994, 1200000)]

2. We have not changed `vertex identity <vertex_identity>`, so our vertices are
also our vertex ids. And they are numbered from 0 on. Thus, we can also use
*GearForIntVertexIDs*. In the following, we do that, in the variant
with integer edge weights and float("infinity") for infinite distances
(just as example, we have several options here):

.. code-block:: python

   >>> gear_test(nog.GearForIntVertexIDsAndIntsMaybeFloats())  #doctest:+SLOW_TEST
   [816674, (0, 1, 2, 8, 14), (1199976, 1199982, 1199988, 1199994, 1200000)]

3. Our vertices themselves, not only their vertex ids, are numbered from 0 on, and our
weights are integers values that can be stored in float objects. Thus, we can also use
*GearForIntVerticesAndIDsAndCFloats* (again, just as example, since we have several
options here):

.. code-block:: python

   >>> gear_test(nog.GearForIntVerticesAndIDsAndCFloats())  #doctest:+SLOW_TEST
   [816674.0, (0, 1, 2, 8, 14), (1199976, 1199982, 1199988, 1199994, 1200000)]


Of cause, the results are the same in each case. But the needed memory differs:

+-------------+-------+--------+--------------------------------+
| library     | runtime (sec.) | peak memory (bytes)            |
+=============+================+================================+
| Default     | 2.62           | ___126,332,524                 |
+-------------+----------------+--------------------------------+
| IntIDs      | 2.19           | ____46,153,544                 |
+-------------+----------------+--------------------------------+
| IntVertices | 2.45           | ____22,287,388                 |
+-------------+----------------+--------------------------------+

In section `Comparison of NoGraphs gears <performance_gears>`, we will
see the large impact that choosing a more specific and optimized gear
can have on the performance of NoGraphs. The table shown above is an excerpt
of the benchmark results described there.

Side note about the implementation:

- The NoGraphs gears do not emulate one collection based on an
  other, or implement some generalized collection interface based on standard library
  collections. Both would require delegation, and would reduce the runtime performance
  significantly (in fact, in the inner loops of graph traversal, not a single method
  call of any NoGraphs library code takes place, at least not in regular cases).

- And NoGraphs does not use specific implementations of traversal
  algorithms for each collection type. That would hinder maintenance and application
  specific extensions.

- Instead, NoGraphs directly knows how to work with hash-oriented
  and with index-oriented collections in a generalized way, and in specific
  and rare cases, that are not relevant for the runtime performance, an adaptation layer
  steps in, that deals with the differences between different types of collections. So,
  NoGraphs can provide high flexibility and performance, but does not need duplicated
  and adapted code.

.. _new_gear:

Defining your own gear
~~~~~~~~~~~~~~~~~~~~~~

You can define your own gear by subclassing one of the gear classes
described in the previous section and overwriting one of more of the
factory methods.

.. tip:

   The set of methods that a gear needs to implement might grow
   in future versions of NoGraphs without further notice, even in versions
   marked as compatible! By subclassing an existing class instead of
   manually implementing the `gear` protocol, your gear will automatically
   inherit the new methods and comply to the extended protocol.

**Example:**

Let us assume we had installed package *intbitset* for *CPython* from *PyPI*,
and imported its module *intbitset* as *intbitset*.
Intbitset is a 3rd party library that efficiently handles sets of integers.

We use the example of the `previous section <choosing_gear>`, but we like to
find out the depth of vertex 1200000 w.r.t vertex 0.
Our vertices are natural numbers starting with 0 and our weights are floats.
We could use gear *GearForIntVerticesAndIDs*, but we like to have *intbitset*
used instead of *set* of the standard library, because it is better optimized
for our scenario.

So, in a subclass of `nographs.GearForIntVerticesAndIDsAndCFloats`, we simply
overwrite method *vertex_id_set*, that returns a suitable implementation of a vertex
id set for given vertices, by an implementation that returns an *intbitset*.

.. hidden

   >>> try:
   ...    from intbitset import intbitset  # type: ignore
   ... except ImportError:  # for PyPy, we have not imported it...
   ...     intbitset = set

.. code-block:: python

   >>> class GearBitsetAndArrayForIntVerticesAndCFloats(
   ...     nog.GearForIntVerticesAndIDsAndCFloats
   ... ):
   ...    def vertex_id_set(self, vertices):
   ...       return intbitset(list(vertices))

We can use the new gear just like the predefined ones:

.. code-block:: python

   >>> our_gear = GearBitsetAndArrayForIntVerticesAndCFloats()
   >>> traversal = nog.TraversalBreadthFirstFlex(
   ...     next_edges=next_edges, gear=our_gear, vertex_to_id=nog.vertex_as_id)
   >>> traversal.start_from(0).go_to(1200000)  #doctest:+SLOW_TEST
   1200000
   >>> traversal.depth  #doctest:+SLOW_TEST
   200000

Section `Comparison of NoGraphs gears <performance_gears>` shows the
`effect of this change <gear_results>` on performance for the example of
a benchmark: intbitset reduces the memory needed for storing vertex sets
as much as the step from GearDefault to GearForIntVerticesAndIDs can, but
without the 50% runtime disadvantage that GearForIntVerticesAndIDs has.


.. _initializing_bookkeeping:

Pre-initializing bookkeeping data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `start_from <general-start_from>` methods of most of the
`strategy classes <traversals>` offer options that the application can use
to provide data about some specific start state.
An example: In `BreadthFirstSearch <nographs.TraversalBreadthFirst>`,
the application can provide a collection *already_visited* with vertices that
NoGraphs will regard as being already visited when starting the traversal.
See the API reference of the respective `traversal class <traversal-classes-api>`
for more details.

**NoGraphs directly use provided collections with start state data**
**for its internal bookkeeping**.

The application can use such options to define, what bookkeeping collection
NoGraphs should use for the respective case. Note: Restrictions might apply.
See the API reference of the respective `traversal class <traversal-classes-api>`
for more details.

.. versionchanged:: 3.0

   Traversal-specific restrictions introduced (necessary for better performance).

This can be used for several purposes. Here are some examples:

- You provide your own implementation, that does the **bookkeeping in your own way**,
  e.g. directly in your vertex objects.

- You provide an object of a suitable container of the standard library or of an
  external library, NoGraphs does the bookkeeping in there, and like this, you get
  **permanent access to this state information during the traversal**.
