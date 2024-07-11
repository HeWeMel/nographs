# At start, most of the distances from a vertex to a start vertex are not
# known. If accessed for comparison for possibly better distances, infinity
# is used, if no other value is given. Each start vertex has distance 0
# from a start vertex (itself), if not defined otherwise.
zero = self._gear.zero()
self.distances = define_distances(
    self._gear,
    self._known_distances,
    ((vertex_id, zero) for vertex, vertex_id in self._start_vertices_and_ids),
    self._is_tree,
)
