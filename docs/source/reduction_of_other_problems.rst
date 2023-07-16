Problem reduction - the lazy way
--------------------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

The concept
~~~~~~~~~~~

Often, we can solve some type of problem by building upon algorithms
that solve other types of problems (*problem reduction*), e.g.,
we can compute the *cosine* of some angle *a* by computing the *sine* of
*a + π/2*.

When we apply problem reduction to graph analysis, three kinds of
computations can be distinguished (they do not need to happen strictly
consecutive):

1) From the original analysis problem, we construct one or more other
   analysis problems.

2) We solve these problems by existing algorithms.

3) Based on their results, we construct a result of the original analysis problem.

When we use NoGraphs in the above computation part 2, we can try to
**extend the lazy computation approach** of NoGraphs
**to other computations of the problem reduction**:

- In part 1, we might **construct the derived problems on the fly**, only when they
  are needed and **as far as they are needed in part 2**.

- In part 3, we might **fetch results from part 2** only when, and
  **as far as, they are needed** to construct the final results.

This can help to reduce the needed runtime and memory. And it can be used to create
a kind of graph analysis that is even more "lazy" than that of NoGraphs alone.
Both is demonstrated in the following sections.


.. _traveling_salesman_example:

Example: Traveling salesman - solved by Dijkstra Shortest Paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**The problem**

In a weighted, directed graph, we search for a path from some vertex back to itself.
The path needs to visit all vertices exactly once. The length
of the graph (sum of edge weights) needs to be minimal under all such paths.
This is an instance of the
`traveling salesman problem <https://en.wikipedia.org/wiki/Travelling_salesman_problem>`_.

We use the graph data shown below as example: The graph has 17 vertices numbered from 0
to 16. It is a complete graph, i.e., each vertex is connected with all other vertices.
The weight of an edge from a vertex *v* to another vertex *w* is given by the value
in row *v* (top down) and column *w* (left to right).
The character '-' stands for value 9999 (it has been replaced for better readability).

This example data stems from the *TSPLIB*, a collection of benchmark instances
of the traveling salesman problem, provided by the University of Heidelberg
(see http://comopt.ifi.uni-heidelberg.de/software/TSPLIB95/).

.. code-block:: python

    >>> data_of_TSP_br17 = """\
    ...  -  3  5 48 48  8  8  5  5  3  3  0  3  5  8  8  5
    ...  3  -  3 48 48  8  8  5  5  0  0  3  0  3  8  8  5
    ...  5  3  - 72 72 48 48 24 24  3  3  5  3  0 48 48 24
    ... 48 48 74  -  0  6  6 12 12 48 48 48 48 74  6  6 12
    ... 48 48 74  0  -  6  6 12 12 48 48 48 48 74  6  6 12
    ...  8  8 50  6  6  -  0  8  8  8  8  8  8 50  0  0  8
    ...  8  8 50  6  6  0  -  8  8  8  8  8  8 50  0  0  8
    ...  5  5 26 12 12  8  8  -  0  5  5  5  5 26  8  8  0
    ...  5  5 26 12 12  8  8  0  -  5  5  5  5 26  8  8  0
    ...  3  0  3 48 48  8  8  5  5  -  0  3  0  3  8  8  5
    ...  3  0  3 48 48  8  8  5  5  0  -  3  0  3  8  8  5
    ...  0  3  5 48 48  8  8  5  5  3  3  -  3  5  8  8  5
    ...  3  0  3 48 48  8  8  5  5  0  0  3  -  3  8  8  5
    ...  5  3  0 72 72 48 48 24 24  3  3  5  3  - 48 48 24
    ...  8  8 50  6  6  0  0  8  8  8  8  8  8 50  -  0  8
    ...  8  8 50  6  6  0  0  8  8  8  8  8  8 50  0  -  8
    ...  5  5 26 12 12  8  8  0  0  5  5  5  5 26  8  8  -
    ... """


With the following code, we extract the values from the data as a list of lists of
integers, and undo the mentioned replacement.

.. code-block:: python

   >>> graph = [[int(weight) if weight != "-" else 9999 for weight in line.split()]
   ...           for line in data_of_TSP_br17.splitlines()]


**The algorithm**

For solving problems like the given one, we define the following function
*demo_traveling_salesman*.
It implements a problem reduction in the three parts explained above. The
traveling salesman problem is reduced to a single source shortest paths problem
in a search graph.

Part 1: It defines a new graph as follows, in the lazy style of NoGraphs:

- A **vertex** in the new graph is a state of our search in the original graph. Such a
  state consists of a
  **tuple** of the **current vertex** and the
  **set of vertices that are still to be visited.**
- An **edge** in the new graph is the
  **transition from a search state to one of the possible next search states**, where
  we have chosen one of the vertices we still had to visit, with the weight according
  to the input graph, and a next state, that consists of the chosen vertex and the
  set of vertices still to be visited when we have visited the chosen one.
  When there is no further vertex to visit any more, there is just one edge from
  the current vertex, and this leads back to the start vertex.

Part 2: It applies `TraversalShortestPaths` on this graph, starting at a start state
that consists of vertex 0 (an arbitrary choice) and the set of all other vertices
as the vertices still to be visited.

It finds the shortest path and its weight when it reaches the first state in a search
depth that equals the number of vertices of the original graph, because
*TraversalShortestPaths* reports paths ordered by ascending length.

Part 3: The length of the computed path is directly the length of the shortest
traveling salesman path. And in each state of the computed path, we find the vertex
visited in this state. So, we can create the path that solves the traveling salesman
problem by extracting these vertices.

(Currently, I call this the *Melcher reduction from TSP to Dijkstra shortest paths*.
Most probably, the algorithm already exists somewhere in the literature. But maybe
not :-). Please inform me if you know a reference.)


