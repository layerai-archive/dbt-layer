#!/usr/bin/env python
from setuptools import find_namespace_packages, setup

package_name = "dbt-dbt-layer-bigquery"
# make sure this always matches dbt/adapters/dbt-layer-bigquery/__version__.py
package_version = "1.2.0a1"
description = """The dbt-layer-bigquery adapter plugin for dbt"""

setup(
    name=package_name,
    version=package_version,
    description=description,
    long_description=description,
    author="Layer",
    author_email="info@layer.ai",
    url="layer.ai",
    packages=find_namespace_packages(include=['dbt', 'dbt.*']),
    include_package_data=True,
    install_requires=[
        "dbt-core==1.2.0a1",
        #<INSERT DEPENDENCIES HERE>
    ]
)
