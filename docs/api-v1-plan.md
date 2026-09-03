# API v1 Development Plan

## Status

In development after the v0.5.0 financial-ingestion milestone.

## Product boundary

Sherlock Home is a single-household system.

The API is not designed for public signup, multi-tenancy, shared SaaS hosting, organization billing, or public account discovery.

## Network boundary

Normal deployment:

```text
household LAN
    ↓
HTTPS
    ↓
Sherlock Home
```

Permitted public-cloud deployment:

```text
authorized device
    ↓
user-controlled VPN
    ↓
private cloud network
    ↓
HTTPS
    ↓
Sherlock Home
```

Direct public Internet exposure is outside the intended architecture.

## Authentication plan

- [ ] local administrator bootstrap
- [ ] PostgreSQL user model
- [ ] Argon2id password hashing
- [ ] PostgreSQL server-side session model
- [ ] cryptographically secure session tokens
- [ ] hashed server-side session-token storage
- [ ] Secure cookie
- [ ] HttpOnly cookie
- [ ] SameSite=Strict
- [ ] login endpoint
- [ ] logout endpoint
- [ ] `/me` endpoint
- [ ] session revocation
- [ ] login rate limiting/backoff

## Authorization plan

- [ ] authentication dependency
- [ ] authorization dependency
- [ ] explicit admin capability
- [ ] deterministic 401 handling
- [ ] deterministic 403 handling
- [ ] protected configuration changes
- [ ] audit events for protected actions

## API structure

Planned base:

```text
/api/v1
```

Planned initial routes:

```text
/api/v1/auth/login
/api/v1/auth/logout
/api/v1/auth/me

/api/v1/config/category-rules
/api/v1/config/merchant-aliases
```

There will be no public `/register` endpoint.

## OpenAPI

- [ ] security scheme represented in generated OpenAPI
- [ ] protected routes marked as authenticated
- [ ] request/response schemas defined with Pydantic
- [ ] deterministic error schemas
- [ ] integration tests against the generated contract

## TLS

HTTPS is part of the intended deployment from the beginning.

Development may run locally on loopback, but the application should be TLS-ready behind a reverse proxy for household deployment.

## LLM boundary

The LLM must not participate in password validation, session validation, authentication, authorization, CSRF validation, rate limiting, security policy, or database credential handling.

## Privacy boundary

Household data must not be sent to external parties for model training, fine-tuning, analytics, advertising, profiling, dataset construction, or unrelated product improvement.

This includes raw and derived household financial information.

## Completion criteria

The API security foundation is complete only when the roadmap items above are implemented and the deterministic test suite covers authentication and authorization failure modes.
