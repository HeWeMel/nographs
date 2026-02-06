import unittest
import nographs as nog

# --- Tests ---


class InitiationForgotten(unittest.TestCase):
    """Check if the library detects the mistake that start_from or one of the
    go_... methods are called on a traversal class instead of an object, i.e., the
    round brackets after the class name have been forgotten.

    If the detection works correctly, CPython and MyPy raise a runtime error
    and MyPyC raises a TypeError.
    We hide the problem from MyPy here, because we make the error on purpose:
    Testing the runtime detection of these errors is the purpose of the tests.
    """

    # todo: NoGraphs´ own detection should also raise TypeError
    def test_TraversalBreadthFirst(self) -> None:
        cls = nog.TraversalBreadthFirst
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_depth_range(None, None, None)  # type: ignore [arg-type]

    def test_TraversalDepthFirst(self) -> None:
        cls = nog.TraversalDepthFirst
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]

    def test_TraversalNeighborsThenDepth(self) -> None:
        cls = nog.TraversalNeighborsThenDepth
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]

    def test_TraversalShortestPaths(self) -> None:
        cls = nog.TraversalShortestPaths
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_distance_range(None, None, None)  # type: ignore [arg-type]

    def test_TraversalShortestPathsInfBranchingSorted(self) -> None:
        cls = nog.TraversalShortestPathsInfBranchingSorted
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_distance_range(None, None, None)  # type: ignore [arg-type]

    def test_TraversalAStar(self) -> None:
        cls = nog.TraversalAStar
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None, None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]

    def test_TraversalMinimumSpanningTree(self) -> None:
        cls = nog.TraversalMinimumSpanningTree
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]

    def test_TraversalTopologicalSort(self) -> None:
        cls = nog.TraversalTopologicalSort
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.__iter__(None)  # type: ignore [arg-type]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_to(None, None)  # type: ignore [call-overload]
        with self.assertRaises((RuntimeError, TypeError)):
            cls.go_for_vertices_in(None, None)  # type: ignore [arg-type]

    def test_BSearchBreadthFirst(self) -> None:
        cls = nog.BSearchBreadthFirst
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]

    def test_BSearchShortestPath(self) -> None:
        cls = nog.BSearchShortestPath
        with self.assertRaises((RuntimeError, TypeError)):
            cls.start_from(None)  # type: ignore [arg-type]
