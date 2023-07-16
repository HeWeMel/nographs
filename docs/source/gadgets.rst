Gadgets
-------

..
   Import nographs for doctests of this document. Does not go into docs.
   >>> import nographs as nog

The functions and classes explained in this section ease the adaptation
of existing graphs, especially for quick tests with some small examples.

They do not belong to the core of NoGraphs, are not needed for
productive use of the library, and are only gradually typed.

.. _edge_gadgets:

Graphs stored in edge indices or edge iterables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you have already computed your graph, you might have stored
it in some dictionary, tuple or list. Then, the following support functions
might help you with `adapting <graphs_and_adaptation>` it for NoGraphs.

Function `nographs.adapt_edge_iterable`
+++++++++++++++++++++++++++++++++++++++

This function returns a `NextVertices` or `NextEdges` function for graphs that are
stored in a **list of edges**. The examples show the use cases and the
respective application of the function:

  - **Iterable of unlabeled, unweighted edges**, e.g. a tuple or list

    .. code-block:: python

     >>> edges1 = (('A', 'B'), ('A', 'C'), ('C', 'D'))
     >>> next_vertices_1 = nog.adapt_edge_iterable(
     ...    edges1, add_inverted=False, attributes=False)

  - **Iterable of labeled and/or weighted edges**, e.g. a tuple or list, and
    the **labels and weights should be ignored**

    .. code-block:: python

     >>> edges2 = (('A', 'B', 30), ('A', 'C', 10), ('C', 'D', 10))
     >>> next_vertices_2 = nog.adapt_edge_iterable(
     ...    edges2, add_inverted=False, attributes=False)

  - **Iterable of labeled and/or weighted edges**, e.g. a tuple or list, and
    the **labels and/or weights should be used**

    .. code-block:: python

     >>> edges2 = (('A', 'B', 30), ('A', 'C', 10), ('C', 'D', 10))
     >>> next_edges_1 = nog.adapt_edge_iterable(
     ...    edges2, add_inverted=False, attributes=True)

..
   Hidden DocTests:

   >>> traversal = nog.TraversalDepthFirst(next_vertices_1)
   >>> tuple(traversal.start_from('A', build_paths=True))
   ('C', 'D', 'B')
   >>> traversal = nog.TraversalShortestPaths(next_edges_1)
   >>> tuple(traversal.start_from('A', build_paths=True))
   ('C', 'D', 'B')
   >>> traversal = nog.TraversalDepthFirst(next_vertices_2)
   >>> tuple(traversal.start_from('A', build_paths=True))
   ('C', 'D', 'B')

**Parameters:**

- Parameter *attributes* informs function `adapt_edge_index` whether the given
  **graph consists of labeled and/or weights edges**
  and the **labels and/or weights should be take into the generated function**.

- Set parameter *add_inverted* to True, **if your graph is undirected** (i.e., two
  vertices are always either connected by edges in both directions or not connected
  by any edge),
  **but in your data structure, each edge is given only in one direction**.
  Then, for each given edge, the edge in the opposite direction will be added
  automatically.

For more details, see the `API reference <adapt_edge_iterable>`.


Function `adapt_edge_index`
++++++++++++++++++++++++++++++

This function returns a `NextVertices` or `NextEdges` function for graphs that are
stored in one of the following **ways that provide a kind of neighborship index**,
i.e. a mapping or indexed sequence, that maps from a vertex to connected vertices
or to outgoing edges. The examples show the use cases and the
respective application of the function:

- **Mapping from vertices to connected vertices**, e.g. in a dictionary

  .. code-block:: python

   >>> edges1 = {'A': ('B', 'C'), 'C': ('D',)}
   >>> next_vertices_1 = nog.adapt_edge_index(
   ...    edges1, add_inverted=False, attributes=False)