.. code-block:: python

   >>> def demo_traveling_salesman(graph):
   ...    # Part 1: Construct a suitable shortest paths problem - the lazy way
   ...    no_of_vertices = len(graph)
   ...    start_vertex = 0
   ...    set_with_start_vertex = frozenset((start_vertex,))
   ...    vertices_to_visit_at_start = frozenset(range(1, no_of_vertices))
   ...
   ...    start_state = (start_vertex, vertices_to_visit_at_start)
   ...
   ...    def next_states(state, _):
   ...        from_vertex, vertices_to_visit = state
   ...        edges_from_here = graph[from_vertex]
   ...        vertices_to_visit_next = (vertices_to_visit if vertices_to_visit
   ...                                  else set_with_start_vertex)
   ...        for to_vertex in vertices_to_visit_next:
   ...            weight = edges_from_here[to_vertex]
   ...            yield ((to_vertex, vertices_to_visit.difference((to_vertex,))), weight)
   ...
   ...    # Part 2: Solve it using the lazy implementation of the Dijkstra algorithm
   ...    traversal = nog.TraversalShortestPaths(next_states)
   ...    for vertex in traversal.start_from(start_state, build_paths=True):
   ...
   ...        # Stop the computation when we have what we need
   ...        if traversal.depth == no_of_vertices:
   ...            # Part 3: Construct the results (and some statistics)
   ...            length = traversal.distance
   ...            path = (v for (v, s) in traversal.paths.iter_vertices_from_start(vertex))
   ...            no_of_visited_states = len(traversal.distances)
   ...            no_of_possible_states = no_of_vertices * (2 ** no_of_vertices)
   ...            return length, path, no_of_visited_states / no_of_possible_states
   ...    raise RuntimeError("No solution found")


**Applying the algorithm**

Now, we call *traveling_salesman* to solve our problem:

.. code-block:: python

   >>> length, path_iterator, percentage_visited = demo_traveling_salesman(graph)
   >>> print(length, list(path_iterator), f"{percentage_visited:.0%}")
   39 [0, 11, 13, 2, 12, 10, 9, 1, 16, 8, 7, 4, 3, 15, 14, 6, 5, 0] 23%


The described algorithm profits from the fact that the Dijkstra algorithm implemented
by *TraversalShortestPaths* visits only the vertices (here: search states) that need to
be visited in order to report shortest paths in ascending order - and we can stop the
computation immediately when we first found a complete loop.
This means,
**due to the lazy approach of NoGraphs,** the
traveling salesman **search graph is often only partially build**.
In the example, only 23% of the possible search states (and their outgoing edges)
have been generated.
This adds up with the advantage of NoGraphs, that edges are generated and
consumed on the fly, but they are not stored.

Note: Dynamic programming algorithms can also show these two advantages - but
explicit graphs as used by typical graph libraries cannot provide them.

.. _tsp_in_nographs:

**The TSP-solving function in the extras section of NoGraphs**

.. versionchanged:: 3.3

   traveling_salesman added.

NoGraphs contains a function *traveling_salesman(vertices, weights)*,
a more general version of the above algorithm
(see `API  <nographs.traveling_salesman>`):

- It can also handle **negative edge weights**,
- can also search for the **longest TSP path**, and
- can search for TSP **tours in subsets of the vertices** of a graph.
- Weights can be given in several forms:
  **Nested tuples, nested lists or nested dicts**. And
  **None as weight, or raising an exception on accessing a weight signals**
  **having no edges** from the respective vertex or between the
  respective vertices.

Its implementation is also more optimized:

- It is based on the bidirectional search `BSearchShortestPath` instead of
  the traversal `TraversalShortestPaths`.
- Internally, it uses bit arrays instead of sets and tuples as representation
  of search states.

