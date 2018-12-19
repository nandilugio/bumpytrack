#!/bin/bash

pipenv lock -r --dev > dev_requirements.txt
pip install -r dev_requirements.txt
python setup.py install .
pytest

