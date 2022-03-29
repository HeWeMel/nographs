from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.rst').read_text(encoding='utf-8')

setup(
    name="nographs",
    version="2.5.0",
    description=("Graph analysis – the lazy (evaluation) way: Analysis on the fly,"
                 + "for graphs, that are computed and/or adapted on the fly."),
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/HeWeMel/nographs",
    author="Dr. Helmut Melcher",
    author_email='HeWeMel@web.de',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    # install_requires=[],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords='graph,search,traverse,analysis,lazy,infinite,large,adapt',
    python_requires='>=3.9, <4',
    project_urls={
        'Documentation': 'https://nographs.readthedocs.io/',
        'Source': 'https://github.com/hewemel/nographs/',
        'Bug Reports': 'https://github.com/hewemel/nographs/issues',
        # 'Say Thanks!': 'http://saythanks.io/to/HeWeMel',
    },
    license_files='LICENSE',
)

# long_description='%s\n%s' % (
#         re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
#         re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
#     ),
