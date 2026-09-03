from getpass import getpass

from app.db.database import SessionLocal
from app.services.auth import (
    create_initial_admin,
)


def main() -> None:
    print(
        "Sherlock Home local admin bootstrap"
    )

    username = input(
        "Admin username: "
    ).strip()

    password = getpass(
        "Admin password: "
    )
    password_confirm = getpass(
        "Confirm password: "
    )

    if password != password_confirm:
        raise SystemExit(
            "Passwords do not match."
        )

    with SessionLocal() as session:
        try:
            admin = create_initial_admin(
                session,
                username=username,
                password=password,
            )
        except (
            RuntimeError,
            ValueError,
        ) as exc:
            raise SystemExit(
                str(exc)
            ) from exc

    print(
        f"Admin created: {admin.username}"
    )


if __name__ == "__main__":
    main()
