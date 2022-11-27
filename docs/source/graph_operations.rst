Graph pruning, abstraction, multiplication, union and intersection
------------------------------------------------------------------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

Sometimes, we focus on just a part of a graph and leave out some vertices and edges,
that are outside of our focus. This is a form of *graph pruning*.

Sometimes, we want to analyze a graph from a simplified point of view, that makes it
easier to understand or more efficient to process the graph, but preserves important
properties of it. This is a form of
*graph abstraction*.

Sometimes, we want to combine two graphs by using one of the
typical binary graph operations like *union* and *intersection*
(see `Wikipedia <https://en.wikipedia.org/wiki/Graph_operations>`_ for
details). For example, we could combine them in the sense of a multiplication:
Vertices are combinations of vertices of the two graphs, end edges are combinations
of edges of the two vertices. This creates a *product graph*
(a *tensor product*, *cartesian product*, *lexicographical product*,
or *strong product*, depending of details of the allowed combinations).

All three kinds of operations on graphs are supported by NoGraphs and its API
concept: We can easily implement them in application code on the basis of
*NextVertices* or *NextEdges* functions (see
`graphs and adaptation <graphs_and_adaptation>`),
what gives us flexibility, and we can
use the mechanisms of NoGraphs for necessary computation, what makes the
implementation easier.

**Example:**

The following example illustrates how graph operations can be used for defining
a graph. For the sake of the example, the different steps are done isolated
from each other, even if they could have been combined easily.

Step 1: We define a graph that connects an integer with itself and with
neighboring integers:

.. code-block:: python

   >>> def next_vertices_1d_all(i, _):
   ...     return (i + delta for delta in range(-1, 2))

Step 2: We **prune the graph** to limit it to coordinates in the range 0...9:

.. code-block:: python

   >>> def next_vertices_1d(i, _):
   ...     return filter(lambda j: j in range(10), next_vertices_1d_all(i,_))

Step 3: We build the **tensor product of the graph with itself** to get moves in
two dimensions (horizontally, vertically, diagonally, and the zero move):

.. code-block:: python

   >>> import itertools
   >>> def next_vertices_2d(pos, _):
   ...     return (itertools.product(next_vertices_1d(pos[0], _),
   ...                               next_vertices_1d(pos[1], _)))

.. tip::

   Not only the tensor product can be implemented that easy:

   If you need a **graph union**, just put the edges of both graphs for a given
   vertex in sets, build the union of them, and return them.

   If you need a **graph intersection**, do the same, but build the intersection of
   the two edge sets, instead of the union.

Step 4: We model the routes of a truck between a home position and 4 positions with
goods. Only the travel distances measured in the needed moves according to step 3 are
relevant for our further steps, not the individual positions along a route.

We use **graph abstraction** to simplify our model accordingly and to preserve the
distance measure. The new graph with its restricted vertices and its weighted edges
are defined by function next_vertices_pos, and the weights are calculated from move
counts (here: vertex depths) in the previous graph.

.. code-block:: python

   >>> home_position = (4, 0)
   >>> goods_positions = (0, 4), (2, 9), (7, 9), (9, 4)  # id to position
   >>> relevant_positions = goods_positions + (home_position,)
   >>> traversal4 = nog.TraversalBreadthFirst(next_vertices_2d)
   >>> import functools
   >>> @functools.cache
   ... def next_vertices_pos(pos, _):
   ...     goals = tuple(p for p in relevant_positions if p != pos)
   ...     return tuple((vertex, traversal4.depth) for vertex in
   ...                  traversal4.start_from(pos).go_for_vertices_in(goals))

.. tip::

   - Without the line @functools.cache, this code demonstrates how **graph abstraction
     can be done on the fly**: Calls to next_vertices_pos trigger the needed
     computation of properties of the underlying graph defined by next_vertices_2d
     (here, some depths are computed).

   - Together with the line @functools.cache, the code demonstrates how repeatedly
     needed parts of a graph can be **materialized**, if the graph is defined in an
     implicit way by using a NextVertices function: Computed edges are stored in a
     cache and the results in the cache are used to avoid repeated computations.

Step 5: At the goods positions, the truck loads the good that lays there. The truck
is slower the more goods it carries. At the home position, the truck unloads all
goods it carries. We model this as follows:

.. code-block:: python

   >>> position_to_good = dict((p, g) for g, p in enumerate(goods_positions))
   >>> def next_edges_way(state, _):
   ...     # truck position, the goods it carries, and the goods that are at home
   ...     position, on_truck, at_home = state
   ...     # Move truck
   ...     for new_position, distance in next_vertices_pos(position, None):
   ...         # Load or unload it
   ...         if new_position == home_position:  # unloading
   ...             new_at_home = at_home.union(on_truck)
   ...             new_on_truck = frozenset()
   ...         else:  # loading
   ...             new_at_home = at_home
   ...             new_on_truck = on_truck.union((position_to_good[new_position],))
   ...         # Time for move is distance * no_of_goods
   ...         yield ((new_position, new_on_truck, new_at_home),
   ...                distance * (1+len(on_truck)))

Step 6: The truck starts its route at the home position. Our goal is to find the most
performant way for the truck to get all goods and carry them back to the home
position.

.. code-block:: python

   >>> start = home_position, frozenset(), frozenset()
   >>> goal = home_position, frozenset(), frozenset((0, 1, 2, 3))

We do not now, whether the truck performs better by repeatedly returning to
the home position with parts of the goods or by collecting all the goods and then
returning to the home position. We use the Dijkstra shortest paths algorithm of
NoGraphs for the analysis with cost optimization.

.. code-block:: python

   >>> traversal = nog.TraversalShortestPaths(next_edges_way)
   >>> traversal = traversal.start_from(start, build_paths=True)
   >>> vertex = traversal.go_to(goal)
   >>> traversal.distance  # The costs of the found best route
   65
   >>> for position, on_truck, at_home in traversal.paths[vertex]:
   ...     # Truck positions, goods on the truck, and goods at home position
   ...     print(position, tuple(on_truck), tuple(at_home))
   (4, 0) () ()
   (9, 4) (3,) ()
   (4, 0) () (3,)
   (7, 9) (2,) (3,)
   (2, 9) (1, 2) (3,)
   (0, 4) (0, 1, 2) (3,)
   (4, 0) () (0, 1, 2, 3)
