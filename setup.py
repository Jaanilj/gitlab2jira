#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitlab2jira",
    version="1.0.0",
    author="GitLab to Jira CLI",
    author_email="",
    description="A command-line tool to create Jira tickets from GitLab merge requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitlab2jira",
    py_modules=["gitlab2jira"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Utilities",
    ],
    python_requires=">=3.12",
    install_requires=[
        "requests>=2.25.0,<3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gitlab2jira=gitlab2jira:main",
        ],
    },
    keywords="gitlab jira automation cli merge-request ticket",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/gitlab2jira/issues",
        "Source": "https://github.com/yourusername/gitlab2jira",
        "Documentation": "https://github.com/yourusername/gitlab2jira#readme",
    },
)
