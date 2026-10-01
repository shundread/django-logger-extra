<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Logger extras for simplified structured logging.](#logger-extras-for-simplified-structured-logging)
  - [Adding django-logger-extra your Django project](#adding-django-logger-extra-your-django-project)
    - [Adding django-resilient-logger Django apps](#adding-django-resilient-logger-django-apps)
    - [Configuring logger formatter in settings.py:](#configuring-logger-formatter-in-settingspy)
    - [Configuring middleware in settings.py:](#configuring-middleware-in-settingspy)
  - [django-auditlog extra context.](#django-auditlog-extra-context)
  - [Logger context usage](#logger-context-usage)
  - [Gunicorn Logging Formatters](#gunicorn-logging-formatters)
- [Development](#development)
  - [Running tests](#running-tests)
  - [Code format](#code-format)
  - [Git blame ignore refs](#git-blame-ignore-refs)
  - [Commit message format](#commit-message-format)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Logger extras for simplified structured logging.

`django-logger-extra` is a collection of logger extras that makes structured logging setup easier.

## Adding django-logger-extra your Django project

Add `django-logger-extra` in your project's dependencies.

### Adding django-resilient-logger Django apps

To install this logger, add `INSTALLED_APPS` in settings.py:

```python
INSTALLED_APPS = (
    "logger_extra",
    ...
)
```

### Configuring logger formatter in settings.py:
To make use of the JSON formatter it must be configured in setting's LOGGING section.
Filter is optional and brings `logger_context()` contexts available as logger extras.

```python
LOGGING = {
    "filters": {
        "context": {
            "()": "logger_extra.filter.LoggerContextFilter",
        }
        ...
    },
    "formatters": {
        "json": {
            "()": "logger_extra.formatter.JSONFormatter",
        }
        ...
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["context"]
        },
        ...
    },
    ...
}
```

### Configuring middleware in settings.py:
```python
MIDDLEWARE = [
    "logger_extra.middleware.XRequestIdMiddleware",
    ...
]
```

## django-auditlog extra context.
This library can also augment django-auditlog's additional_data fields with active context.
To enable this, optional package `django-auditlog` must be installed and it must be explicitly enabled
in `settings.py` file.
```python
LOGGER_EXTRA_AUGMENT_DJANGO_AUDITLOG = True
```

In order to mask actor email on your `django-auditlog` log entries, you can set the following option
in your `settings.py` file.
```python
LOGGER_EXTRA_MASK_ACTOR_EMAIL = True
```

## Logger context usage
Active context can be appended with `logger_context` function. It will return current
context as resource. The current context can also be read using function `get_logger_context`.
```python
import logging
from django.http import HttpRequest, JsonResponse

from logger_extra.logger_context import logger_context

logger = logging.getLogger("audit")

def bar():
  with logger_context({ "who": "World" }) as ctx:
    logger.info(f"{ctx['greet']} {ctx['who']}")

def foo():
  with logger_context({ "greet": "Hello" }):
    bar()
    return JsonResponse({})
```

Will result log entry that looks like:
`{"message": "Hello World", "level": "INFO", "time": "2025-04-14T11:08:22.962222+00:00", "context": {"request_id": "95e787b5-4ce8-46ef-bb6e-31651fc8774b", "greet": "Hello", "who": "World"}}`

## django-resilient-logger resolve_actor patch
This library also provides a utility actor resolver function for `django-resilient-logger` to guarantee
that an actor's email (masked) and UUID is available in the resilient logger entries.

In order to activate the feature, add the following setting to your `django-resilient-logger`
(version 3.1.0 or higher) configuration:
```python
RESILIENT_LOGGER = {
    # ...
    "actor_resolver": "logger_extra.extras.resilient_logger.resolve_actor_with_masked_email",
}
```

## Gunicorn Logging Formatters

This package includes two helpers to format Gunicorn access and error logs as
structured JSON: `JsonFormatter` and `JsonErrorFormatter` (available at
`logger_extra.extras.gunicorn`).

Use the following `logconfig_dict` in your Gunicorn configuration (default:
`gunicorn.conf.py`) to enable JSON output and include the logger context
filter so request context is available in logs:

```python
from logger_extra.extras.gunicorn import JsonErrorFormatter, JsonFormatter

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "context": {
            "()": "logger_extra.filter.LoggerContextFilter",
        }
    },
    "formatters": {
        "json": {
            "()": JsonFormatter,
        },
        "json_error": {
            "()": JsonErrorFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["context"],
            "stream": "ext://sys.stdout",
        },
        "error_console": {
            "class": "logging.StreamHandler",
            "formatter": "json_error",
            "filters": ["context"],
            "stream": "ext://sys.stderr",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": False,
        },
    },
}

```

Notes:

- **Access logs**: `JsonFormatter` expects Gunicorn access log fields
  and will produce a JSON object containing time (in UTC),
  request/response metadata, and any active logger context.
- **Error logs**: `JsonErrorFormatter` formats error messages with an
  ISO 8601 UTC timestamp and the log message. Also note that despite the
  name, all records logged in `gunicorn.error` are not errors, e.g.
  gunicorn's start-up messages are logged through this.
- **Context filter**: Adding `logger_extra.filter.LoggerContextFilter`
  to the `filters` and attaching it to handlers ensures context created
  by `logger_extra.logger_context` is included under `request_id` and
  other context keys.
- **Gunicorn usage**: If you're using a non-default name for your
  config file, point Gunicorn to your config file when starting,
  e.g. `gunicorn -c my_gunicorn_conf.py myapp.wsgi:application`.


# Development

Virtual Python environment can be used. For example:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install package requirements:

```bash
pip install -e .
```

Install development requirements:

```bash
pip install -r requirements-test.txt
```

## Running tests

```bash
pytest
```

## Code format

This project uses [Ruff](https://docs.astral.sh/ruff/) for code formatting and quality checking.

Basic `ruff` commands:

* lint: `ruff check`
* apply safe lint fixes: `ruff check --fix`
* check formatting: `ruff format --check`
* format: `ruff format`

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.


## Git blame ignore refs

Project includes a `.git-blame-ignore-revs` file for ignoring certain commits from `git blame`.
This can be useful for ignoring e.g. formatting commits, so that it is more clear from `git blame`
where the actual code change came from. Configure your git to use it for this project with the
following command:

```shell
git config blame.ignoreRevsFile .git-blame-ignore-revs
```


## Commit message format

New commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/)
specification, and line length is limited to 72 characters.

When [`pre-commit`](https://pre-commit.com/) is in use, [`commitlint`](https://github.com/conventional-changelog/commitlint)
checks new commit messages for the correct format.
