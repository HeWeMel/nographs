Search-aware graphs and start vertices
--------------------------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

During an already running graph traversal, further vertices and edges of
the graph and further start vertices
can be computed based on already available partial results of the same
traversal. This is possible due to the lazy-evaluation style of NoGraphs.
The following sections will explain this and show examples.

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
depth or already computed paths:
as shown `before <graphs_and_adaptation>`,
**you get a traversal object as second parameter**,
and **it provides state information to you**, that is valid in the context of the call
of your function.
This traversal object is of the same class as the traversal object that has been used
to start the traversal.
(Sometimes, it is even the same object, but in other cases, it is a separate object.)

.. Note::

    In the examples shown so far, we have already accessed
    state information when a found vertex is reported, e.g. the depth of this vertex.

    But for search-aware graphs, we
    **access state information when the callback function is called**
    and **use it to define further parts** of the graph - and the library allows for that.


.. _graph_pruning_by_search_depth:

**Example: Pruning a graph depending on search depth and start vertex**

We start with a very simple example:
The vertices of our graph are the integers. Successors of a vertex *v* are
*v+1* and *v+4*.
We have a set of start vertices, and for each of it, we want to compute the
vertices reachable in at most two steps along edges.

We want to use a breadth-first search. This search strategy guarantees that
the search depth (*traversal.depth*) of a vertex equals its depth, i.e., the
minimal number of edges that are necessary to reach it from the start vertex.
So, if *traversal.depth == 2* for some vertex, we do not want to follow
further edges.

We take this condition into the definition of the *next_vertices* function.
So, **we define a graph that, so to say,**
**automatically ends after two search steps**
**- depending of the vertex at which the search begins**.

.. code-block:: python

    >>> def next_vertices(v, traversal):
    ...     if traversal.depth == 2:
    ...         return []
    ...     return [v+1, v+4]

Now we carry out the search for each of the start vertices. We see, that we
get different results depending on the start vertex:
**The graph adapts to the search**.

.. code-block:: python

    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> for start_vertex in [10, 30, 40]:
    ...     print(f"{start_vertex}:",
    ...           list(traversal.start_from(start_vertex)))
    10: [11, 14, 12, 15, 18]
    30: [31, 34, 32, 35, 38]
    40: [41, 44, 42, 45, 48]

.. _eratosthenes_with_Dijkstra:

**Example: Sieve of Eratosthenes, reduced to Dijkstra search**

.. note::

    This example shows what is possible and why
    search-aware graphs open new possibilities.
    But it is a bit complicated.
    Since it is only an example, and does not introduce any other
    features of NoGraph you can safely skip it if you like.

We implement an infinite generator of primes based on the
`Sieve of Eratosthenes <https://en.wikipedia.org/wiki/Sieve_of_Eratosthenes>`_.
The special thing about it is: We implement it in the form of a search in an
infinite and search-aware graph.

We represent the elements of a sequence of numbers
*(j, j+increment, j+2\*increment, ...)*
by tuples *(i, increment)*. For example, the value *8* in sequence *4, 6, 8, 10...*
is represented by *(8, 2)*. These tuples are our vertices.

We start such a sequence, the *base sequence*, at *(1, 1)*. For each prime *i* that we
find, we start an additional sequence, a *multiples sequence*,
at *(i\*i, i)*. And we define edges that connect a vertex
*(i, increment)* of a multiples sequence with *(i, 1)* of the base sequence.

We choose the weights in such a way, that **the length (sum of edge weights)**
**of a path to a number equals**
**the number itself, if it is reached by the base sequence alone,**
**and slightly less, if the path goes through a multiples sequence**.
Here, we use the distance of a vertex from the start vertex
(that means: a partial result of the search), to define elements of
the graphs that are still to be searched: The graph is a search-aware graph.

If the shortest path from *(1, 1)* to some other vertex *(i, 1)* has a length
of *i*, we know that there is no (shorter) path using a multiples sequence, and thus,
that *i* is prime.

