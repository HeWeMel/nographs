from enum import Flag, Enum, auto


class DFSEvent(Flag):
    """
    An enumeration of the events that can trigger the report of a vertex / edge by
    TraversalDepthFirst.

    Events reporting that a vertex is entered or left:

    - ENTERING_START: A start vertex has been entered and the traversal starts
      there.

    - LEAVING_START: A start vertex has been left (the traversal may continue
      with the next one).

    - ENTERING_SUCCESSOR: A vertex is entered, when an edge
      that leads to it is followed. In mode *DFS_TREE*, only *DFS-tree edges*
      are followed.

    - LEAVING_SUCCESSOR: A vertex is left, when an edge that leads to it
      and has been followed, is now followed in reversed direction, during
      backtracking from the edge. In mode *DFS_TREE*, only *DFS-tree edges*
      are followed.

    Events reporting that a vertex (or an edge) has been detected but will not be
    entered (resp. followed):

    - SKIPPING_START: A start vertex was about to be entered, as start of a
      traversal from there, but it has already been visited as descendant of
      another start vertex, and thus, it is skipped.

    - BACK_EDGE: An edge *(u, v)* is found, where v has already been entered,
      but not left so far. In other words, *v* is on the trace (path that
      leads to *u* within the tree).

    - FORWARD_EDGE: An edge *(u, v)* is found, where *v* has already been
      left, and it had been entered after *u*. *(u, v)* is a shortcut
      forwards in the tree branch from *u* to *v*, so to speak.

    - CROSS_EDGE: An edge *(u, v)* is found, where *v* has already been left,
      and it had been entered before *u*. This means, in the DFS tree,
      *u* and *v* do not have any ancestor or descendant relationship
      between them.

    Events that combine other events as a group (*group-events*):

    - SOME_NON_TREE_EDGE: One of the events FORWARD_EDGE, BACK_EDGE, or CROSS_EDGE
      occurred, but it has not been determined which of these events.

    - FORWARD_OR_CROSS_EDGE: One of the events FORWARD_EDGE or CROSS_EDGE
      occurred, but it has not been determined which of these events.


    Aliases for sets of events:

    - NONE = 0

    - ENTERING = ENTERING_START | ENTERING_SUCCESSOR
    - LEAVING = LEAVING_START | LEAVING_SUCCESSOR

    - IN_OUT_START = ENTERING_START | LEAVING_START
    - IN_OUT_SUCCESSOR = ENTERING_SUCCESSOR | LEAVING_SUCCESSOR
    - IN_OUT = IN_OUT_START | IN_OUT_SUCCESSOR

    - NON_TREE_EDGES = FORWARD_EDGE | BACK_EDGE | CROSS_EDGE
    - EDGES = ENTERING_SUCCESSOR | NON_TREE_EDGES

    - ALL = IN_OUT | SKIPPING_START | NON_TREE_EDGES
    """

    ENTERING_START = auto()
    LEAVING_START = auto()

    ENTERING_SUCCESSOR = auto()
    LEAVING_SUCCESSOR = auto()

    SKIPPING_START = auto()
    BACK_EDGE = auto()
    FORWARD_EDGE = auto()
    CROSS_EDGE = auto()

    SOME_NON_TREE_EDGE = auto()
    FORWARD_OR_CROSS_EDGE = auto()

    NONE = 0

    ENTERING = ENTERING_START | ENTERING_SUCCESSOR
    LEAVING = LEAVING_START | LEAVING_SUCCESSOR

    IN_OUT_START = ENTERING_START | LEAVING_START
    IN_OUT_SUCCESSOR = ENTERING_SUCCESSOR | LEAVING_SUCCESSOR
    IN_OUT = IN_OUT_START | IN_OUT_SUCCESSOR

    NON_TREE_EDGES = FORWARD_EDGE | BACK_EDGE | CROSS_EDGE
    EDGES = ENTERING_SUCCESSOR | NON_TREE_EDGES

    ALL = IN_OUT | SKIPPING_START | NON_TREE_EDGES


class DFSMode(Enum):
    """
    An enumeration of the traversing mode to be used by TraversalDepthFirst.

    The modes are:

    - DFS_TREE: The traversal follows the edges of the DFS tree. If demanded,
      non-tree edges are reported, but not followed. Vertices are only
      visited once.

    - ALL_PATHS: A simple path is a path that does not contain a vertex twice.
      In this mode, the traversal follows all edges, also edges leading to
      vertices that have already been visited. But edges to vertices, that are
      already on the trace (current path from a start vertex to the current
      vertex) are ignored. For example, this can be used to search in the set
      of all possible simple paths from some edges to some others.

    - ALL_WALKS: A walk is a sequence of nodes in which each adjacent pair of
      nodes in the sequence is adjacent in the graph.
      A walk can contain the same vertex or edge more than once.
      In this more, the traversal follows all edges, also edges leading to
      vertices that have already been followed as part of the trace (the
      current walk from a start vertex to the current vertex).
    """

    DFS_TREE = auto()
    ALL_PATHS = auto()
    ALL_WALKS = auto()
