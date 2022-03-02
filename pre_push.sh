#!/bin/sh
pipenv run black --check . &&
pipenv run pylint --fail-under=10 *.py **/*.py &&
pipenv run pytest
