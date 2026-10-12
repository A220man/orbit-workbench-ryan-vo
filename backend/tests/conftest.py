"""Backend pytest fixtures and configuration."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure environment variables before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app

# Test in-memory engine
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def app_instance(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client(app_instance):
    return TestClient(app_instance)


@pytest.fixture
def analyst_token():
    return create_access_token(subject="test-analyst", roles=["analyst", "viewer"])


@pytest.fixture
def admin_token():
    return create_access_token(subject="test-admin", roles=["admin", "analyst", "viewer"])


@pytest.fixture
def viewer_token():
    return create_access_token(subject="test-viewer", roles=["viewer"])
