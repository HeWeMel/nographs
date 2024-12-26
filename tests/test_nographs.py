if __name__ == "__main__":
    """Test functionality and documentation of NoGraphs. With parameter *fast*,
    slow tests are skipped.
    """

    # First, we ensure that we test the right thing by showing sys.path
    import sys

    print(">> sys.path used for the tests:")
    for p in sys.path:
        print(p)
    print()

    import doctest
    import unittest
    import coverage
    import importlib
    import pathlib
    from utils import DocTestFinderSkippingSlowTests, DocTestParserSkippingSlowTests

    # Detect if we have package pymacros4py
    skip_macro_consistency_check = False
    try:
        import pymacros4py  # noqa: F401
    except ImportError:
        skip_macro_consistency_check = True

    # Choose test finder for DocTestSuite and test parser for DocFileSuite
    # When skip_slow_tests is True, skip tests marked by "doctest:+SLOW_TEST".
    # (Only tests that are not needed for 100% coverage are marked as slow. Thus,
    # during development, skip_slow_tests can be set to True without compromising
    # test coverage. During CI, the flag needs to be set to FALSE in order to
    # fully test everything, e.g., also long-running examples of the tutorial.)
    skip_slow_tests = False
    compute_coverage = True
    print(">>", sys.argv)
    for arg in sys.argv[1:]:
        if arg == "fast":
            skip_slow_tests = True
            print("Executing only fast tests!")
        elif arg == "no_coverage":
            compute_coverage = False
            print("Coverage not computed!")
    test_finder = (
        DocTestFinderSkippingSlowTests() if skip_slow_tests else doctest.DocTestFinder()
    )
    test_parser = (
        DocTestParserSkippingSlowTests() if skip_slow_tests else doctest.DocTestParser()
    )

    # Start recording coverage
    if compute_coverage:
        cov = coverage.Coverage(source_pkgs=["nographs"])
        cov.start()

    # Create empty TestSuite
    test_suite = unittest.TestSuite()

    # Test modules: doc tests
    # (Slow are here the test of class
    #    test_traversals_and_searches.GearTestsTraversalsWithOrWithoutLabels
    # but they are not marked as slow tests because they are needed for keeping
    # coverage at 100% even during debugging.)
    for file in pathlib.Path("tests").glob("*.py"):
        file_name = file.name.removesuffix(".py")
        if file_name == "test_expanded_template" and skip_macro_consistency_check:
            print("Skipped", file, "(package pymacros4py not available)")
            continue
        __import__(file_name)
        test_suite.addTests(doctest.DocTestSuite(file_name, test_finder=test_finder))

    # Test modules: unit test classes
    new_suite = unittest.defaultTestLoader.discover("tests", pattern="test_unit*.py")
    test_suite.addTests(new_suite)

    # Package module source: doc tests
    root = pathlib.Path("src", "nographs")
    for file in root.glob("**/*.py"):
        if file.name.removesuffix(".py") == "__init__":
            continue
        file = file.relative_to(root)
        parts = list(file.parts)
        parts[-1] = parts[-1][:-3]  # remove suffix
        module = "." + ".".join(parts)
        temp_module = importlib.import_module(module, "nographs")
        test_suite.addTests(doctest.DocTestSuite(temp_module, test_finder=test_finder))

    # Documentation: doc tests
    for file_path in pathlib.Path(".", "docs", "source").glob("*.rst"):
        test_suite.addTests(
            doctest.DocFileSuite(
                str(file_path), module_relative=False, parser=test_parser
            )
        )

    verbosity = 1  # 1 normal, 2 for more details
    failfast = False  # True
    unittest.TextTestRunner(verbosity=verbosity, failfast=failfast).run(test_suite)

    # Stop recording coverage, create HTML from results
    if compute_coverage:
        cov.stop()
        cov.save()
        cov.xml_report()
        cov.html_report()
    sys.exit()
