import codecs
import os

from setuptools import find_packages, setup


def read(*parts):
    filename = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(filename, encoding="utf-8") as fp:
        return fp.read()


setup(
    author="Eldarion, Inc.",
    author_email="development@eldarion.com",
    description="kelctl",
    name="kelctl",
    long_description=read("README.rst"),
    version="0.0.1",
    packages=find_packages(),
    entry_points="""
        [console_scripts]
        kelctl=kelctl.__main__:cli
    """,
    install_requires=[
        "PyYAML==3.11",
        "requests==2.9.1",
        "Click==6.6",
        "kel-cluster",
    ],
    zip_safe=False
)
