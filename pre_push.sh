#!/bin/sh
pipenv run black --check . &&
pipenv run pylint  *.py **/*.py &&
pipenv run pytest
