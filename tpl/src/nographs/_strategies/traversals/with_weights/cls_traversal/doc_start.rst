| Bases: Generic[`T_vertex`, `T_vertex_id`, `T_weight`, `T_labels`],
| `Traversal` [`T_vertex`, `T_vertex_id`, `T_labels`]

:param vertex_to_id: See `VertexToID` function.

:param gear: See `gears API <gears_api>` and class `Gear`.

:param next_edges: See `NextWeightedEdges` function. If None, provide
 next_labeled_edges.

:param next_labeled_edges: See `NextWeightedLabeledEdges` function. Only allowed
 if next_edges equals None. If given, paths will record the given labels.
