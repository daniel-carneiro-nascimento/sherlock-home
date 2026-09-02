import pytest

from sqlalchemy import URL, create_engine, delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.models.transaction import Transaction


def build_test_database_url() -> URL:
    """
    Build the PostgreSQL URL used exclusively by pytest.

    This must never point to the application's normal database.
    """
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_test_db,
    )


def validate_test_database() -> None:
    """
    Fail closed if pytest appears to be configured against
    a non-test database.
    """
    test_db = settings.postgres_test_db
    production_db = settings.postgres_db

    if not test_db:
        raise RuntimeError(
            "POSTGRES_TEST_DB is not configured."
        )

    if test_db == production_db:
        raise RuntimeError(
            "Refusing to run database tests: "
            "POSTGRES_TEST_DB matches POSTGRES_DB."
        )

    if not test_db.endswith("_test"):
        raise RuntimeError(
            "Refusing to run database tests: "
            "POSTGRES_TEST_DB must end with '_test'."
        )


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """
    Create the SQLAlchemy engine used by database tests.

    The safety validation runs before any connection or
    destructive database operation occurs.
    """
    validate_test_database()

    engine = create_engine(
        build_test_database_url(),
        pool_pre_ping=True,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    yield engine

    engine.dispose()


@pytest.fixture()
def db_session(
    test_engine: Engine,
) -> Session:
    """
    Provide an isolated SQLAlchemy session for each test.

    The transaction table is cleaned before and after each
    test. Because test_engine can only point to a database
    ending in '_test', this cleanup cannot target the normal
    Sherlock Home database.
    """
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestSessionLocal()

    try:
        session.execute(
            delete(Transaction)
        )
        session.commit()

        yield session

    finally:
        session.rollback()

        session.execute(
            delete(Transaction)
        )
        session.commit()

        session.close()
