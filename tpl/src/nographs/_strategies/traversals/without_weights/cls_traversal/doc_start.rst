Bases: `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

:param vertex_to_id: See `VertexToID` function.

:param gear: See `gears API <gears_api>` and class `GearWithoutDistances`.

:param next_vertices: See `NextVertices` function. If None, provide next_edges
 or next_labeled_edges.

:param next_edges: See `NextEdges` function. Only allowed if next_vertices equals
 None. If both are None, provide next_labeled_edges.

:param next_labeled_edges: See `NextLabeledEdges` function. Only allowed if
 next_vertices and next_edges equal None. If given, paths will record the given
 labels.

:param is_tree: bool: If it is certain, that during each traversal run,
 each vertex can be reached only once, is_tree can be set to True. This
 improves performance, but attribute *visited* of the traversal will not be
 updated during and after the traversal.
