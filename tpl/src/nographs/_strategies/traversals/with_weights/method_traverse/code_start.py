# ----- Prepare efficient environment for inner loop -----
# Copy Traversal attributes into method scope (faster access)
labeled_edges = self._labeled_edges
maybe_vertex_to_id = (
    None if self._vertex_to_id == vertex_as_id else self._vertex_to_id
)  # Case vertex_as_id: not apply; T_vertex_id > T_vertex
build_paths = self._build_paths
calculation_limit = self._calculation_limit
predecessors = self._predecessors
attributes = self._attributes
next_edges = self._next_edges
