import unittest
import pymacros4py
import pathlib


class TemplateExpansionTest(unittest.TestCase):
    overwrite = False

    def test_expansion_result(self) -> None:
        """Test that all template files have been correctly expanded"""
        pp = pymacros4py.PreProcessor()
        templates_root = pathlib.Path("tpl")
        for template in templates_root.glob("**/*"):
            if not template.is_file() or not template.name.startswith("!"):
                continue
            print("Processing template", template)

            template_without_exclamation_mark = template.with_name(template.name[1:])
            goal = template_without_exclamation_mark.relative_to(templates_root)

            expanded = pp.expand_file(template)

            # format expansion results of .py files with black
            if template.suffix == ".py":
                tmp_file_path = pymacros4py.write_to_tempfile(expanded)
                pymacros4py.run_process_with_file(
                    ["black", tmp_file_path], tmp_file_path
                )
                expanded = pymacros4py.read_file(tmp_file_path, finally_remove=True)

            if goal.exists() and not self.overwrite:
                current_content = pymacros4py.read_file(goal)
                try:
                    self.assertMultiLineEqual(current_content, expanded)
                except AssertionError as e:
                    d = pp.diff(
                        current_content,
                        expanded,
                        str(goal),
                        f'expanded("{str(template)}")',
                    )
                    print(d, "\n")
                    raise e
            else:
                pymacros4py.write_file(goal, expanded)


if __name__ == "__main__":
    # This code allows to start the input/output test cases manually, without
    # all other tests triggered by the test procedure for the whole package.
    # Note: If this module is run on itself, the current directory needs to
    # be the base directory of the package.

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("overwrite", help="If 'True', overwrite")
    args = parser.parse_args()

    c = TemplateExpansionTest()
    c.overwrite = args.overwrite == "True"
    c.test_expansion_result()
