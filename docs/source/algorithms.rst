_`Traversal algorithms`
-----------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

Based on you NextVertices or NextEdges function,
NoGraphs gives you **traversal algorithms in the form
of iterators**.
You can use them to **traverse your graph** following some specific traversal
strategy and to compute values like depths, distances, paths and trees.

Classes for all graphs
~~~~~~~~~~~~~~~~~~~~~~

The following classes can be used both for graphs
with `labeled edged <labeled_graphs>` and for graphs with
`unlabeled edges <unlabeled_graphs>`. See the respective
class documentation in the API reference for details.

- Class `nographs.TraversalBreadthFirst`

    - Algorithm *Breadth First Search* ("BFS").

    - Visits and reports vertices in *breadth first order*, i.e., **with ascending
      depth** (the depth of a vertex is the edge count of the path with least edges
      from a start vertex).

    - The traversal state provides **vertex depth** / **search depth**, **paths**,
      and set of **visited vertices**.

    - Examples: See `example-traversal-breadth-first-in-maze` and
      `example-traversal-breadth-first-towers-hanoi`.

- Class `nographs.TraversalDepthFirst`

    - Algorithm *Depth First Search* ("DFS").

    - Follows just one outgoing edge per vertex as long as possible,
      and **goes back a step to some already visited vertex and follows a
      further edge starting there only when necessary** to come to new vertices.

    - The traversal state provides **search depth**, **paths**,
      and set of **visited vertices**.

    - Example: See `example-traversal-depth-first-integers`.

- Class `nographs.TraversalTopologicalSort`

    - Algorithm *Topological Sort*.

    - Visits vertices using DFS (see above), but reports the vertices in the
      steps backwards, i.e. **from successors to predecessors**. This only works
      if the graph does not contain a cycle on a path from a start vertex, because
      otherwise, each two vertices on the cycle are both (indirect) successors and
      (indirect) predecessors of each other. If there is such a cycle in the
      graph, this is detected.

    - The traversal state provides **search depth**, **paths**, and set of
      **visited vertices**.

    - Example: See `example-topological_sorting_processes`.

.. _examples_all_graphs:

**Comparing example:**

We define a graph with the following edges: From vertex 0, edges lead to vertices
1 and 2, and from each of those, edges lead to vertex 3.

.. code-block:: python

    >>> edges = {0: (1, 2), 1: (3,), 2: (3,)}
    >>> def next_vertices(vertex, _):
    ...     return edges.get(vertex, ())

Then, we compare, how the three strategies traverse the graph starting
from vertex 0.

.. code-block:: python

    >>> list(nog.TraversalBreadthFirst(next_vertices).start_from(0))
    [1, 2, 3]

As you can see, TraversalBreadthFirst starts by exploring the two
vertices 1 and 2 that can be reached directly from vertex 0. Only then, it
goes deeper to vertex 3.

.. code-block:: python

    >>> list(nog.TraversalDepthFirst(next_vertices).start_from(0))
    [2, 3, 1]

TraversalDepthFirst explores vertex 2 and goes directly deeper to vertex 3.
Then, it goes backwards till, at vertex 0, it finds an edge to a further
vertex, here vertex 1.

.. code-block:: python

    >>> list(nog.TraversalTopologicalSort(next_vertices).start_from(0))
    [3, 2, 1, 0]

TraversalTopologicalSort reports the vertices in such an order,
that for each edge of the graph, the successor is reported before the
predecessor.


Classes for weighted graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following classes can be used for
graphs with `weighted edged <labeled_graphs>`. See the
respective class documentation in the API reference for details.

- Class `nographs.TraversalShortestPaths`

    - Algorithm of *Dijkstra*. All weights need to be non-negative.

    - Traverses your graph
      **from short to long distances (minimal sum of edge weights)** from
      some start vertices.

    - The traversal state provides **vertex distance**, **search depth**, **paths**
      and **distances**.

    - Examples: See `example-shortest-paths-in-maze`,
      `Sieve of Eratosthenes <eratosthenes_with_Dijkstra>`,
      and `the examples below <examples_weighted_graphs>`.

- Class `nographs.TraversalAStar`

    - Algorithm *A\**. All weights need to be non-negative.
      **Admissible heuristic function to goal vertex needed**
      (for details, see the API reference for the class).

    - **Finds the shortest path (minimal sum of edge weights)** from one of the start
      vertices to the goal vertex.

    - The traversal state provides **path length**, **search depth** and **paths**.
      For the goal vertex, the path length is the length of the shortest path
      (distance from a start vertex).

    - Examples: See `example-shortest-paths-with-heuristic`
      and `the examples below <examples_weighted_graphs>`.

