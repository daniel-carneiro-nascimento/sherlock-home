from app.db.database import SessionLocal
from app.services.auth import cleanup_sessions


def main() -> None:
    with SessionLocal() as session:
        deleted = cleanup_sessions(session)

    print(
        f"Deleted {deleted} expired or old revoked session(s)."
    )


if __name__ == "__main__":
    main()