- **Sequence of respectively connected vertices**, e.g. built of tuples or lists,
  and vertices are the integers

  .. code-block:: python

   >>> edges2 = ((1, 2), (), (3,))  # same as above, 0...3 used instead of A...D
   >>> next_vertices_2 = nog.adapt_edge_index(
   ...    edges2, add_inverted=False, attributes=False)

- **Mapping from vertices to outgoing edges with edge attributes**
  (weights and/or labels), e.g. in a dictionary

  .. code-block:: python

   >>> edges3 = {'A': (('B', 30), ('C', 10)), 'C': (('D', 10),)}
   >>> next_edges_1 = nog.adapt_edge_index(
   ...    edges3, add_inverted=False, attributes=True)

- **Sequence of respectively outgoing edges with edge attributes**
  (weights and/or labels), e.g. built of tuples or lists

  .. code-block:: python

   >>> edges4 = (((1, 30), (2, 10)), (), ((3, 10),))
   >>> next_edges_2 = nog.adapt_edge_index(
   ...    edges4, add_inverted=False, attributes=True)

..
   Hidden DocTests:

   >>> traversal = nog.TraversalDepthFirst(next_vertices_1)
   >>> tuple(traversal.start_from('A', build_paths=True))
   ('C', 'D', 'B')
   >>> traversal = nog.TraversalDepthFirst(next_vertices_2)
   >>> tuple(traversal.start_from(0, build_paths=True))
   (2, 3, 1)
   >>> traversal = nog.TraversalShortestPaths(next_edges_1)
   >>> tuple(traversal.start_from('A', build_paths=True))
   ('C', 'D', 'B')
   >>> traversal = nog.TraversalShortestPaths(next_edges_2)
   >>> tuple(traversal.start_from(0, build_paths=True))
   (2, 3, 1)

Let's try out one of the generated neighborship functions:

.. code-block:: python

   >>> for vertex in "ABCD":
   ...    print("For vertex {}, it returns {}".format(
   ...          vertex, next_vertices_1(vertex, None)))
   For vertex A, it returns ('B', 'C')
   For vertex B, it returns ()
   For vertex C, it returns ('D',)
   For vertex D, it returns ()

**Parameters:**

- Set parameter *attributes* to *True* if the given graph
  consists of **edges with edge attributes**, and to *False*,
  if **connected vertices** are provided.

- Set parameter *add_inverted* to True, **if your graph is undirected** (i.e., two
  vertices are always either connected by edges in both directions or not connected
  by any edge), **but in your data structure, each edge is given only in one direction**.
  Then, for each given edge, the edge in the opposite direction will be added
  automatically:

  .. code-block:: python

     >>> next_vertices_1b = nog.adapt_edge_index(
     ...    edges1, add_inverted=True, attributes=False)
     >>> for vertex in "ABCD":
     ...    print("For vertex {}, it returns {}".format(
     ...          vertex, next_vertices_1b(vertex, None)))
     For vertex A, it returns ['B', 'C']
     For vertex B, it returns ['A']
     For vertex C, it returns ['A', 'D']
     For vertex D, it returns ['C']

  Please note: when this option is used, a copy of your graph will be held
  by the returned `NextVertices` or `NextEdges` function.

For more details, see the `API reference <adapt_edge_index>`.


.. _matrix_gadgets:

Graphs stored in arrays
~~~~~~~~~~~~~~~~~~~~~~~

In case you have graph content that is
**stored in nested sequences that form a multi-dimensional array**,
the following support functions might help you with
`adapting <graphs_and_adaptation>` it for NoGraphs.


Class `Array <nographs.Array>`
++++++++++++++++++++++++++++++

The functionality of the class can be divided in four groups. We explain them
using the **example of a maze stored in a string**.

