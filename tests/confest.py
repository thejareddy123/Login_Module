import pytest
from app import app, mysql


@pytest.fixture
def test_client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def db_mysql():
    with app.app_context():
        yield mysql


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client