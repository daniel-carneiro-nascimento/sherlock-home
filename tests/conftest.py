import pytest

from sqlalchemy import URL, create_engine, delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

from app.models.category_rule import CategoryRuleModel
from app.models.merchant_alias import MerchantAliasModel
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


def clean_test_tables(
    session: Session,
) -> None:
    """
    Remove synthetic test data from all mutable tables.

    This function must only be called after
    validate_test_database() has succeeded.
    """
    session.execute(
        delete(MerchantAliasModel)
    )

    session.execute(
        delete(CategoryRuleModel)
    )

    session.execute(
        delete(Transaction)
    )

    session.commit()


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

    All mutable test tables are cleaned before and after
    every test.
    """
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestSessionLocal()

    try:
        clean_test_tables(
            session
        )

        yield session

    finally:
        session.rollback()

        clean_test_tables(
            session
        )

        session.close()
