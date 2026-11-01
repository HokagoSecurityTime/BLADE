"""Fetch pinned external evidence without executing or modifying upstream code."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datasets/blade/raw/paired_policy_v1"
SOURCES = {
    "realworld_django": ("gothinkster/django-realworld-example-app", "29c9d42831fa0cfc5a4aa7561f674396eacf20a2", [
        "conduit/apps/articles/views.py", "conduit/apps/articles/urls.py",
        "conduit/apps/authentication/views.py", "conduit/settings.py", "README.md",
        "conduit/apps/articles/serializers.py", "requirements.txt"]),
    "realworld_spec": ("gothinkster/realworld", "ebbcdeb8d55b42a3a613c787560498b8ef10003f", [
        "specs/api/openapi.yml", "specs/api/hurl/errors_authorization.hurl",
        "specs/api/hurl/articles.hurl", "README.md"]),
}


def main():
    manifest_path = OUT / "manifest.json"
    old = json.loads(manifest_path.read_text(encoding="utf8")) if manifest_path.exists() else []
    bypath = {r["path"]:r for r in old}
    expected = set()
    for name, (repo, sha, paths) in SOURCES.items():
        for file in paths:
            relative = name + "/" + file
            expected.add(relative)
            target = OUT / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(urllib.request.urlopen(
                    f"https://raw.githubusercontent.com/{repo}/{sha}/{file}", timeout=60).read())
            record = dict(path=relative, repository=repo, commit=sha,
                          sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            if relative in bypath:
                assert record == bypath[relative], relative
            else:
                old.append(record); bypath[relative] = record
    assert set(bypath) == expected
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps(old, indent=2), encoding="utf8")
    print("Verified pinned evidence files:", len(old))


if __name__ == "__main__":
    main()
