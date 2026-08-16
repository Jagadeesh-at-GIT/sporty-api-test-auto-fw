# config for the suite - everything here can be overridden with an env var, see README
from __future__ import annotations

import os
from datetime import date


class Settings:
    BASE_URL: str = os.getenv("REST_BASE_URL", "https://date.nager.at/api/v3")
    TIMEOUT: int = int(os.getenv("REST_TIMEOUT", "10"))
    MAX_RESPONSE_MS: int = int(os.getenv("REST_MAX_RESPONSE_MS", "3000"))  # used by the latency test
    HOLIDAY_YEAR: int = int(os.getenv("REST_HOLIDAY_YEAR", str(date.today().year)))
    # defaults to the current year if REST_HOLIDAY_YEAR isn't set

settings = Settings()
