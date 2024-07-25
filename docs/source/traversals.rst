Traversal algorithms
--------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

Based on your NextVertices or NextEdges function,
NoGraphs gives you **traversal algorithms in the form
of iterators**.
You can use them to **traverse your graph** following some specific traversal
strategy and to compute values like depths, distances, paths and trees.

Note that these strategies and their description below do not fully specify
the behaviour of the implemented algorithms. For instance, if a vertex has
edges to different successor vertices, the order in which these vertices are
reported is often undefined. In such cases, the implementation, and the order,
might change without prior notice.


Classes for all graphs
~~~~~~~~~~~~~~~~~~~~~~

The following classes can be used both for graphs
`with edge attributes <graphs_with_attributes>` and for graphs
`without edge attributes <graphs_without_attributes>`. See the respective
class documentation in the API reference for details.

- Class `nographs.TraversalBreadthFirst`

    - Algorithm *Breadth First Search* ("BFS").

    - Visits and reports vertices in *breadth first order*, i.e.,
      **with ascending depth** (the depth of a vertex is the edge count of
      the path with least edges from a start vertex).
      A vertex is reported when it is "seen" (read from the graph) for the
      first time. Start vertices are not reported.

    - The traversal state provides **vertex depth** / **search depth**,
      **paths** (all optionally), and set of **visited vertices**.

    - Examples: See `example-traversal-breadth-first-in-maze` and
      `example-traversal-breadth-first-towers-hanoi`.

- Class `nographs.TraversalDepthFirst`

    - Algorithm *Depth First Search* ("DFS").

    - Follows just one outgoing edge per vertex as long as possible,
      and **goes back a step and follows a further edge starting there,**
      **or then an edge starting at the next start vertex,**
      **only when necessary** to come to new vertices.
      A vertex is considered *visited* when its expansion starts (its
      successors are about to be read from the graph). And, by default,
      the vertex is also reported at this moment, except for the start
      vertices - they are not reported.

    - The traversal state provides **search depth**, **paths**,
      **trace**, **trace_labels**, **on_trace**, **index**,
      and set of **visited vertices** (all optionally),
      and **event** (when a vertex is reported).

    - Examples: See
      `depth-first search in the integers <example-traversal-depth-first-integers>`,
      `depth-limited depth-first search <graph_pruning_by_search_depth>`,
      `iterative deepening depth-first search <iterative_deepening_dfs>`,
      `longest path <longest_path_two_vertices>`
      between two vertices in a weighted graph or in an unweighted graph,
      `strongly connected components <strongly_connected_components>`
      of a graph, and
      `biconnected components of a connected undirected graph
      <biconnected_components>`.

    - Note: This class supports to
      `skip the expansion of individual vertices <dfs_expansion_skipping>`.

    .. versionchanged:: 3.4
       Start vertices are now evaluated successively.
       Attributes event, trace, trace_labels,
       on_trace, and index added. Options to control them
       added. Expansion of vertices can be skipped.

- Class `nographs.TraversalNeighborsThenDepth`

    - Algorithm similar to *Depth First Search* ("DFS"), but with changed
      vertex order.

    - Follows just one outgoing edge per vertex as long as possible,
      and **goes back a step and follows a further edge starting there,**
      **or then an edge starting at the next start vertex,**
      **only when necessary** to come to new vertices.

      A vertex is reported and marked as *visited* when it is "seen"
      (read from the graph) for the first time. Start vertices
      are considered visited, but they are not reported.

    - The traversal state provides **search depth**, **paths** (all optionally),
      and set of **visited vertices**.

    - Examples: See `example-traversal-depth-first-integers`.

    .. versionadded:: 3.0

- Class `nographs.TraversalTopologicalSort`

    - Algorithm *Topological Sort*.

    - Visits vertices using DFS (see above), but reports the vertices in the
      steps backwards, i.e. **from successors to predecessors**. This only works
      if the graph does not contain a cycle on a path from a start vertex, because
      otherwise, each two vertices on the cycle are both (indirect) successors and
      (indirect) predecessors of each other. If there is such a cycle in the
      graph, this is detected.

    - The traversal state provides **search depth**, **paths** (all optionally),
      and set of **visited vertices**.

    - Example: See `example-topological_sorting_processes`,
      `critical path in a weighted, acyclic graph <example-critical-path>`,
      and
      `longest path between two vertices in a weighted, acyclic graph
      <example-longest-path-acyclic-graph>`.


