# P4 Changelist Weblink Trigger

A small trigger/utility that scans Perforce changelist descriptions for external weblinks (for example Jira or Plan links) and attaches them to the corresponding depot assets in the DAM via the DAM API.

This repository contains the trigger implementation and helper code used to parse changelist descriptions, detect service-specific links, and post weblinks to the DAM.

## Quick start

[Descript Video Explanation](https://share.descript.com/view/umz1rrArmF7)

Requirements
- Python 3.9+
- See `requirements.txt` for Python package dependencies (p4python, requests, ...).

Environment variables
Set the following environment variables before running the tool:

- `DAM_SERVER_ADDRESS` — base URL of the DAM API (e.g. `https://dam.example.com`)
- `DAM_ACCOUNT_KEY` — account key used to authenticate to the DAM API
- `P4PORT` — Perforce server address (used by p4python)
- `P4USER` — Perforce user name

Example (PowerShell):

```powershell
$env:DAM_SERVER_ADDRESS = 'https://dam.example.com'
$env:DAM_ACCOUNT_KEY = 'c531XXXXXXXXXXXXXXXX'
$env:P4PORT = 'ssl:perforce.example.com:1666'
$env:P4USER = 'builduser'
```

Running the tool

From the repository root you can run the trigger script against a changelist id:

```powershell
python src/main.py 12345
```

The script will describe the changelist via p4python, extract weblinks from the changelist description and attempt to attach those weblinks to each depot file listed in the changelist.

Tests

This project uses pytest and the tests live under `tests/`.

Run the tests from the `p4_cl_link` directory:

```powershell
cd e:\repos\p4_cl_link
pytest -q
```

The test suite uses `unittest.mock` to avoid network calls and inserts the `src/` directory onto `sys.path` so the package modules can be imported directly during tests.

Development notes

- The tool is intentionally defensive: missing/invalid environment variables, non-JSON API responses, and network errors are handled by printing/logging errors rather than raising exceptions by default. You may prefer a fail-fast mode for CI or automation — this can be added.
- The code currently posts one weblink per depot file. If your DAM deduplicates weblinks or you want to avoid duplicate posts, consider adding a check for existing links before POSTing.
- The `main.py` helpers `gather_changelist_links` and `gather_cr_links` are covered by tests. `gather_cr_links` currently uses `re.match` (matches at start of description); if you want it to find numeric IDs anywhere in the description we can update the regex and tests.

Recent changes

- Added robust tests for `dam_api.write_weblink` (webhook config parsing, weblink type detection, and attach behavior).
- Added tests for `main.py` including a fake `P4` module to avoid real Perforce connections.

Contributing

Contributions, bug reports and PRs are welcome. When adding tests, prefer fast, deterministic unit tests that mock external services.

License

See `LICENSE` in the repository root for license information.
