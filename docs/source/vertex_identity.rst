Identity and equivalence of vertices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each of the classes described in the sections
`traversal algorithms <traversals>` and
`bidirectional search algorithms <bidirectional_search>`,
there is another, more flexible class,
with "Flex" appended to the class name. These classes have two more parameters,
*vertex_to_id* and *gear*. In this section, we explain the former parameter,
in the `next section <gears>` the latter parameter.

.. versionchanged:: 3.0

   Traversal classes and their "...Flex" variants separated in order to
   get easier and more intuitive signatures for both variants.

The default behavior of NoGraphs with respect to **vertex identity** is the
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

  Example:

  You use instances of some vertex class of your application as vertices.
  They are mutable, and thus not hashable. Each vertex object is to be
  seen as a different vertex.

  In this situation, you can simply use the Python
  function *id* as *VertexToID* function.

- **Mutable vertex objects, and their immutable counterparts identify them**

  Example:

  You use lists as your vertices. You know that their content will not
  change during a traversal run. And the immutable tuple counterpart of a
  vertex is well suited for getting a hash value.

  In this situation, you can use function *tuple* as *VertexToID* function.

- **Traversal in equivalence classes of vertices**

  Example:

  You have defined an abstraction function, that assigns an equivalence class to a
  vertex. And you know: Whenever there is a path of vertices, there is a
  respective path in the equivalence classes of these vertices. And whenever
  their is a path in the equivalence classes, there is a respective path in
  the vertices of these classes. You would like to solve some analysis
  problem in the equivalence classes instead of the vertices, because there,
  the analysis is easier to do.

  Here, you can use your abstraction function as *VertexToID* function.

.. _equivalence_class_example:

**Example: Traversal of vertex equivalence classes, on the fly**

We have a maze of the following form, where "S" denotes a start position
of a player, "G" a goal position, "." additional positions that can be occupied,
and "#" forbidden positions.

::

    SSSS.
    ..#..
    ....#
    .#...
    .GGGG

We play a game. We start with the state, where each start position is occupied by
exactly one player. In each step of the game, each player makes a move to a horizontal
of vertical neighbor position that is not forbidden, or it stays at
his position. After each step, no two players can have the same position.

We like to find out, how many steps of the game are necessary to come to the state
where all players are at goal positions.

..
  This block does not go into the docs.

  Import nographs for doctests of this document.
  >>> import nographs as nog

  Define again the same neighbors_in_grid.
  >>> def neighbors_in_grid(position):
  ...     pos_x, pos_y = position
  ...     for move_x, move_y in (-1, 0), (1, 0), (0, -1), (0, 1):
  ...         new_x, new_y = pos_x + move_x, pos_y + move_y
  ...         if new_x in range(5) and new_y in range(5):
  ...             yield new_x, new_y
  ...

Based on function *neighbors_in_grid* of example
`example-traversal-breadth-first-in-maze`, we define how to compute the allowed
next positions for a player from his position.

.. code-block:: python

    >>> forbidden_fields = {(2, 1), (4, 2), (1, 3)}
    >>> def allowed_next_positions(position):
    ...     yield position
    ...     for x, y in neighbors_in_grid(position):
    ...         if not (x, y) in forbidden_fields:
    ...             yield (x, y)

Then, we define the states that can follow after a given state, then the start state and
the goal states.

.. code-block:: python

    >>> import itertools
    >>> def next_vertices(state, _):
    ...     for next_state in itertools.product(
    ...         *(allowed_next_positions(pos) for pos in state)
    ...     ):
    ...         # For python 3.10: The following check is equal to:
    ...         # all(p1 != p2 for p1, p2 in itertools.pairwise(sorted(next_state)))
    ...         sorted_pos = sorted(next_state)
    ...         if all(sorted_pos[i] != sorted_pos[i+1]
    ...                for i in range(len(sorted_pos)-1)):
    ...             yield next_state
    >>> start_state = ((0, 0), (1, 0), (2, 0), (3, 0))
    >>> goal_states = set(itertools.permutations(((1, 4), (2, 4), (3, 4), (4, 4))))

In our search, we count the states that we needed to evaluate.

.. code-block:: python

    >>> def search(traversal):
    ...     iter_vertices = iter(traversal.start_from(start_state, build_paths=True))
    ...     for c, state in enumerate(iter_vertices):
    ...         if state in goal_states:
    ...             print("Reached", state, "after", c, "steps in depth", traversal.depth)
    ...             return state

We search the smallest depth of some goal state from the start state.

**First, we search directly in the graph**. We call `TraversalBreadthFirst` of
NoGraphs, and get the following result:

.. code-block:: python

    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> vertex = search(traversal)
    Reached ((1, 4), (2, 4), (3, 4), (4, 4)) after 76519 steps in depth 5
    >>> traversal.paths[vertex]  # doctest: +NORMALIZE_WHITESPACE
    (((0, 0), (1, 0), (2, 0), (3, 0)), ((0, 1), (1, 1), (3, 0), (3, 1)),
    ((0, 2), (1, 2), (3, 1), (3, 2)), ((0, 3), (2, 2), (3, 2), (3, 3)),
    ((0, 4), (2, 3), (3, 3), (4, 3)), ((1, 4), (2, 4), (3, 4), (4, 4)))

Now, we repeat the search, but **this time, we search in the equivalence classes of**
**the states**:

With `VertexToID` function *vertex_to_id* as shown below, we declare
that for the search, each state is equivalent to the state where the positions of the
players are sorted.

We can do that because the moves of the players are completely independent from
their identity: A player at some position can move exactly the same way another
player at this position could move. With other words, important is not, which
player is where, but only, which positions are occupied by a player. The same
holds for the goal states.

.. code-block:: python

    >>> def vertex_to_id (state):
    ...     return tuple(sorted(state))

Instead of `TraversalBreadthFirst`, we now use class `TraversalBreadthFirstFlex`,
because it has the two additional parameters *vertex_to_id* and *gear*. As first
argument, we give our function *vertex_to_id*. As second argument, we give the
default value `nog.GearDefault() <GearDefault>`, because we do not need anything
special there.

.. code-block:: python

    >>> traversal = nog.TraversalBreadthFirstFlex(
    ...    vertex_to_id, nog.GearDefault(), next_vertices)
    >>> vertex = search(traversal)
    Reached ((1, 4), (2, 4), (3, 4), (4, 4)) after 7290 steps in depth 5
    >>> traversal.paths[vertex]  # doctest: +NORMALIZE_WHITESPACE
    (((0, 0), (1, 0), (2, 0), (3, 0)), ((0, 1), (1, 1), (3, 0), (3, 1)),
    ((0, 2), (1, 2), (3, 1), (3, 2)), ((0, 3), (2, 2), (3, 2), (3, 3)),
    ((0, 4), (2, 3), (3, 3), (4, 3)), ((1, 4), (2, 4), (3, 4), (4, 4)))

Of cause, we get the same result: depth 5. But now, we get it
after only 7,290 instead of 76,519 search steps.
So, **vertex equivalences helped us to reduce the needed search effort**.

And NoGraphs assisted us:

- We just define the `VertexToID` function, and NoGraphs **computes the graphs**
  **of vertex equivalence classes automatically**.

- This graph is **computed on the fly**. So, it is not necessary to fully compute it.
  **Only the necessary computations are done**.

- We **get the results**, the goal vertex and the vertices of the path,
  **as vertices of our original graph**. Neither do we need to map a found goal
  equivalence class back to a vertex, nor a path of equivalence classes back to a
  path of vertices.