.. _examples_all_graphs:

**Comparing example:**

We define a graph with the following edges: From vertex 0, edges lead to vertices
1 and 2, and from each of those, edges lead to vertex 3.

.. code-block:: python

    >>> edges = {0: [3, 2, 1],
    ...          2: [5], 5: [3],
    ...          1: [4], 4: [3]}
    >>> def next_vertices(vertex, _):
    ...     return edges.get(vertex, ())

Then, we compare, how the three strategies traverse the graph starting
from vertex 0.

.. code-block:: python

    >>> list(nog.TraversalBreadthFirst(next_vertices).start_from(0))
    [3, 2, 1, 5, 4]

As you can see, TraversalBreadthFirst starts by exploring the three
vertices 3, 2 and 1 that can be reached directly from vertex 0
(distance "level" 1). Only then, it
goes deeper to vertices 5 and 4 (one distance "level" up).

.. code-block:: python

    >>> list(nog.TraversalDepthFirst(next_vertices).start_from(0))
    [1, 4, 3, 2, 5]

TraversalDepthFirst explores vertex 1, reports it, and goes directly deeper
to vertex 4, and then till vertex 3. Then, it goes backwards till at vertex 0,
it finds an edge to a further vertex, vertex 2, and from there vertex 5.

.. code-block:: python

    >>> list(nog.TraversalNeighborsThenDepth(next_vertices).start_from(0))
    [3, 2, 1, 4, 5]

TraversalNeighborsThenDepth reports the neighbors 3, 2 and 1 of the start vertex,
then explores vertex 1 and reports the neighbor 4, and then it explores
vertex 2 and reports neighbor 5. Backtracking leads to no new vertices.

.. code-block:: python

    >>> list(nog.TraversalTopologicalSort(next_vertices).start_from(0))
    [3, 4, 1, 5, 2, 0]

TraversalTopologicalSort reports the vertices in such an order,
that for each edge of the graph, the successor is reported before the
predecessor.


Classes for weighted graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following classes can be used for
graphs with weighted edges (see sections
`graphs with edge attributes <graphs_with_attributes>` and
`edge weights <weights>`).
See the respective class documentation in the API reference for details.

- Class `nographs.TraversalShortestPaths`

    - Algorithm of *Dijkstra*. All weights need to be non-negative.

    - Traverses your graph
      **from short to long distances (minimal sum of edge weights)** from
      some start vertices, and report the vertices in this order.
      Start vertices are not reported.

    - The traversal state provides **vertex distance**, **search depth**,
      **paths** (optionally) and **distances** (optionally).

    - Examples: See `example-shortest-paths-in-maze`,
      `Sieve of Eratosthenes <eratosthenes_with_Dijkstra>`,
      and `the examples below <examples_weighted_graphs>`.

- Class `nographs.TraversalAStar`

    - Algorithm *A\**. All weights need to be non-negative.
      **Admissible heuristic function to goal vertex needed**
      (for details, see the API reference for the class).

    - **Finds the shortest path (minimal sum of edge weights)** from one of the start
      vertices to the goal vertex.
      Start vertices are not reported.

    - The traversal state provides **path length**, **search depth** and
      **paths** (optionally). For the goal vertex, the path length is the
      length of the shortest path (distance from a start vertex).

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

    - The traversal state provides **edge** and **paths** (optionally).

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

State and standard methods of traversal objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section explains the lifecycle of traversal objects, and in which
state which methods can be used.
See the API reference of the `traversal classes <traversal-classes-api>` for
further details about methods and signatures.

**The state transitions**:

- **Instantiation** of a traversal class, leading to state *created*

  - In this step, you **choose the traversal strategy** and
    **define what graph** should be traversed
    (you provide a `NextEdges` or a `NextVertices` function).

  - Optionally, you define some specific **graph properties** (see
    `identity and equivalence of vertices <vertex_identity>`
    and `traversing trees <is_tree>`).


  The traversal object stores this data.

- **Starting** a traversal, leading from any state to state *started*

  You (re-) start the traversal by calling its method **start_from(...)**:

  - You **choose one or more start vertices**.
  - Optionally, you choose between some **traversal options**, e.g., that paths
    should be created, and whether there should be a calculation limit for
    the traversal.

  The traversal object creates an iterator (*base iterator*) that is able to
  traverse your graph starting at your start vertices and following the class
  specific traversal strategy.

  .. tip::

     The method *start_from* returns the traversal object itself to allow for
     direct calls of other methods, like in
     *traversal.start_from(...).go_to(...))*.

