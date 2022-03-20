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
**the analysis and the reporting of results by the library happens on the fly**
(when, and as far as, results can already be derived).

Think of it as *graph analysis - the lazy (evaluation) way*.

**Feature overview**

- Algorithms: DFS, BFS, topological search,
  Dijkstra, A\* and MST.
- Flexible graph notion: Infinite directed multigraphs with loops and
  attributes (this includes
  multiple adjacency, cycles, self-loops,
  directed edges,
  weighted edges and edges with application specific attributes).
  Your vertices can be nearly anything.
  Currently, all algorithms are limited to locally finite
  graphs (i.e., a vertex has only finitely many outgoing edges).
- Results: Reachability, depth, distance, paths and trees.
  Paths can be
  calculated with vertices or edges or attributed edges
  and can be iterated in both directions.
- Flexible API: It eases operations like
  graph pruning, graph product and graph abstraction, the
  computation of search-aware graphs and
  traversals of vertex equivalence classes on the fly. It is even
  possible to replace some of the internal data structures
  and to interfere with them during the search.
- Implementation: Pure Python (>=3.9). It introduces no further dependencies.
  Runtime and memory performance have been goals.
- Source: Available `here <https://github.com/HeWeMel/nographs>`__.
- Licence: `MIT <https://github.com/HeWeMel/nographs/blob/main/LICENSE>`__.

**Documentation**

- The `homepage of the project and its documentation can be found here <https://nographs.readthedocs.io>`__
- The `installation is described here <https://nographs.readthedocs.io/en/latest/installation.html>`__.
- The `tutorial <https://nographs.readthedocs.io/en/latest/concept_and_examples.html>`__ explains how the library can be used
  and contains many `examples <https://nographs.readthedocs.io/en/latest/concept_and_examples.html#examples>`__.
- The `API reference <https://nographs.readthedocs.io/en/latest/api.html>`__ documents
  the classes, functions, signatures and types of the library.

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
    ...     elif i > 5:
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

The state data of this vertex visit contains our result:

.. code-block:: python

    >>> traversal.distance
    24
    >>> traversal.paths[5]
    (0, 1, 2, 3, 4, 10, 16, 17, 11, 5)

We learn that we need to examine the graph at least till vertex 17 to find the
shortest path from 0 to 5. It is not easy to see that from the definition
of the graph...

The graph is shown in the following picture. Arrows denote directed edges.
The edges in red show shortest paths from 0 to other vertices.

Welcome to NoGraphs!

.. image:: https://nographs.readthedocs.io/en/latest/_images/nographs_example_graph.PNG
   :class: with-shadow
   :width: 600px
