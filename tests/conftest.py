import pytest

from sqlalchemy import (
    URL,
    create_engine,
    delete,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from app.core.config import settings
from app.db.base import Base

from app.models.api_audit_event import ApiAuditEvent
from app.models.category_rule import CategoryRuleModel
from app.models.merchant_alias import MerchantAliasModel
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_session import UserSession


def build_test_database_url() -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_test_db,
    )


def validate_test_database() -> None:
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
    # Foreign-key-safe order.
    session.execute(delete(ApiAuditEvent))
    session.execute(delete(UserSession))
    session.execute(delete(User))
    session.execute(delete(MerchantAliasModel))
    session.execute(delete(CategoryRuleModel))
    session.execute(delete(Transaction))
    session.commit()


@pytest.fixture(scope="session")
def test_engine() -> Engine:
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
    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestSessionLocal()

    try:
        clean_test_tables(session)
        yield session

    finally:
        session.rollback()
        clean_test_tables(session)
        session.close()