**The states**:

- **State created** (inactive)

  The traversal has not been started so far.

  Example:

  .. code-block:: python

   >>> def next_vertices(i, _):
   ...     return [2*i] if abs(i)<512 else []

   >>> traversal = nog.TraversalBreadthFirst(next_vertices)

  In this state, you cannot use any of the iteration methods of the traversal object,
  and its public attributes contain arbitrary content:

  .. code-block:: python

     >>> next(traversal)
     Traceback (most recent call last):
     RuntimeError: Traversal not started, iteration not possible

.. _general-start_from:

- **State started** (active)

  Method *start_from* has already been called.

  .. code-block:: python

     >>> traversal = traversal.start_from(1)

  In this state, you can
  **use the traversal object for iterating over the graph**:

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

  **When a vertex is expanded** (the traversal calls the `NextEdges` or `NextVertices`
  function provided by the application)
  **or a vertex is reported, specific attributes of the traversal object**
  **contain additional data** about the state of the traversal
  w.r.t. this vertex (see the API reference of the
  `traversal classes <traversal-classes-api>`).


  .. code-block:: python

     >>> print(next(traversal), traversal.depth)
     2 1

     >>> for vertex in traversal:
     ...     print(vertex, traversal.depth)
     ...     if vertex == 8: break
     4 2
     8 3

     >>> # Skip till one of the listed vertices is reached, repeat, stop on last one
     >>> for vertex in traversal.go_for_vertices_in([128, 32]):
     ...     print(vertex, traversal.depth)
     32 5
     128 7

  At any time, you can **restart the traversal** at the same or some
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

- **State exhausted** (inactive)

  When the traversal has iterated through all vertices that are reachable from
  your chosen start vertices, the iterator is exhausted. Upon calls, it raises
  a *StopIteration* exception. This ends loops like the *for* loop.

  .. code-block:: python

     >>> # iterator will be exhausted after vertex -512
     >>> for vertex in traversal:
     ...     print(vertex, traversal.depth)
     -256 3
     -512 4

     >>> next(traversal)
     Traceback (most recent call last):
     StopIteration

  You can still start the traversal again, if you like.

**At any state:**

  Method **state_to_str() returns the content of the public state attributes** of the
  traversal in form of a string. It can be used for logging and debugging.

  Some attributes of a traversal are containers that cannot iterate their content, or
  collections that guarantee for the validity of stored results only for vertices that
  have already been reported (see the API reference of the
  `traversal classes <traversal-classes-api>`).
  If state_to_str is called with some vertices as parameter, it also returns the
  respective state data for these vertices.

  **Example:** When a vertex is expanded, we print the state in default form,
  and when it is reported, we print the state in full form.

  .. code-block:: python

    >>> edges = {0: ((1,2), (2,1)), 1: ((3,2),), 2: ((3,2),)}
    >>> def next_edges(vertex, t):
    ...     print(f"Expanded: {vertex}. State: {t.state_to_str()}")
    ...     return edges.get(vertex, ())
    >>> start = 0

    >>> traversal = nog.TraversalShortestPaths(next_edges).start_from(
    ...     start, keep_distances=True)
    >>> visited = [start]
    >>> for vertex in traversal:
    ...    visited.append(vertex)
    ...    print(f"Reported: {vertex}. State: {traversal.state_to_str(visited)}"
    ...         )  # doctest: +NORMALIZE_WHITESPACE
    Expanded: 0. State: {'distance': 0, 'depth': 0}
    Reported: 2. State: {'distance': 1, 'depth': 1,
      'distances': {0: 0, 2: 1}, 'paths': {}}
    Expanded: 2. State: {'distance': 1, 'depth': 1}
    Reported: 1. State: {'distance': 2, 'depth': 1,
      'distances': {0: 0, 2: 1, 1: 2}, 'paths': {}}
    Expanded: 1. State: {'distance': 2, 'depth': 1}
    Reported: 3. State: {'distance': 3, 'depth': 2,
      'distances': {0: 0, 2: 1, 1: 2, 3: 3}, 'paths': {}}
    Expanded: 3. State: {'distance': 3, 'depth': 2}

  .. versionchanged:: 3.1

     Method state_to_str() introduced.

.. _class_specific_methods:

Methods for depth and distance ranges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two traversal classes offer additional iteration methods that focus on ranges of
vertex depths or distances. These are the following:

