import unittest
import nographs as nog


class TestWeight(unittest.TestCase):
    """Check if the library detects the mistake that abstract methods
    of a protocol are called.

    If the detection works correctly, CPython and MyPy raise a runtime error
    and MyPyC raises a TypeError.
    We hide the problem from MyPy here, because we make the error on purpose:
    Testing the runtime detection of these errors is the purpose of the tests.
    """

    def test_protocol_and_ABC_not_implemented_errors(self) -> None:
        cls = nog.Weight
        with self.assertRaises((NotImplementedError, TypeError)):
            cls.__add__(0, 0)
        with self.assertRaises((NotImplementedError, TypeError)):
            cls.__sub__(0, 0)
        with self.assertRaises((NotImplementedError, TypeError)):
            cls.__lt__(0, 0)
        with self.assertRaises((NotImplementedError, TypeError)):
            cls.__le__(0, 0)


class TestVertex_AS_ID(unittest.TestCase):
    """Test function vertex_as_id. Test needed here, since this
    function is not intended to be really called anywhere in NoGraphs.
    """

    def test_functionality(self) -> None:
        self.assertEqual(nog.vertex_as_id(0), 0)
