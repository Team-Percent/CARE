#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "django",
    "djangorestframework",
    "django-environ",
    "django-filter",
    "celery",
    "pypdf",
    "requests",
]

test_requirements = []

setup(
    author="Team-Percent",
    author_email="connect@snbhowmik.dev",
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    description="CARE EMR Plugin for MedGemma AI, FHIR R5 Export, Consent & Audit",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="care_medgemma",
    name="care_medgemma",
    packages=find_packages(include=["care_medgemma", "care_medgemma.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/Team-Percent/CARE",
    version="0.1.0",
    zip_safe=False,
)
