"$$ insert_from('$$/code_start.py') $$"

# Copy further traversal attributes into method scope (faster access)
is_tree = self._is_tree
visited = self.visited

# Get further references of used gear objects and methods
# (avoid attribute resolution)
"$$ import_from('$$/../../../MStrategy.py') $$"
"$$ MVertexSet.access(name='visited') $$"
