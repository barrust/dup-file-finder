from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="deduper",
    version="0.0.1",
    author="Tyler Barrus",
    description="A Python library to find and manage duplicate files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/barrust/deduper",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "deduper=deduper.cli:main",
        ],
    },
)
