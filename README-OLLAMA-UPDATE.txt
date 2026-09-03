Sherlock Home README — Ollama prerequisite update

This update is based on the current public `main` README.

It modifies only the `## Current AI Runtime` section and preserves the rest of README.md.

Recommended use from the repository root:

    unzip -o sherlock-home-readme-ollama-prerequisite.zip -d .
    python scripts/apply_readme_ollama_prerequisite.py

Then review:

    git diff -- README.md
    git diff --check

Alternative:

    git apply README-ollama-prerequisite.patch

The updater validates that the current README still contains:
- the Sherlock Home banner
- the visual roadmap
- Authenticated API section
- Financial Data Pipeline section
- Current Development Frontier
- the 234-test baseline

If those markers are missing, it refuses to write the file.
