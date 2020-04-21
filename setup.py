from setuptools import setup

with open("README.md") as f:
    readme = f.read()

setup(
    name="crabtools",
    version=__import__("crab").__version__,
    url="https://github.com/dabapps/crab",
    author="DabApps",
    description="A simple unix toolkit for working with local development environments.",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="BSD",
    packages=["crab"],
    install_requires=["Flask", "psutil", "requests", "python-dotenv"],
    entry_points={"console_scripts": ["crab=crab.cli:main"]},
)
