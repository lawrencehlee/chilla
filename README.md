# Chilla

More useful info tbd here.

## Setup

Chilla uses Python 3.9 and MongoDB.

Quickstart, assuming all necessary tools are installed:

1. `docker compose up -d` to start up Mongo
2. `pipenv install` to install Python dependencies
3. Make a copy of `.env.example` called `.env` in the root directory and fill out all values
4. `pipenv run python main.py` to run the bot

### MongoDB

By default, Chilla looks for a MongoDB instance at localhost:27017 with no authentication. You can override the Mongo
via environment variables (see "Configuration" below).

This project includes a very basic docker-compose.yml file to spin up a Mongo container if you don't want to download
and install Mongo. To use, simply run `docker compose up -d` to start a Mongo instance at `mongodb://localhost:27017` (
with no auth).

### Python

Assuming that you already have Python installed, you'll need [pip](https://pip.pypa.io/en/stable/installing/) and
[Pipenv](https://pipenv.pypa.io/en/latest/).

Pipenv is a dependency management tool that centralizes the dependencies required by a project. It does this by
combining virtual environments (virtualenv) and a Pipfile. The Pipfile contains the list of dependencies required by the
project, and running `pipenv install` will install all the specified dependencies into an automatically-managed
virtualenv.

### Configuration

Chilla uses environment variables for configuration in combination with `.env` files and python-dotenv. `.env` is
excluded from source control, and the template for all variables can be found in `.env.example`.

### Testing

Tests are mostly integration tests and require a standing MongoDB instance; they target a separate test database instead
of the regular application one.

To run tests, first install dev dependencies with `pipenv install --dev`. Then simply run `pipenv run pytest`.

## Conventions

### Quotes

* For _text_, use double quotes
* For _variables inside strings_, use single quotes
* For _keys/symbols_, use single quotes

## Misc

### Getting Real Data

To get real data from prod into your local db for manual testing:

```
# Open a shell into the mongo container
docker exec -it chilla_mongo_1 bash
# Dump prod data - fill in with your creds
mongodump mongodb+srv://<username>:<password>@<url>/Chilla
# Restore
mongorestore dump
```