.. code-block:: python

    >>> def next_edges(vertex, traversal):
    ...     i, increment = vertex
    ...     if increment == 1:  # Base sequence
    ...         # Return edge to next number i+1, path length i+1
    ...         yield (i+1, 1), (i+1) - traversal.distance
    ...         if traversal.distance == i:  # i is prime
    ...             # (i is neither 1 nor reached via a multiples sequence)
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


In the tutorial section about `infinitely branching graphs <infinite_branching>`,
we will see a simplified version of this graph
(function `next_edges_prime_search <infinite_branching>`),
that shows the idea of the graph more directly.


.. _search_aware_start_vertices:

Search-aware start vertices
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not only a graph can be `search-aware <search_aware_graphs>`, but also
the start vertices. This is possible with *TraversalDepthFirst*
that implements the strategy depth-first search in the lazy
style of NoGraphs:

TraversalDepthFirst accepts an iterable as start vertices, like other
algorithms of NoGraphs. But it is special in that it fetches
a single start vertex at a time, traverses all vertices reachable from there,
and only then continues with the next start vertex. So, the
**computation of further start vertices can use**
**the partial search results available so far**.

In the following example, both the computation of further start vertices and
the computation of further edges depend on partial search results.

.. _iterative_deepening_dfs:

**Example: Iterative deepening depth-first search with just a single**
**run of TraversalDepthFirst**.

We use the graph and the function *next_vertices* from example
`Breadth First Search in a maze <example-traversal-breadth-first-in-maze>`
(see there for details), and want to get from field *S* to field *G*
by the shortest route (number of horizontal and/or vertical steps)
without entering the fields *\**:

::

    S*.*.
    .*...
    .*.*.
    ...*.
    .*.*G

..
  Repetition of the example from section Graphs and Adaptation. Does not
  go into docs.
  >>> def neighbors_in_grid(position):
  ...     pos_x, pos_y = position
  ...     for move_x, move_y in (-1, 0), (1, 0), (0, -1), (0, 1):
  ...         new_x, new_y = pos_x + move_x, pos_y + move_y
  ...         if new_x in range(5) and new_y in range(5):
  ...             yield new_x, new_y
  ...
  >>> def next_vertices(position, _):
  ...     for x, y in neighbors_in_grid(position):
  ...         # Report the neighbor position, if it is allowed to enter it
  ...         if not((x==1 and y!=3) or (x==3 and y!=1)):
  ...             yield (x, y)

But unlike in the example mentioned above, we will
not use a breadth-first search:
We want to avoid its bookkeeping
of the vertices that have been found at a specific depth and
of the vertices, that have already been visited.

Thus, we implement an
`iterative deepening depth-first search (IDDFS)
<https://en.wikipedia.org/wiki/Iterative_deepening_depth-first_search>`_:
We use the depth-first strategy to generate either
`paths or walks <dfs_all_paths_and_walks>` to reachable vertices.
We limit the search depth by limiting the length of the generated paths (resp. walks).
And we search several times, with an increasing limit for the search depth. So, when
we first find the / a goal vertex, we have found it following a shortest path.
When we are at a certain depth limit and recognize that a higher limit
would not lead to finding additional vertices, we know that we cannot find the / a goal
vertex in the graph.

If we generate
`paths <dfs_all_paths_and_walks>`
in an IDDFS, we avoid the effort of generating walks that are no paths.
If we generate
`walks <dfs_all_paths_and_walks>`,
we avoid using memory for storing the vertices that are on the
current path. Thus, we implement both options.

IDDFS can search paths from any vertex of a set of start vertices to any vertex
of a set of goal vertices. We also implement this flexibility.

The special thing about the following implementation of the IDDFS is:

1)  The start vertices for the search
    are provided by a generator (here: function *start_vertices*),
    that yields the original start vertices several time,
    but each time with an increased search depth. And its stops to do so when
    the search with the current depth limit could not detect further vertices that
    require a higher limit.

2)  The NextVertices function *next_vertices_pruned* implements the
    depth restriction based on the depth limit set within *start_vertices*. And
    it detects whether increasing the limit would result in further vertices
    (variable *successors_over_depth_limit*)
    - information, that *start_vertices* uses to decide when to stop going deeper.

