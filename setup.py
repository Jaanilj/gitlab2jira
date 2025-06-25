#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["setuptools>=61.0.0"]
# ///


from setuptools import setup

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
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: Utilities",
    ],
    python_requires=">=3.12",
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