- Class `nographs.TraversalMinimumSpanningTree`

    - Algorithm of **Jarnik, Prim, Dijkstra**. For undirected edges. These
      edges need to be given as directed edges with the same weight in both
      directions.

    - Traverses your graph s.t. the traversed edges form a minimum spanning tree,
      i.e., each vertices reachable in the graph is also reachable in the tree,
      and there is no other such tree, that has a smaller total of edge weights
      than the found tree.

    - The traversal state provides **edge** and **paths**.

    - Example: See `the examples below <examples_weighted_graphs>`.

.. _examples_weighted_graphs:

**Comparing example:**

Like in the previous section, we define a graph with the following edges:
From vertex 0, edges lead to vertices 1 and 2, and from each of those, edges
lead to vertex 3.

This time, we assign weights to the edges: Each edge has weight 2,
but for the edge from vertex 0 to vertex 2, we choose 1 as weight.

.. code-block:: python

    >>> edges = {0: ((1,2), (2,1)), 1: ((3,2),), 2: ((3,2),)}
    >>> def next_edges(vertex, _):
    ...     return edges.get(vertex, ())

Then, we compare how the three strategies traverse the graph starting from
vertex 0 till vertex 3:

.. code-block:: python

    >>> traversal = nog.TraversalShortestPaths(next_edges).start_from(0)
    >>> for vertex in traversal:
    ...    print(vertex, traversal.distance)
    ...    if vertex == 3: break
    2 1
    1 2
    3 3

As you can see, TraversalShortestPaths reports vertices in ascending
distance. As a consequence, it has to evaluate vertex 1 before going to
vertex 3. This way, it can be sure to have already found the best starting
point to go to vertex 3 before doing this step.

.. code-block:: python

    >>> def heuristic(v):
    ...    return {0:3, 1:2, 2:2, 3:0}[v]
    >>> traversal = nog.TraversalAStar(next_edges).start_from(heuristic, 0)
    >>> for vertex in traversal:
    ...    print(vertex)
    ...    if vertex == 3: break
    2
    3
    >>> traversal.path_length
    3

TraversalAStar can make use of function *heuristic* that gives an estimation
of the distance (minimally needed sum of edge weights) to the goal, and that
guarantees to never overestimate the distance (*admissible heuristic*). With
this help, TraversalAStar knows that the path through vertex 2 (total edge
weight of 1 + 2 = 3) is shorter than the path through vertex 1
(distance 2 + admissible estimation of 2 = 4
as minimum) and avoids to further explore the path over vertex 1.

.. code-block:: python

    >>> traversal = nog.TraversalMinimumSpanningTree(next_edges).start_from(0)
    >>> for vertex in traversal:
    ...    print(vertex, traversal.edge)
    ...    if vertex == 3: break
    2 (0, 2, 1)
    1 (0, 1, 2)
    3 (2, 3, 2)

TraversalMinimumSpanningTree chooses and reports edges in such a way, that
together, they form a minimum spanning tree: Vertices 0, 1, 2, 3 can all
be reached in the tree when starting from vertex 0. The total edge weight
of the tree is 1 + 2 + 2 = 5, and there is no other spanning tree with
smaller edge weight: We cannot leave out the edges to vertices 1 and 2,
because they would become unreachable. And we cannot use the edge from
vertex 1 to vertex 3 instead of the chosen one from 2 to 3, because this
would increase the total edge weight.


.. _methods:

States and standard methods of traversal objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section explains the lifecycle of traversal objects, and in which
state which methods can be used.
See the API reference of the `traversal classes <traversal-classes-api>` for
further details about methods and signatures.

- **Instantiation** of a traversal class, leading to state *created*

  - In this step, you **define what graph** should be traversed
    (you provide a `NextEdges` or a `NextVertices` function).

  - Optionally, you define some specific **graph properties** (see
    `identity and equivalence of vertices <vertex-identity>`
    and `traversing trees <is_tree>`).


  The traversal object stores this data.

  Example:

  .. code-block:: python

   >>> def next_vertices(i, _):
   ...     return [2*i] if abs(i)<512 else []

   >>> traversal = nog.TraversalBreadthFirst(next_vertices)


- State **created** (inactive)

  In this state, you cannot use any of the iterator methods of the traversal object:

  .. code-block:: python

     >>> next(traversal)
     Traceback (most recent call last):
     RuntimeError: Traversal not started, iteration not possible

.. _general-start_from:

