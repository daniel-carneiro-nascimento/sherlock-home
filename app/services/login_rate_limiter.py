import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field


LOGIN_PRINCIPAL_MAX_FAILURES = 5
LOGIN_SOURCE_MAX_FAILURES = 20
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60
LOGIN_BACKOFF_BASE_SECONDS = 2
LOGIN_BACKOFF_MAX_SECONDS = 60


@dataclass
class _Bucket:
    failures: deque[float] = field(
        default_factory=deque
    )
    blocked_until: float = 0.0


class LoginRateLimiter:
    """
    In-process login rate limiter.

    Two independent buckets are maintained:
    - source address
    - source address + normalized username

    This avoids a global username lockout that an attacker could use to deny
    another household user access from a different client.

    The limiter is deliberately based on the ASGI client address and does not
    inspect X-Forwarded-For directly. Reverse-proxy trust must be configured at
    the ASGI server/proxy boundary rather than accepted from arbitrary clients.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._source_buckets: dict[
            str,
            _Bucket,
        ] = {}
        self._principal_buckets: dict[
            tuple[str, str],
            _Bucket,
        ] = {}

    @staticmethod
    def _normalize_source(
        source: str | None,
    ) -> str:
        value = (source or "").strip()
        return value or "unknown"

    @staticmethod
    def _normalize_username(
        username: str,
    ) -> str:
        return username.strip().lower()

    @staticmethod
    def _prune(
        bucket: _Bucket,
        now: float,
    ) -> None:
        cutoff = (
            now
            - LOGIN_RATE_LIMIT_WINDOW_SECONDS
        )

        while (
            bucket.failures
            and bucket.failures[0] <= cutoff
        ):
            bucket.failures.popleft()

        if (
            not bucket.failures
            and bucket.blocked_until <= now
        ):
            bucket.blocked_until = 0.0

    @staticmethod
    def _retry_after(
        bucket: _Bucket,
        now: float,
    ) -> int:
        if bucket.blocked_until <= now:
            return 0

        return max(
            1,
            math.ceil(
                bucket.blocked_until - now
            ),
        )

    @staticmethod
    def _apply_backoff(
        bucket: _Bucket,
        *,
        threshold: int,
        now: float,
    ) -> None:
        failure_count = len(
            bucket.failures
        )

        if failure_count < threshold:
            return

        exponent = (
            failure_count - threshold
        )

        backoff = min(
            LOGIN_BACKOFF_MAX_SECONDS,
            LOGIN_BACKOFF_BASE_SECONDS
            * (2 ** exponent),
        )

        bucket.blocked_until = max(
            bucket.blocked_until,
            now + backoff,
        )

    def check(
        self,
        *,
        source: str | None,
        username: str,
    ) -> int:
        source_key = self._normalize_source(
            source
        )
        principal_key = (
            source_key,
            self._normalize_username(
                username
            ),
        )

        now = time.monotonic()

        with self._lock:
            source_bucket = (
                self._source_buckets.get(
                    source_key
                )
            )
            principal_bucket = (
                self._principal_buckets.get(
                    principal_key
                )
            )

            retry_after = 0

            if source_bucket is not None:
                self._prune(
                    source_bucket,
                    now,
                )
                retry_after = max(
                    retry_after,
                    self._retry_after(
                        source_bucket,
                        now,
                    ),
                )

            if principal_bucket is not None:
                self._prune(
                    principal_bucket,
                    now,
                )
                retry_after = max(
                    retry_after,
                    self._retry_after(
                        principal_bucket,
                        now,
                    ),
                )

            return retry_after

    def record_failure(
        self,
        *,
        source: str | None,
        username: str,
    ) -> None:
        source_key = self._normalize_source(
            source
        )
        principal_key = (
            source_key,
            self._normalize_username(
                username
            ),
        )

        now = time.monotonic()

        with self._lock:
            source_bucket = (
                self._source_buckets.setdefault(
                    source_key,
                    _Bucket(),
                )
            )
            principal_bucket = (
                self._principal_buckets.setdefault(
                    principal_key,
                    _Bucket(),
                )
            )

            self._prune(
                source_bucket,
                now,
            )
            self._prune(
                principal_bucket,
                now,
            )

            source_bucket.failures.append(
                now
            )
            principal_bucket.failures.append(
                now
            )

            self._apply_backoff(
                source_bucket,
                threshold=(
                    LOGIN_SOURCE_MAX_FAILURES
                ),
                now=now,
            )

            self._apply_backoff(
                principal_bucket,
                threshold=(
                    LOGIN_PRINCIPAL_MAX_FAILURES
                ),
                now=now,
            )

    def record_success(
        self,
        *,
        source: str | None,
        username: str,
    ) -> None:
        """
        Clear only the source+username bucket.

        Source-wide failures remain so a successful credential does not erase
        evidence of username spraying from the same client.
        """
        source_key = self._normalize_source(
            source
        )
        principal_key = (
            source_key,
            self._normalize_username(
                username
            ),
        )

        with self._lock:
            self._principal_buckets.pop(
                principal_key,
                None,
            )

    def reset(self) -> None:
        with self._lock:
            self._source_buckets.clear()
            self._principal_buckets.clear()


login_rate_limiter = LoginRateLimiter()
