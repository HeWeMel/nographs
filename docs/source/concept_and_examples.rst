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
of NoGraphs and their use in the context of different traversal algorithms.

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
It implements the *Breadth First Search* graph algorithm in the NoGraphs style.

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
(see https://en.wikipedia.org/wiki/Tower_of_Hanoi).
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

We check that 20000000 (20 million) can be reached from 0. This means, that the number
is even. There might be easier ways to find that out... :-)

We use the *TraversalDepthFirst* strategy of NoGraphs (see
`Traversal algorithms <traversals>`). It implements the well-known
*Depth First Search* algorithm in the NoGraphs style.

.. code-block:: python

   >>> traversal = nog.TraversalDepthFirst(next_vertices, is_tree=True)
   >>> traversal.start_from(0).go_to(20000000)
   20000000

Now, we choose some odd number and try to
**check that it cannot be reached**.
Here are two examples for techniques we can use to to that:

In the first case, we use a *sentinel vertex*, here 20000002, together with
our goal vertex. When the sentinel vertex is reached, we know by the structure
or our graph, that our goal vertex 20000001 - a lower number - will not be
reached anymore.

.. code-block:: python

   >>> next(traversal.start_from(0).go_for_vertices_in( (20000001, 20000002) ))  #doctest:+SKIP
   20000002

In the second case, we define an
*upper limit for the number of allowed calculation steps*,
i.e., a maximal number of vertices to be read in from the graph.
We choose a limit, here 10000001, that is surely high enough to reach the goal
vertex, if it is reachable, but prevents an unnecessarily high run time
or, like in our case, even an infinite run time, if it is not reachable.

.. code-block:: python

   >>> traversal.start_from(0, calculation_limit=10000001).go_to(20000001)  #doctest:+SKIP
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
   >>> traversal.start_from(0).go_to(20000000)  #doctest:+SKIP
   20000000


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

When calculations for a vertex depend on results of (positively) connected
other vertices, we can use the topological sorting of the vertices for ordering
the calculations in the graph.

Example: We assign (local) runtimes to the tasks. For each task, the minimal global
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
*Dijkstra* algorithm in the style of NoGraphs.

.. code-block:: python

   >>> traversal = nog.TraversalShortestPaths(next_edges)
   >>> found = traversal.start_from((0,0), build_paths=True).go_to((4,2))
   >>> traversal.distance, traversal.paths[found]  # doctest: +NORMALIZE_WHITESPACE
   (12, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (3, 1), (4, 1),
   (4, 2)))


.. _example-shortest-paths-with-heuristic:

Shortest path search with distance heuristic
............................................

Again, vertices are tuples of x and y coordinates ("position vector"), and a
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
(see `Traversal algorithms <traversals>`). It implements the *A\* search*
algorithm in the style of NoGraphs.

    >>> traversal =nog.TraversalAStar(next_edges)
    >>> _ = traversal.start_from(heuristic, start, build_paths=True)
    >>> vertex = traversal.go_to(goal)
    >>> traversal.paths[vertex]  # doctest: +NORMALIZE_WHITESPACE
    ((0, 0), (1, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (3, 7), (3, 8),
    (3, 9), (3, 10), (2, 11), (2, 12))
    >>> traversal.path_length  # for the goal vertex, this is the distance
    12
