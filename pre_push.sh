#!/bin/sh
pipenv run black --check . &&
pipenv run pylint --fail-under=5 *.py **/*.py &&
pipenv run pytest
