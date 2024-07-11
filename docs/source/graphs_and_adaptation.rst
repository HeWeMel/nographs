Graphs and adaptation
---------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

In the shown `examples <examples>`, you saw functions named *next_vertices* and
*next_edges*. In the following sections, we will explain how to define and use
functions like these.

.. _graphs_without_attributes:

Graphs without edge attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An edge of your graph is called *directed*, *unweighted*, and *unlabeled*,
if it consists of a start vertex and an end vertex and carries no further
information. In the graph, the end vertex is called a *successor* of the start vertex.

If your graph consists of such edges, you can give the library access to it
by providing a callback function in the form of a so-called `NextVertices` function:

- Input: A **vertex** and a **traversal object**
- Output: An **Iterable that reports the successors** of the vertex

We will discuss in section `search-aware graphs <search_aware_graphs>`, what the
traversal object is for, and ignore this parameter for the time being.


.. tip::

    A typical `NextVertices` function for graphs with unweighted, unlabeled edges
    looks like this::

       def my_next_vertices(vertex, _):
            # determine the vertices following the current vertex,
            # e.g. as a list
            successors = ...
            return successors

    Or like this::

       def my_next_vertices(vertex, _):
            yield successor_1
            ...
            yield successor_n


Note: The current version of NoGraphs is limited to *locally finite graphs*, i.e.,
each vertex is start vertex of only finitely many edges.

**Example:**

In the `previous section <concept_and_examples>`,
we have seen the following function:

      .. code-block:: python

        >>> def next_vertices(i, _):
        ...     return i + 3, i - 1

.. tip::

   If you graph is *undirected*, i.e., each edge is meant to connect two
   vertices in both directions, then the `NextVertices` function needs to
   report the edges in both directions.

.. _graphs_with_attributes:

Graphs with edge attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An edges is called *weighted*, if it carries data in the form of a weight,
i.e., some number assigned to the edge. For more information abouts weights,
see section `edge weights <weights>`.

An edge is called *labeled*, if it carries other data than a weight.
For example, you might assign a name to an edge. Or you assign a dictionary with
key/value pairs, so that the edge can carry more than one value.
The labels of an edge must be given to NoGraphs in the form of a single object.

If your graph consists of weighted and/or labeled edges, you can give NoGraphs
access to it by providing a callback function in the form of a so-called
`NextEdges` function.

**Example**:
For a vertex *i*, we define *i+1*, *2\*i* and *i\*i* to be its successors. We attach
weights 1, 2 and 3 to these edges. And we attach names to them, so that we can
easily identify them in computation results. We use an algorithm of the library to
find a shortest path (in the sum of edge weights) from vertex 0 to vertex 99, that
does not only show the visited vertices, but also the labels of the traversed edges.

.. code-block:: python

    >>> def next_edges(i, _):
    ...     yield i + 1, 1, "i+1"
    ...     yield 2 * i, 2, "2*i"
    ...     yield i * i, 3, "i*i"
    >>> traversal = nog.TraversalShortestPaths(next_labeled_edges=next_edges)
    >>> _ = traversal.start_from(0, build_paths=True)
    >>> vertex = traversal.go_to(99)
    >>> traversal.distance
    12
    >>> for edge in traversal.paths[vertex]:
    ...     print(edge)
    (0, 1, 'i+1')
    (1, 2, 'i+1')
    (2, 3, 'i+1')
    (3, 6, '2*i')
    (6, 7, 'i+1')
    (7, 49, 'i*i')
    (49, 98, '2*i')
    (98, 99, 'i+1')


A `NextEdges` function has the following signature:

- Input: A **vertex** and a **traversal object**
- Output: An Iterable that **reports each outgoing edge in the form of a tuple**:

  - **The end vertex of the edge** has to be the first element of the tuple.
  - **The weight (optionally)** comes next.

    (Note: Some algorithms of NoGraphs
    require weights, others just ignore them. See section
    `traversal algorithms <traversals>`.)

  - **The labels object (optionally) comes next.**

    (Note: If you inform NoGraphs that you provide a labels object, it will be
    included in analysis results. Otherwise, the labels object will be ignored.
    See section `traversal algorithms <traversals>`.)

.. versionchanged:: 3.0

   An edge can only carry one labels object. If you need to assign several values,
   you must put them in a collection. (The change was necessary to allow
   for strict `typing <typing>` of all signatures of NoGraphs.)

We will discuss in section `search-aware graphs <search_aware_graphs>`, what the
traversal object is for, and continue to ignore this parameter for the time being.

