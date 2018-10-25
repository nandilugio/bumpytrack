#!/usr/bin/env bash

pipenv run pip install --upgrade twine
#pipenv run twine upload --repository-url https://test.pypi.org/legacy/ dist/*
pipenv run twine upload dist/*

