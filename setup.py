import sys
from os.path import join, dirname, abspath

from setuptools import setup, find_packages

# this is a trick to get the version before the package is installed
directory = dirname(abspath(__file__))
sys.path.insert(0, join(directory, "bigg_models"))
version = __import__("version").__version__

setup(
    name="bigg_models",
    version=version,
    author="Justin Lu & Zachary King",
    author_email="zaking@ucsd.edu",
    url="http://bigg.ucsd.edu",
    packages=find_packages(),
    package_data={
        "bigg_models": [
            "static/assets/*",
            "static/css/*",
            "static/js/*",
            "static/lib/*",
            "static/lib/tablesorter/*",
            "templates/*",
            "db_management/*",
        ]
    },
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    install_requires=[
        "cobradb",
        "Jinja2",
        "simplejson",
        "progressbar2",
    ],
)
