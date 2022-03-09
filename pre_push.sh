#!/bin/sh
pipenv run black --check . &&
pipenv run pylint --fail-under=0 *.py **/*.py &&
pipenv run pytest
