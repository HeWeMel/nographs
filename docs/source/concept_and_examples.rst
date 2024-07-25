Concept & examples
------------------

On the fly - the basics
~~~~~~~~~~~~~~~~~~~~~~~

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

The main elements of the concept of NoGraphs are the following:

1) **Graphs are computed and/or adapted in application code on the fly**
   (when needed and as far as needed).

   The library does not offer graph containers and it stores no graphs. This is where
   the name *NoGraphs* library comes from.

   Instead,
   your application computes the graph on the fly, or it stores a graph and
   adapts it on the fly. From the perspective of NoGraphs, a so-called
   *implicit graph* is given. This works as follows:

   -  Your application makes the graph
      **accessible for NoGraphs by providing a callback function** to the library.
      `This function <graphs_and_adaptation>` gets a vertex and returns data about
      connected vertices or outgoing edges of the graph.

      **Example:** Here is a (trivial) graph, that is computed on the fly by
      function *next_vertices*. The function gets a vertex identified by an integer
      *i* (the second parameter will be explained
      `later on <search_aware_graphs>`, it is just ignored here)
      and returns connected vertices, here *i + 3* and *i - 1*.

      .. code-block:: python

        >>> def next_vertices(i, _):
        ...     return i + 3, i - 1

   -  NoGraphs calls such a function to **access the parts of the graph
      that are relevant** for the computation of the requested results.

      This means, other parts of the graph need not to be calculated / adapted.
      This way, NoGraphs can deal with graphs that can not or
      should not be fully computed or adapted, e.g. infinite graphs, large graphs and graphs
      with expensive computations.

2) **The analysis and the reporting of results by the library happens on the fly**
   (when, and as far as, results can already be derived).

   -  NoGraphs **returns (partial) results immediately**,
      when they have been derived from the parts of the graph that have already been "seen",
      and it **pauses the computation, till further results are requested**.

      This means, only the required amount of calculation is done.

      **In the example:** We choose the integer 2 as start vertex and use NoGraphs
      to traverse the vertices of the graph in ascending depth from this start vertex.
      The *depths* of a vertex is the minimal number of edges needed to come from the start
      vertex to this vertex. We print the first three results.

      .. code-block:: python

         >>> traversal = nog.TraversalBreadthFirst(next_vertices).start_from(2)
         >>> for j in range(3):
         ...     print(f"Vertex {next(traversal)} in depth {traversal.depth}")
         Vertex 5 in depth 1
         Vertex 1 in depth 1
         Vertex 8 in depth 2

      Then, we ask for further vertices, but only those in depth 4:

      .. code-block:: python

         >>> tuple(traversal.go_for_depth_range(4, 5))
         (14, 10, 6, -2)

   -  **NoGraphs stores no results**, except when they could be needed internally
      for the computation of further results.

      This means, you can store results exactly like you need them in the
      application. And you can avoid unnecessary memory consumption.

      **In the example:** We like to find vertices of depth 6 and 7 and store
      the depths per vertex in a dictionary. We do that as follows:

      .. code-block:: python

         >>> depths = {vertex: traversal.depth
         ...           for vertex in traversal.go_for_depth_range(6, 8)}
         >>> depths
         {20: 6, 16: 6, 12: 6, -4: 6, 23: 7, 19: 7, 15: 7, -5: 7}


   -  **NoGraphs finds out on the fly, what the vertices of the graph are**

      We do not need to declare or define vertices. For NoGraphs, a vertex is
      what occurs in the role of a vertex during traversing the graph
      (for details see section `vertices <vertices>`, and if you like to
      work fully typed, see `usage in typed code <typing>`).


.. _examples:

Examples
~~~~~~~~

In the following sections, we give some small examples that illustrate the
described `concept elements <concept_and_examples>`
of NoGraphs and their use in the context of a selection of traversal algorithms.
More examples and algorithms can be found in the respective sections of this
tutorial.

We start with algorithms that do not require edge weights. Then, we give
examples with weighted edges.

The `building blocks of graph adaptation <graphs_and_adaptation>`,
the support for `operations on graphs <graph_operations>`
and the `algorithms and API <traversals>` that are used here will be
explained afterwards.

.. _example-traversal-breadth-first-in-maze:

Breadth First Search in a maze
..............................

In this example, our vertices are tuples of a *x* and a *y* coordinate. A
coordinate is an integer between 0 and 4. From each position, the horizontal and
vertical neighbors within these limits are the successors, and some vertices are not
allowed to be visited.

