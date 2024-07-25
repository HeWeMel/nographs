if not isinstance(type(self), type(Traversal)):
    raise RuntimeError("Method start_from can only be called on a Traversal object.")

self._start_from(
    start_vertex,
    start_vertices,
    build_paths,
    calculation_limit,
    self._gear,
)

# Explicitly list start vertices and their id. Needed several times.
self._start_vertices_and_ids = tuple(
    iter_start_vertices_and_ids(self._start_vertices, self._vertex_to_id)
)

# ----- Initialize method specific public bookkeeping -----