**1) Array creation from nested sequences**

   **Example:** Character *S* marks
   the start vertex, *G* the goal vertex, and *#* positions we are not allowed to
   enter. We apply the Python functions *strip()* and *splitlines()* and get nested
   sequences: a Python array.

   .. code-block:: python

      >>> maze = '''
      ... S..#.
      ... .#.#G
      ... #G...
      ... '''.strip().splitlines()
      >>> maze
      ['S..#.', '.#.#G', '#G...']

   We use this array data to construct a two-dimensional NoGraphs Array object
   from it.

   Note, that we have to specify the number of dimensions explicitly, because
   iterable content cannot be distinguished syntactically from a further dimension.

   .. code-block:: python

      >>> a = nog.Array(maze, 2)

**2) Accessing the array**

   Now, we can use the methods of the Array class to access array content
   by using tuples of integers to address array cells, search content in the
   array and read properties. The following code illustrates this:

   .. code-block:: python

      >>> # Content at position (1, 4)
      >>> a[(1,4)]
      'G'
      >>> # Positions that contain content "S"
      >>> a.findall("S")
      ((0, 0),)
      >>> # Iterate positions and content
      >>> tuple(a.items())  # doctest: +NORMALIZE_WHITESPACE
      (((0, 0), 'S'), ((0, 1), '.'), ((0, 2), '.'), ((0, 3), '#'), ((0, 4), '.'),
      ((1, 0), '.'), ((1, 1), '#'), ((1, 2), '.'), ((1, 3), '#'), ((1, 4), 'G'),
      ((2, 0), '#'), ((2, 1), 'G'), ((2, 2), '.'), ((2, 3), '.'), ((2, 4), '.'))
      >>> # Size of the array per dimension
      >>> a.size()
      [3, 5]
      >>> # Coordinate ranges per dimension
      >>> a.limits()
      [(0, 3), (0, 5)]

   Note, that coordinates of a position in the array are meant in the order from "outer"
   to "inner" dimensions.

   **In the example:** We now use method *findall* to define our start and goal
   positions based on the array content:

   .. code-block:: python

      >>> starts, goals = (a.findall(c) for c in "SG")

**3) Mutable arrays**

  We can
  **create a mutable array just by initiating it by mutable nested sequences**,
  e.g., a list of lists.

  But it is also possible to use NoGraphs to
  **create a mutable Array from an immutable one**, and then to change its contents:

  .. code-block:: python

    >>> mutable_array = a.mutable_copy()
    >>> mutable_array[(0, 2)] = 'S'
    >>> mutable_array[(0, 2)]
    'S'


.. _class_array_part_4:

**4) Automate the generation of NextVertices or NextEdges function**

   **In the example:** We use the array content to define a `NextVertices`
   function, based on the information, that content "#" means "no edge to
   this position":

       >>> next_vertices = a.next_vertices_from_forbidden("#")

   With both together, we can search for paths that go from start to goal vertices
   and avoid the forbidden positions:

   .. code-block:: python

      >>> traversal = nog.TraversalBreadthFirst(next_vertices)
      >>> for found in traversal.start_from(start_vertices=starts, build_paths=True
      ...     ).go_for_vertices_in(goals):
      ...         traversal.depth, traversal.paths[found]
      (5, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)))
      (7, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (1, 4)))

   Optionally, we can choose that moves (edges) in the array positions should
   wrap at the position limits of each dimension, or that "diagonal" moves
   should be allowed, see
   the `API reference <nographs.Array.next_vertices_from_forbidden>`.

   For **cases where the array content at a position defines the edge weight** of edges
   leading there, we can use method *next_edges_from_cell_weights* instead of
   method *next_vertices_from_forbidden*.
   As input for the function, we give the mapping from array content to edge weight.
   The following code illustrates this based on a new, adapted maze:

   .. code-block:: python

     >>> a = nog.Array('''
     ... S2819
     ... 37211
     ... 212#G
     ... '''.strip().splitlines(), 2)
     >>> start, goal = (a.findall(c)[0] for c in "SG")
     >>> weights = {str(i): i for i in range(10)} | {"G": 0}

     >>> traversal = nog.TraversalShortestPaths(a.next_edges_from_cell_weights(weights))
     >>> found = traversal.start_from(start, build_paths=True).go_to(goal)
     >>> traversal.distance, traversal.paths[found]
     (12, ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (1, 3), (1, 4), (2, 4)))