.. code-block:: python

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

Based on this function *next_vertices*, we can walk through a kind of maze that looks
as follows. Here, "." means an allowed vertex, "*" a forbidden vertex,
the y-axis goes downwards, the x-axis goes to the right, and
positions (0, 0) and (4, 4) are marked by "S" and "G" respectively.

::

    S*.*.
    .*...
    .*.*.
    ...*.
    .*.*G


We start at position (0, 0), traverse the graph, compute the depth of position (4, 4)
, i.e. the number of edges needed from start to come to here, and a path with that
number of edges.

We use the *TraversalBreadthFirst* strategy of NoGraphs (see
`Traversal algorithms <traversals>`).
It implements the graph algorithm **breadth-first search** in the NoGraphs style.

.. code-block:: python

   >>> traversal = nog.TraversalBreadthFirst(next_vertices)
   >>> vertex = traversal.start_from((0, 0), build_paths=True).go_to((4, 4))
   >>> traversal.depth
   12
   >>> traversal.paths[vertex]  # doctest: +NORMALIZE_WHITESPACE
   ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (2, 2), (2, 1), (3, 1),
   (4, 1), (4, 2), (4, 3), (4, 4))

.. tip::

   - We got the result *depth* **from the state information** of the traversal. We
     are free to decide, if and how we like to store it. The state will change
     with the next traversal step.

   - We asked for paths. Then, NoGraphs **stores all computed paths** for us, in an
     optimized internal way. The reason is, that a path can depend on other, previously
     found paths, so they are all needed for NoGraphs to compute further results. But
     only when we require some path in explicit form of a tuple, it will be "unpacked"
     and returned. Like that, NoGraphs avoids the worst case of quadratic runtime and
     memory costs, that an explicit representation of all computed paths would
     have, as long as you do not really need all of them.

   - Function *neighbors_in_grid* can be interpreted as a graph
     on its own (in fact, by just adding an unused second parameter, NoGraphs
     would accept it as input). On this basis, function *next_vertices* can be seen
     as a **restriction of this graph** to the allowed fields ("*graph pruning*").

   - NoGraphs provides some `gadgets <matrix_gadgets>` to play with maze
     examples like this and with other array-like content more easily.


.. _example-traversal-breadth-first-towers-hanoi:

Breadth First Search for the Towers of Hanoi
............................................

We play *Towers of Hanoi*
(see `Wikipedia <https://en.wikipedia.org/wiki/Tower_of_Hanoi>`_).
We model a tower as a tuple of the sizes of its "disks", sorted in ascending order.
We decide that a vertex (state in the game) is a tuple of such towers. During the
game, from one state to the other, we choose a tower, take its smallest disk,
and put it on top of some other tower, that contains only larger disks so far.

.. code-block:: python

   >>> def next_vertices(towers, _):
   ...     n = len(towers)
   ...     for t_from in range(n):
   ...         if not towers[t_from]: continue
   ...         for t_to in range(n):
   ...             if t_from == t_to: continue
   ...             if not towers[t_to] or towers[t_from][0] < towers[t_to][0]:
   ...                 tmp_towers = list(towers)
   ...                 tmp_towers[t_to] = (towers[t_from][0], *towers[t_to])
   ...                 tmp_towers[t_from] = towers[t_from][1:]
   ...                 yield tuple(tmp_towers)

.. tip::

   Due to the special concept of NoGraphs, our **model can be very flexible**:
   It works for different numbers of towers and for different sets of discs in play.
   NoGraphs automatically traverses only those vertices (tower and
   disc configurations) that are relevant for the respective search task.

We choose two problem scenarios:

  1) Three towers, three discs on the first tower, and the goal is to have three discs
     on the second tower.

  2) Three towers, four discs, discs of size 1 and 3 on the first tower, sizes 2 and 4
     on the third tower, and the goal is to have all disks on the second tower.

We solve them, print the reached vertex, and print the minimal number of steps needed.
In order to really see a solution, we print a path with the minimal number of edges for
problem 1.

Again, we use the *TraversalBreadthFirst* strategy of NoGraphs
(see `Traversal algorithms <traversals>`).

