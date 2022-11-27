Performance
-----------

You might value the flexibility and the ease of use of NoGraphs within its domain,
or that it can analyse graphs that can not or should not be fully
computed, stored or adapted, e.g. infinite graphs, large graphs and graphs with
expensive computations.

But you might fear a bad performance, because NoGraphs is implemented in pure Python.

This section gives a first impression of the runtime and memory performance to
expect from NoGraphs in different scenarios and in comparison to other libraries.
You might be surprised by the results.

We start with a qualitative analysis. Then, we analyze the effects in practice
based on a `benchmark <performance_benchmark>` and measurements, and summarize
the `performance of different NoGraph gears <gear_results>`
and the performance of NoGraphs in
`comparison to other libraries <library_comparison_results>`.


Qualitative analysis
~~~~~~~~~~~~~~~~~~~~

The typical approach of classical graph libraries is as follows:

- The application fully computes a graph, and
- the library stores all vertices and edges in an efficient internal
  representation.
- Then, the library performs the required analysis based on this representation.

NoGraphs does graph analysis on the fly:

- It asks the application in each analysis step (only) for the vertices and
  edges needed next, and
- delivers already computed results immediately (before it asks for further
  input).

**The approach of NoGraphs has advantages and disadvantages for the runtime and**
**memory performance:**

- NoGraphs asks the application only for vertices and edges that are really
  needed for the concrete analysis, and the application can stop the analysis
  and the computation of further vertices and edges immediately when the
  partial results computed so far fulfill the needs.

  **The advantage can be large, if:**

  - **the part of the graph, that is needed for the analysis, is quite small,**
    **and unknown in advance**,
  - and **the computation of the whole graph is quite expensive (or impossible), and**
    **the application can save graph computation runtime** if only partial data
    about the graph is requested by the graph library.

- NoGraphs does not store the graph.

  **The advantage can be large, if:**

  - **storing the graph is quite expensive (or impossible).**

  **The disadvantage can be large, if:**

  - **many tasks are performed on the same graph, and computing vertices and**
    **edges is expensive** while **storing and retrieving them is cheap** or
  - **the application is not able to compute / adapt the graph on demand**,
    because it can compute / deliver vertices or edges only in some fixed
    order.

  (Another disadvantage occurs, if an analysis task needs to process
  parts of the graph repeatedly. Currently, NoGraphs does not offer such
  algorithms.)

**Some of the classical libraries are implemented using languages**
**that are known to allow for good runtime performance and memory efficiency**,
e.g., *C* or *Rust*. This is a performance **disadvantage for NoGraphs**,
because it is implemented as pure Python code.

For NoGraphs, a **fair amount of performance optimization has been done**, e.g.,
if you work with numbered vertices, the bookkeeping of NoGraphs can store
them in machine native form (*C* integers in Python arrays) and the
python integer objects can be deallocated. This is an
**advantage in comparison to some other Python libraries, that may not aim**
**at performance to the same degree.**

In practice, these advantages and disadvantages combine to the real
performance. In the following, we show the concrete effects based on a
benchmark and measurements.

If you like to skip the description of the test benchmark, you could
directly continue with the
`comparison of different NoGraph gears <performance_gears>`
or the
`comparison of NoGraphs to other libraries <library_comparison>`.


.. _performance_benchmark:

Setting, graph and analysis tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For our performance tests, we use the following setting, graph and analysis
tasks:

- System: Core i5-4570, 3.2 Ghz, 4 cores, 16 GB memory, Windows

  In other words, **a small office PC, that is nine years old**.

  Python: 3.10

  (Will be updated to 3.11 when all dependencies of the benchmark can be
  fulfilled. NoGraphs itself is compatible with Python 3.11.)

