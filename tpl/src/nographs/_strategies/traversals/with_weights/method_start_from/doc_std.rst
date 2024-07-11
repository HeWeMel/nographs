:param start_vertex: The vertex the search should start at. If None, provide
    start_vertices.

:param start_vertices: The set of vertices the search should start
    at. Only allowed if start_vertex equals None.

:param build_paths: If true, build paths from start vertices for each reported
    vertex, and an empty path for each start vertex.

:param calculation_limit: If provided, maximal number of vertices to process
    (read in) from your graph. If it is exceeded, a RuntimeError will be raised.