.. code-block:: python

   >>> traversal = nog.TraversalBreadthFirst(next_vertices)

   >>> # -- problem 1 --
   >>> start, goal = ((1,2,3), (), ()), ((), (1,2,3), ())
   >>> vertex = traversal.start_from(start, build_paths=True).go_to(goal)
   >>> print(f"Goal {vertex} reachable with a minimum of {traversal.depth} steps.")
   Goal ((), (1, 2, 3), ()) reachable with a minimum of 7 steps.

   >>> for vertex in traversal.paths[vertex]:
   ...     print(vertex)
   ((1, 2, 3), (), ())
   ((2, 3), (1,), ())
   ((3,), (1,), (2,))
   ((3,), (), (1, 2))
   ((), (3,), (1, 2))
   ((1,), (3,), (2,))
   ((1,), (2, 3), ())
   ((), (1, 2, 3), ())

   >>> # -- problem 2 --
   >>> start, goal =  ((1,3), (), (2,4)), ((), (1,2,3,4), ())
   >>> vertex = traversal.start_from(start).go_to(goal)
   >>> print(f"Goal {vertex} reachable with a minimum of {traversal.depth} steps.")
   Goal ((), (1, 2, 3, 4), ()) reachable with a minimum of 11 steps.

.. _example-traversal-depth-first-integers:

Depths first search in the integers
...................................

We choose the integers as our vertices. The (only) successor of a vertex *i* is *i+2*.

.. code-block:: python

   >>> def next_vertices(i, _):
   ...     return i+2,

We check that 20,000,000 **can be reached** from 0. This means, that the number
is even. There might be easier ways to find that out... :-)

We use the *TraversalDepthFirst* strategy of NoGraphs (see
`Traversal algorithms <traversals>`). It implements the well-known
*Depth First Search* algorithm in the NoGraphs style.

.. code-block:: python

   >>> traversal = nog.TraversalDepthFirst(next_vertices, is_tree=True)
   >>> traversal.start_from(0).go_to(20_000_000)  #doctest:+SLOW_TEST
   20000000

Now, we choose some odd number and try to
**check that it cannot be reached**.
Here are two examples for techniques we can use to to that:

In the first case, we use a *sentinel vertex*, here 20,000,002, together with
our goal vertex. When the sentinel vertex is reached, we know by the structure
or our graph, that our goal vertex 20,000,001 - a lower number - will not be
reached anymore.

.. code-block:: python

   >>> next(traversal.start_from(0).go_for_vertices_in( (20_000_001, 20_000_002) ))  #doctest:+SLOW_TEST
   20000002

In the second case, we define an
*upper limit for the number of allowed calculation steps*,
i.e., a maximal number of vertices to be read in from the graph.
We choose a limit, here 10,000,001, that is surely high enough to reach the goal
vertex, if it is reachable, but prevents an unnecessarily high run time
or, like in our case, even an infinite run time, if it is not reachable.

.. code-block:: python

   >>> traversal.start_from(0, calculation_limit=10_000_001).go_to(20_000_001)  #doctest:+SKIP
   Traceback (most recent call last):
   RuntimeError: Number of visited vertices reached limit

Additionally to TraversalDepthFirst, NoGraphs provides the traversal strategy
*TraversalNeighborsThenDepth*. It traverses the graph in a way similar to
TraversalDepthFirst, but it reports the direct neighbors of a current vertex
before it descends deeper into the graph. It can be used to find
a vertex, when the exact traversal order of the vertices is not important.
Typically, it is faster than TraversalDepthFirst and needs less memory.

.. code-block:: python

   >>> traversal = nog.TraversalNeighborsThenDepth(next_vertices, is_tree=True)
   >>> traversal.start_from(0).go_to(20_000_000)  #doctest:+SKIP
   20000000


.. _dfs_forest_edges:

DFS forest: edges, predecessor relation, and paths
..................................................

.. versionadded:: 3.4

In this example, we choose the integers 1...9 as vertices of our finite graph.
The successors *w* of a vertex *i* are *i-2* and *i+4*, if they are valid
vertices.

.. code-block:: python

    >>> vertices = range(1, 10)
    >>> def next_vertices(v, _):
    ...     for w in [v - 2, v + 4]:
    ...         if w in vertices:
    ...              yield w

The edges of this graph are the following:

.. code-block:: python

    >>> [(v, w) for v in vertices for w in next_vertices(v, None)]  # doctest: +NORMALIZE_WHITESPACE
    [(1, 5), (2, 6), (3, 1), (3, 7), (4, 2), (4, 8), (5, 3), (5, 9), (6, 4),
    (7, 5), (8, 6), (9, 7)]

We want to compute a *DFS forest* (set of depth-first search trees) covering all
vertices, store the forest in form of its predecessor relation, and
list the edges of the forest.

