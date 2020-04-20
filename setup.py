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
    install_requires=[
        "Flask==1.0.3",
        "psutil==5.6.3",
        "requests==2.22.0",
        "python-dotenv==0.10.3",
    ],
    entry_points={"console_scripts": ["crab=crab.cli:main"]},
)
