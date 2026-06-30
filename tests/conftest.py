import json
from importlib import resources

import pytest

from hypersignal.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="test")


@pytest.fixture
def load_fixture():
    def _load(name: str):
        with resources.files("hypersignal.fixtures").joinpath(name).open("r", encoding="utf-8") as fh:
            return json.load(fh)

    return _load