We use the *TraversalDepthFirst* strategy of NoGraphs (see
`Traversal algorithms <traversals>`) to traverse the edges of a DFS-tree of the graph.
We tell the traversal to generate paths leading from start vertices to the traversed
vertices, following the edges of the DFS-tree: Then, the
**paths container permanently stores the generated predecessor relation**
**of the DFS-forest** for us.

.. code-block:: python

    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> reported_vertices = list(
    ...    traversal.start_from(start_vertices=vertices, build_paths=True))

Now, for all vertices that has been reported as end vertex of an edge of the
DFS forest, we list the edge consisting of the predecessor and the vertex.

.. code-block:: python

    >>> list((traversal.paths.predecessor(v), v) for v in reported_vertices)
    [(1, 5), (5, 9), (9, 7), (5, 3), (2, 6), (6, 4), (4, 8)]

1 and 2 have no predecessors,
because they have not occurred as end vertex of an edge of the DFS forest, as
they are the root vertices of the two DFS-trees of the DFS forest.

.. code-block:: python

    >>> list((traversal.paths.predecessor(v), v) for v in [1, 2])
    [(None, 1), (None, 2)]

The edges listed above really form a DFS-forest: Starting from one of the roots,
we can reach all other vertices of the graph by following the computed edges, and
there are no two edges ending at the same vertex.

.. note::

   While the start vertices are iterated in the order in which they were
   indicated (1 before 2 - this is guaranted),
   currently,
   the edges computed by *next_vertices* are processed in reversed order
   (e.g., from vertex 5, first the *v+4* edge to 9 is traversed, and later the
   *v-2* edge to 3), as it is typical for non-recursive depth-first traversal
   algorithms.

   The **order of processing the successors of a vertex is an implementation**
   **detail that can change anytime without prior notice**,
   as it is not part of the specification of the search strategies.

As the predecessor relation of the DFS-trees is kept in the paths object, we can also
ask later on for the predecessor of a vertex. And we can ask for a
path that leads from a start vertex to a given vertex using the edges of the DFS-trees:

.. code-block:: python

    >>> traversal.paths.predecessor(3)
    5
    >>> traversal.paths[3]
    (1, 5, 3)


.. _dfs_forest:

DFS forest: events, edge types, and successor relation
......................................................

.. versionadded:: 3.4

We use the same graph as in the example before.

This time, we store the DFS-forest in form of a dictionary of the
**successor relation**
of the trees. For this, we demand that the traversal generates / updates
the *trace*, i.e., the path that leads from a start vertex to the current vertex
following the edges of the DFS forest.
We use the current trace to determine the predecessor of the current vertex.

.. code-block:: python

    >>> from collections import defaultdict
    >>> _ = traversal.start_from(start_vertices=vertices, compute_trace=True)
    >>> successors = defaultdict(list)
    >>> for v in traversal:
    ...     predecessor = traversal.trace[-2]
    ...     successors[predecessor].append(v)
    >>> print(successors)
    defaultdict(<class 'list'>, {1: [5], 5: [9, 3], 9: [7], 2: [6], 6: [4], 4: [8]})

Next, we like to **see each step of the traversal of the DFS-forest in detail**.
The following cases (*events*, see `here <DFSEvent>`) may occur:

- ENTERING SUCCESSOR:
  An edge of the DFS-forest is followed, from a vertex to a successor, and the
  successor is entered.
- LEAVING_SUCCESSOR:
  The successor, that an edge of the DFS-forest leads to, is left and the edge is
  traversed in the opposite direction in the sense of a backtracking.
- BACK_EDGE, CROSS_EDGE, or FORWARD_EDGE:
  An edge has been found, that does not belong to the DFS-forest. The traversal
  does not follow such edges and does not enter the vertex it leads to.
  There are different kinds of such edges. The example shows two of them.
- ENTERING_START, LEAVING_START, SKIPPING_START:
  A start vertex is entered or left. Or it is skipped, because it has already been
  visited as successor of some other vertex.

We tell TraversalDepthFirst, that we like to be informed about all these
kinds of events. When an event is reported, we print it together with up to the
last two vertices of the trace.

