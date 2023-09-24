|PyPI version| |PyPI status| |PyPI pyversions| |PyPI license| |CI| |CodeCov| |Documentation Status| |Code style| |GitHub issues|

.. |PyPI version| image:: https://badge.fury.io/py/nographs.svg
   :target: https://pypi.python.org/pypi/nographs/

.. |PyPI status| image:: https://img.shields.io/pypi/status/nographs.svg
   :target: https://pypi.python.org/pypi/nographs/

.. |PyPI pyversions| image:: https://img.shields.io/pypi/pyversions/nographs.svg
   :target: https://pypi.python.org/pypi/nographs/

.. |PyPy versions| image:: https://img.shields.io/badge/PyPy-3.11-blue
   :target: https://pypi.python.org/pypi/nographs/

.. |PyPI license| image:: https://img.shields.io/pypi/l/nographs.svg
   :target: https://github.com/HeWeMel/nographs/blob/main/LICENSE

.. |CI| image:: https://github.com/hewemel/nographs/workflows/CI%20(tests,%20flake8,%20mypy)/badge.svg?branch=main
   :target: https://github.com/hewemel/nographs/actions?query=workflow%3ACI%20(pip)

.. |CodeCov| image:: https://img.shields.io/codecov/c/gh/HeWeMel/NoGraphs/main
   :target: https://codecov.io/gh/HeWeMel/NoGraphs

.. |Documentation Status| image:: https://readthedocs.org/projects/nographs/badge/?version=latest
   :target: http://nographs.readthedocs.io/?badge=latest

.. |Code style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

.. |GitHub issues| image:: https://img.shields.io/github/issues/HeWeMel/nographs.svg
   :target: https://GitHub.com/HeWeMel/nographs/issues/


NoGraphs: Graph analysis on the fly
===================================

NoGraphs simplifies the analysis of graphs that can not or should not be fully
computed, stored or adapted, e.g. infinite graphs, large graphs and graphs with
expensive computations.
(Here, the word *graph* denotes the
`thing with vertices and edges <https://en.wikipedia.org/wiki/Glossary_of_graph_theory>`_,
not with diagrams.)

The approach: Graphs are
**computed and/or adapted in application code on the fly**
(when needed and as far as needed). Also,
**the analysis and the reporting of results by the library happen on the fly**
(when, and as far as, results can already be derived).

Think of it as *graph analysis - the lazy (evaluation) way*.

**Documentation**

- `Homepage of the documentation <https://nographs.readthedocs.io>`__
- `Installation guide <https://nographs.readthedocs.io/en/latest/installation.html>`__
- `Tutorial <https://nographs.readthedocs.io/en/latest/concept_and_examples.html>`__
  (contains many `examples <https://nographs.readthedocs.io/en/latest/concept_and_examples.html#examples>`__)
- `API reference <https://nographs.readthedocs.io/en/latest/api.html>`__

**Feature overview**

- Unidirectional traversal algorithms: DFS, BFS, topological search,
  Dijkstra, A\* and MST.
- Bidirectional search algorithms: BFS and Dijkstra.
- Results: Reachability, depth, distance, paths and trees.
  Paths can be
  calculated with vertices, edges, or attributed edges,
  and can be iterated in both directions.
- Flexible graph notion:

  - Infinite directed multigraphs with loops and
    attributes (this includes
    multiple adjacency, cycles, self-loops,
    directed edges,
    weighted edges and attributed edges).
  - Infinite graphs are supported, but need to be
    locally finite (i.e., a vertex has only finitely many outgoing edges).

- Generic API:

  - Vertices: Can be anything except for None. Hashable vertices can be
    used directly, unhashable vertices can be used together with
    hashable identifiers.
  - Edge weights and distances: Wide range of data types
    supported (float, int, Decimal, mpmath.mpf and others), e.g.,
    for high precision computations.
  - Edge attributes: Any object, e.g, a container
    with further data.
  - Identity and equivalence of vertices can be chosen / defined.
  - Bookkeeping: Several sets of bookkeeping data structures
    are predefined, optimized for different situations (data types used by the
    application, hashing vs. indexing, collections for *Python* objects or *C* native
    data types,...); Adaptable and extendable, e.g., specialized
    collections of 3rd party libraries can be integrated easily and runtime
    efficiently

