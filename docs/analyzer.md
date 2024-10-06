## Replay analyzer

Prerequisites:

- OS: Linux/Mac
- Python 3.11.3
- [poetry](https://python-poetry.org/docs/#installing-with-pipx)
- GNU make https://gnuwin32.sourceforge.net/packages/make.htm

Install:

```
poetry install
```

Commands:

```
REPLAY_ANALYZER_REPLAY_ID="id" \
  CONTINOUS_DEBUG_MODE="true" \
  make analyze
```

or run on docker container:

```
make analyzed
```