.. code-block:: python

    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> _ = traversal.start_from(start_vertices=vertices, compute_trace=True,
    ...                          report=nog.DFSEvent.ALL)
    >>> for v in traversal:
    ...     print(traversal.event, traversal.trace[-2:])
    DFSEvent.ENTERING_START [1]
    DFSEvent.ENTERING_SUCCESSOR [1, 5]
    DFSEvent.ENTERING_SUCCESSOR [5, 9]
    DFSEvent.ENTERING_SUCCESSOR [9, 7]
    DFSEvent.BACK_EDGE [7, 5]
    DFSEvent.LEAVING_SUCCESSOR [9, 7]
    DFSEvent.LEAVING_SUCCESSOR [5, 9]
    DFSEvent.ENTERING_SUCCESSOR [5, 3]
    DFSEvent.CROSS_EDGE [3, 7]
    DFSEvent.BACK_EDGE [3, 1]
    DFSEvent.LEAVING_SUCCESSOR [5, 3]
    DFSEvent.LEAVING_SUCCESSOR [1, 5]
    DFSEvent.LEAVING_START [1]
    DFSEvent.ENTERING_START [2]
    DFSEvent.ENTERING_SUCCESSOR [2, 6]
    DFSEvent.ENTERING_SUCCESSOR [6, 4]
    DFSEvent.ENTERING_SUCCESSOR [4, 8]
    DFSEvent.BACK_EDGE [8, 6]
    DFSEvent.LEAVING_SUCCESSOR [4, 8]
    DFSEvent.BACK_EDGE [4, 2]
    DFSEvent.LEAVING_SUCCESSOR [6, 4]
    DFSEvent.LEAVING_SUCCESSOR [2, 6]
    DFSEvent.LEAVING_START [2]
    DFSEvent.SKIPPING_START [3]
    DFSEvent.SKIPPING_START [4]
    DFSEvent.SKIPPING_START [5]
    DFSEvent.SKIPPING_START [6]
    DFSEvent.SKIPPING_START [7]
    DFSEvent.SKIPPING_START [8]
    DFSEvent.SKIPPING_START [9]

Note, that the event *ENTERING_START* gives us the *roots of the DFS-trees* in our
DFS-forest.

.. tip::

    *TraversalDepthFirst* and **its event-reporting feature**
    **can be leveraged to implement additional DFS-based algorithms**:
    *TraversalDepthFirst* deals for us with the non-recursive
    implementation of the graph-traversal and the handling of some basic
    bookkeeping. And our application code can
    choose which events are relevant and handle these events in a
    problem-specific way.

    Examples for this approach can be found in the section
    `problem reduction <reduction_of_other_problems>` of this tutorial.
    They include computing the
    `strongly connected components <strongly_connected_components>`
    of a graph and the
    `biconnectec components of a connected undirected graph <biconnected_components>`.


.. _dfs_all_paths_and_walks:

DFS: all paths and walks
........................

.. versionadded:: 3.4

We compute paths and walks.

- A *directed walk* is a finite or infinite sequence of edges directed in the same
  direction which joins a sequence of vertices.

- A *directed path* is a directed walk in which all vertices are distinct.

In the following, we always mean *directed* walks resp. *directed* paths and thus
leave out *directed*.

.. note::

  In the sections before, we always focussed on paths along the edges of the
  DFS forest, while now, we want to regard all possible paths, or even all walks.

We choose the strings as vertices of the following cyclic graph. It contains
a diamond-shaped sub-graph *A*, *B1*, *B2*, *C*. And additionally, there
is a vertex *B* in the middle, that is successor of *C* and is connected
with *B1* and *B2* in both directions.

.. code-block:: python

    >>> successors = {
    ...    "A": ["B1", "B2"],
    ...    "B1": ["C", "B"],
    ...    "B2": ["C", "B"],
    ...    "B": ["B1", "B2"],
    ...    "C": ["B"],
    ... }
    >>> def next_vertices(v, _):
    ...     return successors.get(v, ())

First, we want to compute **all paths starting at vertex** *B*.
A vertex can occur in several paths, unlike the situation in a normal
DFS-tree traversal, where each vertex is visited only once.

We use the *TraversalDepthFirst* strategy of NoGraphs (see
`Traversal algorithms <traversals>`) to traverse the graph in DFS-order,
starting at *B*. And we generate all paths from the start vertex by using
option *mode = DFSMode.ALL_PATHS*.
We tell the traversal to maintain the trace, i.e., the path leading from the
start vertex to the traversed vertex.


.. code-block:: python

    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> _ = traversal.start_from(start_vertices="B", mode=nog.DFSMode.ALL_PATHS, compute_trace=True)
    >>> for v in traversal:
    ...     print(traversal.trace)
    ['B', 'B2']
    ['B', 'B2', 'C']
    ['B', 'B1']
    ['B', 'B1', 'C']

