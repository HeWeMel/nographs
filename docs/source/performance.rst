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

We start with a `qualitative analysis <qualitative-analysis>`.
Then, we analyze the effects in practice,
based on a `benchmark <performance_benchmark>` and measurements, and summarize
the `performance of different NoGraph gears <gear_results>`
and the performance of NoGraphs in
`comparison to other libraries <library_comparison_results>`.

The benchmark only covers the performance of NoGraphs running on CPython,
the interpreter used by most developers. If an even higher performance is needed,
switching to PyPy could be an option: According to published benchmarks for
PyPy, it is often faster by factors in comparison to CPython.
`Ad-hoc tests of NoGraphs with PyPy <performance-pypy>` confirm this.


.. _qualitative-analysis:

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

The approach of NoGraphs has advantages and disadvantages for the runtime and
memory performance:

- **NoGraphs helps to limit computations** to necessary parts.

  NoGraphs asks the application only for vertices and edges that are really
  needed for the concrete analysis, and the application can stop the analysis
  and the computation of further vertices and edges immediately when the
  partial results computed so far fulfill the needs.

  **The advantage can be large, if:**

  - **only a part of the graph is needed** for the analysis,
    and this **part is unknown** in advance, and the application can
    **save a relevant amount of runtime** by avoiding to compute unnecessary parts
    of the graph.

  - or **only a part of the analysis is necessary for the needed results**,
    and this **part is unknown** in advance, and NoGraphs can
    **save a relevant amount of runtime when the application detects that it**
    **can stop the computation** prematurely.

- **NoGraphs does not store the graph.**

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

- **NoGraphs is implemented in pure Python.**

  Some of the classical libraries are implemented using languages
  that are known to allow for good runtime performance and memory efficiency,
  like *C* or *Rust*.

  Typically, they are fast in processing the graph data. Sometimes, they are
  slow in the phase of 'uploading' the graph (reading data from
  Python, bridging the gap to another language, inserting nodes and edges in
  internal graph data structures).

  **The disadvantage of NoGraphs can be large, if:**

  - the **better processing speed of libraries written in other languages dominates**
    the additional
    **runtime for the graph upload (including bridging the language gap)**.

  **The advantage of NoGraphs can be large, if:**

  - the **extra runtime for the graph upload to such a library dominates its**
    **higher processing speed**.

  The processing speed of NoGraphs can often be
  `significantly reduced  <performance-pypy>` by
  switching from CPython to PyPy.


For NoGraphs, a **fair amount of performance optimization has been done**.
Runtime optimizations include measures like avoiding function calls and attribute
lookups in inner loops. Optimizations of memory usage include features like the
following: if you work with numbered vertices, the bookkeeping of NoGraphs can store
them, and depth and length data, in machine native form (*C* integers and floats
in Python arrays), and the python objects can be
deallocated, which reduces the memory needed for large analysis tasks. This is an
**advantage in comparison to some other Python libraries, that may not aim**
**at performance to the same degree.**

In practice, these advantages and disadvantages combine to the real
performance. In the following, we show the concrete effects based on a
benchmark and measurements.

If you like to skip the `description of the test benchmark <performance_benchmark>`,
you can directly continue with the
`comparison of different NoGraph gears <performance_gears>`
or the
`comparison of NoGraphs to other libraries <library_comparison>`.


.. _performance_benchmark:

Setting, graph and analysis tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For our performance tests, we use the following setting, graph and analysis
tasks.

System: **A small office PC** (Core i5-13400, 2500 MHz, 10 cores, 16 logical cores,
Windows).

Python and interpreter: **Python 3.11, CPython**.

The example:

  - Graph: See the end of page `overview <overview_example>`.

    The tasks use different graph sizes. The graphs of these sizes are
    derived by using only the first *n* vertices (starting with vertex 0)
    of the given graph, and the respective edges.

  - Tasks and demanded results:

    **A. Base scenario: Full search**

      In this scenario, a graph has to be (nearly) **fully searched**
      for solving the respective analysis task (bad for NoGraphs).

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
       to be regarded for solving this task (good for NoGraphs).

    C. **Scenario variant: Three analysis runs**

       **Dijkstra: 1,2 M vertices (like in A. 2.)**

       In this scenario, three analysis runs are performed for a graph built
       only once (bad for NoGraphs).

