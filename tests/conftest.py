import pytest
from pkg_resources import resource_filename as pkgrf
from pathlib import Path


@pytest.fixture
def tempdir():
    return Path(pkgrf("tests.data", "."))