- `TraversalBreadthFirstFlex.go_for_depth_range(start, stop)
  <nographs.TraversalBreadthFirstFlex.go_for_depth_range>`

  For a started traversal, the method returns an iterator. During the traversal, the
  iterator skips vertices as long as their depth is lower than *start*. From then on,
  it reports the found vertices. It stops when the reached depth is higher than *stop*.

  .. note::

      The first vertex with a depth higher than *stop* will be consumed from the
      traversal, but will not be reported, so it is lost
      (compare *itertools.takewhile*).

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
  <nographs.TraversalShortestPathsFlex.go_for_distance_range>`

  For a started traversal, the method returns an iterator. During the traversal, the
  iterator skips vertices as long as their distance is lower than *start*. From
  then on, is reports the found vertices. It stops when the reached distance is
  higher than *stop*.

  .. note::

      The first vertex with a distance higher than *stop* will be consumed from the
      traversal, but will not be reported, so it is lost
      (compare *itertools.takewhile*).

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


.. _dfs_expansion_skipping:

Skipping vertex expansion in TraversalDepthFirst
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 3.4

In section
`DFS: all paths and walks <dfs_all_paths_and_walks>`,
when we computed the possible paths from vertex *A* to vertex *C*
in the following graph, we
removed the successors of *C* from the graph before the search to
prevent the search from further extending a path beyond *C*.

    >>> successors = {
    ...    "A": ["B1", "B2"],
    ...    "B1": ["C", "B"],
    ...    "B2": ["C", "B"],
    ...    "B": ["B1", "B2"],
    ...    "C": ["B"],
    ... }
    >>> def next_vertices(v, _):
    ...     return successors.get(v, ())

The class *TraversalDepthFirst* offers another method to achieve the same effect
in a more dynamical way: The
**application code can signal to the traversal that**
**the vertex that has just been entered should not be expanded**, i.e.,
edges to successors should be ignored.

There are two equivalent ways to do this:

- **Calling method** *skip_expanding_entered_vertex()* **of the traversal object**.

- **Throwing a** *StopIteration()* **to the generator** provided by method
  *__iter__* **of the traversal**. This is what the above method does.
  *throw()* returns the vertex to confirm the success.

**Example: Pruning paths at the required end vertex**

The following code shows, how all paths starting at *A* and ending at *C*
can be computed with skipping the expansion of *C* during the traversal
instead of removing the edges from *C* to successors before the traversal.

.. code-block:: python

    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> _ = traversal.start_from("A", mode=nog.DFSMode.ALL_PATHS, compute_trace=True)

    >>> for v in traversal:
    ...     if v == "C":
    ...          print(traversal.trace)
    ...          traversal.skip_expanding_entered_vertex()
    ['A', 'B2', 'B', 'B1', 'C']
    ['A', 'B2', 'C']
    ['A', 'B1', 'B', 'B2', 'C']
    ['A', 'B1', 'C']

Caution is advised when using the
*report* parameter of method *TraversalDepthFirst.start_from()*
to get reports about events other than
*DFSEvent.ENTERING* and *DFSEvent.ENTERING_START*:
If such an event occurs, **no vertex has been entered, and**
it is therefor
**not allowed to signal to the traversal to skip the entered (!) vertex**.
If you do this anyway, the traversal intentionally won’t catch the
*StopIteration* you throw, and a *RuntimeError* will be raised
(according to `PEP 497 <//peps.python.org/pep-0479>`_).

This also means, that it is always save to ignore the return value of
throwing the *StopIteration* into the generator: it can only be the entered
vertex again (the success signal for skipping the expansion of
the vertex). Otherwise, a *RuntimeError* would have been raised.

**Example: Only the expansion of entered (!) vertices can be skipped**

We visit the vertices of the DFS-tree of the above graph.
As start vertices, we give two times (!) vertex *A*.
And we demand that the traversal both reports when a start vertex is entered and
when it is skipped because it has already been entered before.

First, vertex *A* it reported with event *ENTERING_START*. Here,
throwing *StopIteration* is accepted
by the generator and the generator skips expanding the vertex.

Then, vertex *A* is reported with event *SKIPPING_START*.
This means, *A* it is not entered. Here, throwing *StopIteration* is not
accepted and a *RuntimeError* is raised.

