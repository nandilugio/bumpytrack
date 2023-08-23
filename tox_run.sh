#!/bin/bash

echo "Running $(basename $0)..."

set -x

python --version
PIPENV_VERBOSITY=-1 pipenv requirements --dev > dev_requirements_tox.txt
pip install -r dev_requirements_tox.txt
python setup.py install .
pytest