- The example:

  - Graph: See the end of page `overview <overview_example>`.

    The tasks use different graph sizes. The graphs of these sizes are
    derived by using only the first *n* vertices (starting with vertex 0)
    of the given graph, and the respective edges.

  - Tasks and demanded results:

    **A. Base scenario: Full search**

      In this scenario, a graph has to be (nearly) **fully searched**
      for solving the respective analysis task.

      1. **BFS: 1.2 M vertices.**
         Compute depth of vertex 1,200,000 from start vertex 0.

      2. **Dijkstra: 1,2 M vertices.**
         Compute distances of vertices 1,000,000 and 1,150,000 and 1,200,000
         from vertex 0.

      3. **Dijkstra: 1,2 M vertices.**
         Compute shortest path from vertex 0 to vertex 1,200,000.

      4. **Dijkstra, simplified task: 100 T vertices.**
         Compute shortest path to vertex 100,000.

    B. **Scenario variant: Partial search 33%**

       **Dijkstra: 3,6 M vertices.**
       Compute distance of vertex 2,400,000 from vertex 1,200,000.

       The analysis results shows, that only 33% of the graph really need
       to be regarded for solving this task.

    C. **Scenario variant: Three analysis runs**

       **Dijkstra: 1,2 M vertices (like in A. 2.)**

       In this scenario, three analysis runs are performed for a graph built
       only once.

- Download: The source of the benchmark can be found here:

  https://github.com/HeWeMel/nographs-and-others

- About the measurements: Please find further details
  `here <performance_measurement_details>`.

In the following, we compare the performance of different NoGraphs gears.
Then, we
`compare the performance of NoGraphs with other libraries <library_comparison>`.


.. _performance_gears:

Comparison of NoGraphs gears
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Gears
.....

Based on the described `benchmark <performance_benchmark>`,
NoGraphs is tested with different `gears <choosing_gear>`
(factory class for bookkeeping data structures, that are optimized for
different Python data types that the application code might use for
representing vertices and weights/distances).

The abbreviations used in the result data are the following:

- **NoGraphs**

  Class `nographs.GearDefault`, configured for **float weights**.
  See `tutorial <gear_default>`.

  **GearDefault is the most flexible gear**.

- **nog@IntID**

  Class `nographs.GearForIntVertexIDs`, configured for **float weights**.
  See `tutorial <gear_for_int_vertex_ids>`.

  - **@IntIdA0B**

    Like *nog@IntID*, but the packing of boolean values into integers is
    switched off. Tested only for some of the test cases.

  - **@IntIdL0B**

    Like *nog@IntID*, but both the preference for arrays over lists and
    the packing of boolean values into integers are switched off.

    **GearForIntVertexIDs in this configuration is often the fastest gear**.

  - **@IntIdF**

    Like *nog@IntID*, but C-native floats are used as weights
    (class `GearForIntVertexIDsAndCFloats`).
    Tested only for some of the test cases.

  - **@IntIdF0B**

    Like *@IntIdF*, but both the preference for arrays over lists and
    the packing of boolean values into integers are switched off.
    Tested only for some of the test cases.

- **nog@Int**

  Class `nographs.GearForIntVerticesAndIDs`. See
  `tutorial <gear_for_int_vertices_and_ids>`.

  - **@IntF**

    Like *nog@Int*, but C-native floats are used as weights.
    (class `GearForIntVerticesAndIDsAndCFloats`).
    Tested only for some of the test cases.

    **GearForIntVerticesAndIDsAndCFloats is often the most memory efficient gear**.

  - **@IntF0B**

    Like *@IntF*, but the packing of boolean values into integers is
    switched off. Tested only for some of the test cases.

  - **nog+shift**

    Like *@IntF*, but NoGraphs is told to shift the vertex numbers
    internally s.t. the occurring numbers start at 0.
    Tested only for some of the test cases.

  -  **nog+intset**

    Like *@IntF*, but the 3rd party library *intbitset* is used to
    store sets of integers. Tested only for some of the test cases.

In the following two sections, we show the raw data from the measurements and
`interpret and summarize the results <gear_results>`.

Raw data
........

**Task 1: Depth of a vertex (algorithm: BFS)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.14 | ____________0 | ____67,948,224 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __1.66 | ____________0 | _______164,906 |
+-----------+-------+--------+---------------+----------------+
| @IntIdA0B | _0.00 | __1.30 | ____________0 | _____1,232,556 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __1.17 | ____________0 | ____10,781,476 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.66 | ____________0 | _______161,232 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF0B | _0.00 | __1.29 | ____________0 | _____1,232,412 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __1.68 | ____________0 | _______160,976 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __1.69 | ____________0 | _______160,976 |
+-----------+-------+--------+---------------+----------------+
| @IntF0B   | _0.00 | __1.33 | ____________0 | _____1,232,156 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __1.14 | ____________0 | _______169,686 |
+-----------+-------+--------+---------------+----------------+

