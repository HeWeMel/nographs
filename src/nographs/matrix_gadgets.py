from __future__ import annotations

import itertools
import operator
from collections.abc import (
    Sequence,
    Mapping,
    Callable,
    Iterable,
    Iterator,
    Hashable,
)
from numbers import Real
from typing import Optional, Any


Vector = Sequence[int]  # api.rst: documented manually
Vectors = Sequence[Vector]
Limits = Sequence[tuple[int, int]]  # api.rst: documented manually


class Position(tuple[int]):
    """A position in an n-dimensional array. It is initialized
    by a `Vector`."""

    @classmethod
    def at(cls, *coordinates: int) -> Position:
        """Factory method, that creates a position from coordinates given
        as separated parameters.
        """
        return Position(coordinates)

    def __add__(self, other: Vector) -> Position:  # type: ignore[override]
        """Add the *other* `Vector` to the position"""
        return Position(map(sum, zip(self, other)))

    def __sub__(self, other: Vector) -> Position:
        """Subtract the *other* `Vector` from the position."""
        return Position(map(operator.sub, self, other))

    def manhattan_distance(self, other: Vector) -> int:
        """Manhattan distance of the *other* `Vector` from the
        given position vector."""
        return sum(abs(coordinate_diff) for coordinate_diff in self - other)

    def is_in_cuboid(self, limits: Limits) -> bool:
        """Return true if each coordinate of the position is inside
        the respective range defined by the *limits* sequence (see `Limits`).
        """
        return all(
            low_limit <= coordinate < high_limit
            for coordinate, (low_limit, high_limit) in zip(self, limits)
        )

    def wrap_to_cuboid(self, limits: Limits) -> Position:
        """If a coordinate of the position is outside its respective
        limit range *(from, to)* of the *limits* sequence (see `Limits`),
        add or subtract the size (to - from + 1) of the limit range as often
        as necessary to correct this.
        """
        coordinates = []
        for coordinate, (low_limit, high_limit) in zip(self, limits):
            if coordinate < low_limit:
                window_size = high_limit - low_limit
                coordinate = high_limit - (high_limit - coordinate) % window_size
            if coordinate >= high_limit:
                window_size = high_limit - low_limit
                coordinate = (coordinate - low_limit) % window_size + low_limit
            coordinates.append(coordinate)
        return Position(coordinates)

    @staticmethod
    def moves(
        dimensions: int = 2,
        diagonals: bool = False,
        zero_move: bool = False,
    ) -> Vectors:
        """
        Generate vectors of moves to neighbor coordinates in an n-dimensional
        Array in sorted order, i.e., vectors that differ in each coordinate
        by -1, 0 or 1.

        :param dimensions: Number of dimensions of the generated move vectors.
        :param diagonals: Add diagonal moves (no zero in any coordinate).
        :param zero_move: Add the zero move *(0, ...)*.
        """
        moves = []
        for move in itertools.product(range(-1, 2), repeat=dimensions):
            if not zero_move and all(coordinate == 0 for coordinate in move):
                continue
            if not diagonals and all(coordinate != 0 for coordinate in move):
                continue
            moves.append(move)
        return moves

    def neighbors(
        self,
        moves: Iterable[Vector],
        limits: Optional[Limits] = None,
        wrap: bool = False,
    ) -> Iterator[Position]:
        # noinspection PyShadowingNames
        """
        Iterate the positions that are reached by performing the given moves.
        Can limit or wrap moves at a cuboid.

        :param moves: They define what moves lead to neighbors (irrespective the
          optionally given limits).
        :param limits: If given, they define the cuboid the generated positions
          have to stay in.
        :param wrap: If True, moves to positions outside the limits cuboid are
          wrapped at this boundary. If False, such moves are ignored.
        """
        # inspection PyShadowingNames
        for move in moves:
            neighbor_position = self + move
            if limits is None:
                if wrap is True:
                    raise RuntimeError("Limits for Option wrap missing")
                yield neighbor_position
            elif wrap:
                yield neighbor_position.wrap_to_cuboid(limits)
            else:
                if neighbor_position.is_in_cuboid(limits):
                    yield neighbor_position


