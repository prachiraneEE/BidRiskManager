import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_client(client):
    response = client.post("/clients/", json={
        "name": "Test Corp",
        "industry": "Technology",
    })
    return response.json()


@pytest.fixture
def sample_bid(client, sample_client):
    response = client.post("/bids/", json={
        "client_id": sample_client["id"],
        "title": "Test Project",
        "value": 50000,
        "estimated_cost": 35000,
        "deadline": "2026-12-15",
    })
    return response.json()
