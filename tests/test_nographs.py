if __name__ == "__main__":
    import doctest
    import unittest
    import coverage  # type: ignore
    import importlib
    import pathlib

    # import nographs as nog
    #
    # limit = (1 + 128) * 8
    #
    # def next_edges(i, _):
    #     if i < limit:
    #         yield i + 1, 1, 1
    #         yield i + 3, 1, 3
    # t = nog.TraversalDepthFirstFlex(
    #     nog.vertex_as_id,
    #     nog.GearForIntVerticesAndIDs(),
    #     next_labeled_edges=next_edges,
    # )
    # t.debug = True
    # # v = t.start_from(0).go_to(10)
    # for vertex in t.start_from(0):  # , build_paths=True):
    #     pass
    #
    # import sys
    # sys.exit()

    # Start recording coverage
    cov = coverage.Coverage(omit=["tests/test_code.py", "tests/test_nographs.py",
                                  "tests/test_unit_typed.py"])
    cov.start()

    # Create empty TestSuite
    test_suite = unittest.TestSuite()

    # Unittests from doc tests in module with special test cases
    for file in ["test_code"]:
        __import__(file)
        test_suite.addTests(doctest.DocTestSuite(file))

    # Unittests from unit test classes in some unit test files in tests folder
    new_suite = unittest.defaultTestLoader.discover("tests", pattern="test_unit*.py")
    test_suite.addTests(new_suite)

    # Unittests from doc tests in modules of package
    modules = ("types", "strategies", "matrix_gadgets", "edge_gadgets", "paths")
    for f in modules:
        temp_module = importlib.import_module("." + f, "nographs")
        test_suite.addTests(doctest.DocTestSuite(temp_module))

    # Unittests from doc tests in documentation
    p = pathlib.Path("./docs/source")
    for file_path in p.glob("*.rst"):
        test_suite.addTests(doctest.DocFileSuite(str(file_path), module_relative=False))

    verbosity = 1  # 1 normal, 2 for more details
    failfast = True  # True
    unittest.TextTestRunner(verbosity=verbosity, failfast=failfast).run(test_suite)

    # Stop recording coverage, create HTML from results
    cov.stop()
    cov.save()
    cov.xml_report()
    cov.html_report()
