Start the traversal at a vertex or a set of vertices and set parameters.

:param start_vertex: The vertex the search should start at. If None, provide
    start_vertices.

:param start_vertices: The vertices the search should start at. Only
    allowed if start_vertex equals None.

:param build_paths: If true, build paths from some start vertex to each visited
    vertex. Paths of start vertices are empty paths.

:param calculation_limit: If provided, maximal number of vertices to process
    (read in) from your graph. If it is exceeded, a RuntimeError will be raised.

