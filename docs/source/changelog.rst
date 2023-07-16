ChangeLog
---------

**v3.3.0** (2023-07-16)

- Extras: Algorithm for computing an exact solution for traveling salesman problems
  added. (It exemplifies how the lazy computation style of NoGraphs' core
  algorithms can be extended to computations in the course of problem reduction.
  The TSP algorithm itself does not belong to the core of NoGraphs.)

- Extras: Classes added, that implement a Dijkstra shortest paths algorithm for
  infinitely branching graphs with locally sorted edges.
  (The implemented algorithm exemplifies how a "lazy evaluation" - based problem
  reduction allows for a graph analysis that is even more "lazy" than that of
  NoGraphs alone.)

**v3.2.0** (2023-06-09)

- Support for PyPy added: CI pipeline extended by tests for PyPy, incompatibility
  of some tests with PyPy removed.

- Performance data for tests on CPython updated to Python 3.11, and data for PyPy added.

**v3.1.0** (2023-04-23)

- Bidirectional search strategies introduced. They implement DFS and Dijkstra
  Shortest Paths in a bidirectional variant.

- All strategies:

  - Method state_to_str() introduced. It eases logging for
    debugging of graph definitions.

  - The state attributes now have defined content in the two phases
    'before the traversal has been started' and 'after the traversal has been started,
    but before it expanded or reported the first vertex'.

  - The behaviour of method go_for_vertices_in() is
    now also defined for the case of an empty vertex set.

- Exports: minimized

Notes:

- Protocol Weight: A weight type now needs to also provide a __sub__ method.
  The documented compatibility guarantees are not reduced by this.

**v3.0.3** (2023-02-09)

- Small typing problem solved that the new MyPy version 1.0.0 discovered

**v3.0.2** (2023-01-29)

- Traversals that handle distances, with Gears that allow for manually
  choosing a value to be used as positive infinity: Overflows over infinity
  are now detected by NoGraphs if the chosen distance value type cannot do this
  itself, e.g., if the application uses integer distances in the range of a
  C-native size-limited integer type and manually chooses a "large" value as
  infinity value.

Error corrections:

- Gear classes GearForIntVertexIDsAndCInts, GearForIntVerticesAndIDs, and
  GearForIntVerticesAndIDsAndCInts: Sometimes, vertices where not traversed
  due to an error in the computation of the infinity distance value or the
  default vertex value for C-native integers.

**v3.0.1** (2022-12-29)

- Class Position: support for multiplying an integer; new option non_zero_counts of
  method moves

Error corrections:

- Position.moves(): For dimensions >= 3, option add_diagonals adapted to typically
  expected behavior (previous behavior was correctly documented and implemented,
  but might have been surprising).

**v3.0.0** (2022-11-27)

- NoGraphs can be used fully typed (optionally): API refactored,
  traversals made generic, stubs added, documentation extended.
- Edge weights and distances of a wide range of value types can be handled, including
  values of arbitrary precision (e.g., decimal.Decimal or mpf of library
  mpmath).
- Gears added: sets of bookkeeping data structures, with optimized
  performance for different use cases, also allow to storing data as
  C-native values.
- Performance benchmark between gears and between NoGraphs and other libraries:
  separate, public project; results given in NoGraphs documentation.
- New traversal TraversalNeighborsThenDepth (often faster than DFS, if
  DFS reporting order is not important).

API has changed in some points, but adaptation is easy, and large parts of
the API are untouched (e.g., most of the examples of the tutorial run unchanged):

- Parameter *vertex_to_id* of traversals moved to new \*flex traversals (in order
  to ease type handling for standard cases).
- Handling of labels of edges changed (was necessary for strong typing):

  - Restricted to a single object, but this could be anything,
    including a dict.
  - Option *labeled_paths* of traversals removed. Labeled paths are automatically
    generated when labeled edges are given by parameter *next_labeled_edges*.
  - Option *labeled* of functions *adapt_edge_iterable* and *adapt_edge_index*
    of the gadgets section renamed to *attributes*.


**v2.5.1** (2022-04-03)

- Class TraversalShortestPaths: Error in documentation corrected,
  option keep_distances added. 


**v2.5.0** (2022-03-28)

- First public version marked as stable (PyPI and GitHub)

**Till v2.4.0** (2021-03)

- Tests improved, coverage 100%
- Documentation added (sphinx), published to ReadTheDocs
- Examples with DocTests 100%
- README for GitHub and PyPI added
- GitHub repository made public
- Flake8 100%
- Typing improved, MyPy 100%
- PyPI package built
- CI with GitHub added
- Extensions and improvements

**v2.0.0** (2021-10)

- Changed API:

  - An algorithm is a class (and not a function any more)
  - Common functionality provided as common methods instead of
    additional functions

- Path: Representation of predecessor relation changed from linked tuples
  to dict

**Till v1.6.0** (2021-05)

- Further algorithms added
- More support functions for traversal and graph adaptation added
- Better runtime & memory performance

**v1.0.0** (2021-05)

- Harmonized function signatures
- Paths handling extracted and transferred to class

**Till v0.6.0** (2021-05)

- Further algorithms added
- Better runtime & memory performance

**v0.1.0** (2021-02)

- Initial version
- Collection of algorithms in the form of separate functions
