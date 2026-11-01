#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
# Git Bash must leave the Linux container path unchanged.
MSYS_NO_PATHCONV=1 docker compose exec -T admin-api python /app/scripts/demo.py
