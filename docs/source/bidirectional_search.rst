Bidirectional search algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

.. versionadded:: 3.1

The analysis algorithms `presented so far <traversals>` traverse a graph
in "forward" direction, i.e., they start from one or more start vertices, follow the
edges, and terminate when the purpose of the analysis has been achieved. They use
a `NextVertices` (resp. a `NextEdges`) function that provides the **outgoing** edges
of a vertex in **forward** direction.

We can also use them to traverse the graph "backwards", starting from one or more goal
vertices, if we can implement a `NextVertices` (resp. a `NextEdges`) function that
provides the **incoming** edges of a vertex in **backward** direction.

A *bidirectional search* combines both approaches: It works with two traversals,
one for each direction, and terminates the search when both (partial) results
taken together achieve the analysis purpose.

NoGraphs offers two bidirectional search strategies: `nographs.BSearchBreadthFirst` and
`nographs.BSearchShortestPath`. They are suitable for the following kind of situation:

- The **(only) result we need is a path (or just its length)** from some start
  vertices to some goal vertices and
- we **can provide** `NextVertices` (resp. `NextEdges`)
  **functions for both traversal directions**.

In the following, we illustrate these search strategies by examples.

.. _example-bsearch-shortest-path:

**Example for BSearchShortestPath:** We are in the maze shown below. A position in
the maze is described by two integer coordinates *y* and *x*. The position of the upper
left corner is *(0, 0)*.

For each position, the maze shows either a digit, specifying the elevation
of the position, or a dot. On our way through the maze, we can only
use positions with an elevation. In each step, we can go to a direct
neighbor position in either horizontal or vertical direction.

A step from a current elevation to a lower elevation costs one energy unit,
a step to a higher elevation costs one energy unit plus the elevation
difference.

We start at the position of the bottom left corner. Our
goal is to reach the position of the upper right corner, on a path with
minimum total energy costs.

.. code-block:: python

    >>> maze = """\
    ... 0000000000000000000000000000000000000000.00000.5
    ... 0......................................0.0.0.0.4
    ... 0.000000000000000000000000000000000000.0.0.0.0.4
    ... 0.0..................................0.0.0.0.0.4
    ... 0.0.00000000000000000000000000000000.0.0.0.0.0.3
    ... 0.0.0.0..........................0.0.0.0.0.0.0.2
    ... 0.0.0.0.000000000000000000000000.0.0.0.0.0.0.0.1
    ... 0.0.0.0.0......................0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.00000000000000000000.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0..................0.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0000000000000000.0.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0............0.0.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.00000000...0.0.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0......0...0.0.0.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0000900000000000.0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0..0...0.........0.0.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0..0...0000000000000.0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0..0.................0.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0..0000000000000000000.0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.0......................0.0.0.0.0
    ... 0.0.0.0.0.0.0.0.000000000000000000000000.0.0.0.0
    ... 0.0.0.0.0.0.0.0..........................0.0.0.0
    ... 1.0.0.0.0.0.00000000000000000000000000000000.0.0
    ... 2.0.0.0.0.0..................................0.0
    ... 2.0.0.0.0.000000000000000000000000000000000000.0
    ... 2.0.0.0.0......................................0
    ... 3.00000.0000000000000000000000000000000000000000
    ... """.splitlines()

We specify the problem by the following code:

.. code-block:: python

   >>> maze_width, maze_height = len(maze[0]), len(maze)
   >>> start_pos, goal_pos = (0, maze_height-1), (maze_width-1, 0)

   >>> def neighbors_in_grid(position):
   ...     """ For a given position, return all neighbor positions in the maze """
   ...     # Count the regarded positions in the maze (not needed for the problem itself)
   ...     global evaluated_positions
   ...     evaluated_positions += 1
   ...     # Check each neighbor position, return it if it is within the maze limits
   ...     pos_x, pos_y = position
   ...     for move_x, move_y in (-1, 0), (1, 0), (0, -1), (0, 1):
   ...         new_x, new_y = pos_x + move_x, pos_y + move_y
   ...         if new_x in range(maze_width) and new_y in range(maze_height):
   ...             yield new_x, new_y
   >>> def content(maze, pos):
   ...     """ Return content (character) of maze (a list of strings) at given position """
   ...     x, y = pos
   ...     return maze[y][x]
   >>> def weight(maze, from_pos, to_pos):
   ...     """ Compute costs of step from from_pos to to_pos """
   ...     gradient = int(content(maze, to_pos)) - int(content(maze, from_pos))
   ...     return 1 + max(0, gradient)

   >>> def out_edges(previous_position, _):
   ...     """ For a given position, report outgoing edges as (to_position, weight) """
   ...     for next_position in neighbors_in_grid(previous_position):
   ...         if content(maze, next_position) != ".":
   ...             yield next_position, weight(maze, previous_position, next_position)
   >>> def in_edges(next_position, _):
   ...     """ For a given position, report incoming edges as (from_position, weight) """
   ...     for previous_position in neighbors_in_grid(next_position):
   ...         if content(maze, previous_position) != ".":
   ...             yield previous_position, weight(maze, previous_position, next_position)

