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

**Example:** Transportation problem

This example illustrates how graph operations can be used for defining
a graph. For the sake of the example, the different steps are done isolated
from each other, even if they could have been combined easily.

We specify the horizontal, vertical and diagonal movements of a truck in a 10 x 10
array of locations, where it can pick up goods. And we specify that it drives
slower the heavier it is.
We like to know the optimal route for delivering all the goods at the
home position, including the decision, whether or not intermediate deliveries
at the home position speed up the travel.

Step 1: We define a graph that connects an integer with itself and with
neighboring integers:

.. code-block:: python

   >>> def next_coordinates(i, _):
   ...     return (i + delta for delta in range(-1, 2))

Step 2: We **prune the graph** to limit it to coordinates in the range 0...9:

.. code-block:: python

   >>> def next_coordinates_restricted(i, _):
   ...     return filter(lambda j: j in range(10), next_coordinates(i,_))

Step 3: We build the **tensor product of the graph with itself** to get moves in
two dimensions (horizontally, vertically, diagonally, and the zero move):

.. code-block:: python

   >>> import itertools
   >>> def next_positions(pos, _):
   ...     return (itertools.product(next_coordinates_restricted(pos[0], _),
   ...                               next_coordinates_restricted(pos[1], _)))

.. tip::

   Not only the tensor product can be implemented that easy:

   If you need a **graph union**, just put the edges of both graphs for a given
   vertex in sets, build the union of them, and return them.

   If you need a **graph intersection**, do the same, but build the intersection of
   the two edge sets, instead of the union.

Step 4: We model the routes of the truck between the home position and 4 positions with
goods. Only the travel distances measured in the number of needed moves according to
step 3 are relevant for our further steps, not the individual positions along a route.

We use **graph abstraction** to simplify our model accordingly and to preserve the
distance measure. The new graph with its restricted vertices and its weighted edges
is defined by function *next_positions_with_distances*, and the weights are calculated
from move counts (here: vertex depths, computed by a Breadth First Search) in the
previous graph.

.. code-block:: python

   >>> home_position = (4, 0)
   >>> goods_positions = (0, 4), (2, 9), (7, 9), (9, 4)
   >>> relevant_positions = goods_positions + (home_position,)
   >>> position_traversal = nog.TraversalBreadthFirst(next_positions)
   >>> import functools
   >>> @functools.cache
   ... def next_positions_with_distances(pos):
   ...     goals = tuple(p for p in relevant_positions if p != pos)
   ...     return tuple((vertex, position_traversal.depth) for vertex in
   ...                  position_traversal.start_from(pos).go_for_vertices_in(goals))

Line *@functools.cache* demonstrates how repeatedly
needed parts of an implicit graph can be **materialized**:
The edges computed for some vertex are stored in a cache, and later, the cache
content is used to avoid repeated computations.

Typically, next vertices or edges should be cached during several traversals
and stored independently of a concrete traversal:

- One possibility is to simply use *@functools.cache* on a function with just the
  vertex as parameter, as demonstrated in the example. (If, additionally, you need
  its functionality in the form of a callback function for a traversal, you can define
  such a function with the necessary signature as a wrapper around the cached function.)

- Another possibility is to implement your own caching within your
  callback function, e.g. by using a *dict*, and cache next vertices or edges only
  based on the current vertex.

The reason for doing so is:

- It makes no sense to cache edges during a single traversal, because for
  each vertex, NoGraphs asks for next edges only once. There would be no cache hits.
- The same holds, if edges were cached for several traversals, but for
  each of them separately.
- Even if several traversal runs are performed based on the same traversal object,
  it is not a good idea to use @functools.case directly on the used NextVertices
  or NextEdges function:
  there is no guarantee that the callback function is always called with the
  same traversal object (see `search aware graphs <search_aware_graphs>`) as
  argument, and so, the cache content for several runs could again be separated
  from each other, instead of being reused.

.. tip::

   In a variant without the line *@functools.cache*, the code shown in this example
   demonstrates how **graph abstraction can be done on the fly**: Calls to
   *next_positions_with_distances* trigger the needed computation of properties of the
   underlying graph defined by *next_positions* (here, some depths are computed).


Step 5: At the goods positions, the truck loads the good that lays there. The truck
is slower the more goods it carries. At the home position, the truck unloads all
goods it carries. We model this as follows:

.. code-block:: python

   >>> good_of_position = dict((pos, good) for good, pos in enumerate(goods_positions))
   >>> def next_states(state, _):
   ...     # truck position, the goods it carries, and the goods that are at home
   ...     position, on_truck, at_home = state
   ...     # Move truck
   ...     for new_position, distance in next_positions_with_distances(position):
   ...         # Load or unload it
   ...         if new_position == home_position:  # unloading
   ...             new_at_home = at_home.union(on_truck)
   ...             new_on_truck = frozenset()
   ...         else:  # loading
   ...             new_at_home = at_home
   ...             new_on_truck = on_truck.union((good_of_position[new_position],))
   ...         # Time for move is distance * (1+no_of_goods)
   ...         yield ((new_position, new_on_truck, new_at_home),
   ...                distance * (1+len(on_truck)))

Step 6: The truck starts its route at the home position. Our goal is to find the most
time efficient way for the truck to get all goods and carry them back to the home
position. So, our start state and our goal state with their respective
position, goods on the truck, and goods at home, are:

.. code-block:: python

   >>> start_state = home_position, frozenset(), frozenset()
   >>> goal_state = home_position, frozenset(), frozenset((0, 1, 2, 3))

We solve the problem by using the Dijkstra shortest paths algorithm of
NoGraphs for the analysis with cost optimization.

.. code-block:: python

   >>> state_traversal = nog.TraversalShortestPaths(next_states)
   >>> _ = state_traversal.start_from(start_state, build_paths=True)
   >>> _ = state_traversal.go_to(goal_state)
   >>> state_traversal.distance  # The costs of the found best route
   65
   >>> for position, on_truck, at_home in state_traversal.paths[goal_state]:
   ...     # Truck positions, goods on the truck, and goods at home position
   ...     print(position, sorted(on_truck), sorted(at_home))
   (4, 0) [] []
   (9, 4) [3] []
   (4, 0) [] [3]
   (7, 9) [2] [3]
   (2, 9) [1, 2] [3]
   (0, 4) [0, 1, 2] [3]
   (4, 0) [] [0, 1, 2, 3]

The result shows that a solution with minimal driving time is: Drive from the home
position to (9, 4) and get the good from there, bring it back home, get the other
goods in the order (7, 9), (2, 9), and (0, 4), and then bring them home.