In the following, we apply it to the `above problem <traveling_salesman_example>`:

.. code-block:: python

   >>> length, path_iterator = nog.traveling_salesman(range(len(graph)), graph)
   >>> print(length, list(path_iterator))
   39 [0, 5, 6, 14, 15, 3, 4, 16, 8, 7, 12, 10, 9, 1, 13, 2, 11, 0]

Of cause, it computes the same optimal TSP path length. But it returns another path of
this length here: there are several optimal TSP routes for the problem.

Please note: For computing exact solutions of large TSP instances like they occur in
real-life scenarios, highly elaborated, specialized algorithms on very performant
platforms are needed.
`nographs.traveling_salesman` can only solve relatively small instances
(with maybe up to 60 vertices), although, typically, it is faster than
schoolbook-implementations of
the `Held-Karp algorithm <https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm>`_.


.. _infinite_branching:

Example: Shortest paths in infinitely branching graphs with sorted edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**The Problem**

We have the following graph, defined on the positive integers as
vertices. We like to start at vertex 1, iterate the shortest
paths from there in ascending order, and report vertices with a distance that equals
the vertex itself. We will explain the purpose later on.

First, let's have a look on the graph:

.. code-block:: python

   >>> import itertools
   >>> def next_edges_prime_search(i, distance):
   ...     yield i+1, (i+1) - distance
   ...     if i > 1:
   ...         for i_next in itertools.count(i*i, i):
   ...             yield i_next, (i_next - distance) - 0.5

For vertices larger than 1, the graph has
**infinitely many outgoing edges per vertex** (see the *for*-loop).
This is called an *infinitely branching graph*.
NoGraphs itself cannot analyze such graphs.

But still, we can analyze the graph using NoGraphs - in combination with problem
reduction:

We search in a search graph, not directly in the given graph. The idea of the
search graph is, that **instead of having infinitely many edges** starting
at a vertex, we have an
**infinite chain of vertices** starting there, and
**from each of these, a single edge** to
an end vertex of one of the original edges.
The vertices in such a chain are connected by edges with lengths that
equal the **length difference** between consecutive edges of the original graph.
We get non-negative edge lengths because the original edges where given in ascending
order.

Here is the mapping:

- The vertices of the search graph are states of our search in the original graph.
  Such a state is a tuple (*vertex*, *edge_no*), where *vertex* is a vertex of the
  original graph, and *edge_no* is the number of an outgoing edge of this vertex.
- Edges in the search graph go from (*vertex*, *edge_no*) both to:

  - (*vertex*, *edge_no* + 1), i.e., we continue to further edges starting at *vertex*,
    and
  - (*end_vertex*, 0), i.e., we continue to the end vertex of the current edge.

In the following, you find the code for the problem reduction. For the
purpose of this section, it suffices to understand the idea as described above.
The details of the code are not needed.

.. code-block:: python

   >>> def traversal_shortest_paths_inf_branching_sorted(next_edges_inf, start):
   ...     """Dijkstra single source shortest paths for infinite graphs with infinite
   ...     branching, where the edges per vertex are iterable and sorted by ascending
   ...     length.
   ...     :param next_edges_inf: Graph, given as function from a vertex and a distance
   ...         to an iterable of edges, where an edge is given as tuple
   ...         (next_vertex, edge_length).
   ...     :param start: The vertex to start the traversal at.
   ...     :return: A generator that iterates tuples(vertex, distance), where distance
   ...         is the length (sum of edges weights) of the shortest path to vertex,
   ...         with ascending distances.
   ...     """
   ...     def next_edges(state, traversal):
   ...         vertex, edge_no = state
   ...         base_state = (vertex, 0)  # state representing "vertex entered"
   ...         base_state_distance = traversal.distances[base_state]  # distance there
   ...         if edge_no == 0:
   ...              # In the base state of vertex, start the iteration through its edges
   ...              iterator = next_edges_inf(vertex, base_state_distance)
   ...              state_iterators[vertex] = iterator
   ...         else:
   ...              # In other states, continue iterating though the edges of vertex
   ...              iterator = state_iterators[vertex]
   ...         try:
   ...              # Get end vertex and length of next edge from vertex
   ...              next_vertex, length_from_base = next(iterator)
   ...              # Transform length and distance to those in search graph
   ...              next_distance = length_from_base + base_state_distance
   ...              state_distance = traversal.distances[state]
   ...              state_edge_length = next_distance - state_distance
   ...              # Edge to synthetic vertex that stands for "next vertex, first edge"
   ...              yield (next_vertex, 0), state_edge_length
   ...              # Edge to synthetic vertex that stands for "same vertex, next edge"
   ...              yield (vertex, edge_no + 1), state_edge_length
   ...         except StopIteration:
   ...             # The iterator gave us all edges from vertex. We can delete it now.
   ...             del state_iterators[vertex]
   ...
   ...     # Mapping from vertex to edge iterator
   ...     state_iterators = dict()
   ...     # Generate shortest paths starting at state "start vertex, first edge"
   ...     traversal = nog.TraversalShortestPaths(next_edges)
   ...     _ = traversal.start_from((start, 0), keep_distances=True)
   ...     # Extract vertices from the reported base states "vertex, first edge"
   ...     return ((v, traversal.distance) for v, edge_no in traversal if edge_no == 0)