Now, we use the traversal strategy `TraversalShortestPaths` of NoGraphs, based on
`NextEdges` function *out_edges*, to find the length (sum of edge weights)
of the shortest path from start to goal position. And we count, how many
positions we have regarded to find the solution.

.. code-block:: python

   >>> evaluated_positions = 0
   >>> traversal = nog.TraversalShortestPaths(out_edges)
   >>> vertex = traversal.start_from(start_pos).go_to(goal_pos)
   >>> print(f"{traversal.distance=}, {evaluated_positions=}")
   traversal.distance=254, evaluated_positions=685

Then, we do the same again, but we use the bidirectional search strategy
`BSearchShortestPath` of NoGraphs, based both on *out_edges* and *in_edges*:

.. code-block:: python

   >>> evaluated_positions = 0
   >>> search = nog.BSearchShortestPath((out_edges, in_edges))
   >>> length, path = search.start_from((start_pos, goal_pos))
   >>> print(f"{length=}, {evaluated_positions=}")
   length=254, evaluated_positions=270

Of cause, we get the same path length in both cases.
But **the bidirectional search regards only 270 positions** before it finds an
optimal solution, whilst **the unidirectional search regards 685 positions**!
This means that for the given kind of problem, the bidirectional search can
avoid regarding a large percentage of positions in comparison to the unidirectional
search.

.. _example-bsearch-breadth-first:

**Example for BSearchBreadthFirst:** Now, we do a similar comparison between
`TraversalBreadthFirst` and its bidirectional search variant `BSearchBreadthFirst`.
Here, our maze has no elevation profile, but just contains character "#" for allowed
positions and "." for forbidden positions. Again, we search a path from the bottom
left position to the top right position. We re-use the functions *neighbors_in_grid*
and *content* of the previous example.

.. code-block:: python

   >>> maze = """\
   ... ###################################################
   ... .........................#.........................
   ... ###################################################
   ... .........................#.........................
   ... ###################################################
   ... .........................#.........................
   ... ###################################################
   ... .........................#.........................
   ... ###################################################
   ... """.splitlines()

.. code-block:: python

   >>> maze_width, maze_height = len(maze[0]), len(maze)
   >>> start_pos, goal_pos = (0, maze_height-1), (maze_width-1, 0)
   >>> def out_edges(previous_position, s):
   ...     """ For a given position, report the end vertices of outgoing edges """
   ...     for next_position in neighbors_in_grid(previous_position):
   ...         if content(maze, next_position) != ".":
   ...             yield next_position
   >>> def in_edges(next_position, s):
   ...     """ For a given position, report the start vertices of incoming edges """
   ...     for previous_position in neighbors_in_grid(next_position):
   ...         if content(maze, previous_position) != ".":
   ...             yield previous_position

First, we use the traversal strategy `TraversalBreadthFirst`:

.. code-block:: python

   >>> evaluated_positions = 0
   >>> traversal = nog.TraversalBreadthFirst(out_edges)
   >>> vertex = traversal.start_from(start_pos).go_to(goal_pos)
   >>> print(f"{traversal.depth=}, {evaluated_positions=}")
   traversal.depth=58, evaluated_positions=257

Then, we do the same again, but we use the bidirectional search strategy
`BSearchBreadthFirst`:

.. code-block:: python

   >>> evaluated_positions = 0
   >>> search = nog.BSearchBreadthFirst((out_edges, in_edges))
   >>> length, path = search.start_from((start_pos, goal_pos))
   >>> print(f"{length=}, {evaluated_positions=}")
   length=58, evaluated_positions=68

Again, of course, we get the same path length in both cases.
But **the bidirectional search regards only 68 positions** before it finds an
optimal solution, whilst **the unidirectional search regards 257 positions**.

Note, that out_edges and in_edges are identical (apart from variable renaming) here.
The reason is that in this example, our graph is symmetric: if (v, w) is an edge,
(w, v) is also an edge. So, we can also perform the search using just one of the
functions:

.. code-block:: python

   >>> evaluated_positions = 0
   >>> search = nog.BSearchBreadthFirst((out_edges, out_edges))
   >>> length, path = search.start_from((start_pos, goal_pos))
   >>> print(f"{length=}, {evaluated_positions=}")
   length=58, evaluated_positions=68
