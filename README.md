# mtorwaradar - Meteo Rwanda Radar Data Processing

## Documentation: [MeteoRwandaRadar](https://iri.columbia.edu/~rijaf/)

## General
`mtorwaradar` is a Python library that offers a set of function to process data from Meteo Rwanda Radar.
It depends on the Python ARM Radar Toolkit [Py-ART](https://arm-doe.github.io/pyart-docs-travis/).

## Installation
 * Clone the source of this library: `git clone https://github.com/rijaf-iri/meteoRwandaRadar.git`
 * Install dependencies: `pip install -r ./requirements.txt `
 * Building: `python setup.py sdist bdist_wheel`
 * Install using pip: `pip install ./dist/mtorwaradar-1.0.tar.gz` or `pip install ./dist/mtorwaradar-1.0-py3-none-any.whl`

## Quick start

```python
import mtorwaradar
```
