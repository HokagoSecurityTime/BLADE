"""Fetch pinned WFD sources for static analysis only."""
import concurrent.futures
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datasets/blade/raw/source_pilot_wfd"
SHA = "915859080da033fc36feae54bab3ad4a7b04e872"
SERVICES = ["blogapi", "features-service", "user-management"]


def main():
    tree = json.load(urllib.request.urlopen(
        f"https://api.github.com/repos/WebFuzzing/Dataset/git/trees/{SHA}?recursive=1"))
    assert not tree.get("truncated")
    paths = [x["path"] for x in tree["tree"] if x["type"] == "blob" and (
        x["path"] in ["README.md", "LICENSE"] or
        any(x["path"] == f"openapi-swagger/{s}.json" or
            (x["path"].startswith(f"jdk_8_maven/cs/rest/original/{s}/") and
             ("/src/main/" in x["path"] and x["path"].endswith(".java") or
              Path(x["path"]).name.lower().startswith(("license", "readme"))))
            for s in SERVICES))]
    OUT.mkdir(parents=True, exist_ok=True)
    def fetch(path):
        dest = OUT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            data = urllib.request.urlopen(
                f"https://raw.githubusercontent.com/WebFuzzing/Dataset/{SHA}/{path}", timeout=60).read()
            dest.write_bytes(data)
        return dict(path=path, sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        files = list(pool.map(fetch, paths))
    (OUT / "manifest.json").write_text(json.dumps(dict(repository="WebFuzzing/Dataset",
        commit=SHA, services=SERVICES, files=files, executed_source=False), indent=2), encoding="utf8")
    print(f"Downloaded {len(files)} files")


if __name__ == "__main__":
    main()
