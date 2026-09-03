# Private HTTPS Deployment

Sherlock Home is a local-first, single-household application.

A deployment may run on a workstation, home server, or private cloud
infrastructure, but the application is not intended to be directly reachable
from the public Internet.

## Security invariant

The supported network model is:

```text
household client
      |
      | encrypted private network / VPN
      v
HTTPS endpoint
      |
      v
Sherlock Home
      |
      +--> local PostgreSQL
      |
      +--> approved local model runtime
```

For a cloud deployment:

```text
Internet
   |
   +--> VPN entry point only
             |
             v
       private VPC/subnet
             |
             v
       HTTPS reverse proxy
             |
             v
       Sherlock Home
```

Do not expose the Sherlock Home application listener directly to the public
Internet.

## Development HTTPS

The repository includes the local HTTPS launcher:

```bash
python -m scripts.run_https
```

The development certificate is expected at:

```text
~/.config/sherlock-home/tls/dev-cert.pem
~/.config/sherlock-home/tls/dev-key.pem
```

The current development listener is:

```text
https://127.0.0.1:8443
```

A self-signed certificate is acceptable for controlled local development.
`curl -k` is a development-only convenience and is not a production trust
model.

## Private LAN deployment

For household devices on a private LAN, use a trusted TLS certificate.

Practical options include:

- a household/internal certificate authority installed on the participating
  clients;
- a reverse proxy terminating TLS with a certificate for a controlled DNS
  name;
- a publicly trusted certificate obtained through a DNS validation method
  while the actual service remains private.

A certificate does not require the application itself to have public ingress.

## Private cloud deployment

If Sherlock Home is hosted for reliability:

- place application and database resources in private subnets;
- expose access only through a user-controlled VPN;
- do not create a public application load balancer or public application IP;
- terminate TLS at a private reverse proxy or at the application;
- restrict PostgreSQL to the application network;
- restrict the local model runtime to the application network;
- keep security groups/firewall rules deny-by-default.

The intended sequence is:

```text
device
  -> VPN
  -> private HTTPS endpoint
  -> Sherlock Home
```

not:

```text
device
  -> public HTTPS endpoint
  -> Sherlock Home
```

## Reverse proxy

Caddy, nginx, Traefik, or another maintained reverse proxy may be used.

The proxy should:

- accept HTTPS only;
- use modern TLS;
- forward only to the private Sherlock Home listener;
- preserve request size limits;
- set conservative timeouts;
- avoid permissive cross-origin behavior;
- avoid adding public routes to PostgreSQL or the model runtime.

Sherlock Home does not inspect arbitrary `X-Forwarded-For` headers for login
rate limiting. Proxy-address trust must be configured at the ASGI/proxy
boundary so a client cannot spoof its source address.

## Cookie requirements

Sherlock Home uses:

```text
__Host-sherlock_session
__Host-sherlock_csrf
```

The `__Host-` prefix requires the browser-visible cookies to be:

- Secure;
- Path=/;
- without a Domain attribute.

Do not rewrite these cookies to a Domain-scoped form at the reverse proxy.

## Same-origin UI

The recommended browser deployment serves the future UI and `/api/v1` from
the same origin.

Example:

```text
https://sherlock.home/
https://sherlock.home/api/v1/...
```

This minimizes CORS complexity and preserves the intended cookie/CSRF model.

Do not use `Access-Control-Allow-Origin: *` for authenticated API access.

## Database

PostgreSQL should not be reachable from household client devices unless there
is an explicit administrative reason.

Normal operation should be:

```text
Sherlock Home -> PostgreSQL
```

Administrative access should use a controlled local shell or private
administrative path.

## Model runtime

Ollama or another approved local model runtime must remain private.

The API/model path must continue to satisfy Sherlock Home deterministic egress
policy. Financial data must not be sent to external LLM, embedding, telemetry,
analytics, advertising, profiling, or training services.

## Session maintenance

Expired sessions and old revoked sessions can be removed with:

```bash
python -m scripts.cleanup_sessions
```

This is safe to schedule periodically.

For example, a private host may invoke it daily from its native scheduler.
The scheduler choice is deployment-specific and should not become a required
Sherlock Home runtime dependency.

## Deployment validation

After deployment, validate at minimum:

```text
[ ] application endpoint is HTTPS
[ ] no direct public application ingress exists
[ ] VPN/private network access works
[ ] session cookie is Secure + HttpOnly + SameSite=Strict
[ ] CSRF cookie is Secure + SameSite=Strict
[ ] CSRF-protected mutation succeeds with the header
[ ] mutation fails without the CSRF header
[ ] logout revokes the server-side session
[ ] PostgreSQL is private
[ ] local model runtime is private
[ ] OpenAPI shows the SherlockHomeSession security scheme
```
