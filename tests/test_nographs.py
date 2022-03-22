if __name__ == "__main__":
    import doctest
    import unittest
    import coverage
    import importlib
    import pathlib

    # Start recording coverage
    cov = coverage.Coverage()
    cov.start()

    # Create empty TestSuite
    test_suite = unittest.TestSuite()

    # Unittests from doc tests in modules of package
    modules = ("types", "strategies", "matrix_gadgets", "edge_gadgets", "paths")
    for f in modules:
        temp_module = importlib.import_module("." + f, "nographs")
        test_suite.addTests(doctest.DocTestSuite(temp_module))

    # Unittests from doc tests in module with special test cases
    __import__("test_code")
    test_suite.addTests(doctest.DocTestSuite("test_code"))

    # Unittests from doc tests
    p = pathlib.Path('docs/source')
    for file_path in p.glob('*.rst'):
        test_suite.addTests(doctest.DocFileSuite(str(file_path.resolve())))

    unittest.TextTestRunner().run(test_suite)

    # Stop recording coverage, create HTML from results
    cov.stop()
    cov.save()
    cov.xml_report()
    cov.html_report()