- Flexible API: The concept of implicit graphs that NoGraphs is based on
  allows for an API that eases
  operations like
  graph pruning, graph abstraction, the typical binary
  graph operations (union, intersection, several types of products), the
  computation of search-aware graphs,  the combination of
  problem reduction with lazy evaluation,
  and traversals of vertex equivalence classes on the fly.
  Bookkeeping data can be
  pre-initialized and accessed during computations.
- Typing: The API can be used fully typed (optionally).
- Implementation: Pure Python (>=3.9). It introduces no further dependencies.
- CI tests: For all supported versions of Python and both supported interpreters
  CPython and PyPy, both code and docs, 100% code coverage.
- Runtime and memory performance: Have been goals (CPython). In its domain, it often
  even outperforms Rust- and C-based libraries. Using PyPy improves its performance
  further.

**Extras** (outside of the core of NoGraphs)

- Computation of exact solutions for (small)
  traveling salesman problems (shortest / longest route,
  positive / zero / negative edge weights, graph does not need to be complete)
- Dijkstra shortest paths algorithm for
  infinitely branching graphs with locally sorted edges.
- Gadget functions for test purposes. They make the easy task of
  adapting existing explicit test graphs a no brainer, may they be
  stored in edge indices or edge iterables
  or in arrays.

**Example**

Our graph is directed, weighted and has infinitely many edges. These edges are
defined in application code by the following function. For a vertex *i*
(here: an integer) as the first of two
parameters, it yields the edges that start at *i* as tuples
*(end_vertex, edge_weight)*. What a strange graph - we do not know how it
looks like...

.. code-block:: python

    >>> def next_edges(i, _):
    ...     j = (i + i // 6) % 6
    ...     yield i + 1, j * 2 + 1
    ...     if i % 2 == 0:
    ...         yield i + 6, 7 - j
    ...     elif i % 1200000 > 5:
    ...         yield i - 6, 1

We would like to find out the *distance* of vertex 5 from vertex 0, i.e., the minimal
necessary sum of edge weights of any path from 0 to 5, and (one of) the *shortest
paths* from 0 to 5.

We do not know which part of the graph is necessary to look at in order to find the
shortest path and to make sure, it is really the shortest. So, we use the
traversal strategy *TraversalShortestPaths* of NoGraphs.
It implements the well-known *Dijkstra* graph algorithm in the lazy evaluation
style of NoGraphs.

.. code-block:: python

    >>> import nographs as nog
    >>> traversal = nog.TraversalShortestPaths(next_edges)

We ask NoGraphs to traverse the graph starting at vertex 0, to calculate paths
while doing so, and to stop when visiting vertex 5.

.. code-block:: python

    >>> traversal.start_from(0, build_paths=True).go_to(5)
    5

The state data of this vertex visit contains our results:

.. code-block:: python

    >>> traversal.distance
    24
    >>> traversal.paths[5]
    (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)

We learn that we need to examine the graph at least till vertex 17 to find the
shortest path from 0 to 5. It is not easy to see that from the definition
of the graph...

A part of the graph, the vertices up to 41, is shown in the following picture.
Arrows denote directed edges. The edges in red show shortest paths from
0 to other vertices.

.. image:: https://nographs.readthedocs.io/en/latest/_images/nographs_example_graph.PNG
   :class: with-shadow
   :width: 600px

**And now?**

Can you imagine...

- An infinite generator of primes, defined by just a graph and
  a call to a standard graph algorithm?
- Or a graph that defines an infinite set
  of Towers of Hanoi problems in a generic way, without fixing the number of
  towers, disk sizes, and the start and goal configuration - and a specific
  problem instance is solved by just one library call?
- Or a way for computing an exact solution for traveling salesman problems,
  that is based on just a graph and a call of the Dijkstra single source shortest path
  algorithm?
- Or graphs that are dynamically
  computed based on other graphs, or on analysis results about other graphs,
  or even on partial analysis results for already processed parts of the same graph?

Let's `build it <https://nographs.readthedocs.io/en/latest/installation.html>`__.

Welcome to NoGraphs!