Next, we want to compute **all paths from vertex** *A* **to vertex** *C*.
We print the current trace when *C* is reached. And we prevent the search from further
extending such a path beyond *C*.

.. code-block:: python

    >>> def next_vertices_prune_at_c(v, _):
    ...     return next_vertices(v, ()) if v != "C" else []
    >>> traversal = nog.TraversalDepthFirst(next_vertices_prune_at_c)
    >>> _ = traversal.start_from(start_vertices="A", mode=nog.DFSMode.ALL_PATHS, compute_trace=True)
    >>> for v in traversal:
    ...     if v == "C":
    ...         print(traversal.trace)
    ['A', 'B2', 'B', 'B1', 'C']
    ['A', 'B2', 'C']
    ['A', 'B1', 'B', 'B2', 'C']
    ['A', 'B1', 'C']


Now, we want to compute **all walks from from the start vertex** *A*
**to the goal vertex** *C* with a length of at most 4 edges.
The function *next_vertices* shown below only returns the successors of a
node if the search depth
has not already reached *4*. This technique is explained in more detail the
tutorial section about `search-aware graphs <search_aware_graphs>`.

.. code-block:: python

    >>> def next_vertices(v, traversal):
    ...     if traversal.depth == 4:
    ...         return []
    ...     return successors.get(v, ())

    >>> traversal = nog.TraversalDepthFirst(next_vertices)
    >>> _ = traversal.start_from(
    ...     start_vertices="A", compute_depth=True, mode=nog.DFSMode.ALL_WALKS, compute_trace=True
    ... )

    >>> for v in traversal:
    ...     if v == "C":
    ...         print(traversal.trace)
    ['A', 'B2', 'B', 'B2', 'C']
    ['A', 'B2', 'B', 'B1', 'C']
    ['A', 'B2', 'C']
    ['A', 'B1', 'B', 'B2', 'C']
    ['A', 'B1', 'B', 'B1', 'C']
    ['A', 'B1', 'C']


.. tip::

    *TraversalDepthFirst* and **its traversal modes**
    **can be leveraged to implement DFS-based algorithms**
    **that need to regard all possible paths, or even all walks**.

    Example: Section
    `problem reduction <reduction_of_other_problems>`
    of this tutorial shows how *TraversalDepthFirst*
    with mode *ALL_PATHS* can be used to compute the
    `longest path <longest_path_two_vertices>`
    between two vertices in a weighted graph or in an unweighted graph.


.. _example-topological_sorting_processes:

Topological sorting of process steps
....................................

In this example, vertices are strings that name tasks. The successors of a task are
tasks that have to be done before it.

.. code-block:: python

   >>> depends_on = {
   ...    "make coffee": ["heat water", "fill filter"],
   ...    "get coffee": ["stand up"],
   ...    "get water": ["stand up"],
   ...    "heat water": ["get water"],
   ...    "fill filter": ["get filter", "get coffee"],
   ...    "drink coffee": ["make coffee"],
   ...    "get filter": ["stand up"],
   ... }
   >>> def next_vertices(task, _):
   ...     return depends_on.get(task, ())

We use this graph to find out how to proceed to be able to drink coffee. For that, we
traverse the graph in topological order, and start the problem solution process at
our goal vertex "drink coffee".

We use the *TraversalTopologicalSort* strategy of NoGraphs (see
`Traversal algorithms <traversals>`). It implements the *Topological Sort*
graph algorithm in the NoGraphs style.

.. code-block:: python

   >>> traversal = nog.TraversalTopologicalSort(next_vertices)
   >>> sorted_tasks = tuple(traversal.start_from("drink coffee"))
   >>> sorted_tasks   # doctest: +NORMALIZE_WHITESPACE
    ('stand up', 'get coffee', 'get filter', 'fill filter', 'get water', 'heat water',
    'make coffee', 'drink coffee')

Next, we try out what happens when there is a **cyclic dependency** between the tasks:
We add an artificial dependency that states that *get water* also depends on
*make coffee* and ask NoGraphs again to traverse the graph in topological order:

.. code-block:: python

   >>> depends_on["get water"].append("make coffee")
   >>> tuple(traversal.start_from("drink coffee"))
   Traceback (most recent call last):
   RuntimeError: Graph contains cycle