.. tip::
   For cases, where the methods *next_vertices_from_forbidden* and
   *next_vertices_from_cell_weights* of class *Array* do not cover your
   exact scenario, you can easily combine functionality of the other methods of
   class *Array* with functionality of class `Position <nographs.Position>`
   in order to
   `manually define your individual callback function <maze_function_manually>`.
   In fact, this is how the two methods are implemented.


.. _tutorial_position:

Class `Position <nographs.Position>`
++++++++++++++++++++++++++++++++++++

A cell position in a n-dimensional array can be stored and manipulated in an
instance of this class.

We can **create a Position, add and subtract other vectors, multiply an integer,
and calculate the manhattan distance of another vector to our position**:

   .. code-block:: python

      >>> # Position, from sequence of int coordinates ("Vector")
      >>> nog.Position([1, 2, 3])
      (1, 2, 3)
      >>> # Position, from int coordinates given as separate parameters
      >>> nog.Position.at(1, 2, 3)
      (1, 2, 3)
      >>> # Position plus coordinate vector (or Position), returns Position
      >>> nog.Position.at(1, 2, 3) + (1, 1, 1)  + (2, 2, 2)
      (4, 5, 6)
      >>> # Position minus coordinate vector (or Position), returns Position
      >>> nog.Position.at(2, 3, 4) - (1, 1, 1)
      (1, 2, 3)
      >>> # Position vector multiplied by an integer value, returns Position
      >>> nog.Position.at(2, 3, 4) * 3
      (6, 9, 12)
      >>> # Attention: Since a Position is a tuple, i * Position repeats the coordinates
      >>> 3 * nog.Position.at(2,3,4)
      (2, 3, 4, 2, 3, 4, 2, 3, 4)
      >>> # Manhattan distance of some vector
      >>> nog.Position.at(2, 3, 4).manhattan_distance( (1, 1, 1) )
      6

When we use vector addition or subtraction to "move" some increment away from a
position, we could "leave" some coordinate ranges we would like to stay in.
Class Position allows to **check for coordinate boundaries** (range per dimension)
and to **"wrap" moves at such boundaries**:

   .. code-block:: python

      >>> # The lower limit per dimension is meant inclusively, the upper limit exclusively.
      >>> # These ranges define a cuboid of allowed coordinates. Is the position in the cuboid?
      >>> limits = ((0, 3),) * 3
      >>> [nog.Position(v).is_in_cuboid(limits) for v in ((0, 1, 0), (2, 0, 2), (3, 0, 0))]
      [True, True, False]
      >>> # After position changes, wrap the position at the chosen coordinate ranges
      >>> pos = nog.Position.at(0, 1, 2)
      >>> move = (1, 1, 1)
      >>> for i in range(3):
      ...    pos = (pos + move).wrap_to_cuboid(limits)
      ...    print (pos)
      (1, 2, 0)
      (2, 0, 1)
      (0, 1, 2)
      >>> # A coordinate, that is far off, is wrapped like we would go towards
      >>> # the cuboid by the size of the coordinate range as often as necessary
      >>> # to come back to the allowed range.
      >>> [nog.Position(v).wrap_to_cuboid(((-2, 3),) * 2)
      ...  for v in ((0, 0), (-2, 2), (-3, 3), (-7, 7), (-8, 8))]
      [(0, 0), (-2, 2), (2, -2), (-2, 2), (2, -2)]

