#  Copyright 2020 Zeppelin Bend Pty Ltd
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import sys

from setuptools import setup, find_namespace_packages

deps = [
    "zepben.evolve==0.33.0b5",
    "dataclassy==0.6.2",
]

# AsyncMock was not included in the base module until 3.8, so use the backport instead if required
v = sys.version_info
if v.major == 3 and v.minor < 8:
    deps.append("mock==4.0.3")

test_deps = [
    "pytest==7.1.2",
    "pytest-cov==2.10.1",
    "pytest-asyncio==0.19.0",
    "pytest-timeout==1.4.2",
    "grpcio-testing==1.46.3",
    "pylint==2.14.5"
]

setup(
    name="zepben.edith",
    version="0.1.0b3",
    description="Python SDK extensions for the Edith project",
    long_description="Extension functions for interacting with the EWB",
    long_description_content_type="text/markdown",
    url="https://github.com/zepben/edith-sdk",
    author="Kurt Greaves",
    author_email="kurt.greaves@zepben.com",
    license="MPL 2.0",
    classifiers=[
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent"
    ],
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    python_requires='>=3.7',
    install_requires=deps,
    extras_require={
        "test": test_deps,
    }
)
