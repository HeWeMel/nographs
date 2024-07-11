# In the following, all API elements are listed that are
# not private of the module that defines it.
# The elements that are ment to be package private, are
# commented out to document this property.
# All other elements are imported and exported "flat"
# as direct elements of the package.

from ._types import (
    # TypeVars, type aliases, and protocols that are used in NoGraphs to describe its
    # API and to specify type annotations. They are exported only for the rare use
    # case that an applications bases own type annotations on them.
    # vertex_as_id is the only exception, it is defined here because
    # it is used as a singleton, and is the only predefined instance of VertexToID.
    T,
    Weight,
    T_vertex,
    T_vertex_id,
    T_weight,
    # T_weight_zero_inf_or,
    T_labels,
    VertexToID,
    vertex_as_id,
    UnweightedLabeledOutEdge,
    WeightedUnlabeledOutEdge,
    WeightedLabeledOutEdge,
    WeightedOutEdge,
    LabeledOutEdge,
    OutEdge,
    UnweightedUnlabeledFullEdge,
    UnweightedLabeledFullEdge,
    WeightedFullEdge,
    WeightedOrLabeledFullEdge,
    AnyFullEdge,
)
from ._gear_collections import (
    # --- Gear collection types ---
    VertexSet,
    VertexMapping,
    # --- Gear collections for dense integer keys ---
    # -- Protocols for the used kind of sequences and the wrappers
    # (Only needed for defining/configuring new gears)
    GettableSettableForGearProto,
    SequenceForGearProto,
    VertexSequenceWrapperForSetProto,
    VertexSequenceWrapperForMappingProto,
    # -- ABCs and helper functions to allow for type-save down casts
    # get_wrapper_from_vertex_set,
    # access_to_vertex_set,
    # get_wrapper_from_vertex_mapping,
    # access_to_vertex_mapping_expect_none,
    # access_to_vertex_mapping,
    # -- Implementations or VertexSet/VertexMapping based on wrappers
    # (needed to define new gears that are based on sequences)
    VertexSetWrappingSequence,
    VertexSetWrappingSequenceNoBitPacking,
    VertexSetWrappingSequenceBitPacking,
    VertexMappingWrappingSequence,
    VertexMappingWrappingSequenceWithNone,
    VertexMappingWrappingSequenceWithoutNone,
)
from ._gears import (
    # -- ABCs for the needed collection kinds for NoGraphs
    # (Used library-internal to better document special semantics of some objects)
    # VertexIdSet,
    # VertexIdToVertexMapping,
    # VertexIdToDistanceMapping,
    # VertexIdToEdgeLabelsMapping,
    # MutableSequenceOfVertices,
    # -- Gear protocols
    GearWithoutDistances,
    Gear,
    # -- Concrete gears
    GearForHashableVertexIDs,
    GearDefault,
    GearForHashableVertexIDsAndIntsMaybeFloats,
    GearForHashableVertexIDsAndFloats,
    GearForHashableVertexIDsAndDecimals,
    GearForIntVertexIDs,
    GearForIntVertexIDsAndIntsMaybeFloats,
    GearForIntVertexIDsAndDecimals,
    GearForIntVertexIDsAndCFloats,
    GearForIntVertexIDsAndCInts,
    GearForIntVerticesAndIDs,
    GearForIntVerticesAndIDsAndIntsMaybeFloats,
    GearForIntVerticesAndIDsAndDecimals,
    GearForIntVerticesAndIDsAndCFloats,
    GearForIntVerticesAndIDsAndCInts,
)
from ._paths import (
    Paths,
    # PathsOfUnlabeledEdges,
    # PathsOfLabeledEdges,
    # PathsDummy,
    # DummyPredecessorOrLabelsMapping,
)
from ._path import Path
from ._strategies import (
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
    Strategy,
    Traversal,
    TraversalBreadthFirstFlex,
    TraversalBreadthFirst,
    TraversalDepthFirstFlex,
    TraversalDepthFirst,
    DFSEvent,
    DFSMode,
    TraversalNeighborsThenDepthFlex,
    TraversalNeighborsThenDepth,
    TraversalTopologicalSortFlex,
    TraversalTopologicalSort,
    TraversalShortestPathsFlex,
    TraversalShortestPaths,
    TraversalAStarFlex,
    TraversalAStar,
    TraversalMinimumSpanningTreeFlex,
    TraversalMinimumSpanningTree,
    BSearchBreadthFirstFlex,
    BSearchBreadthFirst,
    BSearchShortestPathFlex,
    BSearchShortestPath,
    TraversalShortestPathsInfBranchingSortedFlex,
    TraversalShortestPathsInfBranchingSorted,
)