- Download: The source of the benchmark can be found here:

  https://github.com/HeWeMel/nographs-and-others

- About the measurements: Please find further details
  `here <performance_measurement_details>`.

In the following, we
`compare the performance of different NoGraphs gears <performance_gears>`,
give the raw result data, and
`interpret and summarize the results <gear_results>`.

Then, we
`compare the performance of NoGraphs with other libraries <library_comparison>`,
give the raw result data, and
`interpret and summarize the results <library_comparison_results>`.


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

    Like *nog@IntID*, but C-native floats are used to store weights
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

    Like *nog@Int*, but C-native floats are used to store weights.
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
| NoGraphs  | _0.00 | __0.56 | ____________0 | ____71,952,406 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __0.76 | ____________0 | _______162,852 |
+-----------+-------+--------+---------------+----------------+
| @IntIdA0B | _0.00 | __0.63 | ____________0 | _____1,233,700 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.57 | ____________0 | ____10,782,564 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.76 | ____________0 | _______162,356 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF0B | _0.00 | __0.63 | ____________0 | _____1,233,444 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __0.78 | ____________0 | _______162,004 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __0.78 | ____________0 | _______161,948 |
+-----------+-------+--------+---------------+----------------+
| @IntF0B   | _0.00 | __0.63 | ____________0 | _____1,233,092 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __0.54 | ____________0 | _______169,858 |
+-----------+-------+--------+---------------+----------------+