Based on this implementation of the problem reduction, we can now solve our given problem:

.. code-block:: python

   >>> t = traversal_shortest_paths_inf_branching_sorted(next_edges_prime_search, 1)
   >>> primes = (i for i, distance in t if i == distance)

And what we get is: An infinite generator of primes. Let's test it:

.. code-block:: python

   >>> from itertools import takewhile
   >>> list(takewhile(lambda i: i<=50, primes))
   [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

The graph defined above and the filter *i == distance* is an alternative
implementation of the idea described in section `search_aware_graphs`.
Please see there, if you like to know how it works.


.. tip::

    When defining and using complex problem reductions, it is recommended to develop not
    only the code, but also some kind of correction proof. For the given example, this
    could look like the following (briefly sketched):

    - Well-defined graph for shortest paths computation:

      The edge weight of the first computed edge per vertex is non-negative. Thus,
      also the weight of the respective edge of the synthetic graph is non-negative.

      And the original graph computes its edges for a given (positive) vertex in
      ascending order. Thus, the edge weights of the synthetic graph, that are computed
      as difference of two consecutive edge weights of the original graph, are also
      all positive.

      So, it is allowed to apply the Dijkstra single source shortest paths algorithm.

    - Correctness of the problem reduction:

      By duality of the original graph and the synthetic graph.

      This means: Since we get correct results by the Dijkstra algorithms, we also
      get correct results by the problem reduction.

    - Next result requires only a finite number of computation steps:

      We know, that for the n-th prime *p_n*, with *n > 1*, the (n+1)-th prime
      *p_m* is lower than *2*p_n*
      (`Bertrand's postulate <http://en.wikipedia.org/wiki/Bertrand%27s_postulate>`_).
      But what we still need to make sure is, that if we compute a shortest
      path to each of the numbers *p_n*, *p_n + 1*, ..., *p_m*, each of these
      computations requires only finitely many computation steps.

      We know: All edges of the original graph have weights that are larger than a
      fixed lower bound, here, their weights are at least 0.5. So, when the next
      vertex with the next longer distance is computed, the search
      graph to be regarded contains only finitely many vertices and edges.
      And in such a case, the Dijkstra algorithm needs only finitely many
      computation steps to produce the next shortest path (resp. its end vertex
      and distance from the start).

.. _infinite_branching_in_nographs:

**Functionality for infinitely branching graphs in the extras section of NoGraphs**

.. versionchanged:: 3.3

   TraversalShortestPathsInfBranchingSorted added.

NoGraphs contains a class *TraversalShortestPathsInfBranchingSorted*,
a more general version of the above algorithm
(see `API  <nographs.TraversalShortestPathsInfBranchingSorted>`).
Its signature is more adapted to the other classes in NoGraphs, and it can also
generate paths.

In the following, we apply it to the `above problem <infinite_branching>`:

.. code-block:: python

   >>> import itertools
   >>> def next_edges_prime_search(i, t):
   ...     distance = t.distance
   ...     yield i+1, (i+1) - distance
   ...     if i > 1:
   ...         for i_next in itertools.count(i*i, i):
   ...             yield i_next, (i_next - distance) - 0.5

.. code-block:: python

   >>> t = nog.TraversalShortestPathsInfBranchingSorted(next_edges_prime_search)
   >>> from itertools import takewhile

.. code-block:: python

   >>> _ = t.start_from(1)
   >>> primes = (i for i in t if i == t.distance)
   >>> list(itertools.takewhile(lambda i: i <= 50, primes))
   [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]

No, we also ask for paths, and report the predecessor of each non-prime number as
(one of) its divisors. We go till 20.

.. code-block:: python

   >>> _ = t.start_from(1, build_paths=True)
   >>> path_to_start = t.paths.iter_vertices_to_start
   >>> non_primes = (i for i in t if i != t.distance)
   >>> non_primes_till_20 = itertools.takewhile(lambda i: i <= 20, non_primes)
   >>> for i in non_primes_till_20:
   ...    path_iter = path_to_start(i)
   ...    _, predecessor = next(path_iter), next(path_iter)
   ...    print(i, predecessor)
   4 2
   6 2
   8 2
   9 3
   10 2
   12 3
   14 2
   15 3
   16 4
   18 3
   20 4
