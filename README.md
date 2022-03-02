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

## Formatting with Black
Add the following to settings.json:
```
{
  "[python]": {
    "editor.formatOnSave": true
  },
  "python.formatting.provider": "black"
}
```