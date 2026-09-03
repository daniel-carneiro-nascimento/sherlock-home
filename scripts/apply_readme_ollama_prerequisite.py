#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("README.md")

if not path.is_file():
    raise SystemExit("README.md not found in the current directory.")

text = path.read_text(encoding="utf-8")

heading = "## Current AI Runtime"

replacement = """## Current AI Runtime

The reference development implementation uses Ollama:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Approved local models are controlled by deterministic allowlisting.

The runtime is intentionally environment-agnostic. A compatible deployment may use Linux, WSL, containers, bare metal, or another private architecture that respects Sherlock Home's security boundaries.

### Ollama prerequisite

Sherlock Home expects an approved Ollama runtime to already be installed and running.

Ollama is **not installed or started automatically by Sherlock Home**. Before starting the application, install Ollama using the official instructions for your operating system and make sure the configured model is available locally.

For the reference configuration:

```bash
ollama pull qwen3:14b
ollama list
```

Configure Sherlock Home through `.env`:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:14b
```

Verify that the local Ollama runtime is reachable before starting Sherlock Home:

```bash
curl http://127.0.0.1:11434/api/tags
```

If Ollama is running on another approved local or private endpoint, update `OLLAMA_HOST` accordingly.

The expected startup flow is:

```text
Install Ollama
    ↓
Start Ollama
    ↓
Pull an approved model
    ↓
Configure OLLAMA_HOST and OLLAMA_MODEL
    ↓
Verify the Ollama endpoint
    ↓
Start Sherlock Home
```

> Protected household and financial data must only be sent to an approved local/private Ollama endpoint. Do not configure a public or third-party inference endpoint for protected Sherlock Home data.
"""

pattern = re.compile(
    r"(?ms)^## Current AI Runtime\s*\n.*?(?=^##\s|\Z)"
)

matches = list(pattern.finditer(text))

if len(matches) != 1:
    raise SystemExit(
        "Expected exactly one '## Current AI Runtime' section, "
        f"found {len(matches)}. README.md was not modified."
    )

updated = pattern.sub(
    replacement.rstrip() + "\n\n",
    text,
    count=1,
)

# Preservation checks against the current public-main README structure.
required_markers = [
    "docs/assets/sherlock-home_banner.png",
    "docs/assets/roadmap.svg",
    "## Authenticated API",
    "## Financial Data Pipeline",
    "## Current Development Frontier",
    "234 passed",
]

missing = [
    marker
    for marker in required_markers
    if marker not in updated
]

if missing:
    raise SystemExit(
        "README preservation validation failed. Missing: "
        + ", ".join(missing)
        + ". README.md was not modified."
    )

path.write_text(updated, encoding="utf-8")

print("README.md updated successfully.")
print("Added: Current AI Runtime -> Ollama prerequisite")
print("Preserved: banner, roadmap, API, financial pipeline, Phase 6 frontier, 234-test baseline")