from ._extra_edge_gadgets import (
    adapt_edge_index,
    adapt_edge_iterable,
)
from ._extra_matrix_gadgets import (
    Vector,
    Limits,
    Position,
    Array,
)
from ._extra_tsp import (
    GettableProto,
    traveling_salesman_flex,
    traveling_salesman,
)

__all__ = (
    # -- types --
    "T",
    "Weight",
    "T_vertex",
    "T_vertex_id",
    "T_weight",
    # "T_weight_zero_inf_or",
    "T_labels",
    "VertexToID",
    "vertex_as_id",
    "UnweightedLabeledOutEdge",
    "WeightedUnlabeledOutEdge",
    "WeightedLabeledOutEdge",
    "WeightedOutEdge",
    "LabeledOutEdge",
    "OutEdge",
    "UnweightedUnlabeledFullEdge",
    "UnweightedLabeledFullEdge",
    "WeightedFullEdge",
    "WeightedOrLabeledFullEdge",
    "AnyFullEdge",
    # -- gear collections --
    "VertexSet",
    "VertexMapping",
    "GettableSettableForGearProto",
    "SequenceForGearProto",
    "VertexSequenceWrapperForSetProto",
    "VertexSequenceWrapperForMappingProto",
    "VertexSetWrappingSequence",
    "VertexSetWrappingSequenceNoBitPacking",
    "VertexSetWrappingSequenceBitPacking",
    "VertexMappingWrappingSequence",
    "VertexMappingWrappingSequenceWithNone",
    "VertexMappingWrappingSequenceWithoutNone",
    # -- gears --
    "GearWithoutDistances",
    "Gear",
    "GearForHashableVertexIDs",
    "GearDefault",
    "GearForHashableVertexIDsAndIntsMaybeFloats",
    "GearForHashableVertexIDsAndFloats",
    "GearForHashableVertexIDsAndDecimals",
    "GearForIntVertexIDs",
    "GearForIntVertexIDsAndIntsMaybeFloats",
    "GearForIntVertexIDsAndDecimals",
    "GearForIntVertexIDsAndCFloats",
    "GearForIntVertexIDsAndCFloats",
    "GearForIntVerticesAndIDs",
    "GearForIntVerticesAndIDsAndIntsMaybeFloats",
    "GearForIntVerticesAndIDsAndDecimals",
    "GearForIntVerticesAndIDsAndCFloats",
    "GearForIntVerticesAndIDsAndCInts",
    "GearForIntVertexIDsAndCInts",
    # -- paths --
    "Paths",
    # -- path --
    "Path",
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
    # -- bidir search --
    "BSearchBreadthFirstFlex",
    "BSearchBreadthFirst",
    "BSearchShortestPathFlex",
    "BSearchShortestPath",
    # -- extra_edge_gadgets --
    "adapt_edge_index",
    "adapt_edge_iterable",
    # -- extra_infinite_branching --
    "TraversalShortestPathsInfBranchingSortedFlex",
    "TraversalShortestPathsInfBranchingSorted",
    # -- extra_matrix_gadgets --
    "Vector",
    "Limits",
    "Position",
    "Array",
    # -- extra_tsp --
    "GettableProto",
    "traveling_salesman_flex",
    "traveling_salesman",
)
