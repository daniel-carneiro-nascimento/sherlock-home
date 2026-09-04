from pathlib import Path

path = Path("README.md")

if not path.is_file():
    raise SystemExit(
        "README.md not found in the current directory."
    )

text = path.read_text(encoding="utf-8")

old_arch = """For the complete architecture:
**[docs/architecture.md](docs/architecture.md)**"""

new_arch = """For the complete architecture:

- **[Backend Architecture](docs/architecture.md)** — application services, security boundaries, API, persistence, ingestion, deterministic tools, and local AI runtime
- **[Frontend Architecture](docs/frontend/architecture.md)** — web shell, navigation, view-model boundary, themes, accessibility, household goals, and chat UX"""

if old_arch not in text:
    raise SystemExit(
        "README architecture section did not match the current main. "
        "No changes were written."
    )

text = text.replace(
    old_arch,
    new_arch,
    1,
)

old_docs = """Detailed documentation lives under `docs/`:
- **[Roadmap](docs/ROADMAP.md)** — project phases, status, and next milestones
- **[Architecture](docs/architecture.md)** — security boundaries and system design
- **[API v1](docs/API_V1.md)** — authenticated API contract"""

new_docs = """Detailed documentation lives under `docs/`:
- **[Backend Roadmap](docs/ROADMAP.md)** — backend/application phases, status, and implementation milestones
- **[Frontend Roadmap](docs/frontend/ROADMAP.md)** — household-facing web phases and Holmes-Hat minimum UI
- **[Backend Architecture](docs/architecture.md)** — security boundaries and backend system design
- **[Frontend Architecture](docs/frontend/architecture.md)** — web navigation, UI data flow, accessibility, themes, goals, and chat UX
- **[API v1](docs/API_V1.md)** — authenticated API contract"""

if old_docs not in text:
    raise SystemExit(
        "README documentation index did not match the current main. "
        "No changes were written."
    )

text = text.replace(
    old_docs,
    new_docs,
    1,
)

required = [
    "docs/assets/sherlock-home_banner.png",
    "docs/assets/roadmap.svg",
    "docs/frontend/architecture.md",
    "docs/frontend/ROADMAP.md",
    "## Current AI Runtime",
    "## Authenticated API",
]

missing = [
    marker
    for marker in required
    if marker not in text
]

if missing:
    raise SystemExit(
        "README preservation validation failed. Missing: "
        + ", ".join(missing)
        + ". No changes were written."
    )

path.write_text(
    text,
    encoding="utf-8",
)

print("README.md documentation index updated successfully.")