- **Starting** a traversal, leading to state *started*

  You (re-) start the traversal by calling its method **start_from(...)**:

  - You **choose one or more start vertices**.
  - Optionally, you choose between some **traversal options**, e.g., that paths
    should be created, and - for labeled edges - whether the labels are to be
    reported in the paths, and whether there should be a calculation limit for
    the traversal

  .. code-block:: python

     >>> traversal = traversal.start_from(1)

  The traversal object creates an iterator (*base iterator*) that is able to
  traverse your graph starting at your start vertices and following the class
  specific traversal strategy.

  .. tip::

     The method *start_from* returns the traversal object itself to allow for
     direct calls of other methods, like in
     *traversal.start_from(...).go_to(...))*.

- State **started** (active)

  In this state, you can use the **iterator methods of the traversal object**:

  - It is *Iterable*, i.e., you can use it in statements like
    **for ... in traversal**
    (see method `__iter__ <Traversal.__iter__>`).

  - It is an *Iterator*, and you can use **next(traversal)** to iterate it (see
    method `__next__ <Traversal.__next__>`).

  - Method **go_to(vertex)** (see `here <Traversal.go_to>`) walks through the graph,
    stops at *vertex* and returns it. If the traversal ends without having
    found *vertex*, exception *KeyError* is raised (or *None* is returned,
    if you decided for silent fails).

  - Method **go_for_vertices_in(vertices)**
    (see `here <Traversal.go_for_vertices_in>`) returns an iterator
    that fetches vertices from the base iterator, skips each vertex that is
    not given in the *vertices* and stops when all *vertices* have been found
    and reported. Fails are handled like described for method *go_to*.

  Each (partial) iteration will **continue the traversal** where the
  previous one has ended.

  **When a vertex is reported, specific attributes of the traversal contain
  additional data** about the state of the traversal (see the
  API reference of the `traversal classes <traversal-classes-api>`).

  .. code-block:: python

     >>> print(next(traversal), traversal.depth)
     2 1

     >>> for vertex in traversal:
     ...     print(vertex, traversal.depth)
     ...     if vertex == 8: break
     4 2
     8 3

     >>> # Skip till 32, report till 64
     >>> for vertex in traversal.go_for_vertices_in([128, 32]):
     ...     print(vertex, traversal.depth)
     32 5
     128 7

  At any time, you **can restart the traversal** at the same or some
  other start vertices.

  .. code-block:: python

     >>> _ = traversal.start_from(-32, build_paths=True).go_to(-128)
     >>> for vertex in reversed(sorted(traversal.visited)):
     ...     print(traversal.paths[vertex])
     (-32,)
     (-32, -64)
     (-32, -64, -128)

  .. tip::

     Typically, Python's standard mechanisms for working with iterables
     are well suited for traversing graphs with NoGraphs traversal objects:
     *Comprehensions* (optionally with vertex or state filters in *if* conditions)
     and loops like *for...if ... break* are flexible, easy to use and understand,
     and fast.

     NoGraphs offers specialized methods like *go_to* and *go_for_vertices_in*
     and the methods explained in section `class_specific_methods`
     only when there are good reasons for this.

- State **exhausted** (inactive)

  When the traversal has iterated through all vertices that are reachable from
  your chosen start vertices, the iterator is exhausted. Upon calls, it raises
  a *StopIteration* exception. This ends loops like the *for* loop.

  You can still start the traversal again, if you like.

  .. code-block:: python

     >>> # iterator will be exhausted after vertex -512
     >>> for vertex in traversal:
     ...     print(vertex, traversal.depth)
     -256 3
     -512 4

     >>> next(traversal)
     Traceback (most recent call last):
     StopIteration

.. _class_specific_methods:


Methods for depth and distance ranges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two traversal classes offer additional iteration methods that focus on ranges of
vertex depths or distances. These are the following:

- `TraversalBreadthFirst.go_for_depth_range(start, stop)
  <nographs.TraversalBreadthFirst.go_for_depth_range>`

  For a started traversal, the method returns an iterator. During the traversal, the
  iterator skips vertices as long as their depth is lower than *start*. From then on,
  it reports the found vertices. It stops when the reached depth is higher than *stop*.

  Note: The first vertex with a depth higher than *stop* will be consumed from the
  traversal, but will not be reported, so it is lost (compare *itertools.takewhile*).

  .. _example_go_for_depth_range:

  **Example:**

  In the following graph of integers, each integer *i* is connected to
  *i + 2*. We search for vertices with depth in *range(10, 20)*:

  .. code-block:: python

     >>> def next_vertices(vertex, _):
     ...     return vertex + 2,
     >>> traversal = nog.TraversalBreadthFirst(next_vertices)
     >>> tuple(traversal.start_from(0).go_for_depth_range(10, 20))
     (20, 22, 24, 26, 28, 30, 32, 34, 36, 38)

