# Nager.Date API Tests

## What this is

Automated API test suite for the public [Nager.Date](https://date.nager.at/api/v3) API - country info and public holidays. No API key required, chosen from the [public-apis](https://github.com/public-apis/public-apis) list.

7 test functions, parametrized into 21 test cases, covering happy paths, a negative case, and a non-functional check.

## Tech stack

- **Python 3.12**
- **Pytest** - test runner, uses `parametrize` to keep 21 cases down to 7 functions
- **requests** - HTTP client
- **jsonschema** - validates response shape/types against the schemas in `schemas/`
- **pytest-html** - generates the `report.html` output
- **pytest-xdist** - lets the suite run in parallel

## Setup & run

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest
```

This generates a self-contained `report.html`.

Run it in parallel across multiple workers:

```bash
python -m pytest -n auto   # one worker per CPU core
python -m pytest -n 4      # or pick a fixed number of workers
```

Run just the smoke-tagged tests (a quick sanity check, not the full suite):

```bash
python -m pytest -m smoke
```

Config overrides (all optional):

| Variable | Default | Purpose |
|---|---|---|
| `REST_BASE_URL` | `https://date.nager.at/api/v3` | Point at a different host or a mock |
| `REST_TIMEOUT` | `10` | Request timeout (s) |
| `REST_MAX_RESPONSE_MS` | `3000` | Latency threshold used by test 7 |
| `REST_HOLIDAY_YEAR` | current year | Year queried by test 3 |

## Framework structure

```
restcountries-api-tests/
├── conftest.py              # shared pytest fixture - one API client for the whole run
├── pytest.ini               # pytest config - html report, logging, markers
├── requirements.txt         # pinned dependencies
├── config/
│   └── settings.py          # base URL, timeout, thresholds - all env-overridable
├── clients/
│   └── api_client.py        # wraps requests - one method per endpoint, used by every test
├── schemas/
│   ├── country_schema.py    # expected shape of a /CountryInfo response
│   └── holiday_schema.py    # expected shape of a /PublicHolidays entry
└── tests/
    └── test_nager_date_api.py   # all 7 test functions live here
```

## Test cases

| # | Test | Endpoint | Cases | What's checked |
|---|---|---|---|---|
| 1 | Country lookup returns the right country | `/CountryInfo/{code}` | IN, DE, BR, JP | Status 200, and `commonName` / `countryCode` / `region` match the country requested |
| 2 | Country catalogue is correct | `/AvailableCountries` | DE, BR, JP, US, GB | Status 200, every code is a valid 2-letter code, code maps to the expected name |
| 3 | Holidays returned actually belong to that country | `/PublicHolidays/{year}/{code}` | DE, US, GB | Status 200, every holiday's `countryCode` and date match the request, plus a schema check on each one |
| 4 | Country response matches the expected schema | `/CountryInfo/{code}` | IN, DE, BR, JP | JSON schema validation (required fields, types) |
| 5 | Border countries resolve correctly | `/CountryInfo/DE` → each of its borders | Germany's 9 neighbours | Every border code also resolves via `/CountryInfo` and agrees on the country name |
| 6 | Unknown country returns 404 | `/CountryInfo/{code}` | `ZZ`, a garbage string, a numeric string | Status 404, with a proper RFC 9110 error body |
| 7 | Response time is reasonable | `/CountryInfo/IN` | - | Response comes back under 3000ms |

## Validation approach

Each test checks one or more of these:

- **Status code** - did the request succeed or fail the way it should (200 / 404)?
- **Values** - is it the *right* data, not just *any* data? E.g. does `commonName` actually match the country asked for.
- **Schema** - does the response still have the shape the tests expect? Catches breaking changes in the API.

A status-code check by itself isn't enough. This suite originally targeted REST Countries v3.1, and when that API was deprecated it kept returning HTTP 200 for every request while serving an error page instead of real data - a status-only test would have stayed green through that. Only the value and schema checks would have caught it, which is part of why both are used throughout.

## Maintenance

- **Add a new test case** - add an entry to the relevant list at the top of `tests/test_nager_date_api.py` (e.g. `COUNTRY_CASES`) instead of writing a new function.
- **Add a new endpoint** - add a method to `NagerDateClient` in `clients/api_client.py` that returns an `ApiResponse`; tests should never call `requests` directly.
- **Add a whole new API** - write a separate client class instead of extending `NagerDateClient` (keep one client per API). Once there's a second client, pull the shared bits - session, timing/logging, `ApiResponse` wrapping - into a `BaseApiClient` both inherit from, and only add `post`/`put`/etc. if a test actually needs them.
- **Add a schema for a new endpoint** - drop a new file in `schemas/`, following the existing two as a template.
- **Point the suite at a different host or a mock** - set `REST_BASE_URL`, nothing else needs to change.
