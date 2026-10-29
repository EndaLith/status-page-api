import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base,get_db
from app.main import app

load_dotenv()
TEST_DATABASE_URL=os.getenv("TEST_DATABASE_URL")

assert TEST_DATABASE_URL and TEST_DATABASE_URL.endswith("statuspage_test")

engine=create_engine(TEST_DATABASE_URL)
TestingSessionLocal=sessionmaker(bind=engine)


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine) 
    Base.metadata.create_all(engine)

    def override_get_db():
        db=TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db]=override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)            