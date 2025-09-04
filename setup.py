#!/usr/bin/env python3
"""
Setup script for EKS Cluster Validator
"""

from setuptools import setup, find_packages
import os

# Read the contents of README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Read requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="eks-cluster-validator",
    version="1.0.0",
    description="Comprehensive validation tool for AWS EKS clusters",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Techize",
    author_email="opensource@techize.com",
    url="https://github.com/techize/eks_validator",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "eks-validator=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="aws eks kubernetes validation monitoring infrastructure",
    project_urls={
        "Bug Reports": "https://github.com/techize/eks_validator/issues",
        "Source": "https://github.com/techize/eks_validator",
        "Documentation": "https://github.com/techize/eks_validator#readme",
    },
)
