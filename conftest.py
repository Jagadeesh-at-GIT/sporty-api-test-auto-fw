# pytest fixtures shared across the whole suite
from __future__ import annotations

import pytest

from clients.api_client import NagerDateClient


@pytest.fixture(scope="session")
def client() -> NagerDateClient:
    # one client for the whole run, instead of a new one per test
    return NagerDateClient()