- `TraversalShortestPaths.go_for_distance_range(start, stop)
  <nographs.TraversalShortestPaths.go_for_distance_range>`

  For a started traversal, the method returns an iterator. During the traversal, the
  iterator skips vertices as long as their distance is lower than *start*. From
  then on, is reports the found vertices. It stops when the reached distance is
  higher than *stop*.

  Note: The first vertex with a distance higher than *stop* will be consumed from the
  traversal, but will not be reported, so it is lost (compare *itertools.takewhile*).

  .. _example_go_for_distance_range:

  **Example:**

  In the following graph of integers, consecutive integers are connected
  by edges of weight 2. We search for vertices with distances in *range(20, 40)*:

  .. code-block:: python

     >>> def next_edges(vertex, _):
     ...     return (vertex+1, 2),
     >>> traversal = nog.TraversalShortestPaths(next_edges)
     >>> tuple(traversal.start_from(0).go_for_distance_range(20, 40))
     (10, 11, 12, 13, 14, 15, 16, 17, 18, 19)


.. _is_tree:

Traversing trees
~~~~~~~~~~~~~~~~

If you are sure that within each run of the traversal,
**each vertex of your graph can only be reached once**,
you may set parameter *is_tree* to *True* upon
instantiation of a traversal class.

This deactivates the mechanisms of the traversal that are used to avoid subsequent
visits of already visited vertices in the same traversal run. When you do this,
you will get a **better performance** of the traversal, but some of the
traversal strategies will give you **less state information** (see the
API reference of the respective `traversal class <traversal-classes-api>`).

The formal condition when it is allowed to set *is_tree* to *True* is:
Each occurring search graph needs to be a tree or, in case of
multiple start vertices per search, a disjoint set of trees.
Here, *search graph* denotes the induced sub-graph of the given graph that
consists only of the vertices that are reached during the traversal run
when starting at the start vertex.

**If your graph itself is a tree, this condition is always fulfilled.**

If you use this option when the required condition is not fulfilled, the traversal
will probably run longer, return wrong results or will even not terminate.

Example: See section
`Depths first search in the integers <example-traversal-depth-first-integers>`.

.. _vertex-identity:

Identity and equivalence of vertices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default behavior of NoGraphs with respect to vertex identity is the
following:

1) **Two vertices are regarded as the same vertex, if they are equal** in
   the sense of Python's comparison operators (== and !=).
   That means, e.g., *(1, 2)* and *tuple([1, 2])* both stand
   for the same vertex.

2) **Vertices need to be hashable**, and this implies, that two equal
   vertices have equal hashes.

If this is not what you want, consider to define a `VertexToID` function
and to use this function as parameter *vertex_to_id* when instantiating
a traversal class:

For a given vertex, a *VertexToID* function returns a hashable object, a
so-called *identifier*. The **traversal will use the identifiers instead of
the vertices themselves for equality comparisons and as keys in sets or
mappings** (both in internal ones and in externally accessible ones).

Here are some cases, and examples for each case:

- **Two vertex objects are the same vertex if and only if they are identical**

  You use instances of some vertex class of your application as vertices.
  They are mutable, and thus not hashable. Each vertex object is to be
  seen as a different vertex.

  In this situation, you can simply use the Python
  function *id* as *VertexToID* function.

- **Mutable vertex object, and their immutable counterparts identify them**

  You use lists as you vertices. You know that their content will not
  change during a traversal run. And the immutable tuple counterpart of a
  vertex is well suited for getting a hash value.

  In this situation, you can use function *tuple* as *VertexToID* function.

- **Traversal in equivalence classes of vertices**

  You have defined an abstraction function, that assigns an equivalence class to a
  vertex. And you know: Whenever there is a path of vertices, there is a
  respective path in the equivalence classes of these vertices. And whenever
  their is a path in the equivalence classes, there is a respective path in
  the vertices of these classes. You would like to solve some analysis
  problem in the equivalence classes instead of the vertices, because there,
  the analysis is easier to do.

  Here, you can use your abstraction function as *VertexToID* function.

.. _replace-internals:

Replacing internal data structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *start_from* methods of most strategy classes offer to replace some of the
internal data structures by application specific versions (see the
API reference of the respective `traversal class <traversal-classes-api>`).
You can use this for several purposes.

Examples:

- You provide your own implementation, that does the **bookkeeping in your own way**,
  e.g. directly in your vertex objects. Note: It is likely that
  this makes the traversal slower, since NoGraphs uses the high performance
  data structures of the Python standard library.

- You provide an object of a suitable standard library container,
  NoGraphs does the bookkeeping in there, and like this, you got **permanent
  access to this state information during the traversal**.

- You provide an object of a suitable standard library container that you have
  **pre-loaded with bookkeeping data**, in order to make NoGraphs to use this when it
  starts the traversal.

