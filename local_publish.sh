#!/bin/bash

rm -rf dist/

export TRAVIS_JOB_ID=105 # Some random build number
pipenv run python setup.py sdist bdist_wheel
pipenv run python -m twine upload --repository testpypi dist/*

