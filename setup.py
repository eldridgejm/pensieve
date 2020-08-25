from setuptools import setup, find_packages

setup(
    name="pensieve",
    version="0.2.0",
    packages=["pensieve"],
    install_requires=["pyyaml", "requests"],
    entry_points={"console_scripts": ["pensieve = pensieve.cli:main"]},
)
