# homenet-check
With many network-connected devices in your home from various vendors, how do you know if their software is up to date to keep you secure?

## Goal / Vision

The vision for this project is pretty flexible, but the goal is to help ensure your home network is kept (reasonably) secure. Security is a broad topic and so this can come in various forms. The initial goal is to setup a system that can check different vendor sites to notify you if there's an update available for a device on your network.

## Potential future functionality

Ideas of how the project could evolve in the future (likely through integration with other tools):
- network enumeration with fingerprinting so you know what is connected (nmap?)
- Being able to apply updates for you in limited cases
- Best practices library to help educate (index of links to other sites)
- Run as a webservice or cron
- Make default runtime easy enough for a less-technical user to configure and run
- Scrape/login to devices to retrieve current version (for devices that could easily support it)

## Reqirements:
- Python 3.4+
- pip (`python3 -m ensurepip`)

## Getting started
1. Clone repository
1. `pip3 install -r --user requirements.txt` (or use virtualenv if you prefer)
1. Optional: Build configuration file to use a different database or logging configuration (see [Config]).
1. Initialize inventory database schema (default `inv.db` in project directory) by running `homenet-check.py initialize-db`
1. Populate devices using `homenet-check.py add-device`
1. Run `homenet-check.py query`

## Config
Default configuration that can be overridden via a JSON file and specified with the `-c/--config` parameter.
 
The default implementation uses SQLite, but any database dialects supported by [SQLAlchemy](https://docs.sqlalchemy.org/en/13/dialects/index.html)
should work with the corresponding driver installed and corresponding `dsn` specified.

Structure:
- `cache`: Cache directory for any vendor data files that may need to be downloaded. Defaults to system temp.
- `dsn`: Database connection string (Data Source Name). See [SQLAlchemy.create_engine](https://docs.sqlalchemy.org/en/13/core/engines.html#sqlalchemy.create_engine) for details
- `log.level`: Supported [log levels](https://docs.python.org/3/library/logging.html?highlight=logging#logging-levels) (normalized to upper case)
- `log.file`: Option to redirect log output to a file rather than stdout (useful for scheduled runs)

### Example
Default configuration:
```
{
    "cache": null,
    "dsn": "sqlite:///inv.db",
    "log": {
        "level": "info",
        "file": null
    }
}
```

### Upgrades
The database is versioned using [Alembic](https://alembic.sqlalchemy.org/en/latest/).
Running `initialize-db` after an update should handle performing any schema updates required.