.. tip::

    A typical `NextEdges` function for graphs with weighted and/or labeled edges
    looks like this::

       def my_next_edges(vertex, _):
            # determine the edges that start at the current vertex,
            # e.g. in the form [(end_vertex_1, weight_1, data_1...), ...]
            edges = ...
            return edges

    Or like this::

       def my_next_edges(vertex, _):
            yield successor_1, weight_1, label_data_1
            ...
            yield successor_n, weight_n, label_data_1


.. _vertices:

Vertices
~~~~~~~~

You can directly use any hashable python object as vertex, with the exception of
*None*. In the `examples <examples>`, we made use of this flexibility.

.. tip::

   Typical choices for vertices are the immutable data types of Python, like integers,
   strings, tuples, named tuples and frozenset, combinations of those, and application
   specific hashable data structures.

Additionally, a vertex can be an object that is not hashable, if you provide a
`VertexToID <VertexToID>` function that computes a hashable identifier for it.
The term *identifier* means: if the identifiers of two vertex objects are equal, the
vertex objects denote the same vertex.
For further details, see the `section about vertex identity <vertex_identity>`.

.. tip::

   Typical choices for vertices in combination with a `VertexToID <VertexToID>`
   function are: Mutable data types, like a NamedTuple, data class or other application
   specific classes. Examples for typical hashable identifiers for a vertex are:
   its memory address (*id*), a hash value (if a hash can be computed, but __hash__ is
   not set, because the object is mutable) or by accessing
   an identifying attribute of your vertex object by something like
   *attrgetter('my_attr')*, like a number or name of the vertex.


.. _weights:

Edge weights
~~~~~~~~~~~~

NoGraphs supports a large range of number types as edge weights.

.. tip::

   Typical choices are *float*, *int* and *decimal.Decimal*.

   If you prefer class *mpf* of library *mpmath* for arbitrary-precision
   floating-point arithmetic, you can also directly use such values
   as edge weights.

   If NoGraphs computes distances, their type will be determined by the type of
   your edge weights (with the exception of zero distance, represented by int 0,
   and infinite distance, represented by float("infinity") by default, see
   `GearDefault <gear_default>`).

For details, see the `API documentation <nographs.Weight>`. See section `typing`,
if you like to work strictly type safe with weights.

**Example:**

In the following graph, the vertices *i* with numbers *0, 1, ...* are connected by edges
*(i, i+1), ...* with weights *1/2, 1/4, 1/8, ...*. The distances
(*0, 1/2, 3/4, 7/8, ...*) of the vertices *i* from vertex *0* approach *1*.

.. code-block:: python

    >>> def test_with_small_weights(one_half):
    ...    def next_edges(i, _):
    ...       yield i + 1, one_half ** (i + 1)
    ...
    ...    goal_difference = one_half ** 64
    ...
    ...    traversal = nog.TraversalShortestPaths(next_edges).start_from(0)
    ...    for vertex in traversal:
    ...       assert traversal.distance != 1, f"Distance 1 reached at {vertex=}"
    ...       if 1 - traversal.distance <= goal_difference:
    ...          return vertex


We go until the distance reaches a value with a goal difference to *1* of *0.5\**64*.
We expect this to happen at vertex *64*.

In the first test, we use *float* as type of our edge weights. We run into an
AssertionError that states, that the distance reaches value *1* at vertex *54*.
What happens here? At vertex *54*, the distance from vertex *0*, i.e., the sum of
(*0, 1/2, 3/4, 7/8, ...*), reaches the maximal precision of type *float*. The value
is rounded to *1*. So, we get a wrong result because the precision supported by
*float* is not high enough.

.. code-block:: python

    >>> test_with_small_weights(0.5)
    Traceback (most recent call last):
    AssertionError: Distance 1 reached at vertex=54

Happily, with NoGraphs, we are not limited to using floats.
In the second test, we use *Decimal* with a precision of 70 places as type of
our edge weights. When NoGraphs adds up such edge weights, it always gets
*Decimal* distances of that precision. So, our choice of the type of weights also
determines the type of distances calculated by NoGraphs. This time, we get the
correct result.

.. code-block:: python

    >>> import decimal
    >>> decimal.getcontext().prec = 70  # precision (number of places)
    >>> test_with_small_weights(decimal.Decimal(0.5))
    64

.. _supported-special-cases:

Supported special cases
~~~~~~~~~~~~~~~~~~~~~~~

NoGraphs supports graphs with multiple edges, cycles and self loops:

- If a graph contains several edges with the same start and end vertex, these edges
  are called *multiple edges*.

- If a graph contains a path that starts at some vertex and ends at the same vertex,
  the path is called a *cycle*.

- If a graph contains an edge with identical start and end vertex, this is called a
  *self loop*.
