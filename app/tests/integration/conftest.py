import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from httpx import Client
from app.it_practice import DATABASE_URL, Base


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture
def db_session(engine):
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    yield session
    session.close()

@pytest.fixture
def client():
    with Client(base_url="http://127.0.0.1:8000", headers={"Content-Type": "application/json"}) as test_client:
        yield test_client

