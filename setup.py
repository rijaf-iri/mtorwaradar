import os
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

def read(fname):
    try:
        with open(os.path.join(os.path.dirname(__file__), fname)) as fh:
            return fh.read()
    except IOError:
        return ''

requirements = read('requirements.txt').splitlines()

setup(
    name="mtorwaradar",
    version="1.0",
    author="Rija Faniriantsoa",
    author_email="rijaf@iri.columbia.edu",
    description="Meteo Rwanda Radar Data Processing",
    url="https://github.com/rijaf-iri/mtorwaradar",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Meteo Rwanda",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
)
