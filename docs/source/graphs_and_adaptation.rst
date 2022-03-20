Graphs and adaptation
---------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

In the shown `examples <examples>`, you saw functions named *next_vertices* and
*next_edges*. In the following sections, we will explain how to define and use
functions like these.

.. _unlabeled_graphs:

Graphs with unlabeled edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~

An edge of your graph is called *directed* and *unlabeled*, if it consists of
a start vertex and an end vertex and carries no further information. In the
graph, the end vertex is called a *successor* of the start vertex.

If your graph consists of such edges, you can give the library access to it
by providing a callback function in the form of a so-called `NextVertices` function:

- Input: A **vertex** and the **traversal object**
- Output: The function returns an **Iterable that reports the successors** of the
  vertex

We will discuss in section `search-aware graphs <search_aware_graphs>`, what the
traversal object is for, and ignore this parameter for the time being.


.. tip::

    A typical `NextVertices` function for graphs with unlabeled edges looks like this::

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

   If you graph is *undirected*, i.e., each edge is meant to connects two
   vertices in both directions, then the next_vertices function needs to
   report the edges in both directions.

.. _labeled_graphs:

Graphs with labeled edges
~~~~~~~~~~~~~~~~~~~~~~~~~

A *labeled edge* carries data, e.g. a weight.

If you graph consists of such edges, you can give the library access to it
by providing a callback function in the form of a so-called `NextEdges` function:

- Input: A **vertex** and the **traversal object**
- Output: The function **reports each outgoing edge in the form of a tuple**. The first
  element of the tuple has to be **the end vertex of the edge**, the following elements
  contain your **additional data**.

For algorithms that require *weighted edges*, the
**weights have to be given as the second element** of the tuple, need to be
**mutual comparable**, **comparable to float('infinity')** and it must be possible to
**add them up**. Typical choices are the floats or something that is convertible
to a float (e.g., an int).

Edge data will be included in analysis results, if demanded.

We will discuss in section `search-aware graphs <search_aware_graphs>`, what the
traversal object is for, and continue to ignore this parameter for the time being.

.. tip::

    A typical `NextEdges` function for graphs with labeled edges looks like this::

       def my_next_edges(vertex, _):
            # determine the edges that start at the current vertex,
            # e.g. in the form [(end_vertex_1, weight_1, data_1...), ...]
            labeled_edges = ...
            return labeled_edges

    Or like this::

       def my_next_edges(vertex, _):
            yield successor_1, weight_1, data_1, ...
            ...
            yield successor_n, weight_n, data_n, ...




**Example**:

For a vertex *i*, we define *i+1*, *2\*i* and *i\*i* to be its successors, attach
weights 1, 2 and 3 to these edges, and we attach names to them, so that we can
easily identify them in computation results. We use an algorithm of the library to
find a shortest path (in the sum of edge weights) from vertex 0 to vertex 99, that
does not only show the visited vertices, but also the labels of the traversed edges.

.. code-block:: python

    >>> def next_edges(i, _):
    ...     yield i + 1, 1, "i+1"
    ...     yield 2 * i, 2, "2*i"
    ...     yield i * i, 3, "i*i"
    >>> traversal = nog.TraversalShortestPaths(next_edges)
    >>> _ = traversal.start_from(0, build_paths=True, labeled_paths=True)
    >>> vertex = traversal.go_to(99)
    >>> traversal.distance
    12
    >>> for edge in traversal.paths[vertex]:
    ...     print(edge)
    (0, 1, 1, 'i+1')
    (1, 2, 1, 'i+1')
    (2, 3, 1, 'i+1')
    (3, 6, 2, '2*i')
    (6, 7, 1, 'i+1')
    (7, 49, 3, 'i*i')
    (49, 98, 2, '2*i')
    (98, 99, 1, 'i+1')

.. _vertices:

Vertices
~~~~~~~~

You can use any hashable python object as vertex, with the exception of *None*.
In the `examples <examples>`, we made use of this flexibility.