**Task 2: Length of shortest paths to three vertices (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.22 | ____________0 | ____85,283,776 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __0.97 | ____________0 | _____9,623,396 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.98 | ____________0 | _____9,617,892 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.09 | ____________0 | _____4,916,757 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __0.98 | ____________0 | _____9,617,780 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __1.09 | ____________0 | _____4,916,349 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __1.09 | ____________0 | _____4,916,349 |
+-----------+-------+--------+---------------+----------------+

**Task 3: Shortest path to a single vertex (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.29 | ____________0 | ___130,551,348 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __1.03 | ____________0 | ____49,354,272 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __1.03 | ____________0 | ____49,353,368 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.15 | ____________0 | ____44,652,028 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __1.06 | ____________0 | ____26,989,554 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __1.17 | ____________0 | ____22,287,592 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __1.16 | ____________0 | ____22,287,592 |
+-----------+-------+--------+---------------+----------------+

**Task 4: Regarded graph size reduced by factor 12**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __0.11 | ____________0 | ____16,171,992 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __0.09 | ____________0 | _____4,269,216 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.09 | ____________0 | _____4,269,168 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.10 | ____________0 | _____3,798,928 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __0.09 | ____________0 | _____2,330,368 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __0.10 | ____________0 | _____1,860,128 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __0.10 | ____________0 | _____1,860,128 |
+-----------+-------+--------+---------------+----------------+

**Scenario B: Graph three times larger, only 1/3 to be regarded**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.21 | ____________0 | ____85,291,456 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __0.97 | ____________0 | ____19,483,460 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.97 | ____________0 | ____19,483,460 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.13 | ____________0 | ____10,167,969 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __0.97 | ____________0 | ____19,483,460 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __1.12 | ____________0 | ____10,167,969 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __1.12 | ____________0 | ____10,167,969 |
+-----------+-------+--------+---------------+----------------+
| nog+shift | _0.00 | __1.28 | ____________0 | _____4,916,621 |
+-----------+-------+--------+---------------+----------------+

**Scenario C: Three searches (see task 2) in same graph**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __3.66 | ____________0 | ____85,283,480 |
+-----------+-------+--------+---------------+----------------+
| nog@IntId | _0.00 | __2.91 | ____________0 | _____9,617,916 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.92 | ____________0 | _____9,617,916 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __3.27 | ____________0 | _____4,916,517 |
+-----------+-------+--------+---------------+----------------+
| nog@Int   | _0.00 | __2.91 | ____________0 | _____9,617,916 |
+-----------+-------+--------+---------------+----------------+
| @IntF     | _0.00 | __3.27 | ____________0 | _____4,916,517 |
+-----------+-------+--------+---------------+----------------+
| nog+intset| _0.00 | __3.27 | ____________0 | _____4,916,517 |
+-----------+-------+--------+---------------+----------------+

.. _gear_results:

Choosing the optimal gear makes quite a difference
..................................................

In the `benchmark <performance_benchmark>`, the vertices are the natural numbers
starting at 0 (in the following just "natural numbers"). In this case, we can choose
between several gears, and the benchmark shows the performance differences:

- GearForHashableVertexIDs, subclass **GearDefault**

  *GearDefault* is the most flexible gear w.r.t. suported data types, and it is the
  gear that is used by the
  `traversal classes with simplified API <traversals>`,
  where a gear cannot be chosen.
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

  All this together reduces the memory consumption dramatically (relationship to
  base case GearDefault is shown):

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 89.3%   | 5.8%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 90.9%   | 23.5%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 89.1%   | 34.2%       |
  +--------------------------------+---------+-------------+
  | BFS                            | 135.7%  | 0.2%        |
  +--------------------------------+---------+-------------+
  | BFS without bit packing        | 112.5%  | 1.7%        |
  +--------------------------------+---------+-------------+

  In one case, BFS, the runtime significantly increases, by 35.7%. If this is not
  acceptable in the use case, *GearForIntVertexIDs* offers options to
  reduce runtime but keep most of the memory savings. One option is to
  switch of bit packing: the runtime increases only by 12.5%, but
  the memory usage is still only 1.7% of that of the base case
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
  (relationship to base case GearDefault is shown), but the runtime stays
  nearly the same. In the BFS, no paths are stored, thus there is no effect on memory
  usage (the slightly higher runtime might by an outlier).

  Again, we can use a subclass of the gear, here
  *GearForIntVerticesAndIDsAndCFloats*,
  that can store distances in arrays as C-native values.

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 89.3%   | 5.8%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 90.9%   | 11.5%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 90.7%   | 17.1%       |
  +--------------------------------+---------+-------------+
  | BFS                            | 139.3%  | 0.2%        |
  +--------------------------------+---------+-------------+
  | BFS without bit packing        | 112,5%  | 1.7%        |
  +--------------------------------+---------+-------------+

  And again, we can use options of the gear to trade some memory for a
  better BFS runtime. The last line shows the results without bit packing.

- **GearForIntVerticesAndIDs, with intbitset**

  We can tell NoGraphs to use an external library for efficient
  handling of sets of integers. Here, we choose the C-based
  library **intbitset** (see PyPI).

  The memory consumption decreases comparably to GearForIntVerticesAndIDs,
  but **in the BFS case, intbitset is much faster, by about 30%**
  than the Python-based bit packing of GearForIntVerticesAndIDs.

  +--------------------------------+---------+-------------+
  | Test case                      | runtime | peak memory |
  +================================+=========+=============+
  | Dijkstra + distances           | 89.3%   | 5.8%        |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 90.9%   | 11.5%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 89.9%   | 17.1%       |
  +--------------------------------+---------+-------------+
  | BFS                            | 96.4%   | 0.2%        |
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
  | Dijkstra + distances           | 80.3%   | 11.3%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 100T vertices | 81.8%   | 26.4%       |
  +--------------------------------+---------+-------------+
  | Dijkstra + path, 1.2M vertices | 79.8%   | 37.8%       |
  +--------------------------------+---------+-------------+
  | BFS                            | 101.8%  | 15.0%       |
  +--------------------------------+---------+-------------+

.. tip::

   The numbers shown in these tables illustrate that the feature of NoGraphs
   to work with a large range of different data types does not only improve
   flexibility, but can also be used to massively optimize the memory
   performance of an analysis.

.. _gear-results_not_dense:

(Not really) dense subsets of the natural numbers
.................................................

A special case is scenario B of the `benchmark <performance_benchmark>`:
Here, the same amount of vertices and edges
are regarded as in task 2 of scenario 1. But when we switch to
*GearForIntVertexIDs* or to *GearForIntVerticesAndIDs*, we see
a memory reduction to 22.8% instead of the 11.3% we have seen in task 2 of scenario
1. And when we switch to
*GearForIntVertexIDsAndCFloats* or to **GearForIntVerticesAndIDsAndCFloats**, we see
a memory reduction to 11.9% instead of 5.8%.

The reason is that with these gears, we tell NoGraphs to use vertices from
0 to the highest vertex number that occurs, and the regarded vertex in scenario
B are roughly between 1,200,000 and 2,400,000 instead of between 0 and 1,200,000 in
task 2 of scenario 1.

**This means: In scenario B, the lists (resp. arrays) in the bookkeeping of**
**the sequence-based gears are half empty!**
This reduces the memory-saving effect of using sequence- instead of set- and
dict-based gears. But, of course, a reduction of the needed memory to
22.8% (resp. 11.9%) is still better than nothing.

Sometimes, counter-measures are possible:
In the raw data for scenario B, an additional setting *nog+shift* is listed.
Here, we tell NoGraphs to convert vertices from the range above 1,2 M to the range
above 0. The memory consumption decreases by an additional factor of 50% and
reaches the values of task 2 of scenario 1.

So, the
**conversion of the number range removes the problem of empty sequence entries**
**and the suboptimal reduction of memory consumption**.
The runtime increases by 6 percent points,
this is the time needed for calling and executing the conversion function
for each vertex, when a (converted) vertex id for the vertex is needed.

of course, such a conversion can only be applied if the range of relevant vertices
is roughly known. Otherwise, we have to live with empty list or array cells,
or we need to use a mapping-based (e.g., dict-based) gear.


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

- **rustworkx: Core written in Rust**

  - Description: "High performance general purpose graph library."
  - PyPI package: https://pypi.org/project/rustworkx

- **NetworkX: Pure Python code**

  - Description: "Python package for creating and manipulating graphs and networks"
  - PyPI package: https://pypi.org/project/networkx

They use the classical phased approach: in the first phase, the graph is
computed, and in the second phase, it is analyzed. In contrast, NoGraphs is
focused on graph analysis on the fly.

The tested versions of these libraries can be found in file
`requirements.txt <http://github.com/HeWeMel/nographs-and-others/blob/master/requirements.txt>`_
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
| NoGraphs  | _0.00 | __0.56 | ____________0 | ____71,952,406 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.57 | ____________0 | ____10,782,564 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.76 | ____________0 | _______162,356 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _8.72 | __8.99 | ___21,590,880 | ____21,590,880 |
+-----------+-------+--------+---------------+----------------+
| rustworkx | 27.73 | _28.15 | ___39,898,108 | ____86,476,080 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _4.57 | __5.33 | 1,297,009,024 | _1,359,923,768 |
+-----------+-------+--------+---------------+----------------+

**Task 2: Length of shortest paths to three vertices (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.22 | ____________0 | ____85,283,776 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.98 | ____________0 | _____9,617,892 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.09 | ____________0 | _____4,916,757 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _8.57 | __8.79 | ___21,590,880 | ____21,590,880 |
+-----------+-------+--------+---------------+----------------+
| rustworkx | 24.68 | _24.82 | ___39,898,300 | ____39,898,300 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _4.56 | __5.73 | 1,297,014,184 | _1,424,230,152 |
+-----------+-------+--------+---------------+----------------+

**Tasks 3: Shortest path to a single vertex (algorithm: Dijkstra)**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.29 | ____________0 | ___130,551,348 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __1.03 | ____________0 | ____49,353,368 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.15 | ____________0 | ____44,652,028 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _8.28 | __8.52 | ___21,590,880 | ____31,823,628 |
+-----------+-------+--------+---------------+----------------+
| rustworkx |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+
| NetworkX  |  n.a. |   n.a. |          n.a. |           n.a. |
+-----------+-------+--------+---------------+----------------+

rustworkx and NetworX run in memory allocation errors. Thus, the table
shows no values for them. They might have a problem with the length
of the path to compute: it is 283.338 vertices long.

**Task 4: Regarded graph size reduced by factor 12**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __0.11 | ____________0 | ____16,171,992 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.09 | ____________0 | _____4,269,168 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __0.10 | ____________0 | _____3,798,928 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _0.09 | __0.11 | ____2,927,552 | _____2,927,552 |
+-----------+-------+--------+---------------+----------------+
| rustworkx | _2.40 | _49.23 | ____4,698,364 | _____4,698,364 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _0.32 | _79.22 | __113,316,144 | _9,584,256,016 |
+-----------+-------+--------+---------------+----------------+

For the task with reduced graph size, each of the libraries can compute
the demanded path.

**Scenario B: Graph three times larger, only 1/3 to be regarded**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __1.21 | ____________0 | ____85,291,456 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __0.97 | ____________0 | ____19,483,460 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __1.13 | ____________0 | ____10,167,969 |
+-----------+-------+--------+---------------+----------------+
| igraph    | 74.06 | _74.35 | ___60,035,232 | ____60,035,232 |
+-----------+-------+--------+---------------+----------------+
| rustworkx | 72.24 | _72.56 | __116,698,108 | ___116,698,108 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | 13.78 | _16.33 | 4,016,894,984 | _4,271,338,140 |
+-----------+-------+--------+---------------+----------------+

**Scenario C: Three searches (see task 2) in same graph**

+-----------+-------+--------+--------------------------------+
| lib+gear  | runtime (sec.) |   peak memory (bytes)          |
+-----------+-------+--------+---------------+----------------+
|           | graph |  total |     graph     |     total      |
+===========+=======+========+===============+================+
| NoGraphs  | _0.00 | __3.66 | ____________0 | ____85,283,480 |
+-----------+-------+--------+---------------+----------------+
| @IntIdL0B | _0.00 | __2.92 | ____________0 | _____9,617,916 |
+-----------+-------+--------+---------------+----------------+
| @IntIdF   | _0.00 | __3.27 | ____________0 | _____4,916,517 |
+-----------+-------+--------+---------------+----------------+
| igraph    | _8.31 | __8.99 | ___21,590,880 | ____21,590,880 |
+-----------+-------+--------+---------------+----------------+
| rustworkx | 24.31 | _24.71 | ___39,898,300 | ____39,898,300 |
+-----------+-------+--------+---------------+----------------+
| NetworkX  | _4.50 | __7.43 | 1,297,014,072 | _1,424,230,128 |
+-----------+-------+--------+---------------+----------------+

.. _library_comparison_results:

Configuration of NoGraphs
.........................

In the following, we compare the results of the three libraries with these
of NoGraphs in the memory optimized configuration
(class `GearForIntVerticesAndIDsAndCFloats`). See the
`previous section <library_comparison>` for faster options.

One analysis task, and search covers graph: NoGraphs mostly fastest
...................................................................

In scenario A of the `benchmark <performance_benchmark>`,
where **only one analysis task** has to be done,
**the advantage of NoGraphs**, that no representation of the
graph needs to be stored, and no language gap needs to be bridged,
**is very large**: Building the graph brings no advantage for the other libraries,
since the graph will only be used once.
**In comparison to the** *C* **and** *Rust* **libraries, the advantage is even larger**
**than their advantage from their more runtime and memory efficient**
**implementation languages**.

- **In total runtime, NoGraphs is always the fastest, often by far**

  In all test cases of scenario A, NoGraphs is faster, often much faster than
  the other libraries. It solves
  the tasks **in average in only 19% of the time the C- and Rust-based**
  **libraries need** to build up the graph representation and to solve the task based
  on this, and in less than **12% of the time NetworkX needs**.

  Notes:

  - Based on CPython for Python 3.11, even NetworX is sometimes faster than igraph and
    rustworkx: its runtime for the analysis phase is much higher than that of igraph
    and rustworkx, but it profits much from a higher speed in the graph building phase
    (from Python 3.10 to 3.11, igraphs became faster, retworx became slower, but
    NetworX became much faster in the benchmark).

  - rustworkx is relatively slow at building up large graphs, although
    the tests use code that is slightly optimized for the library. igraphs
    often needs only 1/3 of the runtime of rustworkx (in the test one year ago,
    igraphs was slower...)

  rustworkx and NetworkX show problems with the calculation of long paths
  and could not solve task 3 for the original graph on the test
  machine. Even for task 4, a much simplified version with a graph that is 12
  times smaller, they already show extremely high analysis run times.

- **The memory consumption of NoGraphs is always the lowest, often by far**

  **For tasks with low bookkeeping volume** (BFS),
  **NoGraphs needs dramatically less memory than rustworkx and igraph**:
  about **0.2%** of the memory rustworkx needs, and **below 0.8%** of that of igraph.

  **With larger bookkeeping volume** (Dijkstra for task 2 and path generation
  for task 3), there is
  **still quite an advantage, but it is moderately smaller**:
  For Dikstra distances, NoGraphs needs about 21% of the memory of igraph
  and about 12% of that of rustworkx. For Dijkstra with path generation, it
  needs about 67% of the memory need of igraph (rustworkx can not solve the
  original problem). When we drastically reduce the graph and path size (task 4),
  NoGraphs needs 64%, resp., 40%, of the memory igraphs, resp. rustworkx, need.

  **NetworkX** needs enormous amounts of memory for the tasks,
  **compared to NoGraphs, between 290 and 8400 times more**.


Larger graph, or smaller part to be analyzed: Advantage for NoGraphs
....................................................................

If we make the **graph larger, the advantage of NoGraphs scales up.**
And **if we reduce the relative part of the graph that is to be**
**regarded for the analysis, the advantage of NoGraphs increases.**

Scenario B of `benchmark <performance_benchmark>` illustrates this:
Its task is of the same type as task 2 of
scenario A. Its graph is three times larger, but
only 1/3 of the graph has to be regarded to solve the task.
This means the number of regarded vertices and edges are similar.

Thus, NoGraphs searches only 1/3 of the graph. Its runtime is comparable to that
for task 2 of scenario A. But the other libraries have
to compute the graph in full size, before they even start searching.

**NoGraphs needs only about 2% of the runtime of igraph and of rustworkx**.
This is much better than the relative values for task 2 of
scenario A. And the **advantage of NoGraphs w.r.t. the needed memory also increases,**
**to 17% (igraph) and 9% (rustworkx)**.

(Please note that in the example, the memory consumption of NoGraphs doubles in
comparison to task 2
of scenario A. The reason is bad numbering in combination with using a sequence-based
gear - here done intentionally. For more details, see section
`Comparison of NoGraphs gears <gear-results_not_dense>`. But this is still
much less than the other libraries.)


More analysis tasks, same graph: Advantage for C and Rust libraries
...................................................................

Scenario C of the `benchmark <performance_benchmark>`
is based on task 2 of scenario A, but the same analysis is
executed three times for the same graph. This means, once an internal
representation of the graph has been built, it can be used for all three
task runs.

Here, the memory consumption of each library is comparable to scenario A.
The memory allocated for an analysis is released when the analysis is completed.

The runtime of NoGraphs is three times higher now. There is no re-use between
the analysis runs.

NetworkX re-uses the graph, and only the analysis time multiplies. In total,
its runtime is 2.5 time higher now. igraph and rustworkx can do the same. But since
their graph build-up runtime is high in comparison to their analysis time, their
total runtimes are factor 2.86, resp. 2.5, higher now.

**In total, the runtime advantages of NoGraphs decrease, the disadvantages**
**increase: Its runtime is now 37% of that of igraph**
and **14% of that of rustworkx** (compared to 13% and 5% for scenario A task 2).

(Please note, that both scenarios A and C demand to fully search a graph, but NoGraphs
is made for scenarios where a graph cannot be fully computed and/or adapted.)

.. _performance-pypy:

Switching to another interpreter: Advantage for NoGraphs
........................................................

If an even higher performance is needed, switching to another interpreter
can be an option, since NoGraphs is implemented in pure Python. PyPy, for example,
is often faster than CPython by factors, according to the published benchmark results
of PyPy.

For the given benchmark, **NoGraphs is between 1.5 and 7.6 times faster with PyPy**
than with CPython, and **in average by a factor of 2.8**. igraphs does not
profit much. NetworkX profits from PyPy by a factor of 1.7.


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

- igraphs can directly work with positive integer vertices. That is used
  to get the full speed out of it.

- rustworkx provide an efficient iterator for BFS, but it does not provide
  the depth of vertices. For that purpose, a suitable visitor object
  have been defined, that does this.

- rustworkx can return all internally used vertex indices as a single list
  when the number of vertices is pre-defined. And it can convert from
  internal vertex ids to Python vertices on its own. All this is used.

- igraphs and rustworkx are slow in adding individual edges to a graph. So,
  large chunks of edges, e.g., 10 000 edges, are loaded into the libraries,
  as a compromise between needing too much memory on the Python side, and needing too
  much runtime on the library side.

- In the original version of task 3, not only the shortest path but also
  its length (weight) was demanded. NoGraphs and NetworkX can directly
  provide the length after the path has been created. igraph and
  rustworkx return only the path, and since manually computing its length
  in Python code takes some time, and this could distort the message
  of the tests, the task was simplified and the path length is not
  demanded.

- NetworkX can directly work on Python vertices. This is used to avoid
  dealing with vertex ids of the library.
