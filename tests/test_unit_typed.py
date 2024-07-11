import sys
from decimal import Decimal, getcontext
from collections.abc import Iterator, Iterable
from typing import Any, TypeVar, Union, TYPE_CHECKING

import nographs as nog

if sys.version_info >= (3, 11):
    from typing import assert_type
import unittest

from mpmath import mp, mpf  # type: ignore

# noinspection PyProtectedMember
from nographs._extra_tsp import GettableProto


# --- Types ---

T_any_typical_weight_type = TypeVar("T_any_typical_weight_type", float, Decimal, mpf)


# --- Tests ---


class TestWithTypes(unittest.TestCase):
    def test_variable_edge_weights(self) -> None:
        def test_with_small_weights(
            zero: T_any_typical_weight_type,
            one_half: T_any_typical_weight_type,
            one: T_any_typical_weight_type,
        ) -> int:
            def next_edges(
                i: int, _: Any
            ) -> Iterator[tuple[int, T_any_typical_weight_type]]:
                yield i + 1, one_half**i

            traversal = nog.TraversalShortestPaths[int, T_any_typical_weight_type, Any](
                next_edges
            )

            goal_difference = one_half**64
            previous_distance = zero
            for vertex in traversal.start_from(1):
                distance = traversal.distance
                assert isinstance(distance, type(one))
                if one - distance == goal_difference:
                    return vertex
                if distance == previous_distance:
                    raise RuntimeError("Error: Distance stays constant")
                previous_distance = distance
            raise RuntimeError("Unexpected end of loop")  # pragma: no cover

        with self.assertRaises(RuntimeError) as cm:
            test_with_small_weights(float(0), float("0.5"), float(1))
        self.assertEqual(cm.exception.args, ("Error: Distance stays constant",))

        getcontext().prec = 75  # precision (number of places)
        self.assertEqual(
            test_with_small_weights(Decimal(0), Decimal("0.5"), Decimal(1)), 65
        )

        mp.prec = 64
        self.assertEqual(test_with_small_weights(mpf(0), mpf("0.5"), mpf(1)), 65)

    def test_traversal_typing_docs_example(self) -> None:
        def next_edges(i: int, _: Any) -> Iterator[tuple[int, int]]:
            j = (i + i // 6) % 6
            yield i + 1, j * 2 + 1
            if i % 2 == 0:
                yield i + 6, 7 - j
            elif i % 1200000 > 5:
                yield i - 6, 1

        traversal = nog.TraversalShortestPaths[int, int, Any](next_edges)
        v = traversal.start_from(0, build_paths=True).go_to(5)
        d = traversal.distance
        p = tuple(traversal.paths.iter_vertices_from_start(v))
        if sys.version_info >= (3, 11):
            if TYPE_CHECKING:
                # for Python>=3.11, check types
                assert_type(v, int)
                assert_type(d, Union[int, float])
                assert_type(p, tuple[int, ...])
        else:
            reveal_type = print  # will never be used; just for IDEs
            # for Python<3.11, reveal types
            if TYPE_CHECKING:
                reveal_type(v)  # reveals: int
                reveal_type(d)  # reveals: Union[int, float]
                reveal_type(p)  # reveals: tuple[int, ...]
        self.assertEqual(v, 5)
        self.assertEqual(d, 24)
        self.assertEqual(p, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5))

    def test_tsp_typing_docs_example(self) -> None:
        """The MyPy run will detect if the typing goes wrong here.

        The NOQA tells flake8 that it is on purpose that g1 and g2 are
        assigned but never used.
        """
        g1: GettableProto[int, str] = dict[int, str]([(0, "a"), (1, "b")])  # NOQA F841
        g2: GettableProto[int, str] = ["a", "b"]  # NOQA F841

    def test_dfs_throw(self) -> None:
        """DFS function iter() returns a Collections.Generator. Its type is tested
        my the MyPy run here. And The behaviour of the throw, both for stops
        at a start vertex and at other vertices."""

        def next_vertices(i: int, _: Any) -> Iterator[int]:
            yield i + 1

        stop = StopIteration()
        traversal = nog.TraversalDepthFirst[int, None](next_vertices)

        # Check effect of throw
        it = iter(
            traversal.start_from(start_vertices=[0, 10], report=nog.DFSEvent.ENTERING)
        )
        vertices = []
        for v in it:
            if v >= 5:
                # noinspection PyUnresolvedReferences
                _ = it.throw(stop)
            vertices.append(v)
        self.assertEqual(vertices, [0, 1, 2, 3, 4, 5, 10])

        # Check if the following reports 0
        def next_vertices2(i: int, _: Any) -> Iterable[int]:
            return []

        traversal = nog.TraversalDepthFirst[int, None](next_vertices2)
        it = iter(
            traversal.start_from(
                start_vertices=[0, 0, 0], report=nog.DFSEvent.SKIPPING_START
            )
        )
        self.assertEqual(next(it), 0)
        # Check if throwing StopIteration at this moment falls through
        try:
            # noinspection PyUnresolvedReferences
            _ = it.throw(stop)
        except RuntimeError:
            return
        self.fail("StopIteration, thrown at illegal moment, raises RuntimeError.")
