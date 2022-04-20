#!/usr/bin/env python
import sys
import re

# require python 3.7 or newer
if sys.version_info < (3, 7):
    print("Error: layer-bigquery does not support this version of Python.")
    print("Please upgrade to Python 3.7 or higher.")
    sys.exit(1)


# require version of setuptools that supports find_namespace_packages
from setuptools import setup

try:
    from setuptools import find_namespace_packages
except ImportError:
    # the user has a downlevel version of setuptools.
    print("Error: dbt requires setuptools v40.1.0 or higher.")
    print('Please upgrade setuptools with "pip install --upgrade setuptools" ' "and try again")
    sys.exit(1)


from pathlib import Path


this_directory = Path().absolute()

with open(this_directory / "README.md") as f:
    long_description = f.read()


# get this package's version from dbt/adapters/<name>/__version__.py
def _get_plugin_version_dict():
    _version_path = this_directory / "dbt" / "adapters" / "layer_bigquery" / "__version__.py"
    _semver = r"""(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"""
    _pre = r"""((?P<prekind>a|b|rc)(?P<pre>\d+))?"""
    _version_pattern = rf"""version\s*=\s*["']{_semver}{_pre}["']"""
    with open(_version_path) as f:
        match = re.search(_version_pattern, f.read().strip())
        if match is None:
            raise ValueError(f"invalid version at {_version_path}")
        return match.groupdict()


# require a compatible minor version (~=), prerelease if this is a prerelease
def _get_dbt_core_version():
    parts = _get_plugin_version_dict()
    minor = "{major}.{minor}.0".format(**parts)
    pre = parts["prekind"] + "1" if parts["prekind"] else ""
    return f"{minor}{pre}"


package_name = "dbt-layer-bigquery"
package_version = "0.1.0"
dbt_core_version = _get_dbt_core_version()
description = """The Layer-BigQuery adapter plugin for dbt"""


requirements = [
    "dbt-core~={}".format(dbt_core_version),
    "dbt-bigquery==1.0.0",
]

setup_requirements = [
]

test_requirements = [
    'pytest-dbt-adapter==0.6.0'
]

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=description,
    author="Layer",
    author_email="info@layer.ai",
    url="https://layer.ai",
    packages=find_namespace_packages(include=['dbt', 'dbt.*']),
    include_package_data=True,
    install_requires=requirements,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    classifiers=[
        "Development Status :: 1 - Planning",
        # "License :: OSI Approved :: Apache Software License",
        # "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)
