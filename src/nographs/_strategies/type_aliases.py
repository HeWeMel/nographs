""" Type aliases used for defining the signatures of methods of strategies

Warning: The following types are manually documented in api.rst
"""

from __future__ import annotations

from typing import TypeVar, Callable, Iterable, Any, Union

from nographs._types import (
    T_vertex,
    OutEdge,
    LabeledOutEdge,
    T_labels,
    WeightedUnlabeledOutEdge,
    T_weight,
    WeightedLabeledOutEdge,
    UnweightedLabeledOutEdge,
)
from .strategy import Strategy


T_strategy = TypeVar("T_strategy", bound=Strategy)


# next vertices and next edges functions for traversals
# that work with and without weights

NextVertices = Callable[[T_vertex, T_strategy], Iterable[T_vertex]]
NextEdges = Callable[[T_vertex, T_strategy], Iterable[OutEdge[T_vertex, Any, Any]]]


# next edges functions for traversal that work with weights
NextLabeledEdges = Callable[
    [T_vertex, T_strategy], Iterable[LabeledOutEdge[T_vertex, Any, T_labels]]
]
NextWeightedEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            WeightedUnlabeledOutEdge[T_vertex, T_weight],
            WeightedLabeledOutEdge[T_vertex, T_weight, Any],
        ]
    ],
]
NextWeightedLabeledEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[WeightedLabeledOutEdge[T_vertex, T_weight, T_labels]],
]


# The same, but as a tuple, for bidirectional search strategies

BNextVertices = tuple[
    NextVertices[T_vertex, T_strategy],
    NextVertices[T_vertex, T_strategy],
]
BNextEdges = tuple[
    NextEdges[T_vertex, T_strategy],
    NextEdges[T_vertex, T_strategy],
]
BNextLabeledEdges = tuple[
    NextLabeledEdges[T_vertex, T_strategy, T_labels],
    NextLabeledEdges[T_vertex, T_strategy, T_labels],
]
BNextWeightedEdges = tuple[
    NextWeightedEdges[T_vertex, T_strategy, T_weight],
    NextWeightedEdges[T_vertex, T_strategy, T_weight],
]
BNextWeightedLabeledEdges = tuple[
    NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
    NextWeightedLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
]


# --------------- package internal types -------------

NextEdgesOrVertices = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            T_vertex,
            WeightedUnlabeledOutEdge[T_vertex, Any],
            UnweightedLabeledOutEdge[T_vertex, T_labels],
            WeightedLabeledOutEdge[T_vertex, Any, T_labels],
        ]
    ],
]
NextWeightedMaybeLabeledEdges = Callable[
    [T_vertex, T_strategy],
    Iterable[
        Union[
            WeightedUnlabeledOutEdge[T_vertex, T_weight],
            WeightedLabeledOutEdge[T_vertex, T_weight, T_labels],
        ]
    ],
]
# The same, but as a tuple, for bidirectional search strategies

BNextEdgesOrVertices = tuple[
    NextEdgesOrVertices[T_vertex, T_strategy, T_labels],
    NextEdgesOrVertices[T_vertex, T_strategy, T_labels],
]
BNextWeightedMaybeLabeledEdges = tuple[
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
    NextWeightedMaybeLabeledEdges[T_vertex, T_strategy, T_weight, T_labels],
]
