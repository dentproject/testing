import pytest


@pytest.fixture
def test_fixture(request):
    print("Test fixture")