.. tip::

   Typical choices for vertices are the immutable data types of Python, like integers,
   strings, tuples, named tuples and frozenset, combinations of those, and application
   specific hashable data structures.

Additionally, a vertex can be an object that is not hashable, if you provide a
`VertexToID <VertexToID>` function that computes a hashable identifier for it,
and the hash stays the same during computations of the library.
For further details, see the `section about vertex identity <vertex-identity>`.


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


.. _search_aware_graphs:

Search-aware graphs
~~~~~~~~~~~~~~~~~~~

A graph is a *search-aware* graph (to be exact: a graph that is defined in a
search-aware way), if existence or attributes of some **vertices or edges are defined
using partial results**  that an **algorithm traversing the graph** has computed
**based on the already traversed part of the graph**.

From a mathematical point of view, this is just an ordinary graph with a special form
of recursive definition, and the definition uses a function that calculates
properties of parts of the graph that are already known. From a practical point of
view, search-aware graphs enrich our possibilities: we can use a traversal algorithm
as such function.

With NoGraphs, you can define search-aware graphs. In your NextEdges or NextVertices
function, you can easily use state attributes of the search, like the current search
depth or already computed paths: as shown before, **you get the current traversal as
second parameter**, and **the traversal object provides state information to you**.

Note: In the examples shown so far, we have already accessed the traversal object to
read current state information as part of the traversal results, e.g. the depth of
the currently visited vertex, or one of the paths that have already been calculated.
But for search-aware graphs, we **access the state in the callback function** and
**use it to define further parts** of the graph - and the library allows for that.

.. _eratosthenes_with_Dijkstra:

**Example: Sieve of Eratosthenes, reduced to Dijkstra search**

We implement an infinite generator version for the *Sieve of Eratosthenes*
(see https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes) in the form of a search in an
infinite and search-aware graph.

We represent the elements of a sequence of numbers
*(j, j+increment, j+2\*increment, ...)*
by tuples *(current_value_i, increment)*. These tuples are our vertices.

We start such a sequence, the *base sequence*, at *(1, 1)*. For each prime *i* that we
find, we start an additional sequence, a *multiples sequence*,
at *i\*i* with increment *i*. And we define edges that connect a vertex
*(current_number, i)* of a multiples sequence with *(current_number, 1)* of
the base sequence.

**We choose the weights in such a way, that the weight of a path to a number equals the
number itself, if it is reached by the base sequence alone, and slightly less, if the
path goes through a multiples sequence.** Here, we use the distance of a vertex from
the start vertex (that means: a partial result of the search), to define elements of
the graphs that are still to be searched: The graph is a search-aware graph.

.. code-block:: python

    >>> def next_edges(vertex, traversal):
    ...     i, increment = vertex
    ...     if increment == 1:  # Base sequence
    ...         # Return edge to next number i+1, path length i+1
    ...         yield (i+1, 1), (i+1) - traversal.distance
    ...         if traversal.distance == i:  # i is prime
    ...             # (Is neither 1 nor reached via a multiples sequence)
    ...             # Then start sequence of i multiples at i*i, with
    ...             # distance advantage -0.5.
    ...             yield (i*i, i), i*i - i - 0.5
    ...     else:  # Multiples sequence
    ...         # Return edge to next multiple, with increment as weight
    ...         yield (i+increment, increment), increment
    ...         # Return edge to vertex for i of base sequence, length 0
    ...         yield (i, 1), 0

Now, we start the search at vertex *(1, 1)*, go till number 50, and print the found
primes.

.. code-block:: python

    >>> import itertools
    >>> traversal = nog.TraversalShortestPaths(next_edges).start_from((1, 1))
    >>> list(itertools.takewhile(lambda i: i<=50,  # Results up to 50
    ...      (i for i, factor in traversal  # Only the value of a vertex
    ...         if i == traversal.distance)))  # Only the primes
    [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]


