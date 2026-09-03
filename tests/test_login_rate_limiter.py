from app.services.login_rate_limiter import (
    LOGIN_PRINCIPAL_MAX_FAILURES,
    LoginRateLimiter,
)


def test_principal_bucket_enters_backoff():
    limiter = LoginRateLimiter()

    for _ in range(
        LOGIN_PRINCIPAL_MAX_FAILURES
    ):
        assert limiter.check(
            source="127.0.0.1",
            username="admin",
        ) == 0

        limiter.record_failure(
            source="127.0.0.1",
            username="admin",
        )

    assert limiter.check(
        source="127.0.0.1",
        username="admin",
    ) >= 1


def test_rate_limit_is_not_global_by_username():
    limiter = LoginRateLimiter()

    for _ in range(
        LOGIN_PRINCIPAL_MAX_FAILURES
    ):
        limiter.record_failure(
            source="10.0.0.10",
            username="admin",
        )

    assert limiter.check(
        source="10.0.0.10",
        username="admin",
    ) >= 1

    assert limiter.check(
        source="10.0.0.11",
        username="admin",
    ) == 0


def test_success_clears_principal_bucket():
    limiter = LoginRateLimiter()

    for _ in range(2):
        limiter.record_failure(
            source="127.0.0.1",
            username="admin",
        )

    limiter.record_success(
        source="127.0.0.1",
        username="admin",
    )

    assert limiter.check(
        source="127.0.0.1",
        username="admin",
    ) == 0
