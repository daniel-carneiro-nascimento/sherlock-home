# Sherlock Home API v1 Contract

Sherlock Home exposes a versioned authenticated API under:

```text
/api/v1
```

The API is intended for a single household. It is not a public SaaS API and
does not provide public registration.

## Transport

HTTPS is required.

Authentication cookies are `Secure`, so plain HTTP is not a supported
authenticated transport.

## Authentication

Authentication uses a server-side session referenced by a secure cookie:

```text
__Host-sherlock_session
```

Properties:

- Secure
- HttpOnly
- SameSite=Strict
- Path=/
- no Domain attribute
- absolute TTL: 8 hours
- idle timeout: 30 minutes

The raw session token is not stored in PostgreSQL. Sherlock Home stores a
SHA-256 hash of the token.

## CSRF

State-changing authenticated requests require the CSRF header:

```text
X-CSRF-Token
```

The browser obtains the token from:

```text
__Host-sherlock_csrf
```

The CSRF cookie is intentionally readable by the browser so the UI can echo
the value in the request header. Its server-side representation is stored as a
hash bound to the session.

## Login throttling

`POST /api/v1/auth/login` applies source-aware rate limiting and exponential
backoff.

Two buckets are used:

1. client source address;
2. client source address + normalized username.

This avoids relying on a global username lockout, which could otherwise be
used to deny another household user access from a different client.

When throttled, login returns:

```text
429 Too Many Requests
Retry-After: <seconds>
```

The application does not trust `X-Forwarded-For` directly. Reverse-proxy trust
must be established at the ASGI server/proxy boundary.

## Authentication endpoints

### POST `/api/v1/auth/login`

Request:

```json
{
  "username": "admin",
  "password": "..."
}
```

Success:

```text
200 OK
```

Returns the authenticated user and session expiration timestamp and sets the
session and CSRF cookies.

Expected authentication errors:

```text
401 Invalid credentials
429 Too many login attempts
```

Unknown users, disabled users, and incorrect passwords use generic credential
failure responses.

### GET `/api/v1/auth/me`

Requires a valid session.

Returns the current authenticated household user.

### POST `/api/v1/auth/logout`

Requires:

- valid session;
- valid CSRF header.

Revokes the current server-side session.

### POST `/api/v1/auth/logout-all`

Requires:

- valid session;
- valid CSRF header.

Revokes all active sessions belonging to the current user.

### POST `/api/v1/auth/change-password`

Requires:

- valid session;
- valid CSRF header;
- current password.

A successful password change revokes all active sessions for the user,
including the session that performed the change.

## Configuration endpoints

All configuration endpoints require an authenticated `admin` user.

### Category rules

```text
GET    /api/v1/config/category-rules
POST   /api/v1/config/category-rules
GET    /api/v1/config/category-rules/{rule_id}
PUT    /api/v1/config/category-rules/{rule_id}
PATCH  /api/v1/config/category-rules/{rule_id}/enabled
DELETE /api/v1/config/category-rules/{rule_id}
```

Public identifiers use the opaque prefix:

```text
cr_
```

Internal integer database IDs are not API resource identifiers.

### Merchant aliases

```text
GET    /api/v1/config/merchant-aliases
POST   /api/v1/config/merchant-aliases
GET    /api/v1/config/merchant-aliases/{alias_id}
PUT    /api/v1/config/merchant-aliases/{alias_id}
PATCH  /api/v1/config/merchant-aliases/{alias_id}/enabled
DELETE /api/v1/config/merchant-aliases/{alias_id}
```

Public identifiers use the opaque prefix:

```text
ma_
```

Internal integer database IDs are not API resource identifiers.

## Configuration audit

Protected configuration mutations are written to the persistent
`api_audit_events` table in the same database transaction as the mutation.

Audit public identifiers use:

```text
ae_
```

The audit record intentionally does not copy the configuration payload,
regular-expression pattern, financial data, credentials, session token, or
CSRF token.

## Common status codes

```text
200 request completed
201 resource created
204 request completed with no response body
401 authentication required or invalid credentials
403 authenticated but unauthorized, or CSRF rejected
404 resource not found
409 deterministic configuration conflict
422 invalid request payload
429 login rate limit/backoff active
```

## Browser/UI integration

The intended UI deployment is same-origin with the API.

Do not enable permissive CORS as a convenience workaround. If a future UI
must use a distinct origin, allowed origins should be explicit and narrowly
configured.

The UI must:

1. use HTTPS;
2. allow the browser to send the session cookie;
3. read `__Host-sherlock_csrf`;
4. send it as `X-CSRF-Token` on state-changing requests;
5. treat `401` as session loss/expiration;
6. treat `403` separately from `401`;
7. respect `Retry-After` after a `429` login response;
8. use opaque resource IDs exactly as returned by the API.

## OpenAPI

FastAPI exposes the generated OpenAPI schema. It contains the
`SherlockHomeSession` cookie security scheme and the versioned `/api/v1`
operations.

The OpenAPI schema is the machine-readable contract. This document defines
the deployment and client-side security expectations that are not fully
expressible in OpenAPI.
