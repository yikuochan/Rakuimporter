#!/usr/bin/env python3
"""
Setup script for Power Importer

This script installs the Power Importer package and its dependencies.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="power-importer",
    version="1.0.0",
    author="VicOne",
    author_email="support@vicone.com",
    description="A tool for importing financial data into ERP systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vicone/power-importer",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.0",
        "chardet>=4.0.0",
        "certifi>=2020.12.5",
        "urllib3>=1.26.0",
    ],
    entry_points={
        "console_scripts": [
            "power-importer=run_importer:main",
        ],
    },
)
