"""Run: python -m demo_backend.export_openapi [--url http://127.0.0.1:9000]."""

import argparse
import json
from pathlib import Path

import httpx

from demo_backend.main import app


def export_openapi(url: str | None = None) -> Path:
    if url:
        response = httpx.get(f"{url.rstrip('/')}/openapi.json", timeout=10)
        response.raise_for_status()
        document = response.json()
    else:
        document = app.openapi()
    destination = Path(__file__).with_name("openapi.json")
    destination.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url")
    print(export_openapi(parser.parse_args().url))
