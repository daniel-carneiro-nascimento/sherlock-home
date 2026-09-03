from fastapi.security import APIKeyCookie


# "__Host-" cookies are browser-enforced to be Secure, Path=/ and have no Domain.
SESSION_COOKIE_NAME = "__Host-sherlock_session"
CSRF_COOKIE_NAME = "__Host-sherlock_csrf"
CSRF_HEADER_NAME = "X-CSRF-Token"

SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "strict"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "strict"

session_cookie_scheme = APIKeyCookie(
    name=SESSION_COOKIE_NAME,
    scheme_name="SherlockHomeSession",
    description=(
        "Secure server-side Sherlock Home household session."
    ),
    auto_error=False,
)
