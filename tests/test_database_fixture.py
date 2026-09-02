from sqlalchemy import text
from sqlalchemy.orm import Session


def test_database_fixture_uses_test_database(
    db_session: Session,
):
    database_name = db_session.scalar(
        text("SELECT current_database()")
    )

    assert database_name is not None
    assert database_name.endswith("_test")
    assert database_name == "sherlock_home_test"
