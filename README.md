# TV Show Tracker

**Category:** Databases

## Problem

Got a favorite show you don't want to miss? Don't have a PVR or want to be able to find the show to then PVR it later? Make an application which can search various online TV Guide sites, locate the shows/times/channels and add them to a database application. The database/website then can send you email reminders that a show is about to start and which channel it will be on.

## Solution

Uses the TVMaze public API (no key) to search shows and list episodes, stores followed shows in SQLite, and computes the next episode by airdate. The demo runs both API endpoints from a local stub so the whole flow is testable offline; `--next` is the hook a reminder job would call.

## How to run

Requires Python 3.8+ and no third-party packages.

```bash
python3 main.py --search "Game of Thrones"
python3 main.py --follow 82 --name "Game of Thrones"
python3 main.py --next
python3 main.py --demo
```

## Example

```text
search: [{'id': 82, 'name': 'Game of Thrones', 'premiered': '2011-04-17'}]
following: [(82, 'Game of Thrones')]
next episode: {'season': 9, 'number': 1, 'name': 'A Dream of Spring', 'airdate': '2027-04-01'}
```

## Attribution

The problem statement is from [karan/Projects](https://github.com/karan/Projects), a list of practical projects that anyone can solve in any programming language (MIT License, Copyright (c) 2013 Karan Goel). The Python solution in this repository was implemented by [bspreston-esq](https://github.com/bspreston-esq).

This repository is part of the [Projects-Python-All](https://github.com/bspreston-esq/Projects-Python-All) collection.
