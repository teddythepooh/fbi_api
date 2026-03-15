import pytest
from fbi_api import FBI

@pytest.fixture(scope = "session")
def fbi_client():
    return FBI()
