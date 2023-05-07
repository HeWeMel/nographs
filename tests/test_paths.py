import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)


class PathsHandling:
    # noinspection PyShadowingNames
    """
    - Error handling in Paths objects
      (Path detects illegal calls with None as vertex and with non-existing vertices.)
    - Iteration works for both types of paths both with vertices and with edges.

    >>> # noinspection PyProtectedMember
    >>> _paths = nog._paths

    -- Unlabeled paths --

    >>> gear = nog.GearDefault()
    >>> path_unlabeled = _paths.PathsOfUnlabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path_unlabeled[None]  # Calls p.iter_vertices_to_start
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> None in path_unlabeled
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_unlabeled.iter_vertices_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_unlabeled.iter_edges_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_unlabeled.iter_edges_to_start(2))
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.
    >>> path_unlabeled.append_edge(0, 0, None)
    >>> path_unlabeled.append_edge(0, 1, None)
    >>> # Calls p.iter_vertices_from_start and p.iter_vertices_to_start
    >>> path_unlabeled[1]
    (0, 1)
    >>> # Also calls p.iter_edges_to_start
    >>> tuple(path_unlabeled.iter_edges_from_start(1))
    ((0, 1),)
    >>> path_unlabeled.append_edge(1, 2, None)
    >>> path_unlabeled[2]
    (0, 1, 2)
    >>> tuple(path_unlabeled.iter_edges_from_start(2))
    ((0, 1), (1, 2))

    -- Paths (and not overridden in PathsOfUNlabeledEdges) --
    >>> path_unlabeled.iter_labeled_edges_from_start(2)
    Traceback (most recent call last):
    RuntimeError: Edges with labels needed, and Traversal needs to know about them
    >>> path_unlabeled.iter_labeled_edges_to_start(2)
    Traceback (most recent call last):
    RuntimeError: Edges with labels needed, and Traversal needs to know about them

    -- Labeled paths --

    >>> path_labeled = _paths.PathsOfLabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path_labeled[None]
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> None in path_labeled
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_labeled.iter_vertices_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.
    >>> tuple(path_labeled.iter_edges_to_start(None))
    Traceback (most recent call last):
    RuntimeError: Paths: None instead of vertex given.

    >>> tuple(path_labeled.iter_edges_to_start(2))
    Traceback (most recent call last):
    RuntimeError: Paths: No path for given vertex.

    >>> path_labeled.append_edge(0, 0, (None, None))
    >>> path_labeled.append_edge(0, 1, (None, "labeled"))
    >>> tuple(path_labeled.iter_vertices_from_start(1))
    (0, 1)
    >>> tuple(path_labeled.iter_edges_from_start(1))
    ((0, 1),)
    >>> tuple(path_labeled[1])  # Calls iter_labeled_edges_from_start
    ((0, 1, 'labeled'),)

    >>> path_labeled.append_edge(1, 2, (None, "labeled"))
    >>> tuple(path_labeled.iter_vertices_from_start(2))
    (0, 1, 2)
    >>> tuple(path_labeled.iter_edges_from_start(2))
    ((0, 1), (1, 2))
    >>> path_labeled[2]  # Calls iter_labeled_edges_from_start
    ((0, 1, 'labeled'), (1, 2, 'labeled'))
    >>> tuple(path_labeled.iter_labeled_edges_to_start(2))
    ((1, 2, 'labeled'), (0, 1, 'labeled'))

    -- Any Path --
    >>> 2 in path_labeled
    True


    -- Unlabeled Path with sequence based predecessor--
    >>> gear = nog.GearForIntVertexIDsAndCFloats()
    >>> path = _paths.PathsOfUnlabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    None
    ... )
    >>> path.append_edge(0, 0, [0])
    >>> path.append_edge(0, 1, [1])
    >>> path[1]
    (0, 1)

    -- Labeled Path with sequence based predecessor--
    >>> gear = nog.GearForIntVertexIDsAndCFloats()
    >>> path = _paths.PathsOfLabeledEdges(
    ...    gear.vertex_id_to_vertex_mapping(()),
    ...    gear.vertex_id_to_path_attributes_mapping(()),
    ...    None
    ... )
    >>> path.append_edge(0, 0, [0])
    >>> path.append_edge(0, 1, [1])
    >>> path[1]
    ((0, 1, 1),)


    -- Dummy paths --

    >>> # noinspection PyProtectedMember
    >>> paths_dummy = _paths.PathsDummy(nog.vertex_as_id)
    >>> # noinspection PyProtectedMember
    >>> paths_dummy._check_vertex(None)
    Traceback (most recent call last):
    RuntimeError: No paths available: Traversal not started or no paths requested.
    >>> # noinspection PyProtectedMember
    >>> paths_dummy.__getitem__(None)
    Traceback (most recent call last):
    RuntimeError: No paths available: Traversal not started or no paths requested.
    >>> # noinspection PyProtectedMember
    >>> predecessor = paths_dummy._predecessor
    >>> predecessor[None]
    Traceback (most recent call last):
    KeyError
    >>> del predecessor[None]
    Traceback (most recent call last):
    KeyError
    >>> predecessor[None] = None
    Traceback (most recent call last):
    RuntimeError: Cannot add a path, traversal not started or no paths requested.
    >>> tuple(iter(predecessor)), len(predecessor), None in predecessor
    ((), 0, False)
    """
