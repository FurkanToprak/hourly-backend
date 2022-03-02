# hourly-backend
## Installation
```
pipenv install
```
## Starting Local Server
```
pipenv run start
```

## Adding Dependency
```
pipenv install <module>
```

## Formatting with Black and Linting
Add the following to settings.json:
```
{
  "[python]": {
    "editor.formatOnSave": true
  },
  "python.formatting.provider": "black",
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.testing.unittestEnabled": false,
  "python.testing.pytestEnabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.enabled": true,
  "python.linting.pylintArgs": ["--disable=C0114"]
}
```