import decimal
from decimal import Decimal
from collections.abc import Iterator
from typing import Any, TypeVar, TYPE_CHECKING
import unittest

from mpmath import mp, mpf  # type: ignore

import nographs as nog


T_any_typical_weight_type = TypeVar("T_any_typical_weight_type", float, Decimal, mpf)


class Test1(unittest.TestCase):
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

        decimal.getcontext().prec = 75  # precision (number of places)
        self.assertEquals(
            test_with_small_weights(Decimal(0), Decimal("0.5"), Decimal(1)), 65
        )

        mp.prec = 64
        self.assertEquals(test_with_small_weights(mpf(0), mpf("0.5"), mpf(1)), 65)

    def test_typing_docs_example(self) -> None:
        def next_edges(i: int, _) -> Iterator[tuple[int, int]]:
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
        if TYPE_CHECKING:  # pragma: no cover
            reveal_type(v)  # noqa: F821, reveals: int
            reveal_type(d)  # noqa: F821, reveals: float
            reveal_type(p)  # noqa: F821, reveals: tuple[int, ...]
        self.assertEquals(v, 5)
        self.assertEquals(d, 24)
        self.assertEquals(p, (0, 1, 2, 3, 4, 10, 16, 17, 11, 5))