.. code-block:: python

    >>> _ = traversal.start_from(
    ...     start_vertices="AA", mode=nog.DFSMode.DFS_TREE,
    ...     report=nog.DFSEvent.ENTERING_START | nog.DFSEvent.SKIPPING_START)
    >>> generator = iter(traversal)
    >>> next(generator), str(traversal.event)
    ('A', 'DFSEvent.ENTERING_START')
    >>> generator.throw(StopIteration())
    'A'
    >>> next(generator), str(traversal.event)
    ('A', 'DFSEvent.SKIPPING_START')
    >>> generator.throw(StopIteration())
    Traceback (most recent call last):
    RuntimeError: generator raised StopIteration

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

.. _typing:

Usage in typed code
~~~~~~~~~~~~~~~~~~~

NoGraphs can be used in a fully typed way and, given its flexibility w.r.t.
data types, with a very good level of type safety.

.. versionchanged:: 3.0

   Type stubs and API for good typing support introduced.

`Application code can specify, what data types it uses <type_variables>`
for vertices, `vertex ids <vertex_identity>`, weights and edge labels.
Then, based on the generic signatures of NoGraphs,
a static type checker can check whether the application uses
`suitable classes of NoGraphs for graph analysis <traversal_api>`, the
`handling of vertex identity <vertex_identity>` and for
`bookkeeping of graph data <gears>`
of these types,
and whether the application is ready to receive the result types returned by
NoGraphs.

The signatures of NoGraphs have been tested for the use of MyPy as static type
checker, and its implementation is fully type checked with MyPy (where casts
where necessary, manual correctness arguments support them).

**Example**:

The following code is a fully typed variant of the example of the
`overview page <overview_example>`.

- When instantiating `TraversalShortestPaths`,
  the types used for `vertices <vertices>`, `weights <weights>`
  and `edge labels <graphs_with_attributes>` are
  given as [int, int, Any].

- Parameters and return value of the function *next_edges* are also specified.
  When the function is given as argument to the traversal, MyPy can check
  its signature against the needs of `TraversalShortestPaths`.

- The correct use of methods *start_from* and *go_to* and its parameters can be
  checked by MyPy.

- The guaranteed types of the three result values can be derived by MyPy.

.. code-block:: python

    >>> from typing import Any, Iterator
    >>> def next_edges(i: int, _) -> Iterator[tuple[int, int]]:
    ...     j = (i + i // 6) % 6
    ...     yield i + 1, j * 2 + 1
    ...     if i % 2 == 0:
    ...         yield i + 6, 7 - j
    ...     elif i % 1200000 > 5:
    ...         yield i - 6, 1
    >>> traversal = nog.TraversalShortestPaths[int, int, Any](next_edges)
    >>> traversal.start_from(0, build_paths=True).go_to(5)  # derived type: int
    5
    >>> traversal.distance  # derived type: Union[int, float]
    24
    >>> tuple(traversal.paths.iter_vertices_from_start(5)
    ... )  # Derived type: tuple[int, ...]
    (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)

.. tip::

   Please note, that all the algorithms, that have been
   explained so far and work with weighted edges, add *float* to the
   possible type of edge weights and distances, because internally, they
   use float("infinity") for infinite weight/distance and the integer 0
   for zero weight/distance. See the respective
   `API specification <traversal_api>` and `GearDefault`.

   **Example:**

   | `TraversalShortestPaths` [T_vertex, T_weight, T_labels]
   | is, according to its specification, a
   | `TraversalShortestPathsFlex` [T_vertex, T_vertex, Union[T_weight, float], T_labels]

   And a TraversalShortestPathsFlex with these generic types is allowed to
   return floats, additionally to the T_weight specified by the application code.

   **It is possible to avoid this** by choosing the `gear (see there) <gears>` that
   fits the typing needs of the application optimally.

   Examples:

   - You could use `GearForHashableVertexIDsAndFloats`
     or `GearForIntVertexIDsAndCFloats`, if you like to
     work with float weights and distances only.

   - You could use `GearForHashableVertexIDsAndDecimals` or
     `GearForIntVertexIDsAndDecimals`, if you like to
     work with Decimal weights and distances only.

   - You could use `GearForHashableVertexIDs` or `GearForIntVertexIDs`,
     both with 0 as *zero* value and
     some large integer as *inf* value (it need to be larger than any integer
     that could occur as edge weights of paths length),
     or `GearForIntVertexIDsAndCInts` (the *zero* and *inf* values are
     predefined here), if you like to
     work with integer weights and distances only.
