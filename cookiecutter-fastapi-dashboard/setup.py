#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" setup.py for cookiecutter-fastapi-dashboard."""

from setuptools import setup

__version__ = "2026.10.16"

with open("README.md", encoding="utf-8") as readme_file:
    long_description = readme_file.read()

setup(
    name="cookiecutter-fastapi-dashboard",
    version=__version__,
    description="A Cookiecutter template for creating FastAPI dashboard / KPI APIs quickly.",
    long_description=long_description,
    author="Kaeyros Analytics",
    url="",
    download_url="",
    packages=[],
    include_package_data=True,
    license="MIT",
    classifiers=[
        "Framework :: FastAPI",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
    ],
    keywords=(
        """
        cookiecutter, Python, projects, project templates, FastAPI,
        dashboard, KPI, skeleton, scaffolding, project directory, setup.py
        """
    ),
)
