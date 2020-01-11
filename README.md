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

## Reqirements:
- Python 3.4+
- pip (`python -m ensurepip`)
- SQLite 3 for initial DB editing (until functionality is built for managing db)

## Setup
(Proposed)
1. Clone repository
2. `pip install -r requiements.txt`
3. Initialize inventory database (default `inv.db` in project directory) by running `homenet-check.py initialize-db [--db path/to/file]`
3. Populate sqlite3 database `inv.db` with current inventory
4. Run `homenet-check.py query` 
