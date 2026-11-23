from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database import Base, engine, get_session
from app.main import app


@pytest.fixture
def test_engine():
    schema = f"test_{uuid4().hex}"
    with engine.begin() as connection:
        connection.execute(CreateSchema(schema))

    isolated_engine = engine.execution_options(schema_translate_map={None: schema})
    try:
        Base.metadata.create_all(isolated_engine)
        yield isolated_engine
    finally:
        with engine.begin() as connection:
            connection.execute(DropSchema(schema, cascade=True))


@pytest.fixture
def client(test_engine):

    def test_session():
        with Session(test_engine, expire_on_commit=False) as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session)
