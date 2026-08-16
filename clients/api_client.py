# small wrapper around requests - keeps sessions/urls out of the tests
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ApiResponse:
    status_code: int
    elapsed_ms: float
    json: Any
    raw: requests.Response

    def is_json_list(self) -> bool:
        # true for endpoints that return an array, e.g. /AvailableCountries
        return isinstance(self.json, list)

    def is_json_object(self) -> bool:
        # true for endpoints that return a single object, e.g. /CountryInfo
        return isinstance(self.json, dict)


class NagerDateClient:
    def __init__(self, base_url: str = None, timeout: int = None) -> None:
        # one session reused for every call instead of opening a new connection each time
        self.base_url = (base_url or settings.BASE_URL).rstrip("/")
        self.timeout = timeout or settings.TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict | None = None) -> ApiResponse:
        # does the actual call, logs it, and wraps the result for the tests
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = self.session.get(url, params=params, timeout=self.timeout)
        try:
            body = resp.json()
        except ValueError:
            body = None
        logger.info(
            "GET %s -> %s (%.0fms)\n%s",
            url,
            resp.status_code,
            resp.elapsed.total_seconds() * 1000,
            json.dumps(body, indent=2) if body is not None else "(empty body)",
        )
        return ApiResponse(
            status_code=resp.status_code,
            elapsed_ms=resp.elapsed.total_seconds() * 1000,
            json=body,
            raw=resp,
        )

    def country_info(self, code: str) -> ApiResponse:
        # details for one country, e.g. "DE" (case doesn't matter)
        return self._get(f"CountryInfo/{code}")

    def available_countries(self) -> ApiResponse:
        # countries that have holiday data - smaller list than CountryInfo covers
        return self._get("AvailableCountries")

    def public_holidays(self, code: str, year: int | None = None) -> ApiResponse:
        # holidays for a country in a given year, defaults to settings.HOLIDAY_YEAR
        return self._get(f"PublicHolidays/{year or settings.HOLIDAY_YEAR}/{code}")
