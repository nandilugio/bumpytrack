#!/usr/bin/env bash

pipenv run pip install --upgrade setuptools wheel
pipenv run python setup.py sdist bdist_wheel

