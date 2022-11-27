ChangeLog
---------

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
- More support functions for traversal and graph adaption added
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
