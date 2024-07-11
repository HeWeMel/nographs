"""
Adaptations to the DocTest framework that allows for skipping slow tests
on demand.

Add the following flag to slow tests:  # doctest:+SLOW_TEST


"""

import doctest
from typing import Any
import types


SLOW_TEST = doctest.register_optionflag("SLOW_TEST")


class DocTestFinderSkippingSlowTests(doctest.DocTestFinder):
    """A DocTestFinder that skips examples having option SLOW_TEST set"""

    def find(
        self,
        obj: object,
        name: str | None = None,
        module: None | bool | types.ModuleType = None,
        globs: dict[str, Any] | None = None,
        extraglobs: dict[str, Any] | None = None,
    ) -> list[doctest.DocTest]:
        tests = super().find(obj, name, module, globs, extraglobs)
        for test in tests:
            test.examples = [
                example for example in test.examples if SLOW_TEST not in example.options
            ]
        return tests


class DocTestParserSkippingSlowTests(doctest.DocTestParser):
    """A DocTestParser that skips examples having option SLOW_TEST set"""

    def get_doctest(
        self,
        string: str,
        globs: dict[str, Any],
        name: str,
        filename: str | None,
        lineno: int | None,
    ) -> doctest.DocTest:
        test = super().get_doctest(string, globs, name, filename, lineno)
        test.examples = [
            example for example in test.examples if SLOW_TEST not in example.options
        ]
        return test