As you can see, we get a *RuntimeError*, because the tasks cannot be sorted
in a topological order. NoGraphs can **demonstrate the problem** to us by
reporting a path of dependencies from a start vertex (here: our goal to drink
coffee), that leads back to a previous vertex of the same path (here:
we need to *make coffee* before we can *make coffee*):

.. code-block:: python

   >>> traversal.cycle_from_start
   ['drink coffee', 'make coffee', 'heat water', 'get water', 'make coffee']

Finally, we remove the additional dependency again, in order to be able
to re-use the graph in the following section:

.. code-block:: python

   >>> _ = depends_on["get water"].pop()


.. tip::

    When calculations for a vertex depend on results of (positively) connected
    other vertices, we can use the topological sorting of the vertices for ordering
    the calculations in the graph. This is shown in the following two section.


.. _example-critical-path:

Critical path in a weighted, acyclic graph (using topological search)
.....................................................................

We assign (local) runtimes to the tasks shown in the previous section.
For each task, the minimal global
runtime till it is completed (runtime of the **critical path**) is the sum of the
local runtime and the maximum of the total runtimes of the tasks the task depends on.
We order the computations by using the topological sort we got from NoGraphs, so that
each vertex computation is done only after all computations it depends on have been
completed.

.. code-block:: python

   >>> runtime = {
   ...    "make coffee": 2,
   ...    "get coffee": 2,
   ...    "get water": 1,
   ...    "heat water": 3,
   ...    "fill filter": 1,
   ...    "drink coffee": 5,
   ...    "get filter": 2,
   ...    "stand up": 4,
   ... }
   >>> runtime_till_end_of = dict()
   >>> for task in sorted_tasks:
   ...     runtime_till_end_of[task] = runtime[task] + max([0] + [
   ...        runtime_till_end_of[task] for task in next_vertices(task, None)])
   >>> runtime_till_end_of["drink coffee"]
   15


.. _example-longest-path-acyclic-graph:

Longest path in a weighted, acyclic graph (using topological search)
....................................................................

Here, vertices are tuples of *x* and *y* coordinates. A coordinate is an
integer between 0 and 4. There is a cost value assigned to each vertex.

.. code-block:: python

   >>> costs = '''
   ... 02141
   ... 30401
   ... 12121
   ... 50404
   ... 12111
   ... '''.strip().splitlines()

The successors of a vertex are its neighbors to the right and below,
but only those with non-zero costs.
The graph is acyclic, meaning that a path
starting at some vertex cannot lead back to this vertex.
The weight of an edge to a neighbor is determined by the costs of this neighbor.

.. code-block:: python

   >>> def next_edges(vertex, _):
   ...     x, y = vertex
   ...     for dx, dy in [(1, 0), (0, 1)]:
   ...         nx, ny = x + dx, y + dy
   ...         if nx <= 4 and ny <= 4 and (weight := int(costs[ny][nx])) > 0:
   ...             yield (nx, ny), weight

We are searching for a path with the highest total of edge weights from
the start vertex (0, 0) to the goal vertex (4, 4). In other words, we
**are searching for a longest path between two vertices in a weighted, acyclic graph**.

**First, for each vertex reachable from the start vertex, we compute the maximal**
**length of a path to the goal vertex.**

We use the *TraversalTopologicalSort* strategy of NoGraphs (see
`Traversal algorithms <traversals>`).
We traverse the vertices backwards, in topological sorting. This means: When a vertex
is visited, all its successors have already been visited. And we can simply calculate
the maximal length of a path from there to the goal vertex based on the maximal values
we have calculated for its successors and on the respective weights of the edges
leading to them. The value computed for the start vertex is the path length we are
looking for.

.. code-block:: python

   >>> start_vertex, goal_vertex = (0, 0), (4, 4)
   >>> goal_distance = dict()
   >>> traversal = nog.TraversalTopologicalSort(next_edges=next_edges)
   >>> for position in traversal.start_from(start_vertex):
   ...     if position == goal_vertex:
   ...         goal_distance[position] = 0
   ...     else:
   ...         goal_distance[position] = max(
   ...             (goal_distance[successor] + weight
   ...              for successor, weight in next_edges(position, None)
   ...             ), default=-float('inf'))
   >>> goal_distance[start_vertex]
   16

We did not get *-float('inf')* as result, so we can be sure, there is a path to
the goal, and we know its maximal length.

**Then, we compute a longest path, i.e., a path with the already known**
**maximal length.**

For this, we start at the start vertex, and for each vertex, we follow an edge to a
neighbor with the maximal distance to the goal under all neighbors:

