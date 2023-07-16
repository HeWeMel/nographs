import itertools
import unittest
from typing import Iterator

import nographs as nog


class TestCasePrimes(unittest.TestCase):
    def test_sorted(self) -> None:
        def next_edges_prime_search(
            i: int, t2: nog.TraversalShortestPathsInfBranchingSortedFlex[int, float]
        ) -> Iterator[nog.WeightedUnlabeledOutEdge[int, float]]:
            distance = t2.distance
            yield i + 1, (i + 1) - distance
            if i > 1:
                for i_next in itertools.count(i * i, i):
                    yield i_next, (i_next - distance) - 0.5

        t = nog.TraversalShortestPathsInfBranchingSorted(
            next_edges_prime_search
        ).start_from(1)
        primes = (i for i in t if i == t.distance)

        result50 = list(itertools.takewhile(lambda i: i <= 50, primes))
        primes50 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
        self.assertEqual(result50, primes50)


if __name__ == "__main__":
    unittest.main()
