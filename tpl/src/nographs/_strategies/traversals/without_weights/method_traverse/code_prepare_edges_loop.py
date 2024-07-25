# ----- Typing preparation of inner loop -----

# The following type Any opens no space for typing problems, since
# the content of next_edge_or_vertex is type checked and iterates
# objects of type T_vertex for edges_with_data==False and otherwise of
# one of the following:
#   WeightedUnlabeledOutEdge[T_vertex, Any],
#   UnweightedLabeledOutEdge[T_vertex, T_labels],
#   WeightedLabeledOutEdge[T_vertex, Any, T_labels],
# And if labeled_edges==True, the first case is excluded.
# (Any alternative code version of the inner loop without
#  Any or 'type: ignore' is slower)
edge_or_vertex: Any  # "Hole" in typing, but types "around" make it safe
neighbor: T_vertex  # Re-establish type "after" the "hole"
data_of_edge: T_labels  # Re-establish type "after" the "hole"