Class Position can **generate some types of "move vectors"**:
with or without "diagonal" moves, with or without the zero move, and we can choose
the number of dimensions:

   .. code-block:: python

      >>> # We generate some types of 2-dimensional move vectors
      >>> nog.Position.moves()
      [(-1, 0), (0, -1), (0, 1), (1, 0)]
      >>> nog.Position.moves(diagonals=True)
      [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
      >>> nog.Position.moves(zero_move=True)
      [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]
      >>> # Now, we generate some 3-dimensional move vectors
      >>> nog.Position.moves(3)
      [(-1, 0, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (0, 1, 0), (1, 0, 0)]
      >>> nog.Position.moves(3, diagonals=True)   # doctest: +NORMALIZE_WHITESPACE
      [(-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, 0, -1), (-1, 0, 0), (-1, 0, 1),
      (-1, 1, -1), (-1, 1, 0), (-1, 1, 1), (0, -1, -1), (0, -1, 0), (0, -1, 1),
      (0, 0, -1), (0, 0, 1), (0, 1, -1), (0, 1, 0), (0, 1, 1), (1, -1, -1), (1, -1, 0),
      (1, -1, 1), (1, 0, -1), (1, 0, 0), (1, 0, 1), (1, 1, -1), (1, 1, 0), (1, 1, 1)]
      >>> nog.Position.moves(3, non_zero_counts=range(2, 3))   # doctest: +NORMALIZE_WHITESPACE
      [(-1, -1, 0), (-1, 0, -1), (-1, 0, 1), (-1, 1, 0), (0, -1, -1), (0, -1, 1),
      (0, 1, -1), (0, 1, 1), (1, -1, 0), (1, 0, -1), (1, 0, 1), (1, 1, 0)]

Class Position can **calculate "neighbor" positions** based on such moves, and keeps
given coordinate limits:

   .. code-block:: python

      >>> v = nog.Position((5, 5))
      >>> moves = nog.Position.moves()
      >>> tuple(v.neighbors(moves))
      ((4, 5), (5, 4), (5, 6), (6, 5))
      >>> tuple(v.neighbors(moves, limits=((0, 6), (0, 6))))
      ((4, 5), (5, 4))
      >>> tuple(v.neighbors(moves, limits=((0, 6), (0, 6)), wrap=True))
      ((4, 5), (5, 4), (5, 0), (0, 5))
      >>> # When we choose wrapping, of cause we have to provide limits
      >>> tuple(v.neighbors(moves, wrap=True))
      Traceback (most recent call last):
      RuntimeError: Limits for Option wrap missing

Please find details in the `API reference <nographs.Position>`.


.. _maze_function_manually:

Example: Hand-made NextVertices function for a maze
+++++++++++++++++++++++++++++++++++++++++++++++++++

In the following example code, we use the functionality of classes *Array* and
*Position* to manually define a maze adaptation function.

We initiate a NoGraphs array by our maze:

.. code-block:: python

   >>> array = nog.Array('''
   ... S..#.
   ... .#.#G
   ... #G...
   ... '''.strip().splitlines(), 2)

Instead of calling method
`Array.next_vertices_from_forbidden <nographs.Array.next_vertices_from_forbidden>`
like we saw it in `the section about class Array <class_array_part_4>`,
we now create our `NextVertices` function manually, to be able to adapt
the code to our needs:

.. code-block:: python

   >>> limits = array.limits()
   >>> moves = nog.Position.moves(2)
   >>> def next_vertices(position, _):
   ...     for neighbor in position.neighbors(moves, limits):
   ...         if array[neighbor] != "#":
   ...            yield neighbor
   ...     return next_vertices

Then, we test it by traversing the maze from start to both goal positions:

.. code-block:: python

   >>> traversal = nog.TraversalBreadthFirst(next_vertices)
   >>> traversal = traversal.start_from(start_vertices=starts, build_paths=True)
   >>> for found in traversal.go_for_vertices_in(goals):
   ...     traversal.depth, traversal.paths[found]
   (5, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)))
   (7, ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 3), (2, 4), (1, 4)))