**Task 2: Length of shortest paths to three vertices (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.45 | ____________0 | ____82,489,608 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __2.04 | ____________0 | _____9,619,092 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.04 | ____________0 | _____9,616,420 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.28 | ____________0 | _____4,915,489 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __2.05 | ____________0 | _____9,616,420 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __2.28 | ____________0 | _____4,915,089 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __2.27 | ____________0 | _____4,915,089 |
+-----------+-------+--------+---------------+----------------+

**Task 3: Shortest path to a single vertex (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.62 | ____________0 | ___126,332,524 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __2.19 | ____________0 | ____46,153,544 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.20 | ____________0 | ____46,153,544 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.43 | ____________0 | ____41,452,352 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __2.22 | ____________0 | ____26,988,580 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __2.45 | ____________0 | ____22,287,388 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __2.63 | ____________0 | ____22,287,388 |
+-----------+-------+--------+---------------+----------------+

**Task 4: Regarded graph size reduced by factor 12**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __0.22 | ____________0 | ____15,793,736 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __0.18 | ____________0 | _____4,004,268 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.18 | ____________0 | _____4,002,956 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.20 | ____________0 | _____3,532,748 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __0.18 | ____________0 | _____2,331,378 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __0.21 | ____________0 | _____1,860,380 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __0.21 | ____________0 | _____1,859,932 |
+-----------+-------+--------+---------------+----------------+

**Scenario B: Graph three times larger, only 1/3 to be regarded**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.44 | ____________0 | ____82,494,776 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __2.03 | ____________0 | ____19,482,160 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.03 | ____________0 | ____19,482,160 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.35 | ____________0 | ____10,166,713 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __2.04 | ____________0 | ____19,482,160 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __2.35 | ____________0 | ____10,166,713 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __2.35 | ____________0 | ____10,166,713 |
+-----------+-------+--------+---------------+----------------+
| nog+shift | _0.00 | __2.75 | ____________0 | _____4,916,593 |
+-----------+-------+--------+---------------+----------------+

**Scenario C: Three searches (see task 2) in same graph**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __7.33 | ____________0 | ____82,488,320 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __6.08 | ____________0 | _____9,617,068 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __6.08 | ____________0 | _____9,617,068 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __6.79 | ____________0 | _____4,915,729 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __6.07 | ____________0 | _____9,617,068 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __6.80 | ____________0 | _____4,915,729 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __6.79 | ____________0 | _____4,915,729 |
+-----------+-------+--------+---------------+----------------+

.. _gear_results:

Choosing the optimal gear makes quite a difference
..................................................

In the `benchmark <performance_benchmark>`, the vertices are the natural numbers
starting at 0 (in the following just "natural numbers"). In this case, we can choose
between several gears, with different performance:

- GearForHashableVertexIDs, subclass **GearDefault**

  *GearDefault* is the gear that is used by the
  `traversal classes with simplified API <algorithms>`,
  where a gear cannot be chosen, and it is the most flexible gear w.r.t. typing.
  In the following, **we compare the performance**
  of `other gears <gears>` **with this base case**.

- **GearForIntVertexIDs**

  If we use this gear in order to tell NoGraphs, that we have
  **natural numbers as vertex ids**,
  it switches **from mappings** (from vertex ids to something, e.g., to vertices
  or floats) and **sets** (of vertex ids) **to lists and arrays**, where the vertex
  ids are the indices. In arrays, **floats and bytes are stored as C-native values**,
  **flag bits are packed into bytes**, and the original *Python* value objects will
  be disposed by the garbage collector.
  If we use subclass *GearForIntVertexIDsAndCFloats*, also distances can
  be stored in arrays as C-native values.

  All this together reduces memory consumption dramatically (relationship to
  base case GearDefault is shown):

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 93.1%   | 6.0%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 90.9%   | 22.4%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 92.7%   | 32.8%       |
  +--------------------------------+---------+-------------+
  | DFS                            | 145.6%  | 0.2%        |
  +--------------------------------+---------+-------------+
  | DFS without bit packing        | 113.2%  | 1.8%        |
  +--------------------------------+---------+-------------+

  In one case, DFS, the runtime significantly increases, by 46%. If this is not
  acceptable in the use case, *GearForIntVertexIDs* offers options to
  reduce runtime but keep most of the memory savings. One option is to
  switch of bit packing: the runtime increases only by 13.2%, but
  the memory usage is still only 1.8% of that of the base case
  (see the last line in the table).

- **GearForIntVerticesAndIDs**

  If we use this gear in order to tell NoGraphs, that
  the **vertices themselves are natural numbers**, it switches
  **to arrays** instead of lists in more cases, e.g., in the predecessor
  collection used to store paths, because vertices represented
  by non-negative integers can be stored in an array.
  During the graph analysis, most of the vertices are only be kept in such
  arrays, as native *C* integers. The original *Python* vertex objects are
  disposed by the garbage collector.

  In the Dijkstra cases with paths generation, this further reduces memory consumption
  (relationship to base case GearDefault is shown), at the cost of roughly
  10 percent points of runtime. In DFS, the effects are much smaller.

  Again, we can use a subclass of the gear, here
  *GearForIntVerticesAndIDsAndCFloats*,
  that can store distances in arrays as C-native values.

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 93.1%   | 6.0%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 95.5%   | 11.8%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 93.5%   | 17.6%       |
  +--------------------------------+---------+-------------+
  | DFS                            | 148.2%  | 0.2%        |
  +--------------------------------+---------+-------------+
  | DFS without bit packing        | 116,7%  | 1.8%        |
  +--------------------------------+---------+-------------+

  And again, we can use options of the gear to trade some memory for a
  better DFS runtime. The last line shows the results without bit packing.

- **GearForIntVerticesAndIDs, with intbitset**

  We can tell NoGraphs to use an external library for efficient
  handling of sets of integers. Here, we choose the C-based
  library **intbitset** (see PyPI).

  The memory consumption decreases comparably to GearForIntVerticesAndIDs,
  but **in the DFS case, intbitset is much faster, by about 1/3**
  than the Python-based bit packing of GearForIntVerticesAndIDs.

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 92.7%   | 6.0%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 95.5%   | 11.8%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 100.4%  | 17.6%       |
  +--------------------------------+---------+-------------+
  | DFS                            | 100.0%  | 0.2%        |
  +--------------------------------+---------+-------------+

- **GearForIntVerticesAndIDs, configured for performance**

  If our goal is the best performance, but without external libraries,
  we can use *GearForIntVerticesAndIDs* and switch on its
  options *no_arrays* and *no_bit_packing*. So, we profit
  from the advantages of lists when compared to sets or dicts, but we
  avoid the slower arrays and the slow Python-based bit packing.

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 83.3%   | 11.7%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 81.8%   | 25.3%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 84.0%   | 36.5%       |
  +--------------------------------+---------+-------------+
  | DFS                            | 102.6%  | 15.9%       |
  +--------------------------------+---------+-------------+

.. tip::

   The numbers shown in these tables illustrate that the feature of NoGraphs
   to work with a large range of different data types does not only improve
   flexibility, but can also be used to massively optimize the memory
   performance of an analysis.

(Not really) dense subsets of the natural numbers
.................................................

A special case is scenario B of the `benchmark <performance_benchmark>`:
Here, the same amount of vertices and edges
are regarded as in task 2 of scenario 1. But when we switch to
*GearForIntVertexIDs*, we see
a memory reduction to 23,6% instead of 11,7%. And when we switch to
*GearForIntVerticesAndIDs*, we see a reduction to 12,3% instead of 6%.

The reason is that with these gears, we tell NoGraphs to use vertices from
0 to the highest vertex number that occurs, and the regarded vertex in scenario
B are roughly between 1,200,000 and 2,400,000 instead of between 0 and 1,200,000 in
task 2 of scenario 1. This means, the lists (resp. arrays) in the bookkeeping
are half empty!

Still, the reduction of the needed memory to 12.3% is worth choosing
*GearForIntVerticesAndIDs*.

In the raw data table for scenario B, an additional setting *nog+shift* is listed.
Here, we tell NoGraphs to convert vertices from the range above 1,2 M to the range
above 0. The memory consumption decreases by an additional factor of 50% and
reaches the values of task 2 of scenario 1.

So, the
**conversion of the number range removes the problem of empty sequence entries**
**and the smaller reduction of memory consumption**.
The runtime increases by 14 percent points,
this is the time needed for calling and executing the conversion function
for each vertex, when a (converted) vertex id for the vertex is needed.

Of cause, such a conversion can only be applied if the range of regarded
vertices is roughly known.


.. _library_comparison:

Comparison to other libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Libraries
.........

Now, we use the `benchmark <performance_benchmark>` to compare the
performance of the following graph libraries with the performance of NoGraphs:

- **igraph: Core written in C**

  - Description: "Python interface to the igraph high performance graph
    library, primarily aimed at complex network research and analysis."
  - PyPI package: https://pypi.org/project/igraph

- **RetworkX: Core written in Rust**

  - Description: "High performance graph data structures and algorithms"
  - PyPI package: https://pypi.org/project/retworkx

- **NetworkX: Pure Python code**

  - Description: "Python package for creating and manipulating graphs and networks"
  - PyPI package: https://pypi.org/project/networkx

They use the classical phased approach: in the first phase, the graph is
computed, and in the second phase, it is analyzed. In contrast, NoGraphs is
focused on graph analysis on the fly.

The tested versions of these libraries can be found in file
`requirements.txt <https://github.com/HeWeMel/nographs-and-others/blob/master/requirements.txt>`
of the benchmark.

See section `comments about the used test code <library_comparison_comments>`
for details about the test code for the different libraries and about specific
problems that occurred.

NoGraphs is tested with three different gears: In the following, *NoGraphs* denotes
the flexible default configuration, *@IntIdL0B* needs less memory, but is also
optimized for runtime, and *@IntIdF* is optimized for best memory performance.
See the section with the `gear comparison <performance_gears>` for details.

In the following two sections, we show the raw data from the measurements and
`interpret and summarize the results <library_comparison_results>`.

Raw data
.........

**Task 1: Depth of a vertex (algorithm: BFS)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.14 | ____________0 | ____67,948,224 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __1.17 | ____________0 | ____10,781,476 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.66 | ____________0 | _______161,232 |
+-----------+-------+--------+---------------+----------------+
| igraph    | 13.95 | _14.58 | ___21,531,780 | ____21,531,780 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  | _1.64 | __2.66 | ___33,594,160 | ____76,761,129 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _8.86 | _10.65 | 1,417,015,717 | _1,479,936,905 |
+-----------+-------+--------+---------------+----------------+

**Task 2: Length of shortest paths to three vertices (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.45 | ____________0 | ____82,489,608 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.04 | ____________0 | _____9,616,420 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.28 | ____________0 | _____4,915,489 |
+-----------+-------+--------+---------------+----------------+
| igraph    | 13.82 | _14.34 | ___21,530,892 | ____21,530,892 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  | _1.62 | __1.97 | ___33,593,824 | ____33,596,252 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _8.86 | _11.60 | 1,417,016,696 | _1,541,442,000 |
+-----------+-------+--------+---------------+----------------+

**Tasks 3: Shortest path to a single vertex (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.62 | ____________0 | ___126,332,524 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.20 | ____________0 | ____46,153,544 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.43 | ____________0 | ____41,452,352 |
+-----------+-------+--------+---------------+----------------+
| igraph    | 13.25 | _13.78 | ___21,530,892 | ____30,690,568 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+
| NetworkX  |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+

RetworkX and NetworX run in memory allocation errors. Thus, the table
shows no values for them. They might have a problem with the length
of the path to compute: it is 283.338 vertices long.

**Task 4: Regarded graph size reduced by factor 12**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __0.22 | ____________0 | ____15,793,736 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.18 | ____________0 | _____4,002,956 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.20 | ____________0 | _____3,532,748 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _0.19 | __0.23 | ____2,867,708 | _____2,867,708 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  | _0.14 | _57.84 | ____2,793,880 | _____2,989,541 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _0.67 | _82.67 | __123,319,124 | _9,593,863,188 |
+-----------+-------+--------+---------------+----------------+

For the task with reduced graph size, each of the libraries can compute
the demanded path.

**Scenario B: Graph three times larger, only 1/3 to be regarded**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __2.44 | ____________0 | ____82,494,776 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.03 | ____________0 | ____19,482,160 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __2.35 | ____________0 | ____10,166,713 |
+-----------+-------+--------+---------------+----------------+
| igraph    |110.30 | 110.90 | ___59,975,244 | ____59,975,244 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  | _4.89 | __5.66 | __100,793,656 | ___100,794,448 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+

**Scenario C: Three searches (see task 2) in same graph**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __7.33 | ____________0 | ____82,488,320 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __6.08 | ____________0 | _____9,617,068 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __6.79 | ____________0 | _____4,915,729 |
+-----------+-------+--------+---------------+----------------+
| igraph    | 13.17 | _14.63 | ___21,530,892 | ____21,530,892 |
+-----------+-------+--------+---------------+----------------+
| RetworkX  | _1.63 | __2.58 | ___33,593,824 | ____33,594,756 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+

.. _library_comparison_results:

Used NoGraphs configuration
...........................

In the following, we compare the results of the three libraries with these
of NoGraphs in the memory optimized configuration
(class `GearForIntVerticesAndIDsAndCFloats`). See the
`previous section <library_comparison>` for faster options.

One analysis task, search covers graph: NoGraphs mostly fastest
...............................................................

In scenario A of the `benchmark <performance_benchmark>`,
where **only one analysis task** has to be done,
**the advantage of NoGraphs**, that is does not need to build and
store an internal representation of the graph, **is very large**,
**even though the whole graph has to be regarded**
**to solve the task** in this scenario
(and NoGraphs is not even build / intended for this).

**In comparison to the** *C* **and** *Rust* **libraries, the advantage is even larger**
**than their advantage from their more runtime and memory efficient**
**implementation languages**.

- **In total runtime, NoGraphs is nearly always the fastest, often by far**

  In all test cases of scenario A, with just a single exception, NoGraphs
  is faster, often much faster: it solves the tasks 1 to 3
  **in the middle in only 45% of the time** the C- and Rust-based libraries need
  to build up the graph representation
  and to solve the task based on this. (The only exception is, that at task 2,
  NoGraphs in the used memory-optimized configuration is about 16% slower than
  RetworkX.)

  **NetworkX is the slowest, often by very large factors** (On average, NoGraphs
  needs only 12% of the runtime of NetworkX. Please note, that runtime and memory
  performance is not a primary goal of NetworkX. So, the result might not be
  surprising.)

  **igraph seams to have a problem with building up large graphs**, although
  the tests use code that is optimized for the library. It often needs
  **up to 9 times longer than RetworkX**.

  **RetworkX and NetworkX show problems with the calculation of long paths**
  and could not solve task 3 for the original graph on the test
  machine. Even for task 4, a much simplified version with a graph that is 12
  times smaller, they already show extremely high run times.

- **The memory consumption of NoGraphs is always the lowest, often by far**

  **For tasks with low bookkeeping volume** (BFS),
  **NoGraphs needs dramatically less memory than RetworkX and igraph**:
  about **0.2%** of the memory RetworkX needs, and **below 0.8%** of that of igraph.

  **With larger bookkeeping volume** (Dijkstra for task 2 and path generation
  for task 3), there is
  **still quite an advantage, but it is moderately smaller**:
  For Dikstra distances, NoGraphs needs about 23% of the memory need of igraph
  and about 15% of that of RetworkX, and for Dijkstra with path generation, it
  needs about 73% of the memory need of igraph (RetworkX can not solve the
  original problem). When we drastically reduce the graph and path size (task 4),
  NoGraphs needs about 63% to 65% of the memory of the two other libraries.

  **NetworkX** needs enormous amounts of memory for the tasks,
  **compared to NoGraphs, between factor 313 and 9.193 more**.


Larger graph, or smaller part to be analyzed: Advantage for NoGraphs
....................................................................

If we make the **graph larger, the advantage of NoGraphs scales up accordingly.**
And **if we reduce the relative part of the graph that is to be**
**regarded for the analysis, the advantage of NoGraphs increases significantly.**

Scenario B of `benchmark <performance_benchmark>` illustrates this:
Its task is of the same type as task 2 of
scenario A. Its graph is three times larger, but
only 1/3 of the graph has to be regarded to solve the task.
This means the number of regarded vertices and edges are similar.

This means, NoGraphs searches one 1/3 of the graph, but the other libraries have
to compute the graph in full size, before they even start searching.

The memory consumption of NoGraphs increases just by the empty collection entries
due to bad numbering
(see analysis in section `Comparison of NoGraphs gears <gear_results>`).

Thus, **NoGraphs needs only about 2% of the runtime of igraph and 42% of the runtime**
**of RetworkX**. This is much better than the relative values for task 2 of
scenario A. And the **advantage of NoGraphs w.r.t. the needed memory also increases,**
**to 17% (igraph) and 10% (RetworkX)**.


More analysis tasks, same graph: Advantage for C and Rust libraries
...................................................................

Scenario C of the `benchmark <performance_benchmark>`
is based on task 2 of scenario A, but the same analysis is
executed three times on the same graph. This means, once an internal
representation of the graph has been built, it can be used for all three
task runs.

Here, the runtime of NoGraphs gets three times higher and the memory
consumptions stays the same. The runtime of igraph and RetworkX increase
only slightly, because they are very fast in the analysis phase.

**In total, the runtime advantages of NoGraphs decrease, the disadvantages**
**increase: Its runtime is now 47% of that of igraph**
and **264% of that of RetworkX** (compared to 15% and 116% for scenario A task 2).

**NetworkX does not profit in relation to NoGraphs**, because already its
analysis phase takes longer than the on-the-fly run of NoGraphs.

(Please note, that scenarios A and C demand to fully search a graph, but NoGraphs
is made for scenarios where a graph that cannot be fully computed and/or adapted.)


.. _performance_measurement_details:

Details about the measurements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the `benchmark <performance_benchmark>`, the runtime for a test is
determined as the median of 5 consecutive test runs.

The peak memory consumption of a test is determined with the tracemalloc
module of the Python standard library, measured in a test run separate
from the ones used for measuring the runtime.

The garbage collector is called before a time or memory measurement is started.


.. _library_comparison_comments:

Comments about the used test code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the `comparison of the performance of the libraries <library_comparison>`,
individual properties of the libraries have been used to get good numbers for
each of them:

- Igraph is very slow in adding individual edges to a graph. So,
  chunks of 10 000 edges are loaded into the library, as a compromise
  between needing too much memory on the Python side, and needing too
  much runtime on the library side.

- Igraphs can directly work with positive integer vertices. That is used
  to get the full speed out of it.

- RetworkX provide an efficient iterator for BFS, but it does not provide
  the depth of vertices. For that purpose, a suitable visitor object
  have been defined, that does this.

- RetworkX can return all internally used vertex indices as a single list
  when the number of vertices is pre-defined. And it can convert from
  internal vertex ids to Python vertices on its own. And it is very fast in
  adding individual edges. All this is used.

- In the original version of task 3, not only the shortest path but also
  its length (weight) was demanded. NoGraphs and NetworkX can directly
  provide the length after the path has been created. igraph and
  RetworkX return only the path, and since manually computing its length
  in Python code takes some time, and this could distort the message
  of the tests, the task was simplified and the path length is not
  demanded.

- NetworkX can directly work on Python vertices. This is used to avoid
  dealing with vertex ids of the library.

Side note of the author:

- It stayed unclear, why the search with the Dijkstra algorithm
  of RetworkX takes so long. The library seems to be extraordinarily fast.
  But since the search is done by just one call of a library method, it
  seems that the reason is a problem in the library code and not in the
  way the library is used...
