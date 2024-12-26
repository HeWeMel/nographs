# This file controls the compilation of the modules of the package to extension
# modules by using MyPyC or Cython. If this option is not needed, it can be removed.
#
# Usage: If environment variable SETUP_BUILD_EXTENSION is set to MyPyC or Cython,
# extension modules are build. And if it is set to "False", or not set at all,
# the pure Python modules are copied into the wheel.

import pathlib
import os
from setuptools import setup, find_packages


def find_sources(exclude_from_compilation):
    compile_this = []
    for file_path in pathlib.Path('.', 'src', 'nographs').glob('**/*.py'):
        if file_path.name in exclude_from_compilation:
            print('setup.py: We will skip the compilation of file', file_path)
            continue
        compile_this.append(str(file_path))
    print('setup.py: We will compile these files:\n', compile_this, "\n")
    return compile_this


compiler = os.environ.get('SETUP_BUILD_EXTENSION', "False").capitalize()
match compiler:
    case "False":
        print("\nsetup.py: Building sdist (tarball) / and or pure Python wheel.")
        print("(Set environment variable SETUP_BUILD_EXTENSION to MyPyC or Cython "
              "to compile binaries.)")
        ext_modules = []

    case "Mypyc":
        print(f"\nsetup.py: Compiling binaries using MyPyC.")
        print("(Set environment variable SETUP_BUILD_EXTENSION to False "
              "to build sdist / and or pure Python wheel instead.)")
    
        from mypyc.build import mypycify
        exclude_from_compilation = [
            # The following file contains classes, compilation would be useful, but
            # it is intentionally not compiled here due to the following issue of
            # MyPyC:
            # https://github.com/mypyc/mypyc/issues/1022
            'depth_first_enum_types.py',
            # The following file subclasses tuple[int]. MyPyC does not support this.
            # But on CPython this us much faster than to store the tuple in an attribute
            # Conditional class definition is also not supported. So, we simply exclude
            # this file from compilation.
            '_extra_matrix_gadgets.py',
        ]
        compile_this = find_sources(exclude_from_compilation)
        ext_modules = mypycify(compile_this, strip_asserts=False)

    case "Cython":
        print(f"\nsetup.py: Compiling binaries using Cython.")
        print("(Set environment variable SETUP_BUILD_EXTENSION to False "
              "to build sdist / and or pure Python wheel instead.)")
        from Cython.Build import cythonize
        exclude_from_compilation = []
        compile_this = find_sources(exclude_from_compilation)
        ext_modules = cythonize(compile_this, compiler_directives={'language_level': 3})

    case _:
        raise RuntimeError(
            "Valid values or environment variable SETUP_BUILD_EXTENSION are:"
            "  'False', 'MyPyC', and 'Cython'"
            "If no value is set, this equals to 'False'.")

if ext_modules:
    setup(
        name='nographs',
        package_dir={'': 'src'},
        packages=find_packages('src'),
        ext_modules=ext_modules,
    )
else:
    setup(
        name='nographs',
        package_dir={'': 'src'},
        packages=find_packages('src'),
    )
