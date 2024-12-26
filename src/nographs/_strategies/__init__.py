# In the following, we use absolute imports starting with
# "nographs._strategies." instead of just "." because:
# MyPyC: https://github.com/mypyc/mypyc/issues/996

from nographs._strategies.strategy import Strategy

from nographs._strategies.type_aliases import (
    T_strategy,
    NextVertices,
    NextEdges,
    NextLabeledEdges,
    NextWeightedEdges,
    NextWeightedLabeledEdges,
    BNextVertices,
    BNextEdges,
    BNextLabeledEdges,
    BNextWeightedEdges,
    BNextWeightedLabeledEdges,
)

from nographs._strategies.traversals.traversal import Traversal

from nographs._strategies.traversals.without_weights.breadth_first import (
    TraversalBreadthFirst,
    TraversalBreadthFirstFlex,
)
from nographs._strategies.traversals.without_weights.depth_first import (
    TraversalDepthFirst,
    TraversalDepthFirstFlex,
    DFSEvent,
    DFSMode,
)
from nographs._strategies.traversals.without_weights.neighbors_then_depth import (
    TraversalNeighborsThenDepth,
    TraversalNeighborsThenDepthFlex,
)
from nographs._strategies.traversals.without_weights.topological_sort import (
    TraversalTopologicalSort,
    TraversalTopologicalSortFlex,
)

from nographs._strategies.traversals.with_weights.shortest_paths import (
    TraversalShortestPaths,
    TraversalShortestPathsFlex,
)
from nographs._strategies.traversals.with_weights.a_star import (
    TraversalAStar,
    TraversalAStarFlex,
)
from nographs._strategies.traversals.with_weights.minimum_spanning_tree import (
    TraversalMinimumSpanningTree,
    TraversalMinimumSpanningTreeFlex,
)
from nographs._strategies.traversals.with_weights.extra_infinite_branching import (
    TraversalShortestPathsInfBranchingSortedFlex,
    TraversalShortestPathsInfBranchingSorted,
)

from nographs._strategies.bidirectional_search.breadth_first import (
    BSearchBreadthFirst,
    BSearchBreadthFirstFlex,
)
from nographs._strategies.bidirectional_search.shortest_path import (
    BSearchShortestPath,
    BSearchShortestPathFlex,
)

__all__ = (
    # -- strategy --
    "Strategy",
    "T_strategy",
    "NextVertices",
    "NextEdges",
    "NextLabeledEdges",
    "NextWeightedEdges",
    "NextWeightedLabeledEdges",
    "BNextVertices",
    "BNextEdges",
    "BNextLabeledEdges",
    "BNextWeightedEdges",
    "BNextWeightedLabeledEdges",
    # -- traversal --
    "Traversal",
    "TraversalBreadthFirstFlex",
    "TraversalBreadthFirst",
    "TraversalDepthFirstFlex",
    "TraversalDepthFirst",
    "DFSEvent",
    "DFSMode",
    "TraversalNeighborsThenDepthFlex",
    "TraversalNeighborsThenDepth",
    "TraversalTopologicalSortFlex",
    "TraversalTopologicalSort",
    "TraversalShortestPathsFlex",
    "TraversalShortestPaths",
    "TraversalAStarFlex",
    "TraversalAStar",
    "TraversalMinimumSpanningTreeFlex",
    "TraversalMinimumSpanningTree",
    "TraversalShortestPathsInfBranchingSortedFlex",
    "TraversalShortestPathsInfBranchingSorted",
    # -- bidir search --
    "BSearchBreadthFirstFlex",
    "BSearchBreadthFirst",
    "BSearchShortestPathFlex",
    "BSearchShortestPath",
)
