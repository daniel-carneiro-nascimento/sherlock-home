from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ALLOWED_CONTEXT_FILES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "architecture.md",
]


def load_project_context() -> str:
    sections = []

    for path in ALLOWED_CONTEXT_FILES:
        if not path.exists():
            continue

        content = path.read_text(encoding="utf-8").strip()

        if not content:
            continue

        relative_path = path.relative_to(PROJECT_ROOT)

        sections.append(
            f"## File: {relative_path}\n\n{content}"
        )

    return "\n\n---\n\n".join(sections)
