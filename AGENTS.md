# Agent instructions

Guidance for AI agents working in this repository.

## Environment

- Use the project virtualenv: `./env/bin/python` (not system `python3`)
- Set up once:
  ```shell
  python3 -m venv env --system-site-packages
  source env/bin/activate
  pip install -r requirements.txt
  ```
- `env/` is gitignored. If imports like `pywikibot` fail, the venv is missing or incomplete.
- LibreOffice UNO (`python3-uno`) is required for the full test suite.

## Tests

- Preferred: `make test`
- Single module: `./env/bin/python -m unittest discover -s pywikitools/test -p test_correctbot.py`

## Lint and format

- Check: `make lint` (runs `ruff check` and `ruff format --check`)
- Format: `make format`

**Always run `make format` at the end of code changes.** CI runs `ruff format --check` and fails if files are not formatted.

## Running tools

- Entry scripts live at the repo root (e.g. `resourcesbot.py`, `correct_bot.py`)
- Run with: `./env/bin/python correct_bot.py PAGE LANG`
- Config: `config.ini` (copy from `config.example.ini`; not in git)
- Default log level is usually `warning`; use `-l info` for more output

## Conventions

- Match patterns from existing bots (`correctbot`, `resourcesbot`, `translateodt`)
- Keep changes focused; reuse existing helpers and abstractions
- Only create git commits when explicitly asked
