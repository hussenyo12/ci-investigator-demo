"""Validate a non-sensitive demo setting without contacting any service."""

import os


def main() -> None:
    endpoint = os.environ.get("DEMO_SERVICE_ENDPOINT", "").strip()
    if not endpoint:
        raise RuntimeError("DEMO_SERVICE_ENDPOINT environment variable is required")
    print("Demo endpoint configured; no network request is made.")


if __name__ == "__main__":
    main()
