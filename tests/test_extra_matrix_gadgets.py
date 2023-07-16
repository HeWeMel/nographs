import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)


class ArrayTests:
    """
    Only test cases that are not covered by examples in the documentation

    Array positions should wrap at the position limits of each dimension:

    >>> array = nog.Array('''
    ... S..#.
    ... .#.#G
    ... #G...
    ... '''.strip().splitlines(), 2)
    >>> starts, goals = (array.findall(c) for c in "SG")
    >>> next_vertices = array.next_vertices_from_forbidden("#", wrap=True)
    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> for found in traversal.start_from(start_vertices=starts, build_paths=True
    ...     ).go_for_vertices_in(goals):
    ...         traversal.depth, traversal.paths[found]
    (2, ((0, 0), (0, 4), (1, 4)))
    (2, ((0, 0), (0, 1), (2, 1)))

    "Diagonal" moves (edges) in the array positions should be allowed:
    >>> array = nog.Array('''
    ... S....
    ... ##...
    ... .G...
    ... '''.strip().splitlines(), 2)
    >>> start, goal = (array.findall(c)[0] for c in "SG")
    >>> next_vertices = array.next_vertices_from_forbidden("#", diagonals=True)
    >>> traversal = nog.TraversalBreadthFirst(next_vertices)
    >>> found = traversal.start_from(start, build_paths=True).go_to(goal)
    >>> traversal.depth, traversal.paths[found]
    (3, ((0, 0), (0, 1), (1, 2), (2, 1)))

    Incompatible options of move
    >>> nog.Position.moves(diagonals = True, non_zero_counts=range(1, 2))
    Traceback (most recent call last):
    RuntimeError: Incompatible options
    >>> nog.Position.moves(zero_move = True, non_zero_counts=range(1, 2))
    Traceback (most recent call last):
    RuntimeError: Incompatible options

    Ascending order
    >>> moves = nog.Position.moves(3, True, True)
    >>> nested_lists = [list(seq) for seq in moves]
    >>> nested_lists == sorted(nested_lists)
    True
    """
