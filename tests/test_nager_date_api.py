# tests for the Nager.Date API - country info + public holidays
# 7 functions, parametrized into 21 cases total, see README for the full list
from __future__ import annotations

import re

import pytest
from jsonschema import validate

from config.settings import settings
from schemas.country_schema import COUNTRY_SCHEMA
from schemas.holiday_schema import HOLIDAY_SCHEMA

COUNTRY_CASES = [
    ("in", "India", "Asia"),
    ("de", "Germany", "Europe"),
    ("br", "Brazil", "Americas"),
    ("jp", "Japan", "Asia"),
]
COUNTRY_CODES = [code for code, _name, _region in COUNTRY_CASES]

# /AvailableCountries only lists countries with holiday data, so it's a
# smaller set than /CountryInfo - India isn't in here, for example.
CATALOGUE_ENTRIES = [
    ("DE", "Germany"),
    ("BR", "Brazil"),
    ("JP", "Japan"),
    ("US", "United States"),
    ("GB", "United Kingdom"),
]

HOLIDAY_CASES = [
    ("de", "New Year's Day"),
    ("us", "New Year's Day"),
    ("gb", "New Year's Day"),
]

ALPHA2 = re.compile(r"^[A-Z]{2}$")


# looking up a country should return that exact country, not just any 200
@pytest.mark.smoke
@pytest.mark.parametrize("code, expected_name, expected_region", COUNTRY_CASES)
def test_country_info_returns_correct_country(client, code, expected_name, expected_region):
    resp = client.country_info(code)

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.is_json_object(), f"Response body should be a JSON object, got {resp.json!r}"

    assert resp.json["commonName"] == expected_name, (
        f"Expected commonName={expected_name} for '{code}', "
        f"got {resp.json.get('commonName')!r}"
    )
    assert resp.json["countryCode"] == code.upper(), (
        f"Asked for '{code}', got countryCode={resp.json.get('countryCode')!r}"
    )
    assert resp.json["region"] == expected_region


# the catalogue every other endpoint keys off of, so it needs to be right
@pytest.mark.parametrize("code, expected_name", CATALOGUE_ENTRIES)
def test_available_countries_lists_country(client, code, expected_name):
    resp = client.available_countries()

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.is_json_list() and len(resp.json) > 0, "Catalogue should be a non-empty array"

    malformed = [e["countryCode"] for e in resp.json if not ALPHA2.match(e["countryCode"])]
    assert not malformed, f"Malformed country codes in catalogue: {malformed}"

    by_code = {e["countryCode"]: e["name"] for e in resp.json}
    assert code in by_code, f"{code} missing from catalogue of {len(resp.json)} countries"
    assert by_code[code] == expected_name, (
        f"Expected {code} -> {expected_name!r}, got {by_code[code]!r}"
    )


# checks every holiday in the list, not just the first one
@pytest.mark.parametrize("code, expected_holiday", HOLIDAY_CASES)
def test_all_holidays_belong_to_requested_country(client, code, expected_holiday):
    resp = client.public_holidays(code)

    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    # a country with no holiday data returns 204 with an empty body, which
    # would pass a status-only check
    assert resp.is_json_list() and len(resp.json) > 0, (
        f"No holidays returned for '{code}' in {settings.HOLIDAY_YEAR} "
        f"(status {resp.status_code}, body {resp.json!r})"
    )

    for holiday in resp.json:
        validate(instance=holiday, schema=HOLIDAY_SCHEMA)

        assert holiday["countryCode"] == code.upper(), (
            f"{holiday['name']!r} came back for '{code}' but is tagged "
            f"{holiday['countryCode']}"
        )
        assert holiday["date"].startswith(f"{settings.HOLIDAY_YEAR}-"), (
            f"{holiday['name']!r} is dated {holiday['date']}, outside the "
            f"requested year {settings.HOLIDAY_YEAR}"
        )

    names = [h["name"] for h in resp.json]
    assert expected_holiday in names, (
        f"Expected {expected_holiday!r} among {code.upper()} holidays, got {names}"
    )


# makes sure the response shape hasn't silently changed
@pytest.mark.parametrize("code", COUNTRY_CODES)
def test_country_info_matches_schema(client, code):
    resp = client.country_info(code)
    assert resp.status_code == 200
    validate(instance=resp.json, schema=COUNTRY_SCHEMA)
    assert resp.json["officialName"].strip(), "officialName must not be blank"


# cross-checks Germany's border list against /CountryInfo for each neighbour
def test_border_codes_resolve_to_the_same_country(client):
    resp = client.country_info("de")
    assert resp.status_code == 200
    borders = resp.json["borders"]
    assert borders, "Germany should report land borders"

    for border in borders:
        code = border["countryCode"]
        looked_up = client.country_info(code)

        assert looked_up.status_code == 200, (
            f"Border code {code} did not resolve: got {looked_up.status_code}"
        )
        assert looked_up.json["commonName"] == border["commonName"], (
            f"{code}: borders list says {border['commonName']!r}, "
            f"CountryInfo says {looked_up.json['commonName']!r}"
        )


# negative case - unknown country codes should fail gracefully
@pytest.mark.parametrize("bad_code", ["ZZ", "thiscountrydoesnotexist", "123"])
def test_unknown_country_returns_404(client, bad_code):
    resp = client.country_info(bad_code)

    assert resp.status_code == 404, (
        f"Expected 404 for unknown country '{bad_code}', got {resp.status_code}"
    )
    assert not resp.is_json_list()
    assert resp.is_json_object(), f"Expected a problem-detail object, got {resp.json!r}"
    assert resp.json.get("status") == 404, (
        f"Expected an RFC 9110 problem body carrying status 404, got {resp.json!r}"
    )


# basic non-functional check - flags a public host that's gotten slow
def test_response_time_within_threshold(client):
    resp = client.country_info("in")
    assert resp.status_code == 200
    assert resp.elapsed_ms < settings.MAX_RESPONSE_MS, (
        f"Response took {resp.elapsed_ms:.0f}ms "
        f"(threshold {settings.MAX_RESPONSE_MS}ms)"
    )
