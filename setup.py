from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="deduper",
    version="0.1.0",
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
    python_requires=">=3.7",
    install_requires=[
        "flask>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "deduper=deduper.cli:main",
        ],
    },
)