.. code-block:: python

    >>> path = []
    >>> vertex = start_vertex
    >>> while vertex != goal_vertex:
    ...     largest = -float('inf')
    ...     for neighbor, weight in next_edges(vertex, None):
    ...         if largest < (distance := goal_distance[neighbor]):
    ...             largest, vertex = distance, neighbor
    ...     path.append(vertex)
    >>> path
    [(1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2), (4, 3), (4, 4)]

.. tip::

    Since *TraversalTopologicalSort* does the work for us, but we defined on our
    own how to compute the optimal *goal_distance*, we can vary this to solve
    similar problems.
    For example, to search for the longest path with an even number of edges,
    we could simply fill two separate containers for optimal goal distances with
    an even and with an odd number of edges.


.. _example-shortest-paths-in-maze:

Shortest paths in a maze with weights
.....................................

Here, vertices are tuples of *x* and *y* coordinates. A coordinate is an
integer between 0 and 4. From each position, the horizontal and vertical
neighbors are the successors, and a move to a neighbor has "costs" that
depend on its position. We re-use function *neighbors_in_grid* from
example `Breadth First Search in a maze <example-traversal-breadth-first-in-maze>`.

.. code-block:: python

   >>> data = '''
   ... 02819
   ... 37211
   ... 21290
   ... 91888
   ... 55990
   ... '''.strip().splitlines()
   >>> def next_edges(position, _):
   ...     for x, y in neighbors_in_grid(position):
   ...         yield (x, y), int(data[y][x])

Based on that, we can take a cost-optimized walk through an area with costs
per place...

We use the traversal strategy *TraversalShortestPaths* of NoGraphs
(see `Traversal algorithms <traversals>`). As already said, it implements the
**Dijkstra** algorithm in the style of NoGraphs.

.. code-block:: python

   >>> traversal = nog.TraversalShortestPaths(next_edges)
   >>> found = traversal.start_from((0,0), build_paths=True).go_to((4,2))
   >>> traversal.distance, traversal.paths[found]  # doctest: +NORMALIZE_WHITESPACE
   (12, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (3, 1), (4, 1),
   (4, 2)))

Later in this tutorial we will see how other types of problems,
e.g., `the traveling salesman <traveling_salesman_example>` problem and
the problem of finding
`shortest paths in infinitely branching graphs with sorted edges <infinite_branching>`,
can be solved using *TraversalShortestPaths* as part of a so-called
`problem reduction <reduction_of_other_problems>`.


.. _example-shortest-paths-with-heuristic:

Shortest path search with distance heuristic (*A\* search*)
...........................................................

Again, vertices are tuples of *x* and *y* coordinates ("position vector"), and a
coordinate is an integer. This time, we use no coordinate limits, valid moves include
the diagonal moves, and all edge weights are 1. We define an obstacle represented by
a set of positions, that build an "L"-form out of two "walls" in the "region" of
positions.

Additionally, we give the search the helpful information, that no path
between two vertices can ever be shorter than the euclidean distance between the
position vectors of the two vertices.

    >>> start, goal = (0, 0), (2, 12)
    >>> moves = ((1, 0), (0, 1), (-1, 0), (0, -1),
    ...          (1, 1), (1, -1), (-1, -1), (-1, 1))
    >>> def next_edges(vertex, _):
    ...     x, y = vertex
    ...     for dx, dy in moves:
    ...         nx, ny = x + dx, y + dy
    ...         if ny == 10 and -1 <= nx <= 2 or nx == 2 and 7 <= ny <= 10:
    ...             continue  # Obstacle in form of two walls forming an L
    ...         yield (nx, ny), 1
    >>> import math
    >>> def heuristic(v):
    ...    return math.dist(v, goal)  # Euclidean distance to goal vertex

Based on that, NoGraphs calculates a path from start to end position that
avoids the obstacle.

We use the traversal strategy *TraversalAStar* of NoGraphs
(see `Traversal algorithms <traversals>`). It implements the **A\* search**
algorithm in the style of NoGraphs.

    >>> traversal =nog.TraversalAStar(next_edges)
    >>> _ = traversal.start_from(heuristic, start, build_paths=True)
    >>> vertex = traversal.go_to(goal)
    >>> traversal.paths[vertex]  # doctest: +NORMALIZE_WHITESPACE
    ((0, 0), (1, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 7), (3, 8),
    (3, 9), (3, 10), (2, 11), (2, 12))
    >>> traversal.path_length  # for the goal vertex, this is the distance
    12
