from setuptools import setup

setup(
    name="bal",
    version="0.1",
    description="A framework for analyzing and manipulating binary data",
    packages=[
        "bal",
        "bal.analyzers"
    ],
    install_requires=[
        "enum34",
        "typing",
        "six",
    ],
    extras_require={
        "docs": ["sphinx", "sphinx-rtd-theme", "m2r"],
        "examples": ["wget"]
    }
)
