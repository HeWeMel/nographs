if __name__ == "__main__":
    import doctest
    import unittest
    import coverage  # type: ignore
    import importlib
    import pathlib

    # Start recording coverage
    cov = coverage.Coverage(source_pkgs=["nographs"])
    cov.start()

    # Create empty TestSuite
    test_suite = unittest.TestSuite()

    # Test modules: doc tests
    for file in pathlib.Path("tests").glob("*.py"):
        file_name = file.name.removesuffix(".py")
        __import__(file_name)
        test_suite.addTests(doctest.DocTestSuite(file_name))

    # Test modules: unit test classes
    new_suite = unittest.defaultTestLoader.discover("tests", pattern="test_unit*.py")
    test_suite.addTests(new_suite)

    # Package module source: doc tests
    for file in pathlib.Path("src", "nographs").glob("*.py"):
        file_name = file.name.removesuffix(".py")
        if file_name == "__init__":
            continue
        module = "." + file_name
        temp_module = importlib.import_module(module, "nographs")
        test_suite.addTests(doctest.DocTestSuite(temp_module))

    # Documentation: doc tests
    for file_path in pathlib.Path(".", "docs", "source").glob("*.rst"):
        test_suite.addTests(doctest.DocFileSuite(str(file_path), module_relative=False))

    verbosity = 1  # 1 normal, 2 for more details
    failfast = True  # True
    unittest.TextTestRunner(verbosity=verbosity, failfast=failfast).run(test_suite)

    # Stop recording coverage, create HTML from results
    cov.stop()
    cov.save()
    cov.xml_report()
    cov.html_report()
