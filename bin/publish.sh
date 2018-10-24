#!/usr/bin/env bash

pipenv run pip install --upgrade setuptools wheel twine
pipenv run python setup.py sdist bdist_wheel
#pipenv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
pipenv run twine upload dist/*