class Array:
    def __init__(self, nested_sequences, dimensions: int = 2):
        """An n-dimensional array.

        Based on *nested sequences* that, up to a given number of
        *dimensions*, define its content. Data in nestings deeper than
        that is interpreted as part of the content of an array cell.

        Coordinates of a position in the array are meant in the order from "outer"
        to "inner" sequences along the nesting. Coordinates used as arguments
        for Array methods can be given as Vector, especially as Position.

        :param nested_sequences: Content of the array to be created.
        :param dimensions: Number of dimensions the array should have.
        """
        self.content = nested_sequences
        self.dimensions = dimensions

    def size(self) -> Sequence[int]:
        # noinspection PyShadowingNames
        """Calculate the size of the array per dimension."""
        # inspection PyShadowingNames
        size = []
        area = self.content
        for d in range(self.dimensions):
            size.append(len(area))
            area = area[0]
        return size

    def limits(self) -> Limits:
        """Calculate coordinate limits (see `Limits`) per dimension as tuples
        (from, to). Since the array consists of nested sequences,
        *from* is always zero and *to* equals the size of the array
        in this dimension."""
        return [(0, upper) for upper in self.size()]

    def mutable_copy(self) -> Array:
        """Create a mutable copy of the array."""

        def _writable(area, dimensions):
            if dimensions > 1:
                return [_writable(sub_area, dimensions - 1) for sub_area in area]
            else:
                return list(area)

        return Array(_writable(self.content, self.dimensions), self.dimensions)

    def __getitem__(self, position: Vector):
        """Get the content at the given position. This allows for using
        the expression syntax *array[...]*.

        :param position: The content at this position `Vector` is returned.
        """
        i = self.content
        for coordinate in position:
            i = i[coordinate]
        return i

    def __setitem__(self, position: Vector, content: Any):
        # noinspection PyShadowingNames
        """Set the content at the given position. Assumption: The nested
        sequence the array is build upon is mutable in its last dimension
        (i.e., a list). Allows for using the assignment syntax
        *array[...] = ...* .

        :param position: The content at this position `Vector` is replaced.
        :param content: This content is stored at the position.
        """
        # inspection PyShadowingNames
        field = self.content
        for coordinate in position[:-1]:
            field = field[coordinate]
        field[position[-1]] = content

    def items(self) -> Iterator[tuple[Position, Any]]:
        """Iterate positions and content."""
        # Attention: Method signature is manually documented, update also there

        def _items_in_dimension(area, dimensions):
            if dimensions == 1:
                for coordinate, sub_area in enumerate(area):
                    yield (coordinate,), sub_area
            else:
                for coordinate, sub_area in enumerate(area):
                    for sub_vector, content in _items_in_dimension(
                        sub_area, dimensions - 1
                    ):
                        yield (coordinate,) + sub_vector, content

        return (
            (Position(coordinates), content)
            for coordinates, content in _items_in_dimension(
                self.content, self.dimensions
            )
        )

    def findall(self, content: Iterable[Any]) -> tuple[Position, ...]:
        """Find content in array and return found positions.
        The content is given in some container, i.e., a set.

        :param content: This content is searched. The found positions
           are returned in the same order as the content elements are given.
        """
        # Attention: Method signature is manually documented, update also there

        content_set = set(content)

        def find_in_dimension(p_matrix, p_dimensions) -> Iterator[tuple[int, ...]]:
            if p_dimensions == 1:
                for coordinate, cell_content in enumerate(p_matrix):
                    if cell_content in content_set:
                        yield (coordinate,)
            else:
                for coordinate, sub_area in enumerate(p_matrix):
                    for found in find_in_dimension(sub_area, p_dimensions - 1):
                        yield (coordinate,) + found

        return tuple(
            Position(v) for v in find_in_dimension(self.content, self.dimensions)
        )

    def next_vertices_from_forbidden(
        self,
        forbidden: Iterable[Hashable],
        wrap: bool = False,
        diagonals: bool = False,
    ) -> Callable:
        # noinspection PyShadowingNames
        """Return a `NextVertices` function for traversal strategies, based on
        given choice of when positions qualify as neighbors (goals of a
        move) of a given position (options *wrap* and *diagonals*) and whether
        such a move is allowed w.r.t. the content of the array at this
        position (parameter *forbidden*).

        :param forbidden: A move to a position with this content is not allowed.
        :param wrap: Positions are wrapped at the array limits.
        :param diagonals: Diagonal moves are allowed.
        """
        # inspection PyShadowingNames
        forbidden_content = set(forbidden)
        limits = self.limits()
        moves = Position.moves(dimensions=self.dimensions, diagonals=diagonals)

        def next_vertices(position, _):
            for neighbor in position.neighbors(moves=moves, limits=limits, wrap=wrap):
                if self[neighbor] not in forbidden_content:
                    yield neighbor

        return next_vertices

    def next_edges_from_cell_weights(
        self,
        content_to_weight: Mapping[Any, Real],
        wrap: bool = False,
        diagonals: bool = False,
    ) -> Callable:
        # noinspection PyShadowingNames
        """Return a `NextEdges` function for traversal strategies, based on
        given choice of when positions qualify as neighbors (goals of a
        move) of a given position (options *wrap* and *diagonals*) and what
        weight such a move has w.r.t. the content of the matrix at this
        position (parameter *content_to_weight*, and no assigned weight means
        the move is impossible).

        :param content_to_weight: Returns the weight of a move to a given position.
        :param wrap: Positions are wrapped at the array limits.
        :param diagonals: Diagonal moves are allowed.
        """
        # inspection PyShadowingNames
        limits = self.limits()
        moves = Position.moves(dimensions=self.dimensions, diagonals=diagonals)

        def next_edges(vector, _):
            for neighbor in vector.neighbors(moves=moves, limits=limits, wrap=wrap):
                weight = content_to_weight.get(self[neighbor], None)
                if weight is not None:
                    yield neighbor, weight

        return next_edges