This means, during the search, **the computation of start vertices and the**
**computation of edges communicate and adapt to results of each other.**

From the perspective of NoGraphs, we do **a single depth-first search**, in
**a graph that always grows when the search continues with the next start vertex.**
And the stream of **start vertices ends, when the graph cannot grow any more**.

.. code-block:: python

    >>> def iterative_deepening_dfs(start_vertices, goal_vertices, next_vertices, mode):
    ...     depth_limit = 0
    ...     successors_over_depth_limit = True
    ...
    ...     def start_vertices_of_the_search():
    ...         nonlocal depth_limit, successors_over_depth_limit
    ...         while successors_over_depth_limit:
    ...             successors_over_depth_limit = False
    ...             yield from start_vertices
    ...             depth_limit += 1
    ...
    ...     def next_vertices_pruned(v, traversal):
    ...         nonlocal successors_over_depth_limit
    ...         depth = len(traversal.trace) - 1
    ...         if depth < depth_limit:
    ...             yield from next_vertices(v, None)
    ...         elif not successors_over_depth_limit:
    ...             for successor in next_vertices(v, None):
    ...                 successors_over_depth_limit = True
    ...                 break
    ...
    ...     traversal = nog.TraversalDepthFirst(next_vertices_pruned)
    ...     _ = traversal.start_from(start_vertices=start_vertices_of_the_search(),
    ...                              compute_trace=True, mode=mode, report=nog.DFSEvent.ENTERING)
    ...     for v in traversal.go_for_vertices_in(goal_vertices, fail_silently=True):
    ...         return traversal.trace
    ...     return []

Now, we start the search: First based on walks and then based on paths.

.. code-block:: python

    >>> iterative_deepening_dfs([(0, 0)], {(4, 4)}, next_vertices, mode=nog.DFSMode.ALL_WALKS) # doctest: +NORMALIZE_WHITESPACE
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1),
    (4, 2), (4, 3), (4, 4)]

    >>> iterative_deepening_dfs([(0, 0)], {(4, 4)}, next_vertices, mode=nog.DFSMode.ALL_PATHS) # doctest: +NORMALIZE_WHITESPACE
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1),
    (4, 2), (4, 3), (4, 4)]


For comparison, a more conventional implementation of the same algorithm is
given below, which works without search-aware start_vertices and next_vertices.
It starts a new search each time the search depth limit is increased.

.. code-block:: python

    >>> import itertools
    >>> def iterative_deepening_dfs(start_vertices, goal_vertices, next_vertices, mode):
    ...     traversal = nog.TraversalDepthFirst(next_vertices)
    ...     for depth_limit in itertools.count(0):
    ...         generator = iter(traversal.start_from(
    ...             start_vertices=start_vertices, compute_trace=True,
    ...             mode=mode, report=nog.DFSEvent.ENTERING))
    ...         successors_over_depth_limit = False
    ...         for v in generator:
    ...             if v in goal_vertices:
    ...                 return traversal.trace
    ...             if (depth:=len(traversal.trace)-1) == depth_limit:
    ...                 _ = generator.throw(StopIteration())
    ...                 if not successors_over_depth_limit:
    ...                     for successor in next_vertices(v, None):
    ...                         successors_over_depth_limit = True
    ...                         break
    ...         if not successors_over_depth_limit:
    ...             return []

Of cause, we get the same results:

.. code-block:: python

    >>> iterative_deepening_dfs([(0, 0)], {(4, 4)}, next_vertices, mode=nog.DFSMode.ALL_WALKS) # doctest: +NORMALIZE_WHITESPACE
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1),
    (4, 2), (4, 3), (4, 4)]

    >>> iterative_deepening_dfs([(0, 0)], {(4, 4)}, next_vertices, mode=nog.DFSMode.ALL_PATHS) # doctest: +NORMALIZE_WHITESPACE
    [(0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1), (4, 1),
    (4, 2), (4, 3), (4, 4)]
