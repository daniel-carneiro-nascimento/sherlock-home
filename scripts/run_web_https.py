from pathlib import Path

import uvicorn


HOST = "127.0.0.1"
PORT = 8443

TLS_DIR = (
    Path.home()
    / ".config"
    / "sherlock-home"
    / "tls"
)
CERT_FILE = TLS_DIR / "dev-cert.pem"
KEY_FILE = TLS_DIR / "dev-key.pem"


def main() -> None:
    missing = [
        path
        for path in (
            CERT_FILE,
            KEY_FILE,
        )
        if not path.is_file()
    ]

    if missing:
        missing_text = "\n".join(
            f"  - {path}"
            for path in missing
        )

        raise SystemExit(
            "Local TLS files are missing:\n"
            f"{missing_text}\n\n"
            "Generate the existing Sherlock Home development certificate "
            "before starting the web UI."
        )

    uvicorn.run(
        "app.web_main:app",
        host=HOST,
        port=PORT,
        ssl_certfile=str(
            CERT_FILE
        ),
        ssl_keyfile=str(
            KEY_FILE
        ),
        log_level="info",
    )


if __name__ == "__main__":
    main